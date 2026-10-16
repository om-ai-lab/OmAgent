from pathlib import Path

from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.general import read_image
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry

CURRENT_PATH = Path(__file__).parents[0]


@registry.register_worker()
class ToTInput(BaseWorker):
    """Input processor component for Tree of Thoughts workflow.
    
    This component is responsible for:
    - Reading and processing user requirements input
    - Reading and processing user question input
    - Formatting inputs for the ToT workflow
    - Managing input validation and error handling
    """

    def _run(self, *args, **kwargs):
        """Process user inputs for the ToT workflow.

        This method:
        - Reads requirements through input interface
        - Reads question through input interface
        - Extracts text content from inputs
        - Formats inputs for downstream processing

        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments

        Returns:
            dict: Contains formatted requirements and query
        """
        try:
            # Read and process requirements input
            requirements_input = self.input.read_input(
                workflow_instance_id=self.workflow_instance_id,
                input_prompt="Please input your requirements:",
            )
            
            # Extract requirements message content
            requirements = requirements_input["messages"][-1]
            
            # Process text content from requirements
            requirements_text = ""
            for each_content in requirements["content"]:
                if each_content["type"] == "text":
                    requirements_text += each_content["data"] + "\n"
            
            # Read and process question input
            question_input = self.input.read_input(
                workflow_instance_id=self.workflow_instance_id,
                input_prompt="Please input your question:",
            )
            
            # Extract question message content
            question = question_input["messages"][-1]
            
            # Process text content from question
            question_text = ""
            for each_content in question["content"]:
                if each_content["type"] == "text":
                    question_text += each_content["data"] + "\n"
            
            # Return formatted inputs for workflow
            return {
                "requirements": requirements_text,
                "query": question_text,
            }
            
        except Exception as e:
            # Log any errors during input processing
            logging.error(f"Error in ToT input processing: {str(e)}")
            raise