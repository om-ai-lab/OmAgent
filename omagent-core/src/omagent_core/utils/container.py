from typing import Dict, List, Type, Optional, Union, Callable
from omagent_core.base import BotBase
from omagent_core.services.connectors.base import ConnectorBase
from omagent_core.utils.registry import registry

class Container:
    def __init__(self):
        self._connectors: Dict[str, ConnectorBase] = {}
        self._handlers: Dict[str, BotBase] = {}
        self._memories: Dict[str, BotBase] = {}
        
    def register_connector(self, name: str, connector: Type[ConnectorBase], **kwargs) -> None:
        """Register a connector"""
        if name not in self._connectors:
            self._connectors[name] = connector(**kwargs)
            
    def get_connector(self, name: str) -> ConnectorBase:
        if name not in self._connectors:
            raise KeyError(f"There is no connector named '{name}' in container.")
        return self._connectors[name]
            
    def _register_component(self, name: str, key: str, component_type: str, config: dict, 
                          target_dict: dict, registry_getter: Callable) -> None:
        """Generic component registration method
        
        Args:
            name: Component name
            key: The key to save and retrieve component
            component_type: Component type description (for error messages)
            config: Component configuration
            target_dict: Target dictionary to store component instances
            registry_getter: Function to get component class from registry
        """
        if name not in target_dict:
            component_cls = registry_getter(name)
            if not component_cls:
                raise ValueError(f"{component_type} {name} not found in registry")
            
            required_connectors = self._get_required_connectors(component_cls)
            if required_connectors:
                for connector, cls_name in required_connectors:
                    if connector not in self._connectors:
                        connector_cls = registry.get_connector(cls_name)
                        if not connector_cls:
                            raise ValueError(f"Required connector {connector} not found")
                        self.register_connector(connector, connector_cls)
                    config[connector] = self._connectors[connector]
            
            target_dict[key or name] = component_cls(**config)

    def register_handler(self, name: str, key: str = None, handler_config: dict = {}) -> None:
        self._register_component(
            name=name,
            key=key,
            component_type="Handler",
            config=handler_config,
            target_dict=self._handlers,
            registry_getter=registry.get_handler
        )
        
    def get_handler(self, name: str) -> BotBase:
        if name not in self._handlers:
            raise KeyError(f"There is no handler named '{name}' in container.")
        return self._handlers[name]
            
    def register_memory(self, name: str, key: str = None, memory_config: dict = {}) -> None:
        self._register_component(
            name=name,
            key=key,
            component_type="Memory",
            config=memory_config,
            target_dict=self._memories,
            registry_getter=registry.get_memory
        )
        
    def get_memory(self, name: str) -> BotBase:
        if name not in self._memories:
            raise KeyError(f"There is no memory named '{name}' in container.")
        return self._memories[name]
    
    def _get_required_connectors(self, cls: Type[BotBase]) -> List[str]:
        required_connectors = []
        for field_name, field in cls.model_fields.items():
            if isinstance(field.annotation, type) and issubclass(field.annotation, ConnectorBase):
                required_connectors.append([field_name, field.annotation.__name__])
        return required_connectors
    
    @property
    def handlers(self) -> Dict[str, BotBase]:
        return self._handlers
        
    @property
    def memories(self) -> Dict[str, BotBase]:
        return self._memories
        
    
    def compile_config(self) -> None:
        config = {
            "connectors": {},
            "handlers": {},
            "memories": {}
        }
        
        for name, connector in self._connectors.items():
            config["connectors"][name] = connector.__class__.get_config_template()
            
        for name, handler in self._handlers.items():
            config["handlers"][name] = handler.__class__.get_config_template()
            
        for name, memory in self._memories.items():
            config["memory"][name] = memory.__class__.get_config_template()
            
        return config

container = Container()