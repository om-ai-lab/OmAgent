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

    def _run(self, agent_task: dict, last_output: str, *args, **kwargs):
        """Task divider that breaks down complex tasks into multiple subtasks.

        Args:
            agent_task (dict): Dictionary containing the current task tree information
            last_output (str): Output from the previous task execution
            *args: Variable positional arguments
            **kwargs: Variable keyword arguments

        Returns:
            dict: A dictionary containing:
                - agent_task: Updated task tree
                - switch_case_value: Task division status ("success"/"failed")
                - last_output: Latest output result
                - kwargs: Additional keyword arguments

        Description:
            1. Checks if task depth exceeds maximum limit
            2. Calls LLM to divide current task into subtasks
            3. Updates task tree structure
            4. Returns division results and status
        """
        task = TaskTree(**agent_task)
        current_node = task.get_current_node()
        # Check if task depth exceeds maximum limit
        if task.get_depth(current_node.id) >= EnvVar.MAX_TASK_DEPTH:
            last_output = "failed: Max subtask depth reached"
            self.callback.info(agent_id=self.workflow_instance_id, progress=f'Divider', message=f'Max subtask depth reached.')
            return {"agent_task": task.model_dump(), "switch_case_value": "failed", "last_output": last_output, "kwargs": kwargs}

        # Call LLM to divide current task into subtasks
        chat_complete_res = self.simple_infer(
            parent_task=current_node.task,
            uplevel_tasks=task.get_parent(current_node.id) if task.get_parent(current_node.id) else [],
            former_results=last_output,
            tools=self.tool_manager.generate_prompt(),
        )
        chat_complete_res = json_repair.loads(chat_complete_res['choices'][0]['message']['content'])

        # Update task tree structure
        if chat_complete_res.get("tasks"):
            task.add_subtasks(current_node.id, chat_complete_res["tasks"])
            subtasks_info = "\n".join([f"{idx}: {each.task}" for idx, each in enumerate(task.get_children(current_node.id))])
            self.callback.info(agent_id=self.workflow_instance_id, progress=f'Divider', message=f'Task "{current_node.task}" has been divided into {len(task.get_children(current_node.id))} subtasks: \n{subtasks_info}')
            return {"agent_task": task.model_dump(), "switch_case_value": "success", "last_output": last_output, "kwargs": kwargs}

        # Handle failed task division
        elif chat_complete_res.get("failed_reason"):
            last_output = (
                "failed: Subtask generation failed. Agent provided reason: {}".format(
                    chat_complete_res.get("failed_reason", "No reason generated.")
                )
            )
            self.callback.info(agent_id=self.workflow_instance_id, progress=f'Divider', message=f'Subtask generation failed.')
            return {"agent_task": task.model_dump(), "switch_case_value": "failed", "last_output": last_output, "kwargs": kwargs}
        
        # Handle invalid LLM generation
        else:
            raise ValueError("LLM generation is not valid.")

