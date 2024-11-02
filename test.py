if __name__ == "__main__":
    import yaml
    def compile_config(bot_classes, output_format: str) -> str:
        """编译所有机器人类的配置模板
        
        Args:
            bot_classes: BotBase子类集合
            output_format: 输出格式，支持 'yaml' 或 'env'
        """
        config = {}
        
        for bot_class in bot_classes:
            if not issubclass(bot_class, BotBase):
                continue
            config[bot_class.__name__] = bot_class.get_config_template()
        print(config)
        if output_format == 'yaml':
            return yaml.dump(config, default_flow_style=False, allow_unicode=True)
        elif output_format == 'env':
            # 生成.env文件格式
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
    
    from omagent_core.base import BotBase, Field
    from typing import Optional
    from omagent_core.engine.worker.base import BaseWorker



    # class AgentTest(BotBase):
    #     # temp:int = Field(default=12, alias='hh')
    #     def aa(self) -> None:
    #         pass

    # yaml_config = compile_config({AgentTest}, output_format='yaml')
    
    class SimpleWorker(BaseWorker):
        def _run(self, my_name:str):
            print(22222222, my_name)
            return {'worker_style': 'class', 'secret_number': 1234, 'is_it_true': False}
    yaml_config = compile_config({SimpleWorker}, output_format='yaml')