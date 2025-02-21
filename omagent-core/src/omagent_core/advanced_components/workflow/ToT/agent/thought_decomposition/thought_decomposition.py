from omagent_core.advanced_components.workflow.ToT.schemas.ToT_structure import ThoughtTree
from omagent_core.utils.registry import registry
from omagent_core.engine.worker.base import BaseWorker

@registry.register_worker()
class ThoughtDecomposition(BaseWorker):
    """A thought decomposition component that initializes and manages the Tree of Thoughts structure.
    
    This component is responsible for:
    - Setting up the initial thought tree structure
    - Initializing tracking variables and search parameters
    - Managing the state of the thought process
    - Establishing the foundation for subsequent thought generation and evaluation
    """
    
    def _run(self, qid: str, requirements: str, problem: str):
        """Initialize and set up the thought decomposition process.

        This method establishes the basic structure and parameters needed for the Tree of Thoughts approach:
        - Creates a record of the current problem
        - Initializes the thought tree with a root node
        - Sets up tracking variables for tree traversal
        - Configures search parameters for the thought process

        Args:
            qid (str): Query identifier for tracking purposes
            requirements (str): Specific requirements or constraints for the task
            problem (str): The problem statement to be processed

        Returns:
            None: Updates are made to shared memory (self.stm)
        """
        try:
            # Create a record entry for the current problem instance
            record = {
                "qid": qid,
                "problem": problem,
            }
            self.stm(self.workflow_instance_id)['record'] = record
            
            # Initialize thought tree structure if not already present
            if self.stm(self.workflow_instance_id).get('thought_tree', None) is None:
                # Create new thought tree and establish root node
                thought_tree = ThoughtTree()
                thought_tree.add_node(thought="", parent_id=None)
                
                # Store fundamental problem information
                self.stm(self.workflow_instance_id)['requirements'] = requirements
                self.stm(self.workflow_instance_id)['problem'] = problem
                
                # Initialize tree traversal tracking variables
                self.stm(self.workflow_instance_id)['thought_tree'] = thought_tree
                self.stm(self.workflow_instance_id)['current_depth'] = 0
                self.stm(self.workflow_instance_id)['current_step'] = 0
                self.stm(self.workflow_instance_id)['current_node_id'] = 0
                
                # Configure search parameters from configuration
                self.stm(self.workflow_instance_id)['search_type'] = self.params['search_type']
                self.stm(self.workflow_instance_id)['dfs_best'] = {"id": 0, "score": 0}  # Track best node in DFS
                self.stm(self.workflow_instance_id)['max_depth'] = int(self.params['max_depth'])
                self.stm(self.workflow_instance_id)['max_steps'] = int(self.params['max_steps'])
                self.stm(self.workflow_instance_id)['b'] = int(self.params['b'])  # Branching factor
                
            # Log initialization status and parameters
            self.callback.info(
                agent_id=self.workflow_instance_id,
                progress=f"Thought Decomposition",
                message=f"\nrecord: {record}\nsearch_type: {self.params['search_type']}\nmax_depth: {self.params['max_depth']}\nmax_steps: {self.params['max_steps']}\nb: {self.params['b']}",
            )
            
        except Exception as e:
            # Handle and log any initialization errors
            self.callback.error(
                agent_id=self.workflow_instance_id,
                message=f"Error occurred: {str(e)}"
            )
            







        