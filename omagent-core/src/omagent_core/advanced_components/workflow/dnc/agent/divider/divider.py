import json
import re
from pathlib import Path
from typing import Any, List, Tuple

import json_repair
from omagent_core.advanced_components.workflow.dnc.schemas.dnc_structure import \
    TaskTree
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.models.llms.prompt.prompt import PromptTemplate
from omagent_core.tool_system.manager import ToolManager
from omagent_core.utils.registry import registry
from pydantic import Field
from tenacity import (retry, retry_if_exception_message, stop_after_attempt,
                      stop_after_delay)
from omagent_core.utils.logger import logging

CURRENT_PATH = Path(__file__).parents[0]


@registry.register_worker()
class TaskDivider(BaseLLMBackend, BaseWorker):
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("sys_prompt.prompt"), role="system"
            ),
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("user_prompt.prompt"), role="user"
            ),
        ]
    )
    tool_manager: ToolManager
    max_task_depth: int = 5

    def _run(self, dnc_structure: dict, last_output: str, *args, **kwargs):
        """Task divider that breaks down complex tasks into multiple subtasks.

        Args:
            dnc_structure (dict): Dictionary containing the current task tree information
            last_output (str): Output from the previous task execution
            *args: Variable positional arguments
            **kwargs: Variable keyword arguments

        Returns:
            dict: A dictionary containing:
                - dnc_structure: Updated task tree
                - switch_case_value: Task division status ("success"/"failed")
                - last_output: Latest output result
                - kwargs: Additional keyword arguments

        Description:
            1. Checks if task depth exceeds maximum limit
            2. Calls LLM to divide current task into subtasks
            3. Updates task tree structure
            4. Returns division results and status
        """
        task = TaskTree(**dnc_structure)
        current_node = task.get_current_node()
        # Check if task depth exceeds maximum limit
        if task.get_depth(current_node.id) >= self.max_task_depth:
            last_output = "failed: Max subtask depth reached"
            self.callback.info(
                agent_id=self.workflow_instance_id,
                progress=f"Divider",
                message=f"Max subtask depth reached.",
            )
            self.stm(self.workflow_instance_id)["dnc_structure"] = task.model_dump()
            self.stm(self.workflow_instance_id)["last_output"] = last_output
            return {
                "dnc_structure": task.model_dump(),
                "switch_case_value": "failed",
                "last_output": last_output,
                "kwargs": kwargs,
            }

        # Call LLM to divide current task into subtasks
        chat_complete_res = self.simple_infer(
            parent_task=current_node.task,
            uplevel_tasks=(
                task.get_parent(current_node.id)
                if task.get_parent(current_node.id)
                else []
            ),
            former_results=last_output,
            tools=self.tool_manager.generate_prompt(),
        )
        logging.info(f"Divider chat_complete_res: {chat_complete_res}")
        chat_complete_res = json_repair.loads(
            chat_complete_res["choices"][0]["message"]["content"]
        )

        # Update task tree structure
        if chat_complete_res.get("tasks"):
            task.add_subtasks(current_node.id, chat_complete_res["tasks"])
            subtasks_info = "\n".join(
                [
                    f"{idx}: {each.task}"
                    for idx, each in enumerate(task.get_children(current_node.id))
                ]
            )
            self.callback.info(
                agent_id=self.workflow_instance_id,
                progress=f"Divider",
                message=f'Task "{current_node.task}" has been divided into {len(task.get_children(current_node.id))} subtasks: \n{subtasks_info}',
            )
            self.stm(self.workflow_instance_id)["dnc_structure"] = task.model_dump()
            self.stm(self.workflow_instance_id)["last_output"] = last_output
            return {
                "dnc_structure": task.model_dump(),
                "switch_case_value": "success",
                "last_output": last_output,
                "kwargs": kwargs,
            }

        # Handle failed task division
        elif chat_complete_res.get("failed_reason"):
            last_output = (
                "failed: Subtask generation failed. Agent provided reason: {}".format(
                    chat_complete_res.get("failed_reason", "No reason generated.")
                )
            )
            self.callback.info(
                agent_id=self.workflow_instance_id,
                progress=f"Divider",
                message=f"Subtask generation failed.",
            )
            self.stm(self.workflow_instance_id)["dnc_structure"] = task.model_dump()
            self.stm(self.workflow_instance_id)["last_output"] = last_output
            return {
                "dnc_structure": task.model_dump(),
                "switch_case_value": "failed",
                "last_output": last_output,
                "kwargs": kwargs,
            }

        # Handle invalid LLM generation
        else:
            raise ValueError("LLM generation is not valid.")
