import contextvars
from abc import ABC
from typing import Any, List, Optional, Union

from omagent_core.utils.container import container
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

REQUEST_ID = contextvars.ContextVar("request_id")


class BotBase(BaseSettings, ABC):
    name: Optional[str] = Field(default=None, validate_default=True)
    id: Optional[str] = Field(default=None, validate_default=True)
    component_stm: Optional[str] = None
    component_ltm: Optional[str] = None
    component_callback: Optional[str] = None
    component_input: Optional[str] = None

    class Config:
        """Configuration for this pydantic object."""

        extra = "allow"
        arbitrary_types_allowed = True

    @field_validator("name", mode="before")
    @classmethod
    def get_type(cls, name) -> str:
        if not name:
            return cls.__name__
        else:
            return name

    @property
    def stm(self) -> str:
        if self.component_stm is None:
            return container.stm
        else:
            return container.get_component(self.component_stm)

    @property
    def ltm(self) -> str:
        if self.component_ltm is None:
            return container.ltm
        else:
            return container.get_component(self.component_ltm)

    @property
    def callback(self) -> str:
        if self.component_callback is None:
            return container.callback
        else:
            return container.get_component(self.component_callback)

    @property
    def input(self) -> str:
        if self.component_input is None:
            return container.input
        else:
            return container.get_component(self.component_input)

    @classmethod
    def get_config_template(
        cls,
        description: bool = True,
        env_var: bool = True,
        exclude_fields: List[str] = [],
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
            if field_name.startswith("_") or field_name in exclude_fields:
                continue

            field_type = field.annotation

            if hasattr(field_type, "__origin__") and field_type.__origin__ is Union:
                types = field_type.__args__
                if any(is_botbase_subclass(t) for t in types):
                    for t in types:
                        if is_botbase_subclass(t):
                            template[field_name] = t.get_config_template(
                                description=description,
                                env_var=env_var,
                                exclude_fields=exclude_fields,
                            )
                            break
                    continue
                elif not all(is_simple_type(t) for t in types):
                    continue
            elif is_botbase_subclass(field_type):
                template[field_name] = field_type.get_config_template(
                    description=description,
                    env_var=env_var,
                    exclude_fields=exclude_fields,
                )
                continue
            elif not is_simple_type(field_type):
                continue

            field_info = {"value": None}
            if description and field.description:
                field_info["description"] = field.description
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

            template[field.alias if field.alias else field_name] = field_info
            template["name"] = cls.__name__
        return template

    @classmethod
    def from_config(cls, config_data: dict) -> "BotBase":
        def clean_config_dict(config_dict: dict) -> dict:
            """Recursively clean up the configuration dictionary, removing all 'description' and 'env_var' keys"""
            cleaned = {}
            for key, value in config_dict.items():
                if isinstance(value, dict):
                    if "value" in value:
                        cleaned[key] = value["value"]
                    else:
                        cleaned[key] = clean_config_dict(value)
                else:
                    cleaned[key] = value
            return cleaned

        class_config = config_data.get(cls.__name__, {})
        clean_class_config = clean_config_dict(class_config)

        return cls(**clean_class_config)
