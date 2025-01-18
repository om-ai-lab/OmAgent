from omagent_core.engine.http.models.tag_object import TagObject
from typing_extensions import Self


class RateLimitTag(TagObject):
    def __init__(self, key: str, value: int) -> Self:
        super().__init__(key=key, type="RATE_LIMIT", value=value)
