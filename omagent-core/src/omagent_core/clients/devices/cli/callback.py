import datetime
import json
import os
from collections import defaultdict
from pathlib import Path
from time import time
from typing import Any, ClassVar

from colorama import Fore, Style

from omagent_core.clients.devices.app.schemas import InteractionType, MessageType
from omagent_core.utils.registry import registry
from omagent_core.utils.error import VQLError
from omagent_core.utils.logger import logging
import omagent_core.base
from omagent_core.clients.base import CallbackBase


@registry.register_component()
class DefaultCallback(CallbackBase):
    bot_id: str = ""
    # start_time: int = time()
    # endpoint: str = ""
    # loop_count: ClassVar[dict] = defaultdict(int)
    # callback_count: ClassVar[dict] = defaultdict(int)

    # def __init__(self, **data: Any):
    #     super().__init__(**data)
    #     self.endpoint = data.get("endpoint", "")

    def visualize_in_terminal(self, *args, **kwargs):
        pass

    def info(self, agent_id, progress, message):
        logging.info(
            f"\n{Fore.BLUE}info:{agent_id} {progress} {message}{Style.RESET_ALL}"
        )

    def send_block(
        self,
        agent_id,
        msg,
        **kwargs
    ):
        logging.info(f"\n{Fore.BLUE}block:{msg}{Style.RESET_ALL}")
        

    def error(self, agent_id, error_code, error_info, **kwargs):
        logging.error(f"\n{Fore.RED}{error_info}{Style.RESET_ALL}")

    def send_answer(self, agent_id, msg, **kwargs):
        logging.info(f"\n{Fore.BLUE}answer:{msg}{Style.RESET_ALL}")

    def finish(self, **kwargs):
        def generate_tree(path, indent=""):
            tree_str = ""
            items = sorted(
                [
                    item
                    for item in os.listdir(path)
                    if os.path.isdir(os.path.join(path, item))
                ]
            )
            for i, item in enumerate(items):
                tree_str += f"{indent}|-- {item}\n"
                new_path = os.path.join(path, item)
                if os.path.isdir(new_path):
                    if i == len(items) - 1:
                        tree_str += generate_tree(new_path, indent + "    ")
                    else:
                        tree_str += generate_tree(new_path, indent + "|   ")
            return tree_str

        execution_flow = generate_tree(self.folder_name)
        with open(f"{self.folder_name}/execution_flow.txt", "w") as file:
            file.write(execution_flow)
        logging.info(
            f"{Fore.BLUE}Finish running at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Execution flow as follow:\n{execution_flow}"
            f"{Style.RESET_ALL}"
        )

    def send_markdown_data(self, data):
        import requests

        data = {"message": data}
        requests.post(self.endpoint, json=data)