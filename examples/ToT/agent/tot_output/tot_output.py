from pathlib import Path
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.general import read_image
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry

CURRENT_PATH = Path(__file__).parents[0]

@registry.register_worker()
class ToTOutput(BaseWorker):
    """Output processor component for Tree of Thoughts workflow.
    
    This component is responsible for:
    - Processing the final results from the ToT workflow
    - Formatting the output for user presentation
    - Managing output logging and callbacks
    - Handling any output-related errors
    """

    def _run(self, result: dict, *args, **kwargs):
        """Process and present the final results from the ToT workflow.

        This method:
        - Receives the final result from the workflow
        - Formats the output for user presentation
        - Logs the output through callback system
        - Handles any output processing errors

        Args:
            result (dict): Final results from the ToT workflow
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments

        Returns:
            None: Output is presented through callback system
        """
        try:
            # Log the final output through callback system
            self.callback.info(
                agent_id=self.workflow_instance_id,
                progress=f"ToT Output",
                message=f"\nlast_output: \n{result['last_output']}"
            )
            
        except Exception as e:
            # Log any errors during output processing
            self.callback.error(
                agent_id=self.workflow_instance_id,
                message=f"Error in ToT output processing: {str(e)}"
            )
            raise