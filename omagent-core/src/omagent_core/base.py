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
    name: Optional[str] = Field(default=None, validate_default=True)
    stm_pool: ClassVar[Dict[str, STM]] = {}
    callback: Optional[BaseCallback] = DefaultCallback()

    class Config:
        """Configuration for this pydantic object."""

        extra = "allow"
        arbitrary_types_allowed = True

    # @property
    # def name(self) -> str:
    #     return self.__class__.__name__
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

    @classmethod
    def get_config_template(
        cls, description: bool = True, env_var: bool = True
    ) -> dict:
        template = {}
        simple_types = (str, int, float, bool, type(None))

        def is_simple_type(type_to_check: Any) -> bool:
            return isinstance(type_to_check, type) and issubclass(
                type_to_check, simple_types
            )

        def is_botbase_subclass(type_to_check: Any) -> bool:
            return (
                isinstance(type_to_check, type)
                and issubclass(type_to_check, BotBase)
                and type_to_check != BotBase
            )

        for field_name, field in cls.model_fields.items():
            # Pass inner attributes
            if field_name.startswith("_"):
                continue

            field_type = field.annotation

            # 处理Union类型
            if hasattr(field_type, "__origin__") and field_type.__origin__ is Union:
                types = field_type.__args__
                if any(is_botbase_subclass(t) for t in types):
                    # 如果Union中包含BotBase子类，取第一个子类进行递归
                    for t in types:
                        if is_botbase_subclass(t):
                            template[field_name] = t.get_config_template()
                            break
                    continue
                elif not all(is_simple_type(t) for t in types):
                    continue
            # 处理BotBase子类
            elif is_botbase_subclass(field_type):
                template[field_name] = field_type.get_config_template()
                continue
            elif not is_simple_type(field_type):
                continue

            field_info = {"value": None}
            if description:
                field_info["description"] = field.description or ""
            if env_var:
                field_info["env_var"] = (
                    field.alias.upper() if field.alias else field_name.upper()
                )
            # Get default value for tag as <required>
            if field.default_factory is not None:
                field_info["value"] = field.default_factory()
            elif field.is_required():
                field_info["value"] = "<required>"
            else:
                field_info["value"] = field.default

            template[field_name] = field_info
            template["name"] = cls.__name__
        return template

    
    @classmethod
    def from_config(cls, config_data: str) -> "BotBase":
        def clean_config_dict(config_dict: dict) -> dict:
            """递归清理配置字典，移除所有的'description'和'env_var'键"""
            cleaned = {}
            for key, value in config_dict.items():
                if isinstance(value, dict):
                    if 'value' in value:
                        # 如果是配置项字典，直接取value值
                        cleaned[key] = value['value']
                    else:
                        # 如果是嵌套字典，递归处理
                        cleaned[key] = clean_config_dict(value)
                else:
                    cleaned[key] = value
            return cleaned
        
        print(666666666, config_data)
        class_config = config_data.get(cls.__name__, {})
        print(7777777,cls.__name__,  class_config)
        
        clean_class_config = clean_config_dict(class_config)
        print(8888888, clean_class_config)

        return cls(**clean_class_config)
