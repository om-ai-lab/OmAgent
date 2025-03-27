from omagent_core.utils.registry import registry
from omagent_core.engine.worker.base import BaseWorker

@registry.register_worker()
class ZoomEyeLoopCheck(BaseWorker):
    """
    Worker class that determines whether the ZoomEye search loop should continue or terminate.
    This component checks if there are any remaining visual cues to process in the workflow.
    """

    def _run(self, *args, **kwargs):
        """
        Main execution method to check if the ZoomEye workflow loop should continue.
            
        Returns:
            dict: Contains the 'loop_check_finish' flag indicating whether to terminate the loop
                 - True: No more visual cues to process, workflow should exit the loop
                 - False: Visual cues still exist, workflow should continue processing
        """
        # Retrieve the current list of visual cues from short-term memory
        visual_cues = self.stm(self.workflow_instance_id).get('visual_cues', None)
        
        # If no visual cues exist or the list is empty, signal to terminate the loop
        if visual_cues is None or len(visual_cues) == 0:
            return {"loop_check_finish": True}
        # Otherwise, continue the loop to process remaining visual cues
        else:
            return {"loop_check_finish": False}