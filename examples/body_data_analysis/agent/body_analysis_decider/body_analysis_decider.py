import json_repair
import re
from pathlib import Path
from typing import List
from pydantic import Field

from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.utils.registry import registry
from omagent_core.models.llms.prompt.prompt import PromptTemplate
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.models.llms.prompt.parser import StrParser
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.utils.logger import logging


CURRENT_PATH = root_path = Path(__file__).parents[0]


@registry.register_worker()
class BodyAnalysisDecider(BaseLLMBackend, BaseWorker):
    llm: OpenaiGPTLLM
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("sys_prompt_en.prompt"), role="system"
            ),
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("user_prompt_en.prompt"), role="user"
            ),
        ]
    )

    def _run(self, *args, **kwargs):

        # Retrieve conversation context from memory, initializing empty if not present
        if self.stm(self.workflow_instance_id).get("user_body_data"):   
            user_body_data = self.stm(self.workflow_instance_id).get("user_body_data")
        else:
            user_body_data = []
        
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
            bodydata=str(user_body_data),
            previous_search=str(search_info),
            feedback=str(feedback)
        )
        content = chat_complete_res["choices"][0]["message"].get("content")
        content = self._extract_from_result(content)
        logging.info(content)

        # Return decision and handle feedback if more information is needed
        if content.get("decision") == "ready":
            return {"decision": True}
        elif content.get("reason"):
            feedback.append(content["reason"])
            self.stm(self.workflow_instance_id)["feedback"] = feedback
            return {"decision": False}
        else:
            raise ValueError("LLM generation is not valid.")
        
        
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