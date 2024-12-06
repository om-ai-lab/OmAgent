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
class LoopDecider(BaseLLMBackend, BaseWorker):
    """Loop decider worker that determines if enough information is available to make a recommendation."""
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
        
        # Retrieve context data from short-term memory, using empty lists as defaults
        if self.stm(self.workflow_instance_id).get("hand_image_cache"):   
            hand_image = self.stm(self.workflow_instance_id).get("hand_image_cache")
        else:
            hand_image = []
        
        if self.stm(self.workflow_instance_id).get("face_image_cache"):
            face_image = self.stm(self.workflow_instance_id).get("face_image_cache")
        else:
            face_image = []
        
        if self.stm(self.workflow_instance_id).get("user_instruction"):
            user_instruction = self.stm(self.workflow_instance_id).get("user_instruction")
        else:
            user_instruction = []

        # Query LLM to analyze available information
        print(self.llm)
        chat_complete_res = self.simple_infer(
            hand_image=hand_image.get("<image_0>"),
            face_image=face_image.get("<image_0>"),
            speed=str(user_instruction)
        )
        content = chat_complete_res["choices"][0]["message"].get("content")
        content = self._extract_from_result(content)
        logging.info(content)

        # Return decision based on LLM output
        if content.get("decision") == "no":
            self.callback.send_answer(agent_id=self.workflow_instance_id, msg=content.get("reason"))
            return {"decision": True}
        else:
            self.callback.send_answer(agent_id=self.workflow_instance_id, msg=content.get("reason"))
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