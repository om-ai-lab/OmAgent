import contextvars
from abc import ABC
from collections import defaultdict, deque
from typing import ClassVar, Dict, Optional

from pydantic import BaseModel, Field, field_validator

from .clients.base.callback import BaseCallback, DefaultCallback

REQUEST_ID = contextvars.ContextVar("request_id")


class STM(BaseModel):
    class Config:
        """Configuration for this pydantic object."""

        extra = "allow"
        arbitrary_types_allowed = True

    image_cache: Dict = {}
    token_usage: Dict = {}
    former_results: Dict = {}
    history: Dict = defaultdict(lambda: deque(maxlen=3))

    def has(self, key: str) -> bool:
        return key in self.__annotations__ or key in self.model_extra


class BotBase(BaseModel, ABC):
    name: Optional[str] = Field(default=None, validate_default=True)
    stm_pool: ClassVar[Dict[str, STM]] = {}
    callback: Optional[BaseCallback] = DefaultCallback()

    class Config:
        """Configuration for this pydantic object."""

        arbitrary_types_allowed = True

    @field_validator("name", mode="before")
    @classmethod
    def get_type(cls, name) -> str:
        if not name:
            return cls.__name__
        else:
            return name

    @property
    def request_id(self) -> str:
        return REQUEST_ID.get()

    @property
    def stm(self) -> STM:
        if self.request_id not in self.stm_pool:
            self.stm_pool[self.request_id] = STM()
        return self.stm_pool[self.request_id]

    def set_request_id(self, request_id: str) -> None:
        REQUEST_ID.set(request_id)

    def free_stm(self) -> None:
        self.stm_pool.pop(self.request_id, None)
