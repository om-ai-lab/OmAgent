import json
import os
import re
from copy import deepcopy
from distutils.util import strtobool
from pathlib import Path
from uuid import uuid4

import yaml

from ..core.node.base import BaseDecider, BaseLoop, BaseProcessor
from ..core.node.base.base import Node
from ..handlers.data_handler.ltm import LTM
from ..schemas import BaseInterface
from .env import EnvVar
from .registry import registry


class Builder:
    def __init__(self, main_conf: dict, ltm_config: list) -> None:
        self.bot = registry.get_node(main_conf["name"])(**main_conf)
        self.ltm = LTM()
        for config in ltm_config:
            self.ltm.handler_register(
                config["name"], registry.get_handler(config["name"])(**config)
            )

    def run_bot(self, input: BaseInterface):
        self.bot.set_request_id(str(uuid4()))
        self.bot.run(input, self.ltm)

    @classmethod
    def visualize_nodes(cls, node: Node, graph, source=None, destination=None):
        current_node_name = node.name
        current_node_type = type(node)
        if source is None:
            source = current_node_name
        else:
            destination = current_node_name
            graph.add_edge(source, destination)
            source = destination
        if isinstance(node, BaseLoop):
            next_node = node.next_step if "next_step" in dir(node) else None
            cls.visualize_loop_nodes(node, graph, source, destination, node)
            destination = node.name + "*"
            graph.add_edge(destination, source)
            source = destination
        elif isinstance(node, BaseProcessor):
            next_node = node.next_step
        elif isinstance(node, BaseDecider):
            next_node = node.next_step
        else:
            raise Exception("Unknown next node type of [{}]".format(current_node_type))
        if next_node:
            if isinstance(next_node, dict):
                for item in next_node.values():
                    if item is not None:
                        cls.visualize_nodes(item, graph, source, destination)
            else:
                cls.visualize_nodes(next_node, graph, source, destination)

    @classmethod
    def visualize_loop_nodes(cls, node, graph, source, destination, loop_parent):
        if isinstance(node, BaseLoop):
            source = node.name
            node_loop_body = node.loop_body
            loop_parent = node
            loop_next_step = (
                node_loop_body.next_step if "next_step" in dir(node) else None
            )
            if loop_next_step:
                destination = node_loop_body.name
                graph.add_edge(source, destination)
                source = destination
                cls.visualize_loop_nodes(
                    loop_next_step, graph, source, destination, loop_parent
                )
            else:
                destination = node_loop_body.name
                graph.add_edge(source, destination)
                graph.add_edge(destination, loop_parent.name + "*")
        elif isinstance(node, BaseProcessor):
            destination = node.name
            graph.add_edge(source, destination)
            source = destination
            if node.next_step is not None:
                if isinstance(node.next_step, dict):
                    for item in node.next_step.values():
                        if item is not None:
                            cls.visualize_loop_nodes(
                                item, graph, source, destination, loop_parent
                            )
                else:
                    cls.visualize_loop_nodes(
                        node.next_step, graph, source, destination, loop_parent
                    )
            else:
                graph.add_edge(destination, loop_parent.name + "*")
        elif isinstance(node, BaseDecider):
            destination = node.name
            graph.add_edge(source, destination)
            source = destination
            if node.next_step is not None:
                if isinstance(node.next_step, dict):
                    for item in node.next_step.values():
                        if item is not None:
                            cls.visualize_loop_nodes(
                                item, graph, source, destination, loop_parent
                            )
                else:
                    cls.visualize_loop_nodes(
                        node.next_step, graph, source, destination, loop_parent
                    )
            else:
                graph.add_edge(destination, loop_parent.name + "*")
        else:
            raise Exception("Unknown next node type of [{}]".format(type(node)))

    @classmethod
    def from_dict(cls, config: dict):
        if "config" in config:
            for k, v in config["config"].items():
                EnvVar.update(k, v)
        if "ltm" not in config:
            config["ltm"] = []
        elif isinstance(config["ltm"], dict):
            config["ltm"] = [config["ltm"]]
        if isinstance(config["ltm"], list):
            for index, ltm_config in enumerate(config["ltm"]):
                cls.prep_config(ltm_config, config["ltm"][index], ["ltm"])
        else:
            cls.prep_config(config["ltm"], config, ["ltm"])
        if "main" not in config:
            raise Exception("Must have a config file named main.json or main.yaml")
        cls.prep_config(config["main"], config, ["main"])
        return cls(config["main"], config["ltm"])

    @classmethod
    def from_file(cls, file_path: str):
        config = {}
        for file in Path(file_path).rglob("*"):
            if file.suffix == ".json":
                with open(file, "r") as f:
                    sub_conf = json.load(f)
            elif file.suffix == ".yaml" or file.suffix == ".yml":
                with open(file, "r") as f:
                    sub_conf = yaml.load(f, Loader=yaml.FullLoader)
            else:
                continue
            key = file.name.split(".", 1)[0]
            if key in config:
                raise Exception("Duplicate module name [{}]".format(key))
            config[key] = sub_conf
        return cls.from_dict(config)

    @classmethod
    def prep_config(cls, sub_config: dict, config: dict, forbid_keys: list):
        for key, conf in sub_config.items():
            if isinstance(conf, str):
                if match := re.search(r"%%(.*)", conf):
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
                    cls.prep_config(sub_config[key], config, forbid_keys + [module_key])
                elif match := re.search(r"\$<(.*)::(.*)>", conf):
                    env_key = match.group(1).strip()
                    env_value = EnvVar.get(env_key, match.group(2).strip())
                    try:
                        env_value = int(env_value)
                    except:
                        try:
                            env_value = float(env_value)
                        except:
                            try:
                                env_value = strtobool(env_value)
                            except:
                                pass
                    sub_config[key] = env_value

            elif isinstance(conf, dict):
                cls.prep_config(sub_config[key], config, forbid_keys)

            elif isinstance(conf, list):
                for i, item in enumerate(conf):
                    if isinstance(item, dict):
                        cls.prep_config(sub_config[key][i], config, forbid_keys)
