from pathlib import Path
from typing import List

from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.utils.registry import registry
from omagent_core.models.llms.schemas import Message, Content
from omagent_core.utils.general import encode_image
from omagent_core.models.llms.prompt.parser import StrParser
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.container import container

from .prompts import *


@registry.register_worker()
class SimpleVQA(BaseWorker, BaseLLMBackend):
    """Simple Visual Question Answering processor that handles image-based questions.
    
    This processor:
    1. Takes user instruction and cached image from workflow context
    2. Creates chat messages containing the text question and base64-encoded image
    3. Sends messages to LLM to generate a response
    4. Returns response and sends it via callback
    """
    llm: OpenaiGPTLLM

    def _run(self, *args, **kwargs):
        assert self.stm(self.workflow_instance_id).get('data_input', None) is not None
        # Initialize empty list for chat messages
        chat_message = []
        # Retrieve cached data from workflow shared memory
        data_input = self.stm(self.workflow_instance_id)['data_input']

        propose_input = propose_prompt.format(input=data_input)
        # Add text question as first message
        chat_message.append(Message(role="user", message_type='text', content=propose_input))
        
        # Get response from LLM model
        chat_complete_res = self.llm.generate(records=chat_message)

        # Extract answer text from response
        next_states_response = chat_complete_res["choices"][0]["message"]["content"]
        
        # Send answer via callback and return
        self.callback.send_answer(self.workflow_instance_id, msg=next_states_response)
        return next_states_response
