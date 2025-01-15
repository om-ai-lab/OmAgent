from typing import Dict, List, Optional, Tuple, Union

import cv2
from omagent_core.utils.logger import logging
from PIL import Image
from pydantic import BaseModel
from pydub import AudioSegment
from pydub.effects import normalize
from scenedetect import (ContentDetector, FrameTimecode, SceneManager,
                         VideoStream, open_video)


class Scene(BaseModel):
    start: FrameTimecode
    end: FrameTimecode
    stt_res: Optional[Dict] = None
    summary: Optional[Dict] = None

    class Config:
        """Configuration for this pydantic object."""

        arbitrary_types_allowed = True

    @classmethod
    def init(cls, start: FrameTimecode, end: FrameTimecode, summary: dict = None):
        return cls(start=start, end=end, summary=summary)

    @property
    def conversation(self):
        # for self deployed whisper
        if isinstance(self.stt_res, list):
            output_conversation = "\n".join(
                [f"{item.get('text', None)}" for item in self.stt_res]
            )
        else:
            output_conversation = self.stt_res
        return output_conversation


class VideoScenes(BaseModel):
    stream: VideoStream
    audio: Union[AudioSegment, None]
    scenes: List[Scene]
    frame_extraction_interval: int

    class Config:
        """Configuration for this pydantic object."""

        extra = "allow"
        arbitrary_types_allowed = True

    @classmethod
    def load(
        cls,
        video_path: str,
        threshold: int = 27,
        min_scene_len: int = 1,
        frame_extraction_interval: int = 5,
        show_progress: bool = False,
    ):
        """Load a video file.

        Args:
            video_path (str): The path of the video file. Only support local file.
            threshold (int): The scene detection threshold.
            min_scene_len (int): Once a cut is detected, this long time must pass before a new one can
                be added to the scene list. Count in seconds, defaults to 1.
            show_progress (bool, optional): Whether to display the progress bar when processing the video. Defaults to False.
        """
        video = open_video(video_path)
        scene_manager = SceneManager()
        scene_manager.add_detector(
            ContentDetector(
                threshold=threshold, min_scene_len=video.frame_rate * min_scene_len
            )
        )
        scene_manager.detect_scenes(video, show_progress=show_progress)
        scenes = scene_manager.get_scene_list(start_in_scene=True)

        try:
            audio = AudioSegment.from_file(video_path)
            audio = normalize(audio)
        except Exception as e:
            logging.warning(f"Failed to load audio from {video_path}: {e}")
            audio = None
        return cls(
            stream=video,
            scenes=[Scene.init(*scene) for scene in scenes],
            audio=audio,
            frame_extraction_interval=frame_extraction_interval,
        )

    def get_video_frames(
        self, scene: Union[int, Scene, Tuple[FrameTimecode]], interval: int = None
    ) -> Tuple[List[Image.Image], List[float]]:
        """Get the frames of a scene.

        Args:
            scene (Union[int, Scene, Tuple[FrameTimecode]]): The scene to get frames. Can be the index of the scene, the scene object or a tuple of start and end frame timecode.
            interval (int, optional): The interval of the frames to get. Defaults to None.
        Raises:
            ValueError: If the type of scene is not int, Scene or tuple.

        Returns:
            List[ndarray]: The frames of the scene.
        """
        if isinstance(scene, int):
            scene = self.scenes[scene]
            start, end = scene.start, scene.end
        elif isinstance(scene, Scene):
            start, end = scene.start, scene.end
        elif isinstance(scene, tuple):
            start, end = scene
        else:
            raise ValueError(
                f"scene should be int, Scene or tuple, not {type(scene).__name__}"
            )
        self.stream.seek(start)
        frames = []
        time_stamps = []
        if interval is None:
            interval = self.frame_extraction_interval * self.stream.frame_rate
        scene_len = end.get_frames() - start.get_frames()
        if scene_len / 10 > interval:
            interval = int(scene_len / 10) + 1
        for index in range(scene_len):
            if index % interval == 0:
                f = self.stream.read()
                if f is False:
                    continue
                f = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
                frames.append(Image.fromarray(f))
                time_stamps.append(self.stream.position.get_seconds())
            else:
                self.stream.read(decode=False)
        self.stream.seek(0)
        return frames, time_stamps

    def get_audio_clip(
        self, scene: Union[int, Scene, Tuple[FrameTimecode]]
    ) -> AudioSegment:
        """Get the audio clip of a scene.

        Args:
            scene (Union[int, Scene, Tuple[FrameTimecode]]): The scene to get audio clip. Can be the index of the scene, the scene object or a tuple of start and end frame timecode.

        Raises:
            ValueError: If the type of scene is not int, Scene or tuple.

        Returns:
            AudioSegment: The audio clip of the scene.
        """
        if self.audio is None:
            return None
        if isinstance(scene, int):
            scene = self.scenes[scene]
            start, end = scene.start, scene.end
        elif isinstance(scene, Scene):
            start, end = scene.start, scene.end
        elif isinstance(scene, tuple):
            start, end = scene
        else:
            raise ValueError(
                f"scene should be int, Scene or tuple, not {type(scene).__name__}"
            )

        return self.audio[
            int(start.get_seconds() * 1000) : int(end.get_seconds() * 1000)
        ]

    def __len__(self):
        return len(self.scenes)

    def __iter__(self):
        self.index = 0
        return self

    def __next__(self):
        if self.index >= len(self.scenes):
            raise StopIteration
        scene = self.scenes[self.index]
        self.index += 1
        return scene

    def __getitem__(self, index):
        return self.scenes[index]

    def __setitem__(self, index, value):
        self.scenes[index] = value
