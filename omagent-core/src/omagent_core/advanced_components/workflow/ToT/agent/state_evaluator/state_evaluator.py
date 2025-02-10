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
    
    """A state evaluation component that assesses the quality of thought chains.
    
    This component is responsible for:
    - Evaluating the quality of generated thought chains
    - Supporting both value-based and voting-based evaluation
    - Managing evaluation scores for different search strategies
    - Integrating LLM feedback into the evaluation process
    """
    
    llm: OpenaiGPTLLM
    prompts: List[PromptTemplate] = Field([])
    
    # Define value mapping for different confidence levels
    value_dict: dict = {
        "sure": 3,
        "likely": 0.5,
        "impossible": -2,
    }
    
    def _run(self, examples: str, *args, **kwargs):
        """Evaluate thought chains and update their scores.

        This method:
        - Retrieves current thought tree state
        - Loads appropriate evaluation prompts
        - Performs either value-based or voting-based evaluation
        - Updates node scores in the thought tree

        Args:
            examples (str): Example evaluations for few-shot learning
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments

        Returns:
            None: Updates are made to shared memory (self.stm)
        """
        
        # Retrieve current state from shared memory
        thought_tree = self.stm(self.workflow_instance_id)['thought_tree']
        current_depth = self.stm(self.workflow_instance_id)['current_depth']
        current_node_id = self.stm(self.workflow_instance_id)['current_node_id']
        evaluation_type = self.params['evaluation_type']
        
        search_type = self.stm(self.workflow_instance_id)['search_type']

        # Load prompts if not already loaded
        if not self.prompts:
            self.prompts = [
                PromptTemplate.from_file(
                    CURRENT_PATH.joinpath(f"{evaluation_type}_sys.prompt"), role="system"
                ),
                PromptTemplate.from_file(
                    CURRENT_PATH.joinpath(f"{evaluation_type}_user.prompt"), role="user"
                ),
            ]
        
        # Determine nodes to evaluate based on search type
        if search_type == "bfs":
            current_nodes = thought_tree.get_nodes_at_depth(current_depth)
        elif search_type == "dfs":
            current_nodes = [thought_tree.nodes[current_node_id]]
        else:
            raise ValueError(f"Invalid search type: {search_type}")
        
        # Prepare few-shot examples if provided
        if examples:
            if evaluation_type == "value":
                few_shots = "You can learn more about how to evaluate the the thought chain from examples below:\n **Examples**:\n" + examples
            elif evaluation_type == "vote":
                few_shots = "You can learn more about how to choose the best thought chain from examples below:\n **Examples**:\n" + examples
        else:
            few_shots = ""

        # Perform value-based evaluation
        if evaluation_type == "value":
            for node in current_nodes:
                thought_chain = thought_tree.get_current_thought_chain(node.id)
                payload = {
                    "few_shots": few_shots,
                    "problem": self.stm(self.workflow_instance_id)['problem'],
                    "requirements": self.stm(self.workflow_instance_id)['requirements'],
                    "Thought_chain": thought_chain,
                }
                # Use N-shot inference if supported
                if hasattr(self, 'support_n') and self.support_n:
                    chat_complete_res = self.infer(input_list=[payload])
                    results = chat_complete_res[0]["choices"]
                else:
                    n = self.llm.n
                    self.llm.n = 1
                    chat_complete_res = [self.infer(input_list=[payload])[0]["choices"][0] for i in range(n)]
                    results = chat_complete_res
                
                # Process each result and update node scores
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
            # Perform voting-based evaluation
            thought_chains = ""
            index_to_node_id = {}
            for index, node in enumerate(current_nodes):
                index_to_node_id[index+1] = node.id
                thought_chain = thought_tree.get_current_thought_chain(node.id).strip()
                thought_chains += f"Thought chain {index+1}: {thought_chain}\n"
            
            # Prepare payload for LLM inference
            payload = {
                "few_shots": few_shots,
                "problem": self.stm(self.workflow_instance_id)['problem'],
                "requirements": self.stm(self.workflow_instance_id)['requirements'],
                "thought_chains": thought_chains,
            }
            # Use N-shot inference if supported
            if hasattr(self, 'support_n') and self.support_n:
                chat_complete_res = self.infer(input_list=[payload])
                results = chat_complete_res[0]["choices"]
            else:
                n = self.llm.n
                self.llm.n = 1
                chat_complete_res = [self.infer(input_list=[payload])[0]["choices"][0] for i in range(n)]
                results = chat_complete_res
            
            # Process each result and update node scores
            for result in results:
                output = result["message"].get("content") 
                response = json_repair.loads(output)
                
                # Log evaluation results
                self.callback.info(
                    agent_id=self.workflow_instance_id,
                    progress=f"State Evaluator-vote",
                    message=f"\nthought_chains: \n{thought_chains}\nresponse: \n{response}"
                )
                
                # Process response and update node scores
                if response.get('choice'):
                    choice = response['choice']
                    if isinstance(choice, str):
                        choice = int(choice) if choice.isdigit() else 1
                    choice_id = index_to_node_id.get(choice, index_to_node_id[1])
                    thought_tree.nodes[choice_id].value += 1


        # Raise error for invalid evaluation type
        else:
            raise ValueError(f"Invalid evaluation type: {evaluation_type}")

        # Update thought tree in shared memory
        self.stm(self.workflow_instance_id)['thought_tree'] = thought_tree

