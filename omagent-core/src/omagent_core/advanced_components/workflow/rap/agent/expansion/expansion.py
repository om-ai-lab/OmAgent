from pathlib import Path
from typing import List, Optional
import re
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.models.llms.prompt import PromptTemplate
from omagent_core.utils.registry import registry
from pydantic import Field
from collections import defaultdict
from ...schemas.rap_structure import Node

CURRENT_PATH = Path(__file__).parents[0]

@registry.register_worker()
class Expansion(BaseLLMBackend, BaseWorker):
    """Expansion worker that implements MCTS expansion phase"""

    def reset_max_tokens(self):
        self.llm.max_tokens = 2048

    def get_actions_math(self, node: Node, path: List[Node]):
        task = self.stm(self.workflow_instance_id)['task']
        question = self.stm(self.workflow_instance_id)['tree'].data_input
        qid = self.n_shot + 1
        question_info = f"Question {qid}: {question}\n"
        
        for i, n in enumerate(path):
            if i == 0:
                continue
            question_info += f"Question {qid}.{i}: {n.action}\n"
            question_info += f"Answer {qid}.{i}: {n.state}\n"
        
        question_info += f"Question {qid}.{len(path)}:"
        self.prompts = self.set_prompts([CURRENT_PATH.joinpath(f'prompts/{task}/ic_examples.prompt')])
        self.llm.n = self.sub_question_gen_num
        responses = self.simple_infer(input=question_info)["choices"]
        sub_questions = [r["message"]["content"].split('\n')[0].strip() for r in responses]
        sub_questions = [s.replace(f"Question {qid}.{len(path)}: ", "") for s in sub_questions]
        self.llm.n = 1

        self.callback.send_answer(self.workflow_instance_id, msg='\n'.join(sub_questions))
        return list(set(sub_questions))  # deduplicate
    
    def get_action_reward_math(self, action, path: List[Node]):
        task = self.stm(self.workflow_instance_id)['task']
        question = self.stm(self.workflow_instance_id)['tree'].data_input
        qid = self.n_shot + 1
        question_info = f"Question {qid}: {question}\n"
        for i, n in enumerate(path):
            if i==0:
                continue
            question_info += f"Question {qid}.{i}: {n.action}\n"
        question_info += f"New question {qid}.{len(path)+1}: {action}"
        self.llm.max_tokens = 1
        # Get YES_SAMPLE_NUM responses in one API call
        # In RAP paper, it calculate the logits ratio between Yes and No just like ZoomEye
        # Since OpenAI's API cannot return logits, I use this approach to replace the original computation method.
        self.prompts = self.set_prompts([CURRENT_PATH.joinpath(f'prompts/{task}/action_reward.prompt')])
        # Generate YES_SAMPLE_NUM responses in one API call
        self.llm.n = self.yes_sample_num
        responses = self.simple_infer(input=question_info)["choices"]
        responses = [r["message"]["content"] for r in responses]
        self.llm.n = 1
        # For debug
        self.callback.send_answer(self.workflow_instance_id, msg='\n'.join(responses))
        yes_ratio = sum(["Yes" in x for x in responses]) / self.yes_sample_num
        self.reset_max_tokens()
        return yes_ratio, {"r_useful": yes_ratio}
    
    def get_state_math(self, action, path):
        task = self.stm(self.workflow_instance_id)['task']
        question = self.stm(self.workflow_instance_id)['tree'].data_input
        qid = self.n_shot + 1
        question_info = f"Question {qid}: {question}\n"
        for i, n in enumerate(path):
            if i==0:
                continue
            if i==len(path) - 1:
                break
            question_info += f"Question {qid}.{i}: {n.action}\n"
            question_info += f"Answer {qid}.{i}: {n.state}"
        question_info += f"Question {qid}.{len(path) - 1}: {n.action}\n"
        question_info += f"Answer {qid}.{len(path) - 1}:"

        force = False
        if path[-1].depth >= self.depth_limit:
            # Answer by force
            question_info += " Now we can answer the question."
            force = True

        self.prompts = self.set_prompts([CURRENT_PATH.joinpath(f'prompts/{task}/ic_examples.prompt')])
        def retrieve_answer(output: str) -> Optional[str]:
            match = re.match(r'.*The answer is .*?([ $.0-9,\-=]+).*\..*', output)
            if match is None:
                return None
            answer = match[1].replace(',', '').replace('$', '').replace(' ', '')
            if '=' in answer:
                answer = answer[answer.rindex('=') + 1:]
            return answer
        # Answering sub_question
        answer_dict = defaultdict(list)  # map from answer to list of thoughts
        result = ""
        # For debug
        self.callback.send_answer(self.workflow_instance_id, msg=question_info)
        # Generate ANSWER_GEN_NUM answers in one API call
        self.llm.n = self.answer_gen_num
        responses = self.simple_infer(input=question_info)["choices"]
        outputs = [r["message"]["content"].split('\n')[0].strip() for r in responses]
        self.llm.n = 1
        for output in outputs:
            self.callback.send_answer(self.workflow_instance_id, msg=output)
            answer = retrieve_answer(output)
            answer_dict[answer].append(output)
        if len(answer_dict) == 0:
            print("Warning: no answer found")
            confidence, answer = 0, result
        else:
            sorted_answer_dict = sorted(answer_dict.items(), key=lambda p: len(p[1]), reverse=True)
            max_answer = sorted_answer_dict[0]
            max_answer_output_list = max_answer[1]
            max_len = len(max_answer_output_list)
            answer = max_answer_output_list[0]  # Here we simply choose the first appearance of the answer
            confidence = max_len / sum(len(v) for v in answer_dict.values())
        
        state = answer
        if force:
            state = "Now we can answer the question. " + state
        aux = {'confidence': confidence}
        return state, aux

    def cal_reward(self, r_useful, confidence=None):
        if confidence is None:
            confidence = 1
        return (r_useful ** 0.8) * confidence ** (1 - 0.8), {'r_useful': r_useful, 'r_conf': confidence}

    def _run(self, *args, **kwargs):
        # Define hyperparameters with defaults from rap_workers.py
        self.n_shot = kwargs.get('n_shot', 4)  # number of in-context examples
        self.depth_limit = kwargs.get('depth_limit', 4)  # avoiding too deep search
        self.sub_question_gen_num = kwargs.get('sub_question_gen_num', 3)
        self.yes_sample_num = kwargs.get('yes_sample_num', 10)
        self.answer_gen_num = kwargs.get('answer_gen_num', 5)

        path = self.stm(self.workflow_instance_id)['selected_path']
        node = path[-1]
        task = self.stm(self.workflow_instance_id)['task']

        # Get state if needed
        if node.state is None:
            get_state = getattr(self, f"get_state_{task}", None)
            state, aux = get_state(node.action, path)
            node.state = state
            node.reward, node.reward_details = self.cal_reward(**node.fast_reward_details, **aux)
            if "Now we can answer" in state:
                node.is_terminal = True

        # Expand if needed
        if node.children is None and not node.is_terminal:
            children = []
            get_actions = getattr(self, f"get_actions_{task}", None)
            actions = get_actions(node, path)

            # Create child nodes
            for action in actions:
                get_action_reward = getattr(self, f"get_action_reward_{task}", None)
                fast_reward, fast_reward_details = get_action_reward(action, path)
                child = Node(state=None, action=action, parent=node, 
                           fast_reward=fast_reward, fast_reward_details=fast_reward_details)
                children.append(child)
            
            node.children = children
            
        self.stm(self.workflow_instance_id)['selected_path'] = path

        return {} 