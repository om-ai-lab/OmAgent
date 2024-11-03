from typing import Dict, List, Type, Optional, Union, Callable
from omagent_core.base import BotBase
from omagent_core.services.connectors.base import ConnectorBase
from omagent_core.utils.registry import registry
import yaml

class Container:
    def __init__(self):
        self._connectors: Dict[str, ConnectorBase] = {}
        self._handlers: Dict[str, BotBase] = {}
        self._ltm: Dict[str, BotBase] = {}
        self._stm: Dict[str, BotBase] = {}
        
    def register_connector(self, name: str, connector: Type[ConnectorBase], **kwargs) -> None:
        """Register a connector"""
        if name not in self._connectors:
            self._connectors[name] = connector(**kwargs)
            
    def _register_component(self, name: str, component_type: str, config: dict, 
                          target_dict: dict, registry_getter: Callable) -> None:
        """Generic component registration method
        
        Args:
            name: Component name
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
            
            target_dict[name] = component_cls(**config)

    def register_handler(self, name: str, handler_config: dict = {}) -> None:
        self._register_component(
            name=name,
            component_type="Handler",
            config=handler_config,
            target_dict=self._handlers,
            registry_getter=registry.get_handler
        )
            
    def register_memory(self, name: str, memory_type: str, memory_config: dict) -> None:
        if memory_type.lower() == 'ltm':
            target_dict = self._ltm
        elif memory_type.lower() == 'stm':
            target_dict = self._stm
        else:
            raise ValueError(f"Unknown memory type: {memory_type}")
            
        self._register_component(
            name=name,
            component_type=f"{memory_type.upper()} Memory",
            config=memory_config,
            target_dict=target_dict,
            registry_getter=registry.get_memory
        )
    
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
    def ltm(self) -> Dict[str, BotBase]:
        return self._ltm
        
    @property 
    def stm(self) -> Dict[str, BotBase]:
        return self._stm
    
    def compile_config(self) -> None:
        config = {
            "connectors": {},
            "handlers": {},
            "ltm": {},
            "stm": {}
        }
        
        for name, connector in self._connectors.items():
            config["connectors"][name] = connector.__class__.get_config_template()
            
        for name, handler in self._handlers.items():
            config["handlers"][name] = handler.__class__.get_config_template()
            
        for name, ltm in self._ltm.items():
            config["ltm"][name] = ltm.__class__.get_config_template()
            
        for name, stm in self._stm.items():
            config["stm"][name] = stm.__class__.get_config_template()
            
        return config

container = Container()