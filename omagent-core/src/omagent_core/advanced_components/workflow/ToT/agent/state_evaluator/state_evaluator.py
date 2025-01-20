from pathlib import Path
from typing import List

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
class StateEvaluator(BaseWorker, BaseLLMBackend):
    llm: OpenaiGPTLLM
    
    prompts: List[PromptTemplate] = Field([])
    
    value_dict: dict = {
        "sure": 3,
        "likely": 0.5,
        "impossible": -2,
    }
    
    def _run(self, examples: str, *args, **kwargs):
        thought_tree = self.stm(self.workflow_instance_id)['thought_tree']
        current_depth = self.stm(self.workflow_instance_id)['current_depth']
        current_node_id = self.stm(self.workflow_instance_id)['current_node_id']
        record = self.stm(self.workflow_instance_id)['record']
        evaluation_type = self.params['evaluation_type']
        
        search_type = self.stm(self.workflow_instance_id)['search_type']

        if not self.prompts:
            self.prompts = [
                PromptTemplate.from_file(
                    CURRENT_PATH.joinpath(f"{evaluation_type}_sys.prompt"), role="system"
                ),
                PromptTemplate.from_file(
                    CURRENT_PATH.joinpath(f"{evaluation_type}_user.prompt"), role="user"
                ),
            ]
        
        if search_type == "bfs":
            current_nodes = thought_tree.get_nodes_at_depth(current_depth)
        elif search_type == "dfs":
            current_nodes = [thought_tree.nodes[current_node_id]]
        else:
            raise ValueError(f"Invalid search type: {search_type}")
        
        if examples:
            if evaluation_type == "value":
                few_shots = "You can learn more about how to evaluate the the thought chain from examples below:\n **Examples**:\n" + examples
            elif evaluation_type == "vote":
                few_shots = "You can learn more about how to choose the best thought chain from examples below:\n **Examples**:\n" + examples
        else:
            few_shots = ""

        
        if evaluation_type == "value":
            for node in current_nodes:
                thought_chain = thought_tree.get_current_thought_chain(node.id)
                payload = {
                    "few_shots": few_shots,
                    "problem": self.stm(self.workflow_instance_id)['problem'],
                    "requirements": self.stm(self.workflow_instance_id)['requirements'],
                    "Thought_chain": thought_chain,
                }
                chat_complete_res = self.infer(input_list=[payload])
                
                record['prompt_tokens'] += self.token_usage['prompt_tokens']
                record['completion_tokens'] += self.token_usage['completion_tokens']
                
                self.callback.info(
                    agent_id=self.workflow_instance_id,
                    progress=f"State Evaluator-value usage",
                    message=f'\nuse_tokens: {self.token_usage}'
                )
                
                results = chat_complete_res[0]["choices"]
                for result in results:
                    output = result["message"].get("content") 
                    response = json_repair.loads(output)
                    
                    self.callback.info(
                        agent_id=self.workflow_instance_id,
                        progress=f"State Evaluator-value",
                        message=f"thought_chain: {thought_chain}\nresponse: {response}"
                    )
                    
                    if response.get('value'):
                        value = response.get('value')
                        evaluation_value = self.value_dict.get(value, 0.0)
                        node.value += evaluation_value
                        

                
        elif evaluation_type == "vote":
            
            thought_chains = ""
            index_to_node_id = {}
            for index, node in enumerate(current_nodes):
                index_to_node_id[index+1] = node.id
                thought_chain = thought_tree.get_current_thought_chain(node.id).strip()
                thought_chains += f"Thought chain {index+1}: {thought_chain}\n"

            # print(index_to_node_id)
            
            payload = {
                "few_shots": few_shots,
                "problem": self.stm(self.workflow_instance_id)['problem'],
                "requirements": self.stm(self.workflow_instance_id)['requirements'],
                "thought_chains": thought_chains,
            }
            # chat_complete_res = self.infer(input_list=[payload], best_of=1, n=1)
            chat_complete_res = [self.infer(input_list=[payload], n=1)[0]["choices"][0] for i in range(3)]


            print(chat_complete_res)
            self.callback.info(
                agent_id=self.workflow_instance_id,
                progress=f"State Evaluator-vote usage",
                message=f'\nuse_tokens: {self.token_usage}'
            )
            
            record['prompt_tokens'] += self.token_usage['prompt_tokens']
            record['completion_tokens'] += self.token_usage['completion_tokens']
            
            # results = chat_complete_res[0]["choices"]
            results = chat_complete_res
            print("*"*100)
            print(results)
            print("*"*100)
            for result in results:
                output = result["message"].get("content") 
                response = json_repair.loads(output)
                
                self.callback.info(
                    agent_id=self.workflow_instance_id,
                    progress=f"State Evaluator-vote",
                    message=f"\nthought_chains: {thought_chains}\nresponse: {response}"
                )
                
                
                if response.get('choice'):
                    choice = response['choice']
                    if isinstance(choice, str):
                        choice = int(choice) if choice.isdigit() else 1
                    choice_id = index_to_node_id.get(choice, index_to_node_id[1])
                    thought_tree.nodes[choice_id].value += 1


                     
        else:
            raise ValueError(f"Invalid evaluation type: {evaluation_type}")

        self.stm(self.workflow_instance_id)['thought_tree'] = thought_tree
        self.stm(self.workflow_instance_id)['record'] = record

        # print(record)
