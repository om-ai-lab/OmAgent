import re
from pathlib import Path
from typing import List

import json_repair
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.models.llms.prompt.parser import StrParser
from omagent_core.models.llms.prompt.prompt import PromptTemplate
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry
from pydantic import Field

CURRENT_PATH = root_path = Path(__file__).parents[0]


@registry.register_worker()
class OutfitDecider(BaseLLMBackend, BaseWorker):
    """Outfit decision processor that determines if enough information has been gathered.

    This processor evaluates whether sufficient information exists to make an outfit recommendation
    by analyzing user instructions, search results, and any feedback received. It uses an LLM to
    make this determination.

    If enough information is available, it returns success. Otherwise, it returns failed along with
    feedback about what additional information is needed.

    Attributes:
        output_parser: Parser for string outputs from the LLM
        llm: OpenAI GPT language model instance
        prompts: List of system and user prompts loaded from template files
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
        """Process the current state to determine if an outfit recommendation can be made.

        Retrieves the current user instructions, search information, and feedback from the
        short-term memory. Uses the LLM to analyze this information and determine if
        sufficient details exist to make a recommendation.

        Args:
            args: Variable length argument list
            kwargs: Arbitrary keyword arguments

        Returns:
            dict: Contains 'decision' key with:
                - True if enough information exists to make a recommendation
                - False if more information is needed, also stores feedback about what's missing
        """
        # Retrieve context data from short-term memory, using empty lists as defaults
        if self.stm(self.workflow_instance_id).get("user_instruction"):
            user_instruct = self.stm(self.workflow_instance_id).get("user_instruction")
        else:
            user_instruct = []

        if self.stm(self.workflow_instance_id).get("search_info"):
            search_info = self.stm(self.workflow_instance_id).get("search_info")
        else:
            search_info = []

        if self.stm(self.workflow_instance_id).get("feedback"):
            feedback = self.stm(self.workflow_instance_id).get("feedback")
        else:
            feedback = []

        # Query LLM to analyze available information
        chat_complete_res = self.simple_infer(
            instruction=str(user_instruct),
            previous_search=str(search_info),
            feedback=str(feedback),
        )
        content = chat_complete_res["choices"][0]["message"].get("content")
        content = self._extract_from_result(content)
        logging.info(content)

        # Return decision and handle feedback if more information is needed
        if content.get("decision") == "ready":
            return {"decision": True}
        else:
            feedback.append(content["reason"])
            self.stm(self.workflow_instance_id)["feedback"] = feedback
            return {"decision": False}

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
