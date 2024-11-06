from typing import Dict, List, Type
from pydantic import BaseModel
from omagent_core.utils.registry import registry


class Container:
    def __init__(self):
        self._connectors: Dict[str, BaseModel] = {}
        self._components: Dict[str, BaseModel] = {}
        self._stm = None
        self._ltm = None
        self._callback = None

    def register_connector(
        self,
        name: str,
        connector: Type[BaseModel],
        overwrite: bool = False,
        **kwargs,
    ) -> None:
        """Register a connector"""
        if name not in self._connectors or overwrite:
            self._connectors[name] = connector(**kwargs)

    def get_connector(self, name: str) -> BaseModel:
        if name not in self._connectors:
            raise KeyError(f"There is no connector named '{name}' in container.")
        return self._connectors[name]

    def register_component(
        self,
        component: str | Type[BaseModel],
        key: str = None,
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

        if (key in self._components or component_name in self._components) and not overwrite:
            return

        required_connectors = self._get_required_connectors(component_cls)
        if required_connectors:
            for connector, cls_name in required_connectors:
                if connector not in self._connectors:
                    connector_cls = registry.get_connector(cls_name)
                    self.register_connector(connector, connector_cls)
                config[connector] = self._connectors[connector]

        self._components[key or component_name] = component_cls(**config)
        return key or component_name

    def get_component(self, component_name: str) -> BaseModel:
        if component_name not in self._components:
            raise KeyError(
                f"There is no handler named '{component_name}' in container."
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
    
    def register_stm(self, stm: str|Type[BaseModel], key: str = None, config: dict = {}, overwrite: bool = False):
        key = self.register_component(stm, key, config, overwrite)
        self._stm = self._components[key]

    @property
    def stm(self) -> BaseModel:
            return self._stm
        
    def register_ltm(self, ltm: str|Type[BaseModel], key: str = None, config: dict = {}, overwrite: bool = False):
        key = self.register_component(ltm, key, config, overwrite)
        self._ltm = self._components[key]
        
    @property
    def ltm(self) -> BaseModel:
            return self._ltm
    
    def register_callback(self, callback: str|Type[BaseModel], key: str = None, config: dict = {}, overwrite: bool = False):
        key = self.register_component(callback, key, config, overwrite)
        self._callback = self._components[key]
        
    @property
    def callback(self) -> BaseModel:
            return self._callback

    def compile_config(self) -> None:
        config = {"connectors": {}, "components": {}}

        for name, connector in self._connectors.items():
            config["connectors"][name] = connector.__class__.get_config_template()

        for name, component in self._components.items():
            config["components"][name] = component.__class__.get_config_template()

        return config

    def update_from_config(self, config_data: dict) -> None:
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

        config_data = clean_config_dict(config_data)

        # connectors
        if "connectors" in config_data:
            for name, config in config_data["connectors"].items():
                connector_cls = registry.get_connector(config.pop("name"))
                if connector_cls:
                    print(111, name, config)
                    self.register_connector(
                        name=name, connector=connector_cls, overwrite=True, **config
                    )

        # components
        if "components" in config_data:
            for name, config in config_data["components"].items():
                self.register_component(
                    component=config.pop("name"),
                    key=name,
                    config=config,
                    overwrite=True,
                )


container = Container()
