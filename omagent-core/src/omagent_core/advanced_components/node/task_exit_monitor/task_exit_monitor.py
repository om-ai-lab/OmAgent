import json
import re
from pathlib import Path
from typing import List, Tuple, Any

from pydantic import Field
from tenacity import (
    retry,
    retry_if_exception_message,
    stop_after_attempt,
    stop_after_delay,
)

from ....memories.ltms.ltm import LTM
from ....utils.env import EnvVar
from ....utils.registry import registry
from ....models.llms.base import BaseLLMBackend
from ....models.llms.prompt.prompt import PromptTemplate
from ....tool_system.manager import ToolManager
from ....engine.worker.base import BaseWorker
from ....engine.workflow.context import BaseWorkflowContext
from ....engine.task.agent_task import TaskTree
import json_repair

CURRENT_PATH = Path(__file__).parents[0]


@registry.register_worker()
class TaskExitMonitor(BaseWorker):

    def _run(self, agent_task: dict, last_output: str, *args, **kwargs):
        task = TaskTree(**agent_task)
        current_node = task.get_current_node()
        if current_node.status == "failed":
            return {"agent_task": task.model_dump(), "exit_flag": True, "last_output": last_output}
        elif task.get_children(current_node.id) != []:
            task.set_cursor(task.get_children(current_node.id)[0].id)
            return {"agent_task": task.model_dump(), "exit_flag": False, "last_output": last_output}
        elif task.get_next_sibling(current_node.id) is not None:
            task.set_cursor(task.get_next_sibling(current_node.id).id)
            return {"agent_task": task.model_dump(), "exit_flag": False, "last_output": last_output}
        else:
            if task.get_parent(current_node.id) is None:
                return {"agent_task": task.model_dump(), "exit_flag": True, "last_output": last_output}
            elif task.get_next_sibling(task.get_parent(current_node.id).id) is None:
                return {"agent_task": task.model_dump(), "exit_flag": True, "last_output": last_output}
            else:
                task.set_cursor(task.get_next_sibling(task.get_parent(current_node.id).id).id)
                return {"agent_task": task.model_dump(), "exit_flag": False, "last_output": last_output}
