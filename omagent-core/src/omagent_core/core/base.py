import contextvars
from abc import ABC
from collections import defaultdict, deque
from typing import ClassVar, Dict, Optional

from pydantic import BaseModel, Field, field_validator

from ..handlers.callback_handler.callback import BaseCallback, DefaultCallback

REQUEST_ID = contextvars.ContextVar("request_id")


class STM(BaseModel):
    """State Machine model to store temporary and contextual information."""

    class Config:
        extra = "allow"
        arbitrary_types_allowed = True

    image_cache: Dict[str, str] = Field(default_factory=dict, description="Cache for storing image data.")
    token_usage: Dict[str, int] = Field(default_factory=dict, description="Tracks token usage per request.")
    former_results: Dict[str, str] = Field(default_factory=dict, description="Stores results of previous requests.")
    history: Dict[str, deque] = Field(default_factory=lambda: defaultdict(lambda: deque(maxlen=3)), 
                                      description="Tracks limited history for each key.")

    def has(self, key: str) -> bool:
        """Check if a key exists either in annotations or in extra fields."""
        return key in self.__annotations__ or key in self.model_extra


class BotBase(BaseModel, ABC):
    """Abstract base model for a bot instance with state management and request tracking."""

    name: Optional[str] = Field(default=None, validate_default=True)
    stm_pool: Dict[str, STM] = {}  # Consider making this an instance attribute if shared state is not desired.
    callback: Optional[BaseCallback] = Field(default_factory=DefaultCallback, description="Callback handler instance.")

    class Config:
        arbitrary_types_allowed = True

    @field_validator("name", mode="before")
    @staticmethod
    def get_type(name: Optional[str]) -> str:
        """Return the name of the instance or the class name if not specified."""
        return name or "BotBase"

    @property
    def request_id(self) -> str:
        """Retrieve the current request ID from context."""
        return REQUEST_ID.get()

    @property
    def stm(self) -> STM:
        """Retrieve or initialize STM instance for the current request."""
        if self.request_id not in self.stm_pool:
            self.stm_pool[self.request_id] = STM()
        return self.stm_pool[self.request_id]

    def set_request_id(self, request_id: str) -> None:
        """Set the request ID in the context."""
        REQUEST_ID.set(request_id)

    def free_stm(self) -> None:
        """Release the STM instance for the current request ID."""
        self.stm_pool.pop(self.request_id, None)
