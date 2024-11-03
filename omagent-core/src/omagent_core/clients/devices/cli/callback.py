import datetime
import json
import os
from collections import defaultdict
from pathlib import Path
from time import time
from typing import Any, ClassVar

from colorama import Fore, Style

from omagent_core.utils.error import VQLError
from omagent_core.utils.logger import logging
import omagent_core.base
from omagent_core.clients.base import BaseCallback



class DefaultCallback(BaseCallback):
    bot_id: str = ""
    start_time: int = time()
    endpoint: str = ""
    loop_count: ClassVar[dict] = defaultdict(int)
    callback_count: ClassVar[dict] = defaultdict(int)

    def __init__(self, **data: Any):
        super().__init__(**data)
        self.endpoint = data.get("endpoint", "")

    def visualize_in_terminal(self, *args, **kwargs):
        pass

    def info(self, msg):
        logging.info(
            f"\n{Fore.BLUE}{json.dumps(msg, indent=2, ensure_ascii=False)}{Style.RESET_ALL}"
        )

    def send_block(self, msg):
        caller, calling_chain = self.get_calling_class()
        logging.info(
            f"\n{Fore.BLUE}{json.dumps(msg, indent=2, ensure_ascii=False)}{Style.RESET_ALL}"
        )
        if len(calling_chain) > 0:
            if len(calling_chain) == 1 and isinstance(
                caller, omagent_core.engine.node.BaseLoop
            ):
                Path(
                    f"{self.folder_name}/{'/'.join(calling_chain)}/{self.loop_count[calling_chain[-1]]}"
                ).mkdir(parents=True, exist_ok=True)
                self.loop_count[calling_chain[-1]] += 1
            else:
                for each in list(self.loop_count.keys()):
                    calling_chain.insert(
                        calling_chain.index(each) + 1, str(self.loop_count[each] - 1)
                    )
                if isinstance(caller, omagent_core.models.llms.base.BaseLLM):
                    Path(f"{self.folder_name}/{'/'.join(calling_chain[:-1])}").mkdir(
                        parents=True, exist_ok=True
                    )
                    json.dump(
                        msg,
                        open(
                            f"{self.folder_name}/{'/'.join(calling_chain[:-1])}/{calling_chain[-1]}_{self.callback_count[calling_chain[-1]]}.json",
                            "w",
                        ),
                        indent=2,
                        ensure_ascii=False,
                    )
                else:
                    Path(f"{self.folder_name}/{'/'.join(calling_chain)}").mkdir(
                        parents=True, exist_ok=True
                    )
                    json.dump(
                        msg,
                        open(
                            f"{self.folder_name}/{'/'.join(calling_chain)}/{self.callback_count[calling_chain[-1]]}.json",
                            "w",
                        ),
                        indent=2,
                        ensure_ascii=False,
                    )
                self.callback_count[calling_chain[-1]] += 1

    def error(self, error: VQLError):
        logging.error(f"\n{Fore.RED}{error}{Style.RESET_ALL}")

    def send_answer(self, msg):
        raise NotImplementedError("Not implemented yet.")

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