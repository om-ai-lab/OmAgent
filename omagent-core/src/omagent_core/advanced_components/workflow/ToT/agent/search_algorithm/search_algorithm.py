from pathlib import Path
from typing import List
import json
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.utils.registry import registry
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.models.llms.prompt.prompt import PromptTemplate
from pydantic import Field
from typing import List
import json_repair

CURRENT_PATH = Path(__file__).parents[0]

@registry.register_worker()
class SearchAlgorithm(BaseWorker, BaseLLMBackend):
    """A search algorithm component that manages the Tree of Thoughts traversal.
    
    This component is responsible for:
    - Implementing both BFS and DFS search strategies
    - Managing the search process and termination conditions
    - Tracking the best solutions found
    - Determining when to stop the search process
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
    
    def _run(self, *args, **kwargs):
        """Execute the search algorithm and manage the search process.

        This method:
        - Retrieves current search state
        - Implements BFS/DFS search logic
        - Manages tree pruning and best solution tracking
        - Determines search termination conditions

        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments

        Returns:
            dict: Contains search results and completion status
        """
        # Retrieve current state from shared memory
        thought_tree = self.stm(self.workflow_instance_id).get('thought_tree', None)
        current_depth = self.stm(self.workflow_instance_id).get('current_depth', None)
        current_step = self.stm(self.workflow_instance_id).get('current_step', None)
        max_depth = self.stm(self.workflow_instance_id).get('max_depth', None)
        max_steps = self.stm(self.workflow_instance_id).get('max_steps', None)
        dfs_best = self.stm(self.workflow_instance_id).get('dfs_best', None)
        current_node_id = self.stm(self.workflow_instance_id).get('current_node_id', None)
        search_type = self.stm(self.workflow_instance_id).get('search_type', None)
        
        # Execute search strategy based on type
        if search_type == "bfs":
            # Implement BFS strategy with beam search
            b = self.stm(self.workflow_instance_id).get('b', None)
            current_nodes_ids = thought_tree.get_nodes_at_depth(current_depth, return_ids=True)
            top_b_nodes_ids = thought_tree.get_top_n_score_nodes(depth=current_depth, sort_region='depth', n=b, return_ids=True)
            
            # Prune nodes not in top-b
            for node_id in current_nodes_ids:
                if node_id not in top_b_nodes_ids:
                    thought_tree.prune(node_id)
            best_node_id = top_b_nodes_ids[0]
            
        elif search_type == "dfs":
            # Implement DFS strategy with backtracking
            current_node_score = thought_tree.nodes[current_node_id].value
            current_path_score = thought_tree.get_current_path_score(current_node_id)
            
            if current_node_score < 0:
                # Backtrack if current node has negative score
                prune_id = current_node_id
                parent_id = thought_tree.get_parent(current_node_id, return_ids=True)
                thought_tree.prune(prune_id)
                current_depth -= 1
                
                # Continue backtracking if parent has no children
                while thought_tree.get_childrens(parent_id) == []:
                    prune_id = parent_id
                    parent_id = thought_tree.get_parent(parent_id, return_ids=True)
                    thought_tree.prune(prune_id)
                    current_depth -= 1
                current_node_id = parent_id
            else:
                # Update best solution if current path is better
                if dfs_best['score'] < current_path_score:
                    dfs_best['id'], dfs_best['score'] = current_node_id, current_path_score
                best_node_id = dfs_best['id']
        else:
            raise ValueError(f"Search type {search_type} is not supported")
        
        # Update shared memory with current state
        self.stm(self.workflow_instance_id)['thought_tree'] = thought_tree
        self.stm(self.workflow_instance_id)['current_node_id'] = current_node_id
        self.stm(self.workflow_instance_id)['current_depth'] = current_depth
        
        # Get current best solution
        current_best_thought_chain = thought_tree.get_current_thought_chain(node_id=best_node_id)
        
        # Log current best solution
        self.callback.info(
            agent_id=self.workflow_instance_id,
            progress=f"Search Algorithm",
            message=f'current_best_thought_chain: {current_best_thought_chain}\n '
        )
        
        # Check completion using LLM if enabled
        if self.use_llm_completion:
            payload = { 
                "problem": self.stm(self.workflow_instance_id)['problem'],
                "thought_chain": current_best_thought_chain,
            }
            chat_complete_res = self.infer(input_list=[payload])
            output = chat_complete_res[0]["choices"][0]["message"].get("content")
            response = json_repair.loads(output)
            
            # Log completion check results
            self.callback.info(
                agent_id=self.workflow_instance_id,
                progress=f"Search Algorithm-completion",
                message=f'response: {response}'
            )
            
            # Return results if solution is complete
            if response.get('completion', None) == "yes":
                self._record_results(current_best_thought_chain, thought_tree)
                return {"finish": True, "result": self.stm(self.workflow_instance_id)['record']}
        
        # Check termination conditions
        if current_depth >= max_depth or current_step >= max_steps:
            self._record_results(current_best_thought_chain, thought_tree)
            return {"finish": True, "result": self.stm(self.workflow_instance_id)['record']}
        
        return {"finish": False}
    
    def _record_results(self, current_best_thought_chain, thought_tree):
        """Helper method to record final results and usage statistics.
        
        Args:
            current_best_thought_chain: The best solution found
            thought_tree: The final state of the thought tree
        """
        self.callback.info(
            agent_id=self.workflow_instance_id,
            progress=f"Search Algorithm-completion",
            message=f'token_usage: {self.token_usage}'
        )
        record = self.stm(self.workflow_instance_id)['record']
        record['last_output'] = current_best_thought_chain
        record['prompt_tokens'] = self.token_usage['prompt_tokens']
        record['completion_tokens'] = self.token_usage['completion_tokens']
        record['total_tokens'] = self.token_usage['total_tokens']
        record['thought_tree'] = thought_tree
                
        print('-'*100)
        print(record)
        print('-'*100)
    