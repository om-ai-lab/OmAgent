import json
import re
from copy import deepcopy
from distutils.util import strtobool
from pathlib import Path
import os
import yaml
import os
from .env import EnvVar




def build_from_file(file_path: str):
    path = Path(file_path)
    workers_path = path / "workers"
    if not workers_path.exists():
        return []

    # 初始化配置字典
    worker_configs = {}
    other_configs = {}
    file_names = {}

    for file in path.rglob("*"):
        if file.suffix not in [".json", ".yaml", ".yml"]:
            continue

        key = file.name.split(".", 1)[0]
        
        if key in file_names:
            raise Exception(
                f"Duplicate file name [{key}] found:\n"
                f"File 1: {file_names[key]}\n"
                f"File 2: {file}"
            )
        file_names[key] = file

        try:
            with open(file, "r") as f:
                if file.suffix == ".json":
                    content = json.load(f)
                else:  # .yaml or .yml
                    content = yaml.load(f, Loader=yaml.FullLoader)
        except Exception as e:
            raise Exception(f"Error loading file {file}: {str(e)}")
        
        if workers_path in file.parents:
            worker_configs[key] = content
        else:
            other_configs[key] = content

    for conf in worker_configs.values():
        prep_config(conf, other_configs, [])

    return list( worker_configs.values())

def prep_config(sub_config: dict, config: dict, forbid_keys: list):
    for key, conf in sub_config.items():
        if isinstance(conf, str):
            if match := re.search(r'\$\{sub\|([^}]+)\}', conf):
                module_key = match.group(1).strip()
                if module_key not in config:
                    raise Exception(
                        "Incomplete configuration, lack module [{}]".format(
                            module_key
                        )
                    )
                elif module_key in forbid_keys:
                    raise Exception(
                        "Can't reference submodule recursively. [{}]".format(
                            module_key
                        )
                    )
                sub_config[key] = deepcopy(config[module_key])
                prep_config(sub_config[key], config, forbid_keys + [module_key])
            elif match := re.search(r'\$\{env\|([^,}]+)(?:,([^}]+))?\}', conf):
                env_key = match.group(1).strip()
                default_value = match.group(2)
                env_value = os.getenv(env_key)
                if env_value:
                    sub_config[key] = env_value
                elif not env_value and default_value:
                    sub_config[key] =default_value.strip()
                    if sub_config[key] == "null" or sub_config[key] == "~":
                        sub_config[key] = None
                else:
                    raise ValueError(f'Environmental variable {env_key} need to be set.')
                

        elif isinstance(conf, dict):
            prep_config(sub_config[key], config, forbid_keys)

        elif isinstance(conf, list):
            for i, item in enumerate(conf):
                if isinstance(item, dict):
                    prep_config(sub_config[key][i], config, forbid_keys)
