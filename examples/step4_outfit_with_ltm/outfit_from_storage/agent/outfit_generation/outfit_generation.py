import re
from pathlib import Path
from typing import List

import json_repair
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.models.llms.prompt import PromptTemplate
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry
from pydantic import Field

CURRENT_PATH = root_path = Path(__file__).parents[0]


@registry.register_worker()
class OutfitGeneration(BaseLLMBackend, BaseWorker):
    """Generates outfit recommendations based on user preferences and weather conditions.

    Uses LLM to process user input and generate contextually appropriate outfit suggestions.
    Structured with prompt templates for consistent LLM interactions.
    """

    llm: OpenaiGPTLLM

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

    def _run(self, *args, **kwargs):
        """Generates outfit recommendations based on user input and weather data.

        Args:
            *args: Variable arguments containing workflow context
            **kwargs: Additional keyword arguments

        Returns:
            dict: Contains the generated outfit recommendation under 'proposed_outfit' key
        """
        # Retrieve user input and weather data from short-term memory
        user_instruct = self.stm(self.workflow_instance_id).get("user_instruction")
        search_info = (
            self.stm(self.workflow_instance_id)["search_info"]
            if "search_info" in self.stm(self.workflow_instance_id)
            else None
        )

        # Generate outfit suggestion using LLM inference
        chat_complete_res = self.simple_infer(
            weather=str(search_info), instruction=str(user_instruct)
        )
        content = chat_complete_res["choices"][0]["message"].get("content")
        content = self._extract_from_result(content)

        self.callback.info(
            agent_id=self.workflow_instance_id,
            progress="outfit_generation",
            message=f"proposed outfit is generated",
        )
        logging.info(f"proposed outfit according instruction: {content}")

        return {"proposed_outfit": content}

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
