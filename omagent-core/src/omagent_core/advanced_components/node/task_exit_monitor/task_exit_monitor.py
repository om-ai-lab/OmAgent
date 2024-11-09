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
from ....engine.task.agent_task import AgentTask
import json_repair

CURRENT_PATH = Path(__file__).parents[0]


@registry.register_worker()
class TaskExitMonitor(BaseWorker):

    def _run(self, agent_task: dict, last_output: str, *args, **kwargs):
        # task = AgentTask(**agent_task)
        task = self.stm['agent_task']
        if task.status == "failed":
            return {"exit_flag": True}
        elif task.children != []:
            task = task.children[0]
            self.stm['agent_task'] = task
            return {"exit_flag": False}
        elif task.next_sibling_task() is not None:
            task = task.next_sibling_task()
            self.stm['agent_task'] = task
            return {"exit_flag": False}
        else:
            if task.parent is None:
                return {"exit_flag": True}
            elif task.parent.next_sibling_task() is None:
                return {"exit_flag": True}
            else:
                task = task.parent.next_sibling_task()
                self.stm['agent_task'] = task
                return {"exit_flag": False}
