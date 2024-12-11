from pathlib import Path

from omagent_core.utils.registry import registry
from omagent_core.utils.general import read_image
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.logger import logging

CURRENT_PATH = Path(__file__).parents[0]


@registry.register_worker()
class InputInterface(BaseWorker):
    """Input interface processor that handles user instructions and image input.
    
    This processor:
    1. Reads user input containing question via input interface
    2. Returns the user instruction for next steps
    """

    def _run(self, *args, **kwargs):
        # Read user input through configured input interface
        user_input = self.input.read_input(workflow_instance_id=self.workflow_instance_id, input_prompt='Hello, lets play a game of guessing names. First, please guess a name in your mind. He/she must be a public figure.')
        # Extract text and image content from input message
        content = user_input['messages'][-1]['content']
        for content_item in content:
            if content_item['type'] == 'text':
                user_instruction = content_item['data']
        
        logging.info(f'User_instruction: {user_instruction}')

        return {'user_instruction': user_instruction}
