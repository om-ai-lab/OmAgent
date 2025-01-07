import json
import re
from pathlib import Path
from typing import Any, List, Tuple

import json_repair
from omagent_core.advanced_components.workflow.dnc.schemas.dnc_structure import \
    TaskTree
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.memories.ltms.ltm import LTM
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.models.llms.prompt.prompt import PromptTemplate
from omagent_core.tool_system.manager import ToolManager
from omagent_core.utils.registry import registry
from pydantic import Field
from tenacity import (retry, retry_if_exception_message, stop_after_attempt,
                      stop_after_delay)

CURRENT_PATH = Path(__file__).parents[0]


@registry.register_worker()
class TaskExitMonitor(BaseWorker):

    def _run(self, *args, **kwargs):
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
            dnc_structure (dict): The task tree containing all tasks and their status
            last_output (str): The output from previous task execution
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            dict: Contains updated task tree, exit flag, and last output
        """
        stm_data = self.stm(self.workflow_instance_id)
        stm_dnc_structure = stm_data.get("dnc_structure", None)
        stm_last_output = stm_data.get("last_output", None)
        task = TaskTree(**stm_dnc_structure)
        current_node = task.get_current_node()
        if current_node.status == "failed":
            self.stm(self.workflow_instance_id)["dnc_structure"] = task.model_dump()
            self.stm(self.workflow_instance_id)["last_output"] = stm_last_output
            return {
                "dnc_structure": task.model_dump(),
                "exit_flag": True,
                "last_output": stm_last_output,
            }
        elif task.get_children(current_node.id) != []:
            task.set_cursor(task.get_children(current_node.id)[0].id)
            self.stm(self.workflow_instance_id)["dnc_structure"] = task.model_dump()
            self.stm(self.workflow_instance_id)["last_output"] = stm_last_output
            return {
                "dnc_structure": task.model_dump(),
                "exit_flag": False,
                "last_output": stm_last_output,
            }
        elif task.get_next_sibling(current_node.id) is not None:
            task.set_cursor(task.get_next_sibling(current_node.id).id)
            self.stm(self.workflow_instance_id)["dnc_structure"] = task.model_dump()
            self.stm(self.workflow_instance_id)["last_output"] = stm_last_output
            return {
                "dnc_structure": task.model_dump(),
                "exit_flag": False,
                "last_output": stm_last_output,
            }
        else:
            if task.get_parent(current_node.id) is None:
                self.stm(self.workflow_instance_id)["dnc_structure"] = task.model_dump()
                self.stm(self.workflow_instance_id)["last_output"] = stm_last_output
                return {
                    "dnc_structure": task.model_dump(),
                    "exit_flag": True,
                    "last_output": stm_last_output,
                }
            elif task.get_next_sibling(task.get_parent(current_node.id).id) is None:
                self.stm(self.workflow_instance_id)["dnc_structure"] = task.model_dump()
                self.stm(self.workflow_instance_id)["last_output"] = stm_last_output
                return {
                    "dnc_structure": task.model_dump(),
                    "exit_flag": True,
                    "last_output": stm_last_output,
                }
            else:
                task.set_cursor(
                    task.get_next_sibling(task.get_parent(current_node.id).id).id
                )
                self.stm(self.workflow_instance_id)["dnc_structure"] = task.model_dump()
                self.stm(self.workflow_instance_id)["last_output"] = stm_last_output
                return {
                    "dnc_structure": task.model_dump(),
                    "exit_flag": False,
                    "last_output": stm_last_output,
                }
