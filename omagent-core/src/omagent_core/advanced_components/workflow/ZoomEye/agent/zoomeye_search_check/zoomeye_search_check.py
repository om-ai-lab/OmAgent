from omagent_core.utils.registry import registry
from omagent_core.engine.worker.base import BaseWorker

@registry.register_worker()
class ZoomEyeSearchCheck(BaseWorker):
    """
    Worker class that checks if the current search iteration has completed.
    Collects successful search candidates and updates the final result list.
    Acts as a checkpoint between iterations in the search process.
    """

    def _run(self, *args, **kwargs):
        """
        Main execution method to check search completion status and collect results.
        
        This component:
        1. Checks if the current search iteration is complete
        2. Collects any found candidates and adds them to the final results
        3. Returns a flag indicating whether to continue or finish the search loop
        """
        # Get the search completion flag from shared memory
        finish = self.stm(self.workflow_instance_id).get('finish', False)
        
        # Get the list of candidate objects found in current search iteration
        candidates = self.stm(self.workflow_instance_id).get('candidates', [])
        
        # If current search iteration is complete, collect the results
        if finish:
            # Get the master list of all candidates found across iterations
            final_all_candidates = self.stm(self.workflow_instance_id).get('final_all_candidates', [])
            
            # If we found candidates in this iteration, add them to master list
            if len(candidates) > 0:
                final_all_candidates.extend(candidates)
                
            # Update the master list in shared memory
            self.stm(self.workflow_instance_id)['final_all_candidates'] = final_all_candidates

        # Return flag indicating whether the search loop should continue or terminate
        # When finish=True, the search loop will terminate and move to next visual cue
        return {"search_check_finish": finish}