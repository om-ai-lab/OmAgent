from typing import Type, Set
import yaml
from omagent_core.base import BotBase

def compile_config(agent_classes: Set[Type[BotBase]], output_format: str = 'yaml') -> str:
    """Compile the config settings
    
    Args:
        bot_classes: BotBase子类集合
        output_format: output format, support 'yaml' or 'env'
    """
    config = {}
    
    for agent_class in agent_classes:
        if not issubclass(agent_class, BotBase):
            continue
        config[agent_class.name] = agent_class.get_config_template()
    
    if output_format == 'yaml':
        return yaml.dump(config, default_flow_style=False, allow_unicode=True)
    elif output_format == 'env':
        env_lines = []
        for class_name, fields in config.items():
            env_lines.append(f"# {class_name} Configuration")
            for field_name, field_info in fields.items():
                env_var = field_info['env_var']
                value = field_info['value']
                description = field_info['description']
                comment = f" # {description}" if description else ""
                env_lines.append(f"{env_var}={value}{comment}")
            env_lines.append("")
        return "\n".join(env_lines)
    
    raise ValueError(f"Unsupported output format: {output_format}")