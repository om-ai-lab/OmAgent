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
    """A thought generation component that expands the Tree of Thoughts using LLM.
    
    This component is responsible for:
    - Generating new thoughts based on previous thought chains
    - Managing the expansion of the thought tree
    - Implementing different search strategies (BFS/DFS)
    - Handling LLM interactions for thought generation
    """
    
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
        """Generate new thoughts to expand the thought tree.

        This method:
        - Retrieves the current state of the thought tree
        - Implements BFS/DFS search strategies
        - Generates new thoughts using LLM
        - Updates the thought tree with new nodes

        Args:
            examples (str): Example thought chains for few-shot learning
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments

        Returns:
            None: Updates are made to shared memory (self.stm)
        """
        # Retrieve current state from shared memory
        thought_tree = self.stm(self.workflow_instance_id)['thought_tree']
        current_depth = self.stm(self.workflow_instance_id)['current_depth']
        current_node_id = self.stm(self.workflow_instance_id)['current_node_id']
        current_step = self.stm(self.workflow_instance_id)['current_step']
        search_type = self.stm(self.workflow_instance_id)['search_type']

        # Determine nodes to expand based on search strategy
        do_generate = True
        if search_type == "bfs":
            # For BFS, get all nodes at current depth
            current_nodes = thought_tree.get_nodes_at_depth(current_depth)
        elif search_type == "dfs":
            # For DFS, process children of current node
            current_node_children_ids = thought_tree.get_childrens(current_node_id, return_ids=True)
            if current_node_children_ids:
                current_node_id = current_node_children_ids[0]
                do_generate = False
            else:
                current_nodes = [thought_tree.nodes[current_node_id]]
        else:
            raise ValueError(f"Invalid search type: {search_type}")
        
        # Prepare few-shot examples if provided
        if examples:
            few_shots = "You can learn more about how to generate the thought chain for solving the problem following the requirements from examples below:\n **Examples**:\n" + examples
        else:
            few_shots = ""
        
        if do_generate:
            # Generate thoughts for each current node
            for node in current_nodes:
                # Get the thought chain leading to current node
                previous_thought_chain = thought_tree.get_current_thought_chain(node.id)
                
                # Prepare input for LLM
                payload = {
                    "few_shots": few_shots,
                    "problem": self.stm(self.workflow_instance_id)['problem'],
                    "requirements": self.stm(self.workflow_instance_id)['requirements'],
                    "previous_thought_chain": previous_thought_chain,
                }
                
                # Generate thoughts using LLM
                if hasattr(self, 'support_n') and self.support_n:
                    chat_complete_res = self.infer(input_list=[payload])
                    results = chat_complete_res[0]["choices"]
                else:
                    n = self.llm.n
                    self.llm.n = 1
                    
                    chat_complete_res = [self.infer(input_list=[payload])[0]["choices"][0] for i in range(n)]
                    results = chat_complete_res

                # Process and add generated thoughts to tree
                for result in results:                    
                    output = result["message"].get("content")
                    response = json_repair.loads(output)
                    
                    # Log generated thoughts
                    self.callback.info(
                        agent_id=self.workflow_instance_id,
                        progress=f"Thought Generator",
                        message=f'\nresponse: {response}'
                    )
                    
                    # Add new thoughts to tree
                    if not isinstance(response, dict):
                        response = {"thoughts": "No response from the model"}
                    if response.get('thoughts'):
                        if not isinstance(response['thoughts'], list):
                            response['thoughts'] = [response['thoughts']]
                        for index, thought in enumerate(response['thoughts']):                            
                            thought_tree.add_node(thought=thought, parent_id=node.id)
                    
        # Update state for DFS strategy
        if search_type == "dfs":
            self.stm(self.workflow_instance_id)['current_node_id'] = thought_tree.nodes[current_node_id].children[0]
        
        # Update shared memory with new state
        self.stm(self.workflow_instance_id)['thought_tree'] = thought_tree
        self.stm(self.workflow_instance_id)['current_depth'] = current_depth + 1
        self.stm(self.workflow_instance_id)['current_node_id'] = current_node_id
        self.stm(self.workflow_instance_id)['current_step'] = current_step + 1
        
