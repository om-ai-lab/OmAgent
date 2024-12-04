import hashlib
import pickle
from pathlib import Path
from typing import List

from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.models.llms.prompt.parser import DictParser
from omagent_core.models.llms.prompt import PromptTemplate
from omagent_core.memories.ltms.ltm import LTM
from omagent_core.engine.workflow.context import BaseWorkflowContext
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry
from pydantic import Field, field_validator
from pydub import AudioSegment
from pydub.effects import normalize
from scenedetect import open_video

from ....models.asr.stt import STT

from omagent_core.services.handlers.video_scenes import VideoScenes

CURRENT_PATH = root_path = Path(__file__).parents[0]
PARSER = DictParser()


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
    stt: STT

    scene_detect_threshold: int = 27
    min_scene_len: int = 1
    frame_extraction_interval: int = 5
    show_progress: bool = True

    use_cache: bool = True
    cache_dir: str = "./running_logs/video_cache"

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
            # 读取文件内容并更新哈希对象
            for byte_block in iter(lambda: file.read(4096), b""):
                md5_hash.update(byte_block)
        # 返回MD5哈希值
        return md5_hash.hexdigest()

    def _run(self, args: BaseWorkflowContext, ltm: LTM) -> BaseWorkflowContext:
        video_path = input("Please input the video path:")
        video_md5 = self.calculate_md5(video_path)
        args.kwargs["video_md5"] = video_md5

        cache_path = (
            Path(self.cache_dir)
            .joinpath(video_path.replace("/", "-"))
            .joinpath("video_cache.pkl")
        )
        if self.use_cache and cache_path.exists():
            with open(cache_path, "rb") as f:
                loaded_scene = pickle.load(f)
                try:
                    audio = AudioSegment.from_file(video_path)
                    audio = normalize(audio)
                except Exception as e:
                    logging.warning(f"Failed to load audio from {video_path}: {e}")
                    audio = None
                video = VideoScenes(
                    stream=open_video(video_path),
                    audio=audio,
                    scenes=loaded_scene,
                    frame_extraction_interval=self.frame_extraction_interval,
                )
                logging.info(
                    "Loaded video scenes from cache.\nResume the interrupted transfer for results with scene.summary of None."
                )
                for index, scene in enumerate(video.scenes):
                    if scene.summary is None:
                        logging.info(
                            f"Resume the interrupted transfer for scene {index}."
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
                            scene.summary = PARSER.parse(
                                chat_complete_res[0]["choices"][0]["message"]["content"]
                            )
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
                            ltm.VideoHandler.text_add(
                                video_md5, content, start_time, end_time
                            )
                        except Exception as e:
                            logging.error(
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
                self.stm.video = video
            with open(cache_path, "wb") as f:
                pickle.dump(video.scenes, f)

        if not self.stm.has("video"):
            video = VideoScenes.load(
                video_path=video_path,
                threshold=self.scene_detect_threshold,
                min_scene_len=self.min_scene_len,
                frame_extraction_interval=self.frame_extraction_interval,
                show_progress=self.show_progress,
            )
            self.stm.video = video

            # HACK: Perform scene detection and ASR separately, and then align their results.
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
                    scene.summary = PARSER.parse(
                        chat_complete_res[0]["choices"][0]["message"]["content"]
                    )
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
                    ltm.VideoHandler.text_add(video_md5, content, start_time, end_time)
                except Exception as e:
                    logging.error(f"Failed to process scene {index}: {e}")
                    scene.summary = None

        if self.use_cache and not cache_path.exists():
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_path, "wb") as f:
                pickle.dump(video.scenes, f)
        return args

    async def _arun(self, args: BaseWorkflowContext, ltm: LTM) -> BaseWorkflowContext:
        video_path = input("Please input the video path:")
        video_md5 = self.calculate_md5(video_path)
        args.kwargs["video_md5"] = video_md5

        cache_path = (
            Path(self.cache_dir)
            .joinpath(video_path.replace("/", "-"))
            .joinpath("video_cache.pkl")
        )
        if self.use_cache and cache_path.exists():
            with open(cache_path, "rb") as f:
                loaded_scene = pickle.load(f)
                video = VideoScenes(
                    stream=open_video(video_path),
                    audio=AudioSegment.from_file(video_path),
                    scenes=loaded_scene,
                    frame_extraction_interval=self.frame_extraction_interval,
                )
                logging.info(
                    "Loaded video scenes from cache.\nResume the interrupted transfer for results with scene.summary of None."
                )
                for index, scene in enumerate(video.scenes):
                    if scene.summary is None:
                        logging.info(
                            f"Resume the interrupted transfer for scene {index}."
                        )
                        video_frames, time_stamps = video.get_video_frames(scene)
                        try:
                            chat_complete_res = await self.ainfer(
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
                            scene.summary = PARSER.parse(
                                chat_complete_res[0]["choices"][0]["message"]["content"]
                            )
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
                            ltm.VideoHandler.text_add(
                                video_md5, content, start_time, end_time
                            )
                        except Exception as e:
                            logging.error(
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
                self.stm.video = video
            with open(cache_path, "wb") as f:
                pickle.dump(video.scenes, f)

        if not self.stm.has("video"):
            video = VideoScenes.load(
                video_path=video_path,
                threshold=self.scene_detect_threshold,
                min_scene_len=self.min_scene_len,
                frame_extraction_interval=self.frame_extraction_interval,
                show_progress=self.show_progress,
            )
            self.stm.video = video

            # HACK: Perform scene detection and ASR separately, and then align their results.
            for index, scene in enumerate(video.scenes):
                print(f"Processing scene {index} / {len(video.scenes)}...")
                audio_clip = video.get_audio_clip(scene)
                if audio_clip is None:
                    scene.stt_res = {"text": ""}
                else:
                    scene.stt_res = await self.stt.ainfer(audio_clip)
                video_frames, time_stamps = video.get_video_frames(scene)
                try:
                    face_rec = registry.get_tool("FaceRecognition")
                    for frame in video_frames:
                        objs = face_rec.ainfer(frame)
                        face_rec.visual_prompting(frame, objs)
                except Exception:
                    pass
                try:
                    chat_complete_res = self.ainfer(
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
                    scene.summary = PARSER.parse(
                        chat_complete_res[0]["choices"][0]["message"]["content"]
                    )
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
                    ltm.VideoHandler.text_add(video_md5, content, start_time, end_time)
                except Exception as e:
                    logging.error(f"Failed to process scene {index}: {e}")
                    scene.summary = None

        if self.use_cache and not cache_path.exists():
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_path, "wb") as f:
                pickle.dump(video.scenes, f)
        return args
