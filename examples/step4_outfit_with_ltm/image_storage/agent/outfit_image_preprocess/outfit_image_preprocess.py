from pathlib import Path
from typing import List

from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.models.llms.prompt import PromptTemplate
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.models.encoders.openai_encoder import OpenaiTextEmbeddingV3
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry
from pydantic import Field
from omagent_core.utils.general import read_image


CURRENT_PATH = root_path = Path(__file__).parents[0]


@registry.register_worker()
class OutfitImagePreprocessor(BaseLLMBackend, BaseWorker):
    llm: OpenaiGPTLLM
    text_encoder: OpenaiTextEmbeddingV3

    # Define prompt templates for image captioning
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("sys_prompt.prompt"), role="system"
            ),
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("user_prompt.prompt"), role="user"
            ),
        ]
    )

    def _run(self, image_data:dict, *args, **kwargs):
        # Clear existing LTM data before processing new images
        try:
            self.ltm.clear()
        except Exception as e:
            pass
        
        self.callback.info(agent_id=self.workflow_instance_id, progress="image_preprocess", message="image preprocess started")
        
        # Load and validate all images
        images = []  
        for image_item in image_data["content"]:
            img_path = image_item["data"]
            try:
                img = read_image(str(img_path))
                images.append((str(img_path), img))
            except Exception as e:
                logging.warning(f"Failed to read image {img_path}: {e}")

        # Process each image - generate caption and store in LTM
        for idx, (img_path, img) in enumerate(images):
            # Create unique key for storing image temporarily
            image_key = f"<image_0>"
            image_cache = {image_key: img}
            self.stm(self.workflow_instance_id)['image_cache'] = image_cache
            
            # Generate caption using LLM
            chat_complete_res = self.simple_infer(image=image_key)
            caption = chat_complete_res["choices"][0]["message"]["content"]
            logging.info(f"generated caption: {caption}")

            # Cleanup STM cache
            self.stm(self.workflow_instance_id).pop('image_cache')

            # Store image metadata and caption embedding in LTM
            caption_vector = self.text_encoder.infer([caption])[0]
            self.ltm[idx] = {
                'value': {
                    'path': img_path,
                    'caption': caption,
                },
                'embedding': caption_vector
            }

        self.callback.info(agent_id=self.workflow_instance_id, progress="image_preprocess", message="image preprocess finished")
        return 
