from typing import Dict, List, Type
from omagent_core.base import BotBase
from omagent_core.services.connectors.base import ConnectorBase
from omagent_core.utils.registry import registry
from omagent_core.engine.configuration.configuration import Configuration


class Container:
    def __init__(self):
        self._connectors: Dict[str, ConnectorBase] = {}
        self._components: Dict[str, BotBase] = {}
        self._connectors["conductor_config"] = Configuration()

    def register_connector(
        self,
        name: str,
        connector: Type[ConnectorBase],
        overwrite: bool = False,
        **kwargs,
    ) -> None:
        """Register a connector"""
        if name not in self._connectors or overwrite:
            self._connectors[name] = connector(**kwargs)

    def get_connector(self, name: str) -> ConnectorBase:
        if name not in self._connectors:
            raise KeyError(f"There is no connector named '{name}' in container.")
        return self._connectors[name]

    def register_component(
        self,
        component: str | Type[BotBase],
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
        elif isinstance(component, type) and issubclass(component, BotBase):
            component_cls = component
            component_name = component.__name__
        else:
            raise ValueError(f"Invalid component type: {type(component)}")

        if (key or component_name in self._components) and not overwrite:
            return

        required_connectors = self._get_required_connectors(component_cls)
        if required_connectors:
            for connector, cls_name in required_connectors:
                if connector not in self._connectors:
                    connector_cls = registry.get_connector(cls_name)
                    self.register_connector(connector, connector_cls)
                config[connector] = self._connectors[connector]

        self._components[key or component_name] = component_cls(**config)

    def get_component(self, component_name: str) -> BotBase:
        if component_name not in self._components:
            raise KeyError(
                f"There is no handler named '{component_name}' in container."
            )
        return self._components[component_name]

    def _get_required_connectors(self, cls: Type[BotBase]) -> List[str]:
        required_connectors = []
        for field_name, field in cls.model_fields.items():
            if isinstance(field.annotation, type) and issubclass(
                field.annotation, ConnectorBase
            ):
                required_connectors.append([field_name, field.annotation.__name__])
        return required_connectors

    @property
    def components(self) -> Dict[str, BotBase]:
        return self._components

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
