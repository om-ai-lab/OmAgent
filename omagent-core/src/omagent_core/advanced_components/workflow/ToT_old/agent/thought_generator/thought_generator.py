import json
from pathlib import Path
import re
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
from omagent_core.advanced_components.workflow.ToT.schemas.ToT_structure import ThoughtTree
# from .prompts import *
# from .utils import *

CURRENT_PATH = Path(__file__).parents[0]

@registry.register_worker()
class ThoughtGenerator(BaseWorker, BaseLLMBackend):
# class ThoughtGenerator(BaseWorker):
    
    llm: OpenaiGPTLLM
    
    # prompts: List[PromptTemplate] = Field(default=[])
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("math_propose_sys.prompt"), role="system"
            ),
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("math_propose_user.prompt"), role="user"
            ),
        ]
    )
    
    generation_value_dict: dict = {
        "no_value": 0.0,
        "certain": 1,
        "high": 0.8,
        "medium": 0.5,
        "low": 0.2,
    }
    # print(prompts)

    
    # def _run(self, fun_path: str = None, *args, **kwargs):
    def _run(self, *args, **kwargs):
        
        
        thought_tree = self.stm(self.workflow_instance_id)['thought_tree']
        current_depth = self.stm(self.workflow_instance_id)['current_depth']
        current_node_id = self.stm(self.workflow_instance_id)['current_node_id']
        
        search_type = self.stm(self.workflow_instance_id)['search_type']

        generation_n = self.params['generation_n']
        generation_type = self.params['generation_type']
        if generation_type not in ["sample", "propose"]:
            raise ValueError(f"Invalid generation type: {generation_type}") 
        
        # use_default_prompt = self.use_default_prompt
        # if self.use_default_prompt:
        #     self.prompts = [
        #         PromptTemplate.from_file(
        #             CURRENT_PATH.joinpath(f"{generation_type}_sys.prompt"), role="system"
        #         ),
        #         PromptTemplate.from_file(
        #             CURRENT_PATH.joinpath(f"{generation_type}_user.prompt"), role="user"
        #         ),
        #     ]
        #     # print(self.prompts)
        # else:
        #     print('not use default prompt')
        #     # print(self.prompts)
        

        
        # print('-----'*10+'prompt_set'+'-----'*10)
        # print(self.prompts)
        # # print(self.prompt_elements)
        # print('-----'*10+'prompt_set'+'-----'*10)
        
        do_generate = True
        if search_type == "bfs":
            current_nodes = thought_tree.get_nodes_at_depth(current_depth)
        elif search_type == "dfs":
            current_node_children = thought_tree.get_childrens(current_node_id)
            if current_node_children != []:
                current_node_id = thought_tree.get_top_n_score_nodes(node_id=current_node_id, sort_region='children', score_type='generation', n=1, return_ids=True)[0]
                do_generate = False
            else:
                current_nodes = [thought_tree.nodes[current_node_id]]
        else:
            raise ValueError(f"Invalid search type: {search_type}")
        
        

        
        if generation_type == "sample" and do_generate:

            for node in current_nodes:
                for i in range(generation_n):
                    
                    response = self.simple_infer(input=node.infer_input)["choices"][0]["message"]["content"]
                    contents = json_repair.loads(response)
                    
                    if contents.get('llm_response') and contents.get('next_input'):
                        if contents.get('value'):
                            generation_value = self.generation_value_dict[contents['value']]    
                        else:
                            generation_value = 0.0
                        thought_tree.add_node(content=contents['llm_response'], infer_input=contents['next_input'], parent_id=node.id, generation_value=generation_value)

                    
        elif generation_type == "propose" and do_generate:
            for node in current_nodes:
                proposals = {}
                for i in range(generation_n):
                    response = self.simple_infer(input=node.infer_input)["choices"][0]["message"]["content"]
                    # print('--'*10)
                    self.callback.info(
                        agent_id=self.workflow_instance_id,
                        progress=f"Thought Generator",
                        message=f'response: {response}'
                    )
                    # print(type(response))
                    contents = json_repair.loads(response)
                    if contents.get('llm_response') and contents.get('next_input'):
                        if contents.get('value'):
                            values = contents['value']
                        else:
                            values = ["no_value" for _ in range(len(contents['llm_response']))]
                        for llm_response, next_input, generation_value in zip(contents['llm_response'], contents['next_input'], values):
                            if llm_response not in proposals:
                                proposals[llm_response] = {
                                    "llm_response": llm_response,
                                    "next_input": next_input,
                                    "generation_value": self.generation_value_dict[generation_value]
                                }
                            else:
                                proposals[llm_response]['generation_value'] += self.generation_value_dict[generation_value]
                for key, proposal in proposals.items():
                    thought_tree.add_node(content=proposal['llm_response'], infer_input=proposal['next_input'], parent_id=node.id, generation_value=proposal['generation_value'])
        

                    
                    
        before_thought_tree = self.stm(self.workflow_instance_id)['thought_tree']
        self.stm(self.workflow_instance_id)['thought_tree'] = thought_tree
        
        self.stm(self.workflow_instance_id)['current_depth'] = current_depth + 1
        
        before_current_node_id = self.stm(self.workflow_instance_id)['current_node_id']
        self.stm(self.workflow_instance_id)['current_node_id'] = current_node_id
        
        # print('--show--stm--'*20)
        # print(f'before thought_tree: {before_thought_tree.nodes}')
        # print(f'before current_depth: {current_depth}')
        # print(f'before current_node_id: {before_current_node_id}')
        # print('--------------'*20)
        # print(f'after thought_tree: {self.stm(self.workflow_instance_id)["thought_tree"].nodes}')
        # print(f'after current_depth: {self.stm(self.workflow_instance_id)["current_depth"]}')
        # print(f'after current_node_id: {self.stm(self.workflow_instance_id)["current_node_id"]}')
        # print('--show--stm--'*20)
        
        
        
        # # Save thought tree to a json file
        # thought_tree_dict = thought_tree.thought_tree_to_dict()
        # self.callback.info(
        #     agent_id=self.workflow_instance_id,
        #     progress=f"Thought Generator",
        #     message=f'after thought_tree: {thought_tree_dict}'
        # )
        # thought_tree_dict['prompt'] = str(self.prompts)
        # record_name = f'math_tot_generation_tree_{search_type}_{generation_type}-3_sys_0.json'
        # whole_path = CURRENT_PATH.joinpath('/data9/myb/OmAgent-myb/OmAgent/test_record/ToT/thought_generator', record_name)
        # with open(whole_path, 'w') as f:
        #     json.dump(thought_tree_dict, f, indent=4)

