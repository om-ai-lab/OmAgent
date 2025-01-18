from pathlib import Path
from typing import List

from omagent_core.engine.worker.base import BaseWorker
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.models.llms.prompt.parser import StrParser
from omagent_core.models.llms.prompt.prompt import PromptTemplate
from omagent_core.models.llms.schemas import Content, Message
from omagent_core.utils.container import container
from omagent_core.utils.general import encode_image, read_image
from omagent_core.utils.registry import registry
from pydantic import Field


@registry.register_worker()
class ImageChat(BaseWorker, BaseLLMBackend):
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_template("You are a helpful assistant.", role="system"),
            PromptTemplate.from_template("describe the {{image}}", role="user"),
        ]
    )

    llm: OpenaiGPTLLM

    def _run(self, image_url: str, *args, **kwargs):
        # read image from url, save as PIL image object
        img = read_image(input_source=image_url)

        """if you save the image in the stm, you can use the following code to get the image

        image_cache = self.stm(self.workflow_instance_id).get('image_cache', {}) # get the image cache from workflow instance
        image_cache['image_0'] = img # save the image to image cache, key is the name of the image
        self.stm(self.workflow_instance_id)['image_cache'] = image_cache # save the image cache to workflow instance
        img = image_cache['image_0'] # get the image from image cache, key is the name of the image
        """

        # `image` variable in user prompt will be replaced by the `img` PIL image object
        chat_completion_res = self.simple_infer(image=img)["choices"][0]["message"].get(
            "content"
        )  # use simple_infer for simple inference
        # chat_completion_res = self.infer(input_list=[{"image": img}])[0]["choices"][0]["message"].get("content") # use infer for inference

        """Also, `image` variable can be a list of text and images, intersected by the text and images
           the order of the list is the order of the text and images in the chat payload to LLM
           you can use the following code:
        
        chat_completion_res = self.simple_infer(image=[img, 'in Chinese.'])["choices"][0]["message"].get("content") # this result will be chinese, use simple_infer for simple inference
        # chat_completion_res = self.infer(input_list=[{"image": [img, 'in Chinese.']}])[0]["choices"][0]["message"].get("content") # this result will be chinese, use infer for inference
        """

        print(chat_completion_res)
        return {"output": chat_completion_res}
