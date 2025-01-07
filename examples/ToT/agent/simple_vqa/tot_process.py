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
from .prompts import *
from .utils import *

CURRENT_PATH = Path(__file__).parents[0]

@registry.register_worker()
class NextStatePrediction(BaseWorker, BaseLLMBackend):

    llm: OpenaiGPTLLM

    def _run(self, *args, **kwargs):
        assert self.stm(self.workflow_instance_id).get('data_input', None) is not None and self.stm(self.workflow_instance_id).get('previous_trajectories', None) is not None
        
        data_input = self.stm(self.workflow_instance_id)['data_input']
        previous_trajectories = self.stm(self.workflow_instance_id)['previous_trajectories']
        task = self.stm(self.workflow_instance_id)['task']

        all_trajectories = []
        # Set prompts for next state prediction 
        self.prompts = self.set_prompts([CURRENT_PATH.joinpath(f'prompts/{task}/propose_prompt.prompt')])
        for pt in previous_trajectories:
            
            input_next_state_prediction = propose_prompt_wrap(x=data_input, y=pt)
            next_states_response = self.simple_infer(input=input_next_state_prediction)["choices"][0]["message"]["content"]

            next_states = next_states_response.split('\n')

            full_trajectories = [pt + next_state + '\n' for next_state in next_states]
            all_trajectories.extend(full_trajectories)
        
        self.stm(self.workflow_instance_id)['all_trajectories'] = all_trajectories
        
        info_str = "\n"
        info_str += '\n'.join(all_trajectories)
        # For debug
        self.callback.send_answer(self.workflow_instance_id, msg=info_str)

        return next_states_response
    
@registry.register_worker()
class StateEvaluation(BaseWorker, BaseLLMBackend):
    llm: OpenaiGPTLLM

    def _run(self, *args, **kwargs):
        assert self.stm(self.workflow_instance_id).get('all_trajectories', None) is not None
        all_trajectories = self.stm(self.workflow_instance_id)['all_trajectories']
        data_input = self.stm(self.workflow_instance_id)['data_input']
        values = []
        local_value_cache = {}

        task = self.stm(self.workflow_instance_id)['task']
        self.prompts = self.set_prompts([CURRENT_PATH.joinpath(f'prompts/{task}/value_prompt.prompt')])

        # Only for game24. If we implement more tasks future, this function should be rewritten.
        def get_value(x, y, n_evaluate_sample):
            current_numbers = get_current_numbers(y)
            value_outputs = []
            for i in range(n_evaluate_sample):
                value_response = self.simple_infer(input=current_numbers)["choices"][0]["message"]["content"]
                value_outputs.append(value_response)
            value = value_outputs_unwrap(x, y, value_outputs)
            # For debug
            # self.callback.send_answer(self.workflow_instance_id, msg=f"\n{y}\nSocre: {value}")
            return value

        for trajectory in all_trajectories:  # each partial output
            if trajectory in local_value_cache:  # avoid duplicate candidates
                value = local_value_cache[trajectory]
            else:    
                value = get_value(x=data_input, y=trajectory, n_evaluate_sample=3)
                local_value_cache[trajectory] = value
            values.append(value)
        self.stm(self.workflow_instance_id)['values'] = values


@registry.register_worker()
class StateSelection(BaseWorker, BaseLLMBackend):

    llm: OpenaiGPTLLM

    def _run(self, *args, **kwargs):
        assert self.stm(self.workflow_instance_id).get('all_trajectories', None) is not None and self.stm(self.workflow_instance_id).get('values', None) is not None
        all_trajectories = self.stm(self.workflow_instance_id)['all_trajectories']
        values = self.stm(self.workflow_instance_id)['values']
        
        ids = list(range(len(all_trajectories)))
        n_select_sample = 2
        select_ids = sorted(ids, key=lambda x: values[x], reverse=True)[:n_select_sample]
        selected_trajectories = [all_trajectories[select_id] for select_id in select_ids]
        sorted_values = [values[select_id] for select_id in select_ids]
        
        info_str = "\n"
        for t, v in zip(selected_trajectories, sorted_values):
            info_str += t
            info_str += f'Score: {v}'
            info_str += '\n'
        # For debug
        self.callback.send_answer(self.workflow_instance_id, msg=info_str)

        self.stm(self.workflow_instance_id)['previous_trajectories'] = selected_trajectories

        if self.stm(self.workflow_instance_id).get('loop_index', None) is None:
            self.stm(self.workflow_instance_id)['loop_index'] = 0
        self.stm(self.workflow_instance_id)['loop_index'] = self.stm(self.workflow_instance_id)['loop_index'] + 1
        # For debug
        print(111, self.stm(self.workflow_instance_id)['loop_index'])

        return {"loop_index": self.stm(self.workflow_instance_id)['loop_index']}


@registry.register_worker()
class CompletionCheck(BaseWorker, BaseLLMBackend):

    llm: OpenaiGPTLLM

    def _run(self, *args, **kwargs):
        finish = False
        trajectories_this_turn = self.stm(self.workflow_instance_id)['previous_trajectories']

        # Only for game24. If we implement more tasks future, this process should be rewritten.
        for t in trajectories_this_turn:
            current_numbers = get_current_numbers(t)
            # For debug
            print(123, current_numbers)
            if current_numbers == '24':
                finish = True
                self.stm(self.workflow_instance_id)['ans_trajectory'] = t
                break

        if self.stm(self.workflow_instance_id)['loop_index'] >= 4:
            finish = True

        return {"finish": finish}

@registry.register_worker()
class OutputInterface(BaseWorker, BaseLLMBackend):

    llm: OpenaiGPTLLM

    def _run(self, *args, **kwargs):
        if self.stm(self.workflow_instance_id).get('ans_trajectory', None) is not None:
            ans_trajectory = self.stm(self.workflow_instance_id)['ans_trajectory']
            data_input = self.stm(self.workflow_instance_id)['data_input']
            task = self.stm(self.workflow_instance_id)['task']
            self.prompts = self.set_prompts([CURRENT_PATH.joinpath(f'prompts/{task}/cot_prompt.prompt')])
            final_response = self.simple_infer(input=data_input, ans_trajectory=ans_trajectory)["choices"][0]["message"]["content"]
            self.callback.send_answer(self.workflow_instance_id, msg=final_response)
        else:
            self.callback.send_answer(self.workflow_instance_id, msg="I cannot finish this task...")

        return None