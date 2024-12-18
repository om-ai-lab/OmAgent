from pathlib import Path
from omagent_core.utils.registry import registry
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.logger import logging

CURRENT_PATH = Path(__file__).parents[0]

@registry.register_worker()
class InputInterface(BaseWorker):
    """Input interface processor that handles user instructions and saves conversation history."""

    def _run(self, *args, **kwargs):
        # Read user input
        print ("111")
        user_input = self.input.read_input(
            workflow_instance_id=self.workflow_instance_id,
            input_prompt='Please enter your question or say "bye" to end the conversation.'
        )
        
        # Extract text content
        content = user_input['messages'][-1]['content']
        for content_item in content:
            if content_item['type'] == 'text':
                user_instruction = content_item['data']
        
        # Log user instruction
        logging.info(f'User instruction: {user_instruction}')
        
        # Save user instruction to conversation history
        conversation_history = self.stm(self.workflow_instance_id).get("conversation_history", [])
        conversation_history.append({"role": "user", "content": user_instruction})
        self.stm(self.workflow_instance_id)["conversation_history"] = conversation_history

        return {"user_instruction": user_instruction}

