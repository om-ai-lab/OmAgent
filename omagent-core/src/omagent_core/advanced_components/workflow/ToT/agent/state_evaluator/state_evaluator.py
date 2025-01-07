from pathlib import Path
from typing import List

import json_repair
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

CURRENT_PATH = Path(__file__).parents[0]\
    

@registry.register_worker()
class StateEvaluator(BaseWorker, BaseLLMBackend):
    llm: OpenaiGPTLLM
    
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("game24_sys_prompt.prompt"), role="system"
            ),
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("game24_user_prompt.prompt"), role="user"
            ),
            # PromptTemplate.from_file(
            #     CURRENT_PATH.joinpath("text.prompt"), role="user"
            # ),
            # PromptTemplate.from_file(
            #     CURRENT_PATH.joinpath("game24.prompt"), role="user"
            # ),
        ]
    )
    value_dict: dict = {
        "sure": 20,
        "likely": 1,
        "impossible": -1,
    }
    
    def _run(self, *args, **kwargs):
        thought_tree = self.stm(self.workflow_instance_id)['thought_tree']
        current_depth = self.stm(self.workflow_instance_id)['current_depth']
        current_node_id = self.stm(self.workflow_instance_id)['current_node_id']
        
        evaluator_parameters = self.stm(self.workflow_instance_id)['evaluator_parameters']
        evaluation_n = evaluator_parameters['evaluation_n']
        evaluation_type = evaluator_parameters['evaluation_type']
        
        search_parameters = self.stm(self.workflow_instance_id)['search_parameters']
        search_type = search_parameters['search_type']
        

        if search_type == "bfs":
            current_nodes = thought_tree.get_nodes_at_depth(current_depth)
            print('-'*100)
            print(len(current_nodes))
            print('-'*100)
        elif search_type == "dfs":
            # current_nodes = thought_tree.get_childrens(current_node_id)
            current_nodes = [thought_tree.nodes[current_node_id]]
        else:
            raise ValueError(f"Invalid search type: {search_type}")
        
        all_evaluation = []
        
        if evaluation_type == "value":
            for node in current_nodes:
                evaluation_value = 0
                for i in range(evaluation_n):
                    response = self.simple_infer(input=node.infer_input)["choices"][0]["message"]["content"]
                    contents = json_repair.loads(response)
                    all_evaluation.append({
                        "input": node.infer_input,
                        "value": contents['value'],
                        "content": contents['llm_response']
                    })
                    evaluation_value += self.value_dict[contents['value']]
                node.evaluation_value = evaluation_value
        elif evaluation_type == "vote":
            
            for i in range(evaluation_n):
                choices = ""
                index_to_node_id = {}
                for index, node in enumerate(current_nodes):
                    index_to_node_id[index] = node.id
                    choices += f"Choice {index}: {node.content}\n"
                response = self.simple_infer(input=choices)["choices"][0]["message"]["content"]
                vote_results = json_repair.loads(response)
                choice = vote_results['choice']
                choice_id = index_to_node_id[choice]
                thought_tree.nodes[choice_id].evaluation_value += 1

        
        self.stm(self.workflow_instance_id)['thought_tree'] = thought_tree
        

        
        print('-'*100)
        print(all_evaluation)
        print('-'*100)


