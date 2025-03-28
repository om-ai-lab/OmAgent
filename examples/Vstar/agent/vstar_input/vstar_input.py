from pathlib import Path

from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry

CURRENT_PATH = Path(__file__).parents[0]


@registry.register_worker()
class VstarInput(BaseWorker):
    """
    A worker class for handling VStar input processing.
    This class is responsible for receiving and processing user input,
    including both text queries and image data.
    """

    def _run(self, *args, **kwargs):
        """
        Main execution method for processing VStar input.
        
        This method handles:
        1. Reading user input through the input interface
        2. Extracting messages from the input
        3. Processing both image and text content
        
        Returns:
            dict: A dictionary containing:
                - 'query': The text query from the user
                - 'image_path': The path to the uploaded image
                
        Raises:
            Exception: If any error occurs during input processing
        """
        try:
            # Request user input through the designated input interface
            user_input = self.input.read_input(
                workflow_instance_id=self.workflow_instance_id,
                input_prompt="Please input your question:",
            )
            
            # Extract the message list from user input
            messages = user_input["messages"]
            # Get the most recent message (last message in the list)
            message = messages[-1]
            
            # Initialize variables to store image and text data
            image_path = None
            text = None
            
            # Iterate through each content item in the message
            for each_content in message["content"]:
                if each_content["type"] == "image_url":
                    # If content is an image, store its path
                    image_path = each_content["data"]
                elif each_content["type"] == "text":
                    # If content is text, store the text query
                    text = each_content["data"]
                    
            # Return a dictionary containing both the text query and image path
            return {
                "query": text,
                "image_path": image_path
            }
            
        except Exception as e:
            # Log any errors that occur during the input processing
            logging.error(f"Error in ToT input processing: {str(e)}")
            # Re-raise the exception for proper error handling upstream
            raise