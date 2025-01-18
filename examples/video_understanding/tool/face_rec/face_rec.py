import pickle
from pathlib import Path
from typing import List, Optional

import cv2
import face_recognition
import numpy as np
from PIL import Image
from pydantic import model_validator

from ....models.od.schemas import Target
from ....utils.registry import registry
from ...base import ArgSchema, BaseModelTool

ARGSCHEMA = {}


@registry.register_tool()
class FaceRecognition(BaseModelTool):
    args_schema: ArgSchema = ArgSchema(**ARGSCHEMA)
    description: str = (
        "This tool can recognize facial information in images/extracted frames and identify who the person is."
        "Images/extracted frames are already loaded."
    )
    threshold: float = 0.6
    num_jitters: int = 1
    face_db: str = "data/face_db"
    model: str = "large"
    loaded_face_db: Optional[dict] = None

    @model_validator(mode="after")
    def face_db_validator(self) -> "FaceRecognition":
        if self.loaded_face_db is None:
            if Path(self.face_db).exists():
                self.loaded_face_db = self._load_face_db(self.face_db)
            else:
                raise ValueError(f"Face database not found at {self.face_db}")
        elif isinstance(self.loaded_face_db, dict):
            if (
                "embeddings" not in self.loaded_face_db
                or "names" not in self.loaded_face_db
            ):
                raise ValueError(
                    "Face database must have 'embeddings' and 'names' keys."
                )
        else:
            raise ValueError("Face database must be a dictionary.")
        return self

    def _load_face_db(self, path: str):
        cached_model = Path(path).joinpath(f"representations_{self.model}_face.pkl")
        # if cached_model.exists():
        #     loaded_face_db = pickle.load(open(cached_model, "rb"))
        # else:
        face_db = Path(path)
        embeddings = []
        names = []
        for known_image in face_db.rglob("*"):
            if known_image.suffix in [".jpg", ".png", ".webp"]:
                loaded_image = np.array(Image.open(known_image).convert("RGB"))
                loaded_image = cv2.cvtColor(loaded_image, cv2.COLOR_RGB2BGR)
                known_encoding = face_recognition.face_encodings(
                    loaded_image, model="large"
                )[0]
                embeddings.append(known_encoding)
                names.append(known_image.parent.name)
        loaded_face_db = {"embeddings": embeddings, "names": names}
        pickle.dump(loaded_face_db, open(cached_model, "wb"))
        return loaded_face_db

    def infer(self, image: Image.Image) -> List[Target]:
        img = np.array(image.convert("RGB"))
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        face_locations = face_recognition.face_locations(img)
        face_encodings = face_recognition.face_encodings(img, face_locations)
        rec_res = []
        for (top, right, bottom, left), face_encoding in zip(
            face_locations, face_encodings
        ):
            face_distances = face_recognition.face_distance(
                self.loaded_face_db.get("embeddings"), face_encoding
            )
            best_match_index = np.argmin(face_distances)
            if face_distances[best_match_index] <= self.threshold:
                name = self.loaded_face_db["names"][best_match_index]
                bbox = [left, top, right, bottom]
                rec_res.append(
                    Target(label=name, bbox=bbox, conf=face_distances[best_match_index])
                )
        return rec_res

    def _run(self):
        names = set()
        for key in self.stm.image_cache.keys():
            anno = self.infer(self.stm.image_cache[key])
            self.stm.image_cache[key] = self.visual_prompting(
                self.stm.image_cache[key], anno
            )
            names.update([item.label for item in anno])

        return f"Recognized {len(names)} faces: {', '.join(names)}"

    async def _arun(self):
        return self._run()
