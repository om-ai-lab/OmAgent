from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.registry import registry
from omagent_core.utils.logger import logging

@registry.register_worker()
class SWITCHTestWorker(BaseWorker):
    """
    Worker to demonstrate the use of a SWITCH statement based on an integer input.
    """

    def _run(self, *args, **kwargs) -> dict:
        # Load the input value from short term memory
        switch_case_value = self.stm(self.workflow_instance_id)["input_value"]

        # Return the case value for the SWITCH statement
        return {"switch_case_value": switch_case_value}