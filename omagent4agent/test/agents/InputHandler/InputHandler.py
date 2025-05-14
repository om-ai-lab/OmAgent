
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.registry import registry
from omagent_core.utils.logger import logging

@registry.register_worker()
class InputHandler(BaseWorker):
    """
    Worker to handle initial input and prepare it for further processing.
    """

    def _run(self, input, *args, **kwargs):
        input_value = input

        logging.info(f"Received input: {input_value}")
        
        # Store the input value in short term memory for further use
        self.stm(self.workflow_instance_id)["input_value"] = input_value
        
        # Prepare output for the SWITCH worker
        return {"input": input_value}
