from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.registry import registry
from pydantic import Field
import uuid
@registry.register_worker()
class InputInterface(BaseWorker):
    """Input interface worker for handling user input"""
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
        # Get main question input
        user_input = self.input.read_input(
            workflow_instance_id=self.workflow_instance_id, 
            input_prompt='Please input your question:'
        )
        query = self._process_input(user_input)
        
        # Return parameters
        return {
            'query': query,                   # User's question
            'id': str(uuid.uuid4())           # Generate unique ID
        } 