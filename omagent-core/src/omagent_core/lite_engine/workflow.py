from pathlib import Path
from typing import List, Union, Callable
import ast

from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.utils.registry import registry
from omagent_core.models.llms.schemas import Message, Content
from omagent_core.utils.general import encode_image
from omagent_core.models.llms.prompt.parser import StrParser
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.engine.worker.base import BaseLocalWorker, BaseWorker
from omagent_core.utils.container import container
from omagent_core.memories.stms.stm_dict import DictSTM
from omagent_core.memories.stms.stm_redis import RedisSTM
from omagent_core.tool_system.manager import ToolManager
from omagent_core.services.connectors.redis import RedisConnector
from omagent_core.tool_system.tools.web_search.search import WebSearch
from omagent_core.utils.logger import logging
from omagent_core.lite_engine.task import Task, SwitchTask

CURRENT_PATH = Path(__file__).parents[0]


class Workflow:
    def __init__(self, name):
        self.name = name
        self.tasks: List[Task] = []

    def add_task(self, task):
        self.tasks.append(task)

    def execute(self):
        if self.tasks:
            print(f"Starting workflow: {self.name}")
            for task in self.tasks:
                task.execute()
        else:
            print("No tasks to execute in the workflow.")

    def __rshift__(self, task_or_dict):
        # If a dict is provided, create a SwitchTask and add it
        if isinstance(task_or_dict, dict):
            switch_task = SwitchTask(name=f"{self.name}_switch", cases=task_or_dict)
            if self.tasks:
                parent_task = self.tasks[-1]
                parent_task.next_tasks.append(switch_task)
                setattr(switch_task, '_parent_task', parent_task)
            else:
                self.tasks.append(switch_task)
            return switch_task
        else:
            if self.tasks:
                last_task = self.tasks[-1]
                last_task.next_tasks.append(task_or_dict)
                if isinstance(task_or_dict, Task):
                    setattr(task_or_dict, '_parent_task', last_task)
                self.tasks.append(task_or_dict)
            else:
                self.tasks.append(task_or_dict)
            return task_or_dict
