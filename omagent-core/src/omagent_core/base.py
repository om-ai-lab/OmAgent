import contextvars
from abc import ABC
from collections import defaultdict, deque
from typing import ClassVar, Dict, Optional, Union, Any

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

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


class BotBase(BaseSettings, ABC):
    stm_pool: ClassVar[Dict[str, STM]] = {}
    callback: Optional[BaseCallback] = DefaultCallback()
    

    class Config:
        """Configuration for this pydantic object."""

        extra = "allow"
        arbitrary_types_allowed = True

    @property
    def name(self) -> str:
        return self.__class__.__name__

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

    @classmethod
    def get_config_template(cls) -> dict:
        template = {}
        simple_types = (str, int, float, bool, type(None))
        
        def is_simple_type(type_to_check: Any) -> bool:
            return isinstance(type_to_check, type) and issubclass(type_to_check, simple_types)
        
        for field_name, field in cls.model_fields.items():
            # Pass inner attributes and complex types
            if field_name.startswith("_"):
                continue
                
            field_type = field.annotation
            if hasattr(field_type, "__origin__") and field_type.__origin__ is Union:
                if not all(is_simple_type(t) for t in field_type.__args__):
                    continue
            elif not is_simple_type(field_type):
                continue
                
            field_info = {
                "value": None,
                "description": field.description or "",
                "env_var": field.alias.upper() if field.alias else field_name.upper(),
            }
            print(field_name, field.is_required())
            # Get default value for tag as <required>
            if field.default_factory is not None:
                field_info["value"] = field.default_factory()
            elif field.is_required():
                field_info["value"] = "<required>"
            else:
                field_info["value"] = field.default

            template[field_name] = field_info

        return template

    @classmethod
    def from_config(cls, config_data: str) -> 'BotBase':
        if cls.__name__ not in config_data:
            raise ValueError(f"Config for {cls.__name__} not found")
        class_config = config_data.get(cls.__name__, {})
        config_values = {
            key: item['value'] if isinstance(item, dict) else item
            for key, item in class_config.items()
        }
        
        return cls(**config_values)
    
    
