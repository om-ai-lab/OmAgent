from omagent_core.engine.workflow.task.simple_task import simple_task
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.do_while_task import DoWhileTask
from omagent_core.engine.workflow.task.switch_task import SwitchTask


class ZoomEyeWorkflow(ConductorWorkflow):
    """
    ZoomEye workflow implementation for processing visual queries.
    Extends the ConductorWorkflow to create a specialized workflow
    for handling image-based search and analysis.
    """

    def __init__(self):
        """
        Initialize the ZoomEye workflow with a lightweight configuration.
        """
        super().__init__(name='zoomeye_workflow', lite_version=True)
        

    def set_input(self, query: str, image_path: str, qid: str="test"):
        """
        Set input parameters for the workflow and configure tasks.
        
        Args:
            query (str): The text query from the user
            image_path (str): Path to the image to be analyzed
            qid (str, optional): Query identifier. Defaults to "test".
        """
        self.qid = qid
        self.query = query
        self.image_path = image_path
        self._configure_tasks()
        self._configure_workflow()

    def _configure_tasks(self):
        """
        Configure all tasks in the ZoomEye workflow pipeline.
        Creates and connects various processing stages for the image analysis workflow.
        """
        
        # Task for generating visual cues from the input image
        self.visual_cue_generation = simple_task(
            task_def_name='VisualCueGeneration',
            task_reference_name='visual_cue_generation',
            inputs={
                "qid": self.qid,
                "query": self.query,
                "image_path": self.image_path
            }
        )
        
        # Task for preprocessing data before search operations
        zoomeye_preprocess = simple_task(
            task_def_name='ZoomEyePreprocess',
            task_reference_name='zoomeye_preprocess',            
        )
        
        # Task for executing the ZoomEye search with current parameters
        zoomeye_search = simple_task(
            task_def_name='ZoomEyeSearch',
            task_reference_name='zoomeye_search'
        )
        
        # Task for checking search results and determining if more searches are needed
        zoomeye_search_check = simple_task(
            task_def_name='ZoomEyeSearchCheck',
            task_reference_name='zoomeye_search_check'
        )
        
        # Loop task for repeated search operations until adequate results are found
        zoomeye_search_loop = DoWhileTask(
            task_ref_name='zoomeye_search_loop', 
            tasks=[zoomeye_search, zoomeye_search_check],
            termination_condition='if ($.zoomeye_search_check["search_check_finish"] == true){false;} else {true;}'
        )
        
        # Task for checking if the entire search process should continue with new parameters
        zoomeye_loop_check = simple_task(
            task_def_name='ZoomEyeLoopCheck',
            task_reference_name='zoomeye_loop_check'
        )
        
        # Main loop task that includes preprocessing, searching, and checking
        # Continues until satisfactory results are found or timeout conditions met
        self.zoomeye_loop = DoWhileTask(
            task_ref_name='zoomeye_loop',
            tasks=[zoomeye_preprocess, zoomeye_search_loop, zoomeye_loop_check],
            termination_condition='if ($.zoomeye_loop_check["loop_check_finish"] == true){false;} else {true;}'
        )
        
        # Final task to format and return the search results
        self.zoomeye_output = simple_task(
            task_def_name='ZoomEyeOutput',
            task_reference_name='zoomeye_output'
        )
        

    def _configure_workflow(self):
        """
        Configure the workflow execution sequence.
        Establishes the flow between different tasks in the pipeline.
        """
        # Connect tasks in sequence: visual cue generation -> search loop -> output formatting
        self >> self.visual_cue_generation >> self.zoomeye_loop >> self.zoomeye_output