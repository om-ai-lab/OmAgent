import re
from typing import Dict, List, Optional
from ..od.schemas import Target

from pydantic import BaseModel, field_validator, model_validator

from enum import Enum

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

    @field_validator("content", mode="before")
    @classmethod
    def content_validator(
        cls, content: List[Content | Dict] | Content | str
    ) -> List[Content] | Content:
        if isinstance(content, str):
            return Content(type="text", text=content)
        elif isinstance(content, list):
            formatted = []
            for c in content:
                if isinstance(c, Content):
                    formatted.append(c)
                elif isinstance(c, dict):
                    formatted.append(Content(**c))
                elif isinstance(c, str):
                    formatted.append(Content(type="text", text=c))
                else:
                    raise ValueError(
                        "Content list must contain Content objects, strings or dicts."
                    )
        else:
            raise ValueError(
                "Content must be a string, a list of Content objects or list of dicts."
            )
        return formatted

    def combine_image_message(self, **kwargs):
        if isinstance(self.content, list):
            for index, each_content in enumerate(self.content):
                if each_content.text is not None:
                    image_patterns = [
                        f"<image_{each}>"
                        for each in re.findall(r"<image_([^_]+)>", each_content.text)
                    ]
                    # set max_num to 20
                    image_patterns = image_patterns[-min(20, len(image_patterns)) :]
                else:
                    image_patterns = []
                if image_patterns:
                    image_cache = kwargs.get("image_cache")
                    if len(image_cache) < len(image_patterns):
                        raise ValueError("Image number is not enough. Please check.")
                    segments = re.split(
                        "({})".format("|".join(map(re.escape, image_patterns))),
                        each_content.text,
                    )
                    segments = [each for each in segments if each.strip()]
                    modified_content = []
                    for segment in segments:
                        if segment in image_patterns:
                            modified_content.append(
                                Content(
                                    type="image_url",
                                    image_url={
                                        "url": f"data:image/jpeg;base64,{image_cache[segment]}"
                                    },
                                )
                            )
                        else:
                            modified_content.append(Content(type="text", text=segment))
                    self.content[index] = modified_content
                    self.message_type = MessageType.MIXED
        else:
            image_patterns = [
                f"<image_{each}>"
                for each in re.findall(r"<image_([^_]+)>", self.content.text)
            ]
            # set max_num to 20
            image_patterns = image_patterns[-min(20, len(image_patterns)) :]
            if image_patterns:
                image_cache = kwargs.get("image_cache")
                if len(image_cache) < len(image_patterns):
                    raise ValueError("Image number is not enough. Please check.")
                segments = re.split(
                    "({})".format("|".join(map(re.escape, image_patterns))),
                    self.content.text,
                )
                segments = [each for each in segments if each.strip()]
                modified_content = []
                for segment in segments:
                    if segment in image_patterns:
                        modified_content.append(
                            Content(
                                type="text",
                                text=f"Image of {re.match(r'<image_([^_]+)>', segment).group(1)}",
                            )
                        )
                        modified_content.append(
                            Content(
                                type="image_url",
                                image_url={
                                    "url": f"data:image/jpeg;base64,{image_cache[segment]}"
                                },
                            )
                        )
                    else:
                        modified_content.append(Content(type="text", text=segment))
                self.content = modified_content
                self.message_type = MessageType.MIXED