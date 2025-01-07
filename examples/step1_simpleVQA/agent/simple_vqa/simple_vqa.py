from pathlib import Path
from typing import List

from omagent_core.engine.worker.base import BaseWorker
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.models.llms.prompt.parser import StrParser
from omagent_core.models.llms.schemas import Content, Message
from omagent_core.utils.container import container
from omagent_core.utils.general import encode_image
from omagent_core.utils.registry import registry


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

    def _run(self, user_instruction: str, *args, **kwargs):
        # Initialize empty list for chat messages
        chat_message = []

        # Add text question as first message
        chat_message.append(
            Message(role="user", message_type="text", content=user_instruction)
        )

        # Retrieve cached image from workflow shared memory
        if self.stm(self.workflow_instance_id).get("image_cache", None):
            img = self.stm(self.workflow_instance_id)["image_cache"]["<image_0>"]

            # Add base64 encoded image as second message
            chat_message.append(
                Message(
                    role="user",
                    message_type="image",
                    content=[
                        Content(
                            type="image_url",
                            image_url={
                                "url": f"data:image/jpeg;base64,{encode_image(img)}"
                            },
                        )
                    ],
                )
            )

        # Get response from LLM model
        chat_complete_res = self.llm.generate(records=chat_message)

        # Extract answer text from response
        answer = chat_complete_res["choices"][0]["message"]["content"]

        # Send answer via callback and return
        self.callback.send_answer(self.workflow_instance_id, msg=answer)
        return answer
