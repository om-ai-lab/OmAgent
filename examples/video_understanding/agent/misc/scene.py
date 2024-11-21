from typing import Dict, List, Optional, Tuple, Union

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
            output_conversation = "\n".join([f"{item.get('text', None)}" for item in self.stt_res])
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
        kernel_size: Optional[int] = None,
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
        weight = ContentDetector.Components(
            delta_hue=1.0,
            delta_sat=1.0,
            delta_lum=0.0,
            delta_edges=1.0,
        )
        if kernel_size is None:
            scene_manager.add_detector(
                ContentDetector(
                    threshold=threshold, min_scene_len=video.frame_rate * min_scene_len, weights=weight
                )
            )
        else:
            scene_manager.add_detector(
                ContentDetector(
                    threshold=threshold, min_scene_len=video.frame_rate * min_scene_len, weights=weight, kernel_size=kernel_size
                )
            )
        scene_manager.detect_scenes(video, show_progress=show_progress)
        scenes = scene_manager.get_scene_list(start_in_scene=True)

        try:
            audio = AudioSegment.from_file(video_path)
            audio = normalize(audio)
        except (IndexError, OSError):
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

    def to_serializable(self) -> dict:
        """Convert VideoScenes to a serializable dictionary."""
        scenes_data = []
        for scene in self.scenes:
            scenes_data.append({
                'start_frame': scene.start.frame_num,
                'end_frame': scene.end.frame_num,
                'stt_res': scene.stt_res,
                'summary': scene.summary
            })
            
        return {
            'video_path': self.stream.path,
            'frame_rate': self.stream.frame_rate,
            'scenes': scenes_data,
            'frame_extraction_interval': self.frame_extraction_interval
        }

    @classmethod
    def from_serializable(cls, data: dict):
        """Rebuild VideoScenes from serialized data."""
        video = open_video(data['video_path'])
        try:
            audio = AudioSegment.from_file(data['video_path'])
            audio = normalize(audio)
        except Exception:
            audio = None
        
        # Rebuild scenes list
        scenes = []
        for scene_data in data['scenes']:
            start = FrameTimecode(scene_data['start_frame'], data['frame_rate'])
            end = FrameTimecode(scene_data['end_frame'], data['frame_rate'])
            scene = Scene.init(start, end)
            scene.stt_res = scene_data['stt_res']
            scene.summary = scene_data['summary']
            scenes.append(scene)
            
        return cls(
            stream=video,
            scenes=scenes,
            audio=audio,
            frame_extraction_interval=data['frame_extraction_interval']
        )
