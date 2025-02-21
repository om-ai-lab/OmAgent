from pathlib import Path
from typing import Dict, List, Optional, Type
from threading import Thread

from omagent_core.engine.configuration.aaas_config import AaasConfig
import yaml
from omagent_core.engine.configuration.configuration import (TEMPLATE_CONFIG,
                                                             Configuration)
from omagent_core.engine.configuration.aaas_config import AAAS_TEMPLATE_CONFIG
from omagent_core.utils.registry import registry
from pydantic import BaseModel
import os


class Container:
    def __init__(self):
        self._connectors: Dict[str, BaseModel] = {}
        self._components: Dict[str, BaseModel] = {}
        self._stm_name: Optional[str] = None
        self._ltm_name: Optional[str] = None
        self._callback_name: Optional[str] = None
        self._input_name: Optional[str] = None
        self.conductor_config = Configuration()
        self.aaas_config = AaasConfig()

    def register_connector(
        self,
        connector: Type[BaseModel],
        name: str = None,
        overwrite: bool = False,
        **kwargs,
    ) -> None:
        """Register a connector"""
        if name is None:
            name = connector.__name__
        if name not in self._connectors or overwrite:
            self._connectors[name] = connector(**kwargs)

    def get_connector(self, name: str) -> BaseModel:
        if name not in self._connectors:
            raise KeyError(f"There is no connector named '{name}' in container.")
        return self._connectors[name]

    def register_component(
        self,
        component: str | Type[BaseModel],
        name: str = None,
        config: dict = {},
        overwrite: bool = False,
    ) -> None:
        """Generic component registration method

        Args:
            component: Component name or class
            key: The key to save and retrieve component
            config: Component configuration
            target_dict: Target dictionary to store component instances
            component_category: One of the register mapping types, should be provided if component is a string
        """
        if isinstance(component, str):
            component_cls = registry.get_component(component)
            component_name = component
            if not component_cls:
                raise ValueError(f"{component} not found in registry")
        elif isinstance(component, type) and issubclass(component, BaseModel):
            component_cls = component
            component_name = component.__name__
        else:
            raise ValueError(f"Invalid component type: {type(component)}")

        if (
            name in self._components or component_name in self._components
        ) and not overwrite:
            return name or component_name

        required_connectors = self._get_required_connectors(component_cls)
        if required_connectors:
            for connector, cls_name in required_connectors:
                if connector not in self._connectors.keys():
                    connector_cls = registry.get_connector(cls_name)
                    self.register_connector(connector_cls, connector)
                config[connector] = self._connectors[connector]

        self._components[name or component_name] = component_cls(**config)
        return name or component_name

    def get_component(self, component_name: str) -> BaseModel:
        if component_name not in self._components:
            raise KeyError(
                f"There is no component named '{component_name}' in container. You need to register it first."
            )
        return self._components[component_name]

    def _get_required_connectors(self, cls: Type[BaseModel]) -> List[str]:
        required_connectors = []
        for field_name, field in cls.model_fields.items():
            if isinstance(field.annotation, type) and issubclass(
                field.annotation, BaseModel
            ):
                required_connectors.append([field_name, field.annotation.__name__])
        return required_connectors

    @property
    def components(self) -> Dict[str, BaseModel]:
        return self._components

    def register_stm(
        self,
        stm: str | Type[BaseModel],
        name: str = None,
        config: dict = {},
        overwrite: bool = False,
    ):
        if os.getenv("OMAGENT_MODE") == "lite":
            name = "SharedMemSTM"
        name = self.register_component(stm, name, config, overwrite)
        self._stm_name = name

    @property
    def stm(self) -> BaseModel:
        if self._stm_name is None:
            if os.getenv("OMAGENT_MODE") == "lite":
                self.register_stm("SharedMemSTM")
                self._stm_name = "SharedMemSTM"
            else:
                raise ValueError(
                    "STM component is not registered. Please use register_stm to register."
                )   

        return self.get_component(self._stm_name)

    def register_ltm(
        self,
        ltm: str | Type[BaseModel],
        name: str = None,
        config: dict = {},
        overwrite: bool = False,
    ):
        name = self.register_component(ltm, name, config, overwrite)
        self._ltm_name = name

    @property
    def ltm(self) -> BaseModel:
        if self._ltm_name is None:
            raise ValueError(
                "LTM component is not registered. Please use register_ltm to register."
            )
        return self.get_component(self._ltm_name)

    def register_callback(
        self,
        callback: str | Type[BaseModel],
        name: str = None,
        config: dict = {},
        overwrite: bool = False,
    ):
        name = self.register_component(callback, name, config, overwrite)
        self._callback_name = name

    @property
    def callback(self) -> BaseModel:
        if self._callback_name is None:
            raise ValueError(
                "Callback component is not registered. Please use register_callback to register."
            )
        return self.get_component(self._callback_name)

    def register_input(
        self,
        input: str | Type[BaseModel],
        name: str = None,
        config: dict = {},
        overwrite: bool = False,
    ):
        name = self.register_component(input, name, config, overwrite)
        self._input_name = name

    @property
    def input(self) -> BaseModel:
        if self._input_name is None:
            raise ValueError(
                "Input component is not registered. Please use register_input to register."
            )
        return self.get_component(self._input_name)

    def compile_config(
        self, output_path: Path, description: bool = True, env_var: bool = True
    ) -> None:
        if (output_path / "container.yaml").exists():
            print("container.yaml already exists, skip compiling")
            config = yaml.load(
                open(output_path / "container.yaml", "r"), Loader=yaml.FullLoader
            )
            return config

        config = {
            "conductor_config": TEMPLATE_CONFIG,
            "aaas_config": AAAS_TEMPLATE_CONFIG,
            "connectors": {},
            "components": {},
        }
        exclude_fields = [
            "_parent",
            "component_stm",
            "component_ltm",
            "component_callback",
            "component_input",
        ]
        for name, connector in self._connectors.items():
            config["connectors"][name] = connector.__class__.get_config_template(
                description=description, env_var=env_var, exclude_fields=exclude_fields
            )
        exclude_fields.extend(self._connectors.keys())
        for name, component in self._components.items():
            config["components"][name] = component.__class__.get_config_template(
                description=description, env_var=env_var, exclude_fields=exclude_fields
            )

        with open(output_path / "container.yaml", "w") as f:
            f.write(yaml.dump(config, sort_keys=False, allow_unicode=True))

        return config

    def from_config(self, config_data: dict | str | Path) -> None:
        """Update container from configuration

        Args:
            config_data: The dict including connectors and components configurations
        """
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

        if isinstance(config_data, str | Path):
            if not Path(config_data).exists():
                if os.getenv("OMAGENT_MODE") == "lite":
                    return 
                else:
                    raise FileNotFoundError(f"Config file not found: {config_data}")
            config_data = yaml.load(open(config_data, "r"), Loader=yaml.FullLoader)
        config_data = clean_config_dict(config_data)

        if "conductor_config" in config_data:
            self.conductor_config = Configuration(**config_data["conductor_config"])
        if "aaas_config" in config_data:
            self.aaas_config = AaasConfig(**config_data["aaas_config"])

        # connectors
        if "connectors" in config_data:
            for name, config in config_data["connectors"].items():
                connector_cls = registry.get_connector(config.pop("name"))
                if connector_cls:
                    self.register_connector(
                        name=name, connector=connector_cls, overwrite=True, **config
                    )

        # components
        if "components" in config_data:
            for name, config in config_data["components"].items():
                self.register_component(
                    component=config.pop("name"),
                    name=name,
                    config=config,
                    overwrite=True,
                )

        self.check_connection()

    def check_connection(self):
        if os.getenv("OMAGENT_MODE") == "lite":
            return 
        
        for name, connector in self._connectors.items():
            try:
                connector.check_connection()
            except Exception as e:
                raise ConnectionError(
                    f"Connection to {name} failed. Please check your connector config in container.yaml. \n Error Message: {e}"
                )

        try:
            from omagent_core.engine.orkes.orkes_workflow_client import \
                OrkesWorkflowClient

            conductor_client = OrkesWorkflowClient(self.conductor_config)
            conductor_client.check_connection()
        except Exception as e:
            raise ConnectionError(
                f"Connection to Conductor failed. Please check your conductor config in container.yaml. \n Error Message: {e}"
            )

        print("--------------------------------")
        print("All connections passed the connection check")
        print("--------------------------------")


container = Container()
