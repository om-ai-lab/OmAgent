from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.registry import registry
from omagent_core.utils.logger import logging

@registry.register_worker()
class IncrementCounter(BaseWorker):
    """
    Worker to increment a counter for testing DO_WHILE loop condition.
    """
    
    def _run(self, *args, **kwargs) -> None:
        workflow_instance_id = self.workflow_instance_id

        # Retrieve the current counter value, initialize if not present
        counter = self.stm(workflow_instance_id).get("counter", 0)
        
        # Increment the counter
        counter += 1
        
        # Store the updated counter back to short term memory
        self.stm(workflow_instance_id)["counter"] = counter

        logging.info(f"Counter incremented to: {counter}")

        # No output required for IncrementCounter as it just updates the STM
        return {}