import json
import re
from pathlib import Path
from typing import List

from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.models.llms.prompt import PromptTemplate
from omagent_core.tool_system.base import ArgSchema, BaseTool
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry
from pydantic import Field
from scenedetect import FrameTimecode

from omagent_core.services.handlers.video_scenes import VideoScenes

CURRENT_PATH = Path(__file__).parents[0]

ARGSCHEMA = {
    "start_time": {
        "type": "number",
        "description": "Start time (in seconds) of the video to extract frames from.",
        "required": True,
    },
    "end_time": {
        "type": "number",
        "description": "End time (in seconds) of the video to extract frames from.",
        "required": True,
    },
    "number": {
        "type": "number",
        "description": "Number of frames of extraction. More frames means more details but more cost. Do not exceed 10.",
        "required": True,
    },
}


@registry.register_tool()
class FrameExtraction(BaseTool, BaseLLMBackend):
    args_schema: ArgSchema = ArgSchema(**ARGSCHEMA)
    description: str = (
        "Rollback and extract frames from video which is already loaded to get more specific details for further analysis."
    )
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("rewinder_sys_prompt.prompt"),
                role="system",
            ),
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("rewinder_user_prompt.prompt"),
                role="user",
            ),
        ]
    )

    def _extract_from_result(self, result: str) -> dict:
        try:
            pattern = r"```json\s*(\{(?:.|\s)*?\})\s*```"
            result = result.replace("\n", "")
            match = re.search(pattern, result, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            else:
                return json.loads(result)
        except Exception as error:
            raise ValueError("LLM generation is not valid.")

    def _run(
        self, start_time: float = 0.0, end_time: float = None, number: int = 1
    ) -> str:
        if self.stm.video is None:
            raise ValueError("No video is loaded.")
        else:
            video: VideoScenes = self.stm.video
        if number > 10:
            logging.warning("Number of frames exceeds 10. Will extract 10 frames.")
            number = 10

        start = FrameTimecode(timecode=start_time, fps=video.stream.frame_rate)
        if end_time is None:
            end = video.stream.duration
        else:
            end = FrameTimecode(timecode=end_time, fps=video.stream.frame_rate)

        if start_time == end_time:
            frames, time_stamps = video.get_video_frames(
                (start, end + 1), video.stream.frame_rate
            )
        else:
            interval = int((end.get_frames() - start.get_frames()) / number)
            frames, time_stamps = video.get_video_frames((start, end), interval)

        # self.stm.image_cache.clear()
        extracted_frames = []
        for i, (frame, time_stamp) in enumerate(zip(frames, time_stamps)):
            img_index = f"image_timestamp-{time_stamp}"
            extracted_frames.append(time_stamp)
            if self.stm.image_cache.get(f"<{img_index}>", None) is None:
                self.stm.image_cache[f"<{img_index}>"] = frame
        res = self.simple_infer(
            image_placeholders="".join(
                [f"<image_timestamp-{each}>" for each in extracted_frames]
            )
        )["choices"][0]["message"]["content"]
        image_contents = self._extract_from_result(res)
        return f"{extracted_frames} described as: {image_contents}."

    async def _arun(
        self, start_time: float = 0.0, end_time: float = None, number: int = 1
    ) -> str:
        return self._run(start_time, end_time, number=number)
