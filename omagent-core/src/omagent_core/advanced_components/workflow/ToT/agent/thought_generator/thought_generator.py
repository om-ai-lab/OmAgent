from pathlib import Path
import json_repair
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.utils.registry import registry
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.models.llms.prompt.prompt import PromptTemplate
from pydantic import Field
from typing import List

CURRENT_PATH = Path(__file__).parents[0]

@registry.register_worker()
class ThoughtGenerator(BaseWorker, BaseLLMBackend):
    
    llm: OpenaiGPTLLM

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

    def _run(self, examples: str, *args, **kwargs):

        thought_tree = self.stm(self.workflow_instance_id)['thought_tree']
        current_depth = self.stm(self.workflow_instance_id)['current_depth']
        current_node_id = self.stm(self.workflow_instance_id)['current_node_id']
        current_step = self.stm(self.workflow_instance_id)['current_step']
        search_type = self.stm(self.workflow_instance_id)['search_type']
        record = self.stm(self.workflow_instance_id)['record']

        do_generate = True
        if search_type == "bfs":
            current_nodes = thought_tree.get_nodes_at_depth(current_depth)
        elif search_type == "dfs":
            current_node_children_ids = thought_tree.get_childrens(current_node_id, return_ids=True)
            if current_node_children_ids:
                current_node_id = current_node_children_ids[0]
                do_generate = False
            else:
                current_nodes = [thought_tree.nodes[current_node_id]]
        else:
            raise ValueError(f"Invalid search type: {search_type}")
        
        if examples:
            few_shots = "You can learn more about how to generate the thought chain for solving the problem following the requirements from examples below:\n **Examples**:\n" + examples
        else:
            few_shots = ""
        
        if do_generate:
            for node in current_nodes:
                previous_thought_chain = thought_tree.get_current_thought_chain(node.id)
                
                payload = {
                    "few_shots": few_shots,
                    "problem": self.stm(self.workflow_instance_id)['problem'],
                    "requirements": self.stm(self.workflow_instance_id)['requirements'],
                    "previous_thought_chain": previous_thought_chain,
                }

                chat_complete_res = self.infer(input_list=[payload])
                results = chat_complete_res[0]["choices"]
                
                record['prompt_tokens'] += self.token_usage['prompt_tokens']
                record['completion_tokens'] += self.token_usage['completion_tokens']
                
                self.callback.info(
                    agent_id=self.workflow_instance_id,
                    progress=f"Thought Generator",
                    message=f'\nuse_tokens: {self.token_usage}'
                )
                
                for result in results:                    
                    output = result["message"].get("content")
                    response = json_repair.loads(output)
                    
                    self.callback.info(
                        agent_id=self.workflow_instance_id,
                        progress=f"Thought Generator",
                        message=f'\nresponse: {response}'
                    )
                    if not isinstance(response, dict):
                        response = {"thoughts": "No response from the model"}
                    if response.get('thoughts'):
                        if not isinstance(response['thoughts'], list):
                            response['thoughts'] = [response['thoughts']]
                        for index, thought in enumerate(response['thoughts']):                            
                            thought_tree.add_node(thought=thought, parent_id=node.id)


                    
        if search_type == "dfs":
            self.stm(self.workflow_instance_id)['current_node_id'] = thought_tree.nodes[current_node_id].children[0]
        
        self.stm(self.workflow_instance_id)['thought_tree'] = thought_tree
        self.stm(self.workflow_instance_id)['current_depth'] = current_depth + 1
        self.stm(self.workflow_instance_id)['current_node_id'] = current_node_id
        self.stm(self.workflow_instance_id)['current_step'] = current_step + 1
        self.stm(self.workflow_instance_id)['record'] = record


        
