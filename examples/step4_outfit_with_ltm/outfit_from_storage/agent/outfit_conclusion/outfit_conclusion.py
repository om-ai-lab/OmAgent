import re
from collections import OrderedDict
from pathlib import Path
from typing import List

import json_repair
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.models.encoders.openai_encoder import OpenaiTextEmbeddingV3
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.models.llms.prompt import PromptTemplate
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry
from pydantic import Field

CURRENT_PATH = root_path = Path(__file__).parents[0]


@registry.register_worker()
class OutfitConclusion(BaseLLMBackend, BaseWorker):
    """Class for finalizing outfit recommendations by matching generated outfits with actual wardrobe items.

    Inherits from BaseLLMBackend and BaseProcessor to handle LLM interactions and processing logic.
    Uses prompt templates to structure interactions with the language model.
    """

    llm: OpenaiGPTLLM
    text_encoder: OpenaiTextEmbeddingV3
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

    def _run(self, proposed_outfit: str, *args, **kwargs):
        """Process generated outfit recommendations and match with actual wardrobe items.

        Args:
            proposed_outfit: Generated outfit recommendation to match with wardrobe
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Dict containing the final outfit recommendation with matched wardrobe items
        """
        # Get user instruction and weather info from short-term memory
        user_instruct = self.stm(self.workflow_instance_id).get("user_instruction")
        search_info = (
            self.stm(self.workflow_instance_id)["search_info"]
            if "search_info" in self.stm(self.workflow_instance_id)
            else None
        )
        generated_outfit = proposed_outfit

        # Track matched wardrobe items and their details
        wardrobe_items_path = OrderedDict()
        wardrobe_items_caption = OrderedDict()
        outfit_count = 0

        self.callback.info(
            agent_id=self.workflow_instance_id,
            progress="outfit_conclusion",
            message=f"start matching generated outfit with wardrobe items",
        )

        # For each outfit piece, find matching items in wardrobe
        for outfit_type, outfit_item_caption in generated_outfit.items():
            logging.info(f"outfit type: {outfit_type}")
            if outfit_type != "style_notes":
                # Get vector embedding of item description and search wardrobe
                caption_vector = self.text_encoder.infer([outfit_item_caption])[0]
                search_res = self.ltm.get_by_vector(
                    embedding=caption_vector, top_k=3, threshold=0.5
                )
                for item in search_res:
                    item_key, item_value, score = item
                    wardrobe_items_path[outfit_count] = item_value["path"]
                    wardrobe_items_caption[outfit_count] = item_value["caption"]
                    outfit_count += 1

        self.callback.info(
            agent_id=self.workflow_instance_id,
            progress="outfit_conclusion",
            message=f"matching generated outfit with wardrobe items finished",
        )

        # Generate final recommendation using LLM
        chat_complete_res = self.simple_infer(
            user_instruct=user_instruct,
            weather=search_info,
            outfit=generated_outfit,
            items=wardrobe_items_caption,
        )
        content = chat_complete_res["choices"][0]["message"].get("content")
        content = self._extract_from_result(content)

        # Map indices to actual wardrobe item paths
        for key, value in content.items():
            if key != "Styling Notes":
                try:
                    image_path = wardrobe_items_path[int(value)]
                    content[key] = image_path
                    self.callback.send_block(
                        agent_id=self.workflow_instance_id,
                        msg=image_path,
                        msg_type="image_url",
                    )
                except:
                    content[key] = None

        self.callback.info(
            agent_id=self.workflow_instance_id,
            progress="outfit_conclusion",
            message=f"final outfit recommendation is generated",
        )

        # Format recommendation for display
        output_str = "\nThe final outfit recommendation is :\n"
        for category, item in content.items():
            if category != "Styling Notes":
                output_str += f"{category.title()}: {item}\n"
        output_str += f"\nStyling Notes:\n{content.get('Styling Notes', '')}\n"

        logging.info(output_str)
        self.callback.send_answer(
            agent_id=self.workflow_instance_id, msg=content.get("Styling Notes", "")
        )

        return {"outfit_conclusion": output_str}

    def _extract_from_result(self, result: str) -> dict:
        try:
            pattern = r"```json\s+(.*?)\s+```"
            match = re.search(pattern, result, re.DOTALL)
            if match:
                return json_repair.loads(match.group(1))
            else:
                return json_repair.loads(result)
        except Exception as error:
            raise ValueError("LLM generation is not valid.")
