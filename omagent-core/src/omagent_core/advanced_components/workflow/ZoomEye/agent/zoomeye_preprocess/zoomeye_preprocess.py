import copy
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.utils.registry import registry
from omagent_core.utils.general import read_image
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.advanced_components.workflow.ZoomEye.schemas.tree import ImageTree
from omagent_core.advanced_components.workflow.ZoomEye.schemas.utils import *

@registry.register_worker()
class ZoomEyePreprocess(BaseWorker):
    """
    Worker class for preprocessing in ZoomEye workflow.
    Prepares the search environment before starting a new visual cue search iteration.
    
    This component:
    1. Extracts the next visual cue to search for in the image
    2. Initializes the search queue with the root node of the image tree
    3. Sets up threshold parameters for the confidence-based search algorithm
    4. Prepares tracking variables for the search process
    """

    def _run(self, *args, **kwargs) -> None:
        """
        Main execution method for preprocessing a visual cue search iteration.
        
        Prepares the search environment by:
        - Extracting the next visual cue from the queue
        - Setting up the search parameters and thresholds
        - Initializing the BFS search queue with the root node
        
        Args:
            *args: Variable length argument list (not used)
            **kwargs: Arbitrary keyword arguments (not used)
            
        Returns:
            None: Updates are made directly to the shared memory
            
        Raises:
            ValueError: If required data is missing from the workflow state
        """
        # Get workflow STM for cleaner access to shared memory
        workflow_stm = self.stm(self.workflow_instance_id)
        
        # Validate that the image tree exists in the workflow state
        if 'tree' not in workflow_stm:
            raise ValueError("Required 'tree' not found in workflow STM")
            
        # Extract the image tree and root node
        image_tree = workflow_stm['tree']
        root_node = image_tree.root
        
        # Get the list of visual cues to process
        visual_cues = workflow_stm.get('visual_cues', None)

        # If there are no visual cues, set the root node as the only candidate and exit
        if visual_cues is None:
            workflow_stm['final_all_candidates'] = [root_node]
            return
            
        # Extract the next visual cue to process and remove it from the list
        visual_cue = visual_cues.pop(0)
        
        # Log the current visual cue being processed and remaining cues
        self.callback.info(
            self.workflow_instance_id, 
            progress='ZoomEyePreprocess', 
            message=f'\ncurrent search visual cues: {visual_cue}\nleft visual cues: {visual_cues}'
        )
        
        # Initialize the search state with parameters for the current visual cue
        workflow_stm.update({
            'current_visual_cue': visual_cue,          # Current object being searched for
            'visual_cues': visual_cues,                # Remaining objects to search for
            'Q': [root_node],                          # BFS queue starting with root node
            'temp_threshold_descrease': copy.deepcopy(THRESHOLD_DECREASE),  # Confidence threshold adjustment factor
            'answering_confidence_threshold_upper': ANSWERING_CONFIDENCE_THRESHOLD_UPPER,  # Upper confidence threshold
            'candidates': [],                          # List to store matching candidates
            'num_pop': 0,                              # Counter for nodes processed
            'pop_trace': [],                           # History of processed nodes
            'max_depth': min(image_tree.max_depth, DEPTH_LIMIT),  # Maximum tree depth to explore
            'finish': False                            # Flag indicating search completion
        })
        
        # Set initial confidence for root node
        root_node.answering_confidence = -1
        
        # Calculate the maximum number of nodes to process based on depth
        pop_num_limit = POP_LIMIT(workflow_stm['max_depth']) if callable(POP_LIMIT) else POP_LIMIT
        workflow_stm['pop_num_limit'] = pop_num_limit

        # Log the initial search state for debugging and monitoring
        self._log_state(workflow_stm)
        return
        
    def _log_state(self, workflow_stm: dict) -> None:
        """
        Helper method to log the current workflow state for monitoring and debugging.
        
        Args:
            workflow_stm (dict): The workflow state dictionary containing search parameters
                                 and tracking variables
        
        Returns:
            None: Output is sent to the logging system
        """
        self.callback.info(
            self.workflow_instance_id, 
            progress='ZoomEyePreprocess', 
            message=f"""\nzoomeye_items:
            Q: {workflow_stm['Q']}                     
            max_depth: {workflow_stm['max_depth']}    
            pop_num_limit: {workflow_stm['pop_num_limit']}  
            current_visual_cue: {workflow_stm['current_visual_cue']} 
            temp_threshold_descrease: {workflow_stm['temp_threshold_descrease']}  
            answering_confidence_threshold_upper: {workflow_stm['answering_confidence_threshold_upper']}  
            candidates: {workflow_stm['candidates']}   
            num_pop: {workflow_stm['num_pop']}         
            pop_trace: {workflow_stm['pop_trace']}     
            finish: {workflow_stm['finish']}           
            image_tree: {workflow_stm['tree']}        
            """
        )
        