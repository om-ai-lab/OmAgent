from pathlib import Path
from typing import List

from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.utils.registry import registry
from omagent_core.models.llms.schemas import Message, Content
from omagent_core.utils.general import encode_image
from omagent_core.models.llms.prompt.parser import StrParser
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.container import container
from omagent_core.models.llms.prompt.prompt import PromptTemplate
from pydantic import Field
from typing import List
import re
# from .prompts import *
# from .utils import *

CURRENT_PATH = Path(__file__).parents[0]

def get_current_numbers(y: str) -> str:
    last_line = y.strip().split('\n')[-1]
    return last_line.split('left: ')[-1].split(')')[0]

def value_outputs_unwrap(x: str, y: str, value_outputs: list) -> float:
    if len(y.strip().split('\n')) == 4 and 'answer' not in y.lower():
        return 0
    value_names = [_.split('\n')[-1].lower() for _ in value_outputs]
    value_map = {'impossible': 0.001, 'likely': 1, 'sure': 20}  # TODO: ad hoc
    value = sum(value * value_names.count(name) for name, value in value_map.items())
    return value

def vote_outputs_unwrap(vote_outputs: list, n_candidates: int) -> list:
    vote_results = [0] * n_candidates
    for vote_output in vote_outputs:
        pattern = r".*best choice is .*(\d+).*"
        match = re.match(pattern, vote_output, re.DOTALL)
        if match:
            vote = int(match.groups()[0]) - 1
            if vote in range(n_candidates):
                vote_results[vote] += 1
        else:
            print(f'vote no match: {[vote_output]}')
    return vote_results

def get_word(key, board):
    if key.startswith('h'):
        row_index = int(key[1:]) - 1
        return "".join(board[row_index])
    else:
        col_index = int(key[1:]) - 1
        return "".join([row[col_index] for row in board])

def set_word(text, data_input):
    if text == "":
        return data_input
    split_text = text.split('. ')
    
    key = split_text[0]
    word = split_text[1]
    if key in data_input['unfilled']:
        data_input['unfilled'].remove(key)
        data_input['filled'].append(key)
    elif key in data_input['filled']:
        data_input['filled'].remove(key)
        data_input['changed'].append(key)
    
    changed_key = set()
    if key.startswith('h'):
        row_index = int(key[1:]) - 1
        for i, w in enumerate(word):
            if data_input['board'][row_index][i] != '_':
                changed_key.add(f'v{i+1}')
            data_input['board'][row_index][i] = w
                
    else:
        col_index = int(key[1:]) - 1
        for i, w in enumerate(word):
            if data_input['board'][i][col_index] != '_':
                changed_key.add(f'h{i+1}')
            data_input['board'][i][col_index] = w
    
    for key in changed_key:
        if key in data_input['filled']:
            data_input['filled'].remove(key)
            data_input['changed'].append(key)
            
    return data_input



def get_lines(data_input):
    lines = []
    for key, value in data_input['clues'].items():
        word = get_word(key, data_input['board'])
        if word.count('_') >= 4: continue
        letters = ' '.join(word.lower())
        lines.append(f"{value}: {letters}")
    return lines


