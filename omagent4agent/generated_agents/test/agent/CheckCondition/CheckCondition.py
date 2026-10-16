from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.registry import registry
from omagent_core.utils.logger import logging

@registry.register_worker()
class CheckCondition(BaseWorker):
    """
    Worker to check if the condition for the DO_WHILE loop is met and set an exit flag.
    """

    def _run(self, *args, **kwargs) -> None:
        workflow_instance_id = self.workflow_instance_id

        # Retrieve the current counter value from short term memory
        counter = self.stm(workflow_instance_id).get("counter", 0)

        # Determine if the loop should exit (e.g., when counter reaches 5)
        exit_flag = counter >= 5

        # Store the exit flag in short term memory
        self.stm(workflow_instance_id)["exit_flag"] = exit_flag

        logging.info(f"CheckCondition: Counter is {counter}. Loop exit flag set to: {exit_flag}")

        # No return value needed as the exit flag is stored in STM for DO_WHILE_TestWorker
        return {"exit_flag": exit_flag}