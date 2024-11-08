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
import pickle

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
        # task = AgentTask(**agent_task)
        task = self.stm['agent_task']
        EXIT_FLAG = False
        if task.task_depth() >= EnvVar.MAX_TASK_DEPTH:
            last_output = "failed: Max subtask depth reached"
            divide_failed_structure = {
                "parent_task": task.task,
                "failed_reason": "Max subtask depth reached",
            }
            self.callback.send_block(divide_failed_structure)
            if task.status == "failed":
                pass
            elif task.children != []:
                task = task.children[0]
                EXIT_FLAG = False
            elif task.next_sibling_task() is not None:
                task = task.next_sibling_task()
                EXIT_FLAG = False
            else:
                if task.parent is None:
                    EXIT_FLAG = True
                elif task.parent.next_sibling_task() is None:
                    EXIT_FLAG = True
                else:
                    task = task.parent.next_sibling_task()
                    EXIT_FLAG = False
            self.stm['agent_task'] = task
            return {"agent_task": task.task_info(), "switch_case_value": "failed", "last_output": last_output, "kwargs": kwargs}

        chat_complete_res = self.simple_infer(
            parent_task=task.task,
            uplevel_tasks=task.parent.sibling_info() if task.parent else [],
            former_results=last_output,
            tools=self.tool_manager.generate_prompt(),
        )
        chat_complete_res = json_repair.loads(chat_complete_res['choices'][0]['message']['content'])
        if chat_complete_res.get("tasks"):
            task.add_subtasks(chat_complete_res["tasks"])
            divided_detail_structure = {
                "parent_task": task.task,
                "children_tasks": [
                    {
                        f"subtask_{idx}": child.task,
                        f"subtask_{idx} milestones": " & ".join(child.milestones),
                    }
                    for idx, child in enumerate(task.children)
                ],
            }
            # task = AgentTask(**task.children[0])
            if task.status == "failed":
                pass
            elif task.children != []:
                task = task.children[0]
                EXIT_FLAG = False
            elif task.next_sibling_task() is not None:
                task = task.next_sibling_task()
                EXIT_FLAG = False
            else:
                if task.parent is None:
                    EXIT_FLAG = True
                elif task.parent.next_sibling_task() is None:
                    EXIT_FLAG = True
                else:
                    task = task.parent.next_sibling_task()
                    EXIT_FLAG = False
            self.callback.send_block(divided_detail_structure)
            self.stm['agent_task'] = task
            return {"agent_task": task.task_info(), "switch_case_value": "success", "last_output": last_output, "kwargs": kwargs, "exit_flag": EXIT_FLAG}

        elif chat_complete_res.get("failed_reason"):
            last_output = (
                "failed: Subtask generation failed. Agent provided reason: {}".format(
                    chat_complete_res.get("failed_reason", "No reason generated.")
                )
            )
            if task.status == "failed":
                pass
            elif task.children != []:
                task = task.children[0]
                EXIT_FLAG = False
            elif task.next_sibling_task() is not None:
                task = task.next_sibling_task()
                EXIT_FLAG = False
            else:
                if task.parent is None:
                    EXIT_FLAG = True
                elif task.parent.next_sibling_task() is None:
                    EXIT_FLAG = True
                else:
                    task = task.parent.next_sibling_task()
                    EXIT_FLAG = False
            return {"agent_task": task.task_info(), "switch_case_value": "failed", "last_output": last_output, "kwargs": kwargs}
        else:
            raise ValueError("LLM generation is not valid.")

