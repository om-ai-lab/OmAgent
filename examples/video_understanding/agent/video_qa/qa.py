import json
import re
from pathlib import Path
from typing import List

import json_repair
from omagent_core.advanced_components.workflow.dnc.schemas.dnc_structure import \
    TaskTree
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.memories.ltms.ltm import LTM
from omagent_core.models.encoders.openai_encoder import OpenaiTextEmbeddingV3
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.models.llms.prompt import PromptTemplate
from omagent_core.utils.registry import registry
from pydantic import Field

from ..misc.scene import VideoScenes

CURRENT_PATH = root_path = Path(__file__).parents[0]


@registry.register_worker()
class VideoQA(BaseWorker, BaseLLMBackend):
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
    text_encoder: OpenaiTextEmbeddingV3

    def _run(self, video_md5: str, *args, **kwargs):
        self.stm(self.workflow_instance_id)["image_cache"] = {}
        self.stm(self.workflow_instance_id)["former_results"] = {}
        question = self.input.read_input(
            workflow_instance_id=self.workflow_instance_id,
            input_prompt="Please input your question:",
        )["messages"][0]["content"][0]["data"]
        chat_complete_res = self.simple_infer(question=question)
        content = chat_complete_res["choices"][0]["message"]["content"]
        content = json_repair.loads(content)
        try:
            start_time = (
                None if content.get("start_time", -1) == -1 else content.get("start_time")
            )
            end_time = (
                None if content.get("end_time", -1) == -1 else content.get("end_time")
            )
        except Exception as e:
            start_time = None
            end_time = None
        question_vector = self.text_encoder.infer([question])[0]
        filter_expr = ""
        if video_md5 is not None:
            filter_expr = f"value['video_md5']=='{video_md5}'"
        if start_time is not None and end_time is not None:
            filter_expr += f" and (value['start_time']>={max(0, start_time - 10)} and value['end_time']<={end_time + 10})"
        elif start_time is not None:
            filter_expr += f" and value['start_time']>={max(0, start_time - 10)}"
        elif end_time is not None:
            filter_expr += f" and value['end_time']<={end_time + 10}"
        related_information = self.ltm.get_by_vector(
            embedding=question_vector, top_k=5, threshold=0.2, filter=filter_expr
        )
        related_information = [
            f"Time span: {each['start_time']} - {each['end_time']}\n{each['content']}"
            for _, each in related_information
        ]
        video = VideoScenes.from_serializable(
            self.stm(self.workflow_instance_id)["video"]
        )
        self.stm(self.workflow_instance_id)["extra"] = {
            "video_information": "video is already loaded in the short-term memory(stm).",
            "video_duration_seconds(s)": video.stream.duration.get_seconds(),
            "frame_rate": video.stream.frame_rate,
            "video_summary": "\n---\n".join(related_information),
        }
        return {"query": question, "last_output": None}
