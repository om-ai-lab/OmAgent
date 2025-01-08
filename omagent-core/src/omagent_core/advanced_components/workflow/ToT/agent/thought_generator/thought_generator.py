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
    examples: str = """1.
Input: 4 4 6 8
Output: {
    "llm_response": ["4 * 4 = 16 (left: 6 8 16)", "4 / 4 = 1 (left: 6 8 1)", "4 + 4 = 8 (left: 6 8 8)", "4 - 4 = 0 (left: 6 8 0)", "6 * 4 = 24 (left: 4 4 24)", "6 / 4 = 1.5 (left: 4 4 1.5)", "6 + 4 = 10 (left: 4 4 10)", "6 - 4 = 2 (left: 4 4 2)", "8 * 4 = 32 (left: 4 4 32)", "8 / 4 = 2 (left: 4 4 2)", "8 + 4 = 12 (left: 4 4 12)", "8 - 4 = 4 (left: 4 4 4)"],
    "next_input": ["6 8 16", "6 8 1", "6 8 8", "6 8 0", "4 4 24", "4 4 1.5", "4 4 10", "4 4 2", "4 4 32", "4 4 2", "4 4 12", "4 4 4"],
}

2.
Input: 2 8 8 14
Output: {
    "llm_response": ["2 + 8 = 10 (left: 8 10 14)", "2 - 8 = -6 (left: 8 -6 14)", "2 * 8 = 16 (left: 8 10 16)", "2 / 8 = 0.25 (left: 8 10 0.25)", "8 + 8 = 16 (left: 2 8 16)", "8 - 8 = 0 (left: 2 8 0)", "8 * 8 = 64 (left: 2 8 64)", "8 / 8 = 1 (left: 2 8 1)", "14 + 2 = 16 (left: 8 8 16)", "14 - 2 = 12 (left: 8 8 12)", "14 * 2 = 28 (left: 8 8 28)", "14 / 2 = 7 (left: 8 8 7)"],
    "next_input": ["8 10 14", "8 -6 14", "8 10 16", "8 10 0.25", "2 8 16", "2 8 0", "2 8 64", "2 8 1", "8 8 16", "8 8 12", "8 8 28", "8 8 7"],
}

Input: 6 8 16
Output: {
    "llm_response": ["6 + 8 = 14 (left: 16 14)", "6 - 8 = -2 (left: 16 -2)", "6 * 8 = 48 (left: 16 48)", "6 / 8 = 0.75 (left: 16 0.75)", "8 + 6 = 14 (left: 16 14)", "8 - 6 = 2 (left: 16 2)", "8 * 6 = 48 (left: 16 48)", "8 / 6 = 1.33 (left: 16 1.33)", "16 + 6 = 22 (left: 8 16)", "16 - 6 = 10 (left: 8 10)", "16 * 6 = 96 (left: 8 96)", "16 / 6 = 2.67 (left: 8 2.67)"],
    "next_input": ["16 14", "16 -2", "16 48", "16 0.75", "8 14", "8 2", "8 48", "8 1.33", "8 16", "8 10", "8 96", "8 2.67"],
}
    """
    # prompts: List[PromptTemplate] = Field(default=[])
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("sys_prompt.prompt"), role="system"
            ),
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("user_prompt.prompt"), role="user"
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
        
        
        if do_generate:
            for node in current_nodes:
                proposals = {}
                for i in range(generation_n):
                    if node.next_step_input is None:
                        next_step_input = thought_tree.get_current_path_contents(node.id)
                    else:
                        next_step_input = node.next_step_input
                        
                    payload = {
                        "examples": self.examples,
                        "task": self.stm(self.workflow_instance_id)['task'],
                        "input": next_step_input,

                    }
                    chat_complete_res = self.infer(input_list=[payload])
                    response = chat_complete_res[0]["choices"][0]["message"].get("content")
                    response = json_repair.loads(response)

                    self.callback.info(
                        agent_id=self.workflow_instance_id,
                        progress=f"Thought Generator",
                        message=f'response: {response}'
                    )

                    if response.get('llm_response'):

                        for index, llm_response in enumerate(response['llm_response']):
                            next_step_input = response.get('next_step_input', None)[index]
                            value = response.get('value', "no_value")[index]
                            thought_tree.add_node(content=llm_response, infer_input=next_step_input, parent_id=node.id, generation_value=value)
                            
        before_thought_tree = self.stm(self.workflow_instance_id)['thought_tree']
        self.stm(self.workflow_instance_id)['thought_tree'] = thought_tree
        
        self.stm(self.workflow_instance_id)['current_depth'] = current_depth + 1
        
        before_current_node_id = self.stm(self.workflow_instance_id)['current_node_id']
        self.stm(self.workflow_instance_id)['current_node_id'] = current_node_id
        
        print('--show--stm--'*20)
        print(f'before thought_tree: {before_thought_tree.nodes}')
        print(f'before current_depth: {current_depth}')
        print(f'before current_node_id: {before_current_node_id}')
        print('--------------'*20)
        print(f'after thought_tree: {self.stm(self.workflow_instance_id)["thought_tree"].nodes}')
        print(f'after current_depth: {self.stm(self.workflow_instance_id)["current_depth"]}')
        print(f'after current_node_id: {self.stm(self.workflow_instance_id)["current_node_id"]}')
        print('--show--stm--'*20)
        
        
        
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

