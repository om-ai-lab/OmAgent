import datetime
import inspect
import json
import os
from abc import ABC, abstractmethod
from collections import defaultdict
from pathlib import Path
from time import time
from typing import Any, ClassVar
from enum import Enum

from colorama import Fore, Style
from pydantic import BaseModel, model_validator

from ...utils.error import VQLError
from ...utils.logger import logging
from ...handlers.redis_handler import RedisHandler
import omagent_core.base

class ContentStatus(Enum):
    INCOMPLETE = "incomplete" # the conversation content is not yet complete
    END_BLOCK = "end_block" # a single conversation has ended, but the overall result is not finished
    END_ANSWER = "end_answer" # the overall return is complete

class InteractionType(Enum):
    DEFAULT = 0
    INPUT = 1

class MessageType(Enum):
    TEXT = "text"
    IMAGE_URL = "image_url"
    IMAGE_BASE64 = "image_base64"

redis_handler = RedisHandler()

class BaseCallback(BaseModel, ABC):
    bot_id: str
    start_time: str = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    folder_name: str = f"./running_logs/{start_time}"

    class Config:
        """Configuration for this pydantic object."""

        arbitrary_types_allowed = True
        extra = "allow"

    @model_validator(mode="after")
    def init_folder(self):
        Path(self.folder_name).mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def send_block(self, **kwargs):
        pass

    @abstractmethod
    def send_answer(self, **kwargs):
        pass

    @abstractmethod
    def info(self, **kwargs):
        pass

    @abstractmethod
    def error(self, **kwargs):
        pass

    @abstractmethod
    def finish(self, **kwargs):
        pass

    def remove_duplicates(self, sorted_list):
        if not sorted_list:
            return []

        result = [sorted_list[0]]
        for item in sorted_list[1:]:
            if item != result[-1]:
                result.append(item)
        return result[::-1]

    def get_calling_class(self):
        stack = inspect.stack()
        # Skipping the first two frames: current frame and the frame of get_calling_class_name
        calling_chain = self.remove_duplicates(
            [
                each.frame.f_locals.get("self").__class__.__name__
                for each in stack[2:]
                if isinstance(
                    each.frame.f_locals.get("self"), omagent_core.base.BotBase
                )
            ]
        )
        for frame_info in stack[2:]:
            frame = frame_info.frame
            # Check for 'self' in local variables to identify the caller object
            self_obj = frame.f_locals.get("self")
            if self_obj:
                return self_obj, calling_chain
        return None, None


class TestCallback(BaseCallback):
    bot_id: str = ""
    start_time: int = time()

    def info(self, *args, **kwargs):
        logging.debug("Callback message [{}] | [{}]".format(args, kwargs))

    def error(self, error: VQLError):
        logging.error("Error message [{}]".format(error))


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


class AppCallback(BaseCallback):
    bot_id: str = ""

    def __init__(self, **data: Any):
        super().__init__(**data)

    def _create_message_data(self, agent_id, code, error_info, took, msg_type, msg, content_status, interaction_type, prompt_tokens, output_tokens):
        message = {
            "role": "assistant",
            "type": msg_type,
            "content": msg
        }
        usage = {
            "prompt_tokens": prompt_tokens,
            "output_tokens": output_tokens
        }
        data = {
            "agent_id": agent_id,
            "code": code,
            "error_info": error_info,
            "took": took,
            "content_status": content_status,
            "interaction_type": int(interaction_type),
            "message": message,
            "usage": usage
        }
        return {"payload": json.dumps(data, ensure_ascii=False)}

    def send_to_group(self, stream_name, group_name, data):
        print(f"Stream: {stream_name}, Group: {group_name}, Data: {data}")
        redis_handler.redis_client.xadd(stream_name, data)
        try:
            redis_handler.redis_client.xgroup_create(stream_name, group_name, id='0')
        except Exception as e:
            print(f"Consumer group may already exist: {e}")

    def send_base_message(self, agent_id, code, error_info, took, msg_type, msg, content_status, interaction_type, prompt_tokens, output_tokens):
        stream_name = f"{agent_id}_output"
        group_name = "omappagent"  # replace with your consumer group name
        data = self._create_message_data(agent_id, code, error_info, took, msg_type, msg, content_status, interaction_type, prompt_tokens, output_tokens)
        self.send_to_group(stream_name, group_name, data)

    def send_incomplete(self, agent_id, took, msg_type, msg):
        self.send_base_message(agent_id, 0, "", took, msg_type, msg, ContentStatus.INCOMPLETE.value, InteractionType.DEFAULT.value, 0, 0)

    def send_block(self, agent_id, took, msg_type, msg, interaction_type=InteractionType.DEFAULT.value):
        self.send_base_message(agent_id, 0, "", took, msg_type, msg, ContentStatus.END_BLOCK.value, interaction_type, 0, 0)

    def send_answer(self, agent_id, took, msg_type, msg):
        self.send_base_message(agent_id, 0, "", took, msg_type, msg, ContentStatus.END_ANSWER.value, InteractionType.DEFAULT.value, 0, 0)

    def info(self, agent_id, progress, message):
        stream_name = f"{agent_id}_running"
        data = {"agent_id": agent_id, "progress": progress, "message": message}
        payload = {"payload": json.dumps(data, ensure_ascii=False)} 
        redis_handler.send_to_stream(stream_name, payload)

    def error(self, agent_id, code, error_info):
        self.send_base_message(agent_id, code, error_info, 0, MessageType.TEXT.value, "", "end_answer", 0, 0)

    def finish(self, agent_id, took, type, msg):
        self.send_answer(agent_id, took, type, msg)
