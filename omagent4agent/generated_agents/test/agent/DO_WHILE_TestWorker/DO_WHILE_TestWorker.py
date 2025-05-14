from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.registry import registry
from omagent_core.utils.logger import logging

@registry.register_worker()
class DO_WHILE_TestWorker(BaseWorker):
    """
    Worker to demonstrate the use of a DO_WHILE loop to repeatedly execute tasks.
    """

    def _run(self, *args, **kwargs):
        workflow_instance_id = self.workflow_instance_id

        # Initialize counter if not already present
        counter = self.stm(workflow_instance_id).get("counter", 0)
        exit_flag = self.stm(workflow_instance_id).get("exit_flag", False)

        # Increment the counter
        counter += 1
        self.stm(workflow_instance_id)["counter"] = counter

        logging.info(f"Counter incremented to: {counter}")

        # Check if the loop should continue
        if counter < 5:
            exit_flag = False
        else:
            exit_flag = True

        # Store the exit flag
        self.stm(workflow_instance_id)["exit_flag"] = exit_flag

        logging.info(f"Exiting loop: {exit_flag}")

        return {"loop_condition": not exit_flag}