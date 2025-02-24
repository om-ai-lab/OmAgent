import hashlib
import pickle
import time
from pathlib import Path
from typing import List, Optional, Union

import json_repair
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.models.asr.stt import STT
from omagent_core.models.encoders.openai_encoder import OpenaiTextEmbeddingV3
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.models.llms.prompt import PromptTemplate
from omagent_core.utils.registry import registry
from pydantic import Field, field_validator
from pydub import AudioSegment
from pydub.effects import normalize
from scenedetect import open_video

from ..misc.scene import VideoScenes

CURRENT_PATH = root_path = Path(__file__).parents[0]


@registry.register_worker()
class VideoPreprocessor(BaseLLMBackend, BaseWorker):
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

    stt: STT
    scene_detect_threshold: Union[float, int] = 27
    min_scene_len: int = 1
    frame_extraction_interval: int = 5
    kernel_size: Optional[int] = None
    show_progress: bool = True

    use_cache: bool = False
    cache_dir: str = "./video_cache"

    @field_validator("stt", mode="before")
    @classmethod
    def validate_asr(cls, stt):
        if isinstance(stt, STT):
            return stt
        elif isinstance(stt, dict):
            return STT(**stt)
        else:
            raise ValueError("Invalid STT type.")

    def calculate_md5(self, file_path):
        md5_hash = hashlib.md5()
        with open(file_path, "rb") as file:
            for byte_block in iter(lambda: file.read(4096), b""):
                md5_hash.update(byte_block)
        return md5_hash.hexdigest()

    def _run(self, test: str, *args, **kwargs):
        """
        Process video files by:
        1. Calculating MD5 hash of input video for caching
        2. Loading video from cache if available and use_cache=True
        3. Otherwise, processing video by:
           - Extracting audio and video streams
           - Detecting scene boundaries
           - Extracting frames at specified intervals
           - Generating scene summaries using LLM
           - Caching results for future use

        Args:
            video_path (str): Path to input video file
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments

        Returns:
            dict: Dictionary containing video_md5 and video_path
        """
        video_path = self.input.read_input(
            workflow_instance_id=self.workflow_instance_id,
            input_prompt="Please input the video path:",
        )["messages"][0]["content"][0]["data"]
        video_md5 = self.calculate_md5(video_path)
        kwargs["video_md5"] = video_md5

        cache_path = (
            Path(self.cache_dir)
            .joinpath(video_path.replace("/", "-"))
            .joinpath("video_cache.pkl")
        )
        # Load video from cache if available
        if self.use_cache and cache_path.exists():
            with open(cache_path, "rb") as f:
                loaded_scene = pickle.load(f)
                try:
                    audio = AudioSegment.from_file(video_path)
                    audio = normalize(audio)
                except Exception:
                    audio = None
                video = VideoScenes(
                    stream=open_video(video_path),
                    audio=audio,
                    scenes=loaded_scene,
                    frame_extraction_interval=self.frame_extraction_interval,
                )
                self.callback.send_block(
                    agent_id=self.workflow_instance_id,
                    msg="Loaded video scenes from cache.\nResume the interrupted transfer for results with scene.summary of None.",
                )
                for index, scene in enumerate(video.scenes):
                    if scene.summary is None:
                        self.callback.send_block(
                            agent_id=self.workflow_instance_id,
                            msg=f"Resume the interrupted transfer for scene {index}.",
                        )
                        video_frames, time_stamps = video.get_video_frames(scene)
                        try:
                            chat_complete_res = self.infer(
                                input_list=[
                                    {
                                        "stt_res": scene.conversation,
                                        "img_placeholders": "".join(
                                            [
                                                f"<image_{i}>"
                                                for i in range(len(video_frames))
                                            ]
                                        ),
                                    }
                                ],
                                images=video_frames,
                            )
                            scene.summary = chat_complete_res[0]["choices"][0][
                                "message"
                            ]["content"]
                            scene_info = scene.summary.get("scene", [])
                            events = scene.summary.get("events", [])
                            start_time = scene.start.get_seconds()
                            end_time = scene.end.get_seconds()
                            content = (
                                f"Time in video: {scene.summary.get('time', 'null')}\n"
                                f"Location: {scene.summary.get('location', 'null')}\n"
                                f"Character': {scene.summary.get('character', 'null')}\n"
                                f"Events: {events}\n"
                                f"Scene: {scene_info}\n"
                                f"Summary: {scene.summary.get('summary', '')}"
                            )
                            content_vector = self.text_encoder.infer([content])[0]
                            self.ltm[index] = {
                                "value": {
                                    "video_md5": video_md5,
                                    "content": content,
                                    "start_time": start_time,
                                    "end_time": end_time,
                                },
                                "embedding": content_vector,
                            }
                        except Exception as e:
                            self.callback.error(
                                f"Failed to resume scene {index}: {e}. Set to default."
                            )
                            scene.summary = {
                                "time": "",
                                "location": "",
                                "character": "",
                                "events": [],
                                "scene": [],
                                "summary": "",
                            }
                self.stm(self.workflow_instance_id)["video"] = video.to_serializable()
            # Cache the processed video scenes
            with open(cache_path, "wb") as f:
                pickle.dump(video.scenes, f)

        # Process video if not loaded from cache
        if not self.stm(self.workflow_instance_id).get("video", None):
            video = VideoScenes.load(
                video_path=video_path,
                threshold=self.scene_detect_threshold,
                min_scene_len=self.min_scene_len,
                frame_extraction_interval=self.frame_extraction_interval,
                show_progress=self.show_progress,
                kernel_size=self.kernel_size,
            )
            self.stm(self.workflow_instance_id)["video"] = video.to_serializable()

            for index, scene in enumerate(video.scenes):
                print(f"Processing scene {index} / {len(video.scenes)}...")
                audio_clip = video.get_audio_clip(scene)
                if audio_clip is None:
                    scene.stt_res = {"text": ""}
                else:
                    scene.stt_res = self.stt.infer(audio_clip)
                video_frames, time_stamps = video.get_video_frames(scene)
                try:
                    face_rec = registry.get_tool("FaceRecognition")
                    for frame in video_frames:
                        objs = face_rec.infer(frame)
                        face_rec.visual_prompting(frame, objs)
                except Exception:
                    pass
                try:
                    chat_complete_res = self.infer(
                        input_list=[
                            {
                                "stt_res": scene.conversation,
                                "img_placeholders": "".join(
                                    [f"<image_{i}>" for i in range(len(video_frames))]
                                ),
                            }
                        ],
                        images=video_frames,
                    )
                    scene.summary = chat_complete_res[0]["choices"][0]["message"][
                        "content"
                    ]
                    scene_info = scene.summary.get("scene", [])
                    events = scene.summary.get("events", [])
                    start_time = scene.start.get_seconds()
                    end_time = scene.end.get_seconds()
                    content = (
                        f"Time in video: {scene.summary.get('time', 'null')}\n"
                        f"Location: {scene.summary.get('location', 'null')}\n"
                        f"Character': {scene.summary.get('character', 'null')}\n"
                        f"Events: {events}\n"
                        f"Scene: {scene_info}\n"
                        f"Summary: {scene.summary.get('summary', '')}"
                    )
                    content_vector = self.text_encoder.infer([content])[0]
                    self.ltm[index] = {
                        "value": {
                            "video_md5": video_md5,
                            "content": content,
                            "start_time": start_time,
                            "end_time": end_time,
                        },
                        "embedding": content_vector,
                    }
                except Exception as e:
                    self.callback.error(f"Failed to process scene {index}: {e}")
                    scene.summary = None

        if self.use_cache and not cache_path.exists():
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_path, "wb") as f:
                pickle.dump(video.scenes, f)
        return {
            "video_md5": video_md5
        }
