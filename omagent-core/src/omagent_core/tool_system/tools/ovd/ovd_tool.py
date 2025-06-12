from pathlib import Path
from typing import List

import requests
from PIL import Image
from scenedetect import FrameTimecode

from ....models.od.schemas import Target
from ....utils.general import encode_image
from ....utils.registry import registry
from ...base import ArgSchema, BaseModelTool

CURRENT_PATH = Path(__file__).parents[0]

ARGSCHEMA = {
    "timestamps": {
        "type": "string",
        "description": "Timestamp(seconds) of frames that need to be object detected, split by comma.",
        "required": True,
    },
    "labels": {
        "type": "string",
        "description": "Labels the object detection tool will use to detect objects in the image, split by comma.",
        "required": True,
    },
}


@registry.register_tool()
class VideoObjectDetection(BaseModelTool):
    args_schema: ArgSchema = ArgSchema(**ARGSCHEMA)
    description: str = (
        "Object detection tool, which can detect any objects and add visual prompting(bounding box and label) to the image."
        "Tasks like object counting, specific object detection, etc. must use this tool."
    )
    ovd_endpoint: str = ""
    model_id: str = "OmDet-Turbo_tiny_SWIN_T"

    class Config:
        """Configuration for this pydantic object."""

        protected_namespaces = ()

    def _run(self, timestamps: str, labels: str) -> str:
        if self.ovd_endpoint is None or self.ovd_endpoint == "":
            raise ValueError("ovd_endpoint is required.")
        timestamps = timestamps.split(",")
        imgs_pil = []
        for each_time_stamp in timestamps:
            if (
                self.stm.image_cache.get(
                    f"<image_timestamp-{float(each_time_stamp)}>", None
                )
                is None
            ):
                frames, time_stamps = self.stm.video.get_video_frames(
                    (
                        FrameTimecode(
                            timecode=float(each_time_stamp),
                            fps=self.stm.video.stream.frame_rate,
                        ),
                        FrameTimecode(
                            timecode=float(each_time_stamp) + 1,
                            fps=self.stm.video.stream.frame_rate,
                        ),
                    ),
                    self.stm.video.stream.frame_rate,
                )
                [
                    self.stm.image_cache.update(
                        {f"<image_timestamp-{each_img_name}>": each_frame}
                    )
                    for each_frame, each_img_name in zip(frames, time_stamps)
                ]
                # timestamps = [f'<image_timestamp-{each_img_name}' for each_img_name in time_stamps]
                imgs_pil = [each_frame for each_frame in frames]
            else:
                imgs_pil.append(
                    self.stm.image_cache[f"<image_timestamp-{float(each_time_stamp)}>"]
                )

        infer_targets = self.infer(imgs_pil, {"labels": labels.split(",")})
        for img_name, img, infer_target in zip(timestamps, imgs_pil, infer_targets):
            self.stm.image_cache[f"<image_timestamp-{img_name}>"] = (
                self.visual_prompting(img, infer_target)
            )

        return f"OVD tool has detected objects in timestamps of {timestamps} and update image."

    async def _arun(self, timestamps: str, labels: str) -> str:
        return self._run(timestamps, labels)

    def infer(self, images: List[Image.Image], kwargs) -> List[List[Target]]:
        labels = kwargs.get("labels", [])
        ovd_payload = {
            "model_id": self.model_id,
            "data": [encode_image(img) for img in images],
            "src_type": "base64",
            "task": f"Detect {','.join(labels)}.",
            "labels": labels,
            "threshold": 0.3,
        }
        res = requests.post(self.ovd_endpoint, json=ovd_payload)
        if res.status_code != 200:
            raise ValueError(
                f"OVD tool failed to detect objects in the images. {res.text}"
            )
        res = res.json()
        targets = []
        for img in res["objects"]:
            current_img_targets = []
            for bbox in img:
                x0 = bbox["xmin"]
                y0 = bbox["ymin"]
                x1 = bbox["xmax"]
                y1 = bbox["ymax"]
                conf = bbox["conf"]
                label = bbox["label"]
                current_img_targets.append(
                    Target(bbox=[x0, y0, x1, y1], conf=conf, label=label)
                )
            targets.append(current_img_targets)
        return targets
