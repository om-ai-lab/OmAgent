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
        """A task exit monitor that determines task completion and loop exit conditions.

        This component acts as a monitor that:
        - Takes a task tree and checks the status of each task node
        - Determines if the current task branch is complete
        - Decides whether to continue to next sibling/child task or exit
        - Manages the traversal and completion of the entire task tree
        - Controls the dynamic task execution loop

        The monitor is responsible for:
        1. Checking if current task failed -> exit loop
        2. If current task has children -> move to first child
        3. If current task has next sibling -> move to next sibling 
        4. If at root with no siblings -> exit loop
        5. If parent has no next sibling -> exit loop
        6. Otherwise -> move to parent's next sibling

        Args:
            agent_task (dict): The task tree containing all tasks and their status
            last_output (str): The output from previous task execution
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            dict: Contains updated task tree, exit flag, and last output
        """
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
