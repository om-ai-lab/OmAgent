import json
import re
from pathlib import Path
from typing import List

from omagent_core.core.llm.base import BaseLLMBackend
from omagent_core.core.node.base import BaseProcessor
from omagent_core.core.node.dnc.interface import DnCInterface
from omagent_core.core.prompt.prompt import PromptTemplate
from omagent_core.handlers.data_handler.ltm import LTM
from omagent_core.utils.registry import registry
from pydantic import Field

CURRENT_PATH = root_path = Path(__file__).parents[0]


@registry.register_node()
class VideoQA(BaseProcessor, BaseLLMBackend):
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

    def _run(self, args: DnCInterface, ltm: LTM) -> DnCInterface:
        video_md5 = args.kwargs.get("video_md5", None)
        self.stm.image_cache.clear()
        self.stm.former_results = {}
        question = input("Please input your question:")
        chat_complete_res = self.simple_infer(question=question)
        content = chat_complete_res["choices"][0]["message"]["content"]
        content = self._extract_from_result(content)
        start_time = (
            None if content.get("start_time", -1) == -1 else content.get("start_time")
        )
        end_time = (
            None if content.get("end_time", -1) == -1 else content.get("end_time")
        )
        # todo: handler alias
        related_information = ltm.VideoHandler.text_match(
            video_md5, question, 0.5, start_time, end_time
        )
        related_information = related_information[: min(50, len(related_information))]
        related_information = [
            f"Time span: {each['start_time']} - {each['end_time']}\n{each['content']}"
            for each in related_information
        ]
        self.stm.video_summary = "\n---\n".join(related_information)
        args.task.task = question

        return args

    def _extract_from_result(self, result: str) -> dict:
        try:
            pattern = r"```json\s+(.*?)\s+```"
            match = re.search(pattern, result, re.DOTALL)
            if match:
                return json.loads(
                    re.sub(r"[\x00-\x1f\x7f]", "", match.group(1)).replace("\n", "")
                )
            else:
                return json.loads(result)
        except Exception as error:
            raise ValueError("LLM generation is not valid.")
