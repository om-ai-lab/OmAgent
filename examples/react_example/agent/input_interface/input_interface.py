from pathlib import Path
from omagent_core.utils.registry import registry
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.logger import logging
import uuid

CURRENT_PATH = Path(__file__).parents[0]

@registry.register_worker()
class InputInterface(BaseWorker):
    def _process_input(self, input_data):
        """Process input data and extract text content"""
        if not input_data or 'messages' not in input_data:
            return None
        
        message = input_data['messages'][-1]
        for content in message.get('content', []):
            if content.get('type') == 'text':
                return content.get('data', '').strip()
        return None

    def _run(self, *args, **kwargs):
        # Get example input
        example_input = self.input.read_input(
            workflow_instance_id=self.workflow_instance_id, 
            input_prompt='Please input example (press Enter to skip):'
        )
        example = self._process_input(example_input)

        # Get max_turns input
        max_turns_input = self.input.read_input(
            workflow_instance_id=self.workflow_instance_id, 
            input_prompt='Please input max turns (default is 10, press Enter to use default):'
        )
        max_turns = 10  # Default value
        max_turns_text = self._process_input(max_turns_input)
        if max_turns_text:
            try:
                max_turns = int(max_turns_text)
            except ValueError:
                logging.warning(f"Invalid max_turns input: {max_turns_text}, using default value: 10")

        # Get main question input
        user_input = self.input.read_input(
            workflow_instance_id=self.workflow_instance_id, 
            input_prompt='Please input your question:'
        )
        query = self._process_input(user_input)
        
        # Return all parameters
        return {
            'query': query,                   # User's question
            'id': str(uuid.uuid4()),          # Generate unique ID
            'example': example,               # User's example or None
            'max_turns': max_turns            # User's max turns or default value
        } 