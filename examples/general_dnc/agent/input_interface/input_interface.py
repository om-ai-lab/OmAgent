from pathlib import Path

from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.general import read_image
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry

CURRENT_PATH = Path(__file__).parents[0]


@registry.register_worker()
class InputInterface(BaseWorker):
    """Input interface processor that handles user instructions and image input.

    This processor:
    1. Reads user input containing question and image via input interface
    2. Extracts text instruction and image path from the input
    3. Loads and caches the image in workflow storage
    4. Returns the user instruction for next steps
    """

    def _run(self, *args, **kwargs):
        # Read user input through configured input interface
        user_input = self.input.read_input(
            workflow_instance_id=self.workflow_instance_id,
            input_prompt="Please input your question:",
        )
        messages = user_input["messages"]
        message = messages[-1]
        image = None
        text = None
        for each_content in message["content"]:
            if each_content["type"] == "image_url":
                image = read_image(each_content["data"])
            elif each_content["type"] == "text":
                text = each_content["data"]
        if image is not None:
            self.stm(self.workflow_instance_id)["image_cache"] = image
        return {"query": text}