@registry.register_worker()
class StateEvaluator(BaseWorker, BaseLLMBackend):
    llm: OpenaiGPTLLM
    
    prompts: List[PromptTemplate] = Field(
        default=[
            # PromptTemplate.from_file(
            #     CURRENT_PATH.joinpath("sys_prompt.prompt"), role="system"
            # ),
            # PromptTemplate.from_file(
            #     CURRENT_PATH.joinpath("user_prompt.prompt"), role="user"
            # ),
            # PromptTemplate.from_file(
            #     CURRENT_PATH.joinpath("text.prompt"), role="user"
            # ),
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("crosswords.prompt"), role="user"
            ),
        ]
    )
    
    def _run(self, *args, **kwargs):
        thought_tree = self.stm(self.workflow_instance_id)['thought_tree']
        current_depth = self.stm(self.workflow_instance_id)['current_depth']
        nodes_at_depth = thought_tree.get_nodes_at_depth(current_depth)
        method_evaluate = self.stm(self.workflow_instance_id)['tot_parameters'].get('method_evaluate', None)

        task = self.stm(self.workflow_instance_id)['tot_parameters'].get('task', None)


        if task == "crosswords":
            count = {'sure': 0, 'maybe': 0, 'impossible': 0}
            current_node_id = self.stm(self.workflow_instance_id)['current_node_id']
            
            # search_path = self.stm(self.workflow_instance_id)['search_path']
            current_path = thought_tree.get_current_path(current_node_id, return_ids=True)
            
            print('-'*100)
            print(current_node_id)
            # print(search_path)
            print(current_path)
            print('-'*100)
            crosswords_env = self.stm(self.workflow_instance_id)['crosswords_env']
            for node_id in current_path:
                node = thought_tree.nodes[node_id]
                set_word(node.content, crosswords_env)
            print(crosswords_env)
            print(crosswords_env['board'])
            lines = get_lines(crosswords_env)
            print(lines)
            for line in lines:
                print(line)
                response = self.simple_infer(input=line)["choices"][0]["message"]["content"]
                print(response)
                res = response.split('\n')[-1].strip()
                if res in count: count[res] += 1
                print(res)
                print(count)
                print('-'*100)
                thought_tree.update_node_value(current_node_id, None, count)

            
            # if count['impossible'] > 1:
            #     prune_id = current_node_id
            #     current_node_id = thought_tree.get_parent(current_node_id)
            #     thought_tree.prune(prune_id)
            #     self.stm(self.workflow_instance_id)['current_node_id'] = current_node_id
            #     self.stm(self.workflow_instance_id)['current_depth'] = current_depth - 1
            #     self.stm(self.workflow_instance_id)['search_path'] = search_path[:-1]
            #     self.stm(self.workflow_instance_id)['thought_tree'] = thought_tree
                # return
            
        
        else:
            if method_evaluate == "value":
                n_evaluate_sample = self.stm(self.workflow_instance_id)['tot_parameters'].get('n_evaluate_sample', None)
                for node in nodes_at_depth:
                    current_numbers = get_current_numbers(node.content)
                    value_outputs = []
                    for i in range(n_evaluate_sample):
                        response = self.simple_infer(input=current_numbers)["choices"][0]["message"]["content"]
                    value_outputs.append(response)
                value = value_outputs_unwrap(x=thought_tree.nodes[node.parent_id].content, y=node.content, value_outputs=value_outputs)
                node.bfs_value = value
            # print_format += f"State: {node.content}\nValue: {value}\n"
            if method_evaluate == "vote":
                choices = ""
                n_evaluate_sample = self.stm(self.workflow_instance_id)['tot_parameters'].get('n_evaluate_sample', None)
                id_to_node = {}
                for index, node in enumerate(nodes_at_depth):
                    choices += f"Choice {index}: {node.content}\n"
                    id_to_node[index] = node.id
                    # current_numbers = get_current_numbers(node.content)
                vote_outputs = []
                for i in range(n_evaluate_sample):
                    response = self.simple_infer(choices=choices)["choices"][0]["message"]["content"]
                    vote_outputs.append(response)
                print('-'*100)
                print(vote_outputs)
                print('-'*100)
                vote_results = vote_outputs_unwrap(vote_outputs=vote_outputs, n_candidates=len(nodes_at_depth))
                for index, res in enumerate(vote_results):
                    thought_tree.update_node_value(id_to_node[index], res, None)
            # node.value = vote_results
        thought_tree_dict = thought_tree.thought_tree_to_dict()
        for key, value in thought_tree_dict.items():
            print(f"Node ID: {key}, Value: {value}")
        
        self.stm(self.workflow_instance_id)['thought_tree'] = thought_tree
        # pass
    
    
    
# @registry.register_worker()
# class StateEvaluation(BaseWorker, BaseLLMBackend):
#     llm: OpenaiGPTLLM

#     def _run(self, *args, **kwargs):
#         assert self.stm(self.workflow_instance_id).get('all_trajectories', None) is not None
#         all_trajectories = self.stm(self.workflow_instance_id)['all_trajectories']
#         data_input = self.stm(self.workflow_instance_id)['data_input']
#         values = []
#         local_value_cache = {}

#         task = self.stm(self.workflow_instance_id)['task']
#         self.prompts = self.set_prompts([CURRENT_PATH.joinpath(f'prompts/{task}/value_prompt.prompt')])

#         # Only for game24. If we implement more tasks future, this function should be rewritten.
#         def get_value(x, y, n_evaluate_sample):
#             current_numbers = get_current_numbers(y)
#             value_outputs = []
#             for i in range(n_evaluate_sample):
#                 value_response = self.simple_infer(input=current_numbers)["choices"][0]["message"]["content"]
#                 value_outputs.append(value_response)
#             value = value_outputs_unwrap(x, y, value_outputs)
#             # For debug
#             # self.callback.send_answer(self.workflow_instance_id, msg=f"\n{y}\nSocre: {value}")
#             return value

#         for trajectory in all_trajectories:  # each partial output
#             if trajectory in local_value_cache:  # avoid duplicate candidates
#                 value = local_value_cache[trajectory]
#             else:    
#                 value = get_value(x=data_input, y=trajectory, n_evaluate_sample=3)
#                 local_value_cache[trajectory] = value
#             values.append(value)
#         self.stm(self.workflow_instance_id)['values'] = values
