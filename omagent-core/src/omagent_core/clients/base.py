import datetime
import inspect
import re
from abc import ABC, abstractmethod
from pathlib import Path
from time import time

from omagent_core.base import BotBase
from pydantic import model_validator

from ..utils.error import VQLError
from ..utils.logger import logging


class CallbackBase(BotBase, ABC):
    bot_id: str
    start_time: str = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    # folder_name: str = f"./running_logs/{start_time}"

    class Config:
        """Configuration for this pydantic object."""

        arbitrary_types_allowed = True
        extra = "allow"

    # @model_validator(mode="after")
    # def init_folder(self):
    #     Path(self.folder_name).mkdir(parents=True, exist_ok=True)

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

    def filter_special_symbols_in_msg(self, msg):
        msg = re.sub(r"[-*#]", "", msg)
        return msg

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
                if isinstance(each.frame.f_locals.get("self"), BotBase)
            ]
        )
        for frame_info in stack[2:]:
            frame = frame_info.frame
            # Check for 'self' in local variables to identify the caller object
            self_obj = frame.f_locals.get("self")
            if self_obj:
                return self_obj, calling_chain
        return None, None


class TestCallback(CallbackBase):
    bot_id: str = ""
    start_time: int = time()

    def info(self, *args, **kwargs):
        logging.debug("Callback message [{}] | [{}]".format(args, kwargs))

    def error(self, error: VQLError):
        logging.error("Error message [{}]".format(error))
