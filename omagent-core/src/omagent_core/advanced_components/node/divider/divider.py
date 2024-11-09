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

    def _run(self, agent_task: dict, last_output: str, workflow_instance_id: str, *args, **kwargs):
        task = TaskTree(**agent_task)
        current_node = task.get_current_node()
        if task.get_depth(current_node.id) >= EnvVar.MAX_TASK_DEPTH:
            last_output = "failed: Max subtask depth reached"
            divide_failed_structure = {
                "parent_task": current_node.task,
                "failed_reason": "Max subtask depth reached",
            }
            self.callback.send_block(agent_id=workflow_instance_id, msg=divide_failed_structure)
            return {"agent_task": task.model_dump(), "switch_case_value": "failed", "last_output": last_output, "kwargs": kwargs}

        chat_complete_res = self.simple_infer(
            parent_task=current_node.task,
            uplevel_tasks=task.get_parent(current_node.id) if task.get_parent(current_node.id) else [],
            former_results=last_output,
            tools=self.tool_manager.generate_prompt(),
        )
        chat_complete_res = json_repair.loads(chat_complete_res['choices'][0]['message']['content'])
        if chat_complete_res.get("tasks"):
            task.add_subtasks(current_node.id, chat_complete_res["tasks"])
            subtasks_info = "\n".join([f"{idx}: {each.task}" for idx, each in enumerate(task.get_children(current_node.id))])
            self.callback.send_block(agent_id=workflow_instance_id, msg=f'Current task "{current_node.task}" has been divided into {len(task.get_children(current_node.id))} subtasks: \n{subtasks_info}')
            return {"agent_task": task.model_dump(), "switch_case_value": "success", "last_output": last_output, "kwargs": kwargs}

        elif chat_complete_res.get("failed_reason"):
            last_output = (
                "failed: Subtask generation failed. Agent provided reason: {}".format(
                    chat_complete_res.get("failed_reason", "No reason generated.")
                )
            )
            return {"agent_task": task.model_dump(), "switch_case_value": "failed", "last_output": last_output, "kwargs": kwargs}
        else:
            raise ValueError("LLM generation is not valid.")

