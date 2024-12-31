import re
from pathlib import Path
from typing import List

import json_repair
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.models.llms.prompt.prompt import PromptTemplate
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry
from pydantic import Field

CURRENT_PATH = root_path = Path(__file__).parents[0]


@registry.register_worker()
class WeatherDecider(BaseLLMBackend, BaseWorker):
    """Weather decider node that determines if weather information is provided in user input.

    This node:
    1. Takes user instruction from workflow context
    2. Uses LLM to analyze if weather information is present in the instruction
    3. Returns a switch case value (0 or 1) to control workflow branching
    4. Logs and sends notifications about weather info status

    Attributes:
        llm (OpenaiGPTLLM): LLM model for analyzing weather info
        prompts (List[PromptTemplate]): System and user prompts loaded from files
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

    def _run(self, user_instruction: str, *args, **kwargs):
        """Process user instruction to determine if it contains weather information.

        Args:
            user_instruction (str): The user's input text to analyze
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments

        Returns:
            dict: Contains 'switch_case_value' key with value:
                  1 if weather info found in instruction
                  0 if weather info not found and needs to be searched

        Raises:
            ValueError: If LLM output cannot be parsed as valid JSON
        """
        self.stm(self.workflow_instance_id)["user_instruction"] = user_instruction

        chat_complete_res = self.simple_infer(instruction=user_instruction)

        content = chat_complete_res["choices"][0]["message"]["content"]
        content = self._extract_from_result(content)
        logging.info(content)

        if content.get("weatherInfo_provided") is not None:
            weatherInfo_provided = content["weatherInfo_provided"]
            if weatherInfo_provided:
                self.callback.info(
                    agent_id=self.workflow_instance_id,
                    progress="Weather Decider",
                    message="Weather information provided",
                )
                return {"switch_case_value": 1}
            else:
                self.callback.info(
                    agent_id=self.workflow_instance_id,
                    progress="Weather Decider",
                    message="Need web search for weather information",
                )
                return {"switch_case_value": 0}
        else:
            raise ValueError("LLM generation is not valid.")

    def _extract_from_result(self, result: str) -> dict:
        """Extract JSON content from LLM response.

        Args:
            result (str): Raw LLM response text

        Returns:
            dict: Parsed JSON content

        Raises:
            ValueError: If response cannot be parsed as valid JSON
        """
        try:
            pattern = r"```json\s*(\{(?:.|\s)*?\})\s*```"
            result = result.replace("\n", "")
            match = re.search(pattern, result, re.DOTALL)
            if match:
                return json_repair.loads(match.group(1))
            else:
                return json_repair.loads(result)
        except Exception as error:
            raise ValueError("LLM generation is not valid.")
