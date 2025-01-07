import datetime
import re
import time
from enum import Enum
from itertools import groupby
from typing import ClassVar, Dict, List, Optional

from PIL import Image
from pydantic import BaseModel, field_validator, model_validator

from ...utils.general import encode_image
from ..od.schemas import Target


class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageType(str, Enum):
    IMAGE = "image"
    TEXT = "text"
    File = "file"
    MIXED = "mixed"


class ImageUrl(BaseModel):
    url: str
    detail: str = "auto"

    @field_validator("detail")
    @classmethod
    def validate_detail(cls, detail: str) -> str:
        if detail not in ["high", "low", "auto"]:
            raise ValueError(
                'The detail can only be one of "high", "low" and "auto". {} is not valid.'.format(
                    detail
                )
            )
        return detail


class Content(BaseModel):
    type: str = "text"
    text: Optional[str] = None
    image_url: Optional[ImageUrl] = None

    @model_validator(mode="after")
    def validate(self):
        if self.type == "text":
            if self.text is None:
                raise ValueError(
                    "The text value must be valid when Content type is 'text'."
                )
        elif self.type == "image_url":
            if self.image_url is None:
                raise ValueError(
                    "The image_url value must be valid when Content type is 'image_url'."
                )
        else:
            raise ValueError(
                "Invalid Conyent type {}. Must be one of text and image_url".format(
                    self.type
                )
            )
        return self


class Message(BaseModel):
    """
    - role (str): The role of this message. Choose from 'user', 'assistant', 'system'.
    - message_type (str): Type of the message. Choose from 'text', 'image' and 'mixed'.
    - src_type (str): Type of the message content. If message is text, src_type='text'. If message is image, Choose from 'url', 'base64', 'local' and 'redis'.
    - content (str): Message content.
    - objects (List[schemas.Target]): The detected objects.
    """

    role: Role = Role.USER
    message_type: MessageType = MessageType.TEXT
    content: List[Content | Dict] | Content | str
    objects: List[Target] = []
    kwargs: dict = {}
    basic_data_types: ClassVar[List[type]] = [
        str,
        list,
        tuple,
        int,
        float,
        bool,
        datetime.datetime,
        datetime.time,
    ]

    @classmethod
    def merge_consecutive_text(cls, content) -> List:
        result = []
        current_str = ""

        for part in content:
            if isinstance(part, str):
                current_str += part
            else:
                if current_str:
                    result.append(current_str)
                    current_str = ""
                result.append(part)

        if current_str:  # 处理最后的字符串
            result.append(current_str)

        return result

    @field_validator("content", mode="before")
    @classmethod
    def content_validator(
        cls, content: List[Content | Dict] | Content | str
    ) -> List[Content] | Content:
        if isinstance(content, str):
            return Content(type="text", text=content)
        elif isinstance(content, list):
            # combine str elements in list
            content = cls.merge_consecutive_text(content)
            formatted = []
            for c in content:
                if not c:
                    continue
                if isinstance(c, Content):
                    formatted.append(c)
                elif isinstance(c, dict):
                    try:
                        formatted.append(Content(**c))
                    except Exception as e:
                        formatted.append(Content(type="text", text=str(c)))
                elif isinstance(c, Image.Image):
                    formatted.append(
                        Content(
                            type="image_url",
                            image_url={
                                "url": f"data:image/jpeg;base64,{encode_image(c)}"
                            },
                        )
                    )
                elif isinstance(c, tuple(cls.basic_data_types)):
                    formatted.append(Content(type="text", text=str(c)))
                else:
                    raise ValueError(
                        f"Content list must contain [Content, str, list, dict, PIL.Image], got {type(c)}"
                    )
        else:
            raise ValueError(
                "Content must be a string, a list of Content objects or list of dicts."
            )
        return formatted

    @classmethod
    def system(cls, content: str | List[str | Dict | Content]) -> "Message":
        return cls(role=Role.SYSTEM, content=content)

    @classmethod
    def user(cls, content: str | List[str | Dict | Content]) -> "Message":
        return cls(role=Role.USER, content=content)

    @classmethod
    def assistant(cls, content: str | List[str | Dict | Content]) -> "Message":
        return cls(role=Role.ASSISTANT, content=content)
