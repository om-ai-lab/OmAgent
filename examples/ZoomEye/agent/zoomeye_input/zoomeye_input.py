from pathlib import Path

from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry

CURRENT_PATH = Path(__file__).parents[0]


@registry.register_worker()
class ZoomEyeInput(BaseWorker):
    """
    Worker class for handling user input in the ZoomEye workflow.
    Processes both text queries and image inputs from users.
    """

    def _run(self, *args, **kwargs):
        """
        Main execution method for processing user input.
        
        Returns:
            dict: Contains the text query and image path (if provided)
        """
        try:
            # Get user input through the input interface
            user_input = self.input.read_input(
                workflow_instance_id=self.workflow_instance_id,
                input_prompt="Please input your question:",
            )
            
            # Extract messages from user input
            messages = user_input["messages"]
            message = messages[-1]  # Get the latest message
            
            # Initialize variables for image and text
            image_path = None
            text = None
            
            # Process each content item in the message
            for each_content in message["content"]:
                if each_content["type"] == "image_url":
                    # Store the image path if an image was provided
                    image_path = each_content["data"]
                elif each_content["type"] == "text":
                    # Store the text content if text was provided
                    text = each_content["data"]
                    
            # Return both the text query and image path
            return {"query": text,
                    "image_path": image_path}
        except Exception as e:
            # Log any errors during input processing
            logging.error(f"Error in ToT input processing: {str(e)}")
            raise