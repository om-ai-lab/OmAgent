import json
import re
from pathlib import Path
from typing import List, Tuple, Any

from colorama import Fore, Style
from pydantic import Field
from tenacity import (
    retry,
    retry_if_exception_message,
    stop_after_attempt,
    stop_after_delay,
)

from ....memories.ltms.ltm import LTM
from ....engine.workflow.context import BaseWorkflowContext
from ....utils.env import EnvVar
from ....utils.registry import registry
from ....models.llms.base import BaseLLMBackend
from ....models.llms.prompt.prompt import PromptTemplate
from ....tool_system.manager import ToolManager
from ....engine.task.agent_task import TaskTree, TaskStatus
from ....engine.worker.base import BaseWorker
from ....models.llms.base import StrParser
import json_repair
from ....models.llms.openai_gpt import OpenaiGPTLLM
from ....utils.container import container
from collections import defaultdict

CURRENT_PATH = Path(__file__).parents[0]


@registry.register_worker()
class TaskConqueror(BaseLLMBackend, BaseWorker):
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
        task = TaskTree(**agent_task)
        current_node = task.get_current_node()
        current_node.status = TaskStatus.RUNNING
        if not self.stm.get('former_results'):
            self.stm['former_results'] = {}
        payload = {
            "task": current_node.task,
            "tools": self.tool_manager.generate_prompt(),
            "sibling_tasks": [
                (
                    {
                        "task": each.task,
                        "criticism": each.criticism,
                        "milestones": each.milestones,
                    }
                    if each.id > current_node.id
                    else None
                )
                for each in task.get_siblings(current_node.id)
            ],
            "parent_task": (
                [
                    {
                        "task": each.task,
                        "criticism": each.criticism,
                        "milestones": each.milestones,
                    }
                    for each in [task.get_parent(current_node.id)]
                ][0]
                if task.get_parent(current_node.id)
                else []
            ),
            "former_results": self.stm['former_results'],
            "extra_info": self.stm.get("extra"),
            "img_placeholders": "".join(list(self.stm.get("image_cache", {}).keys()))
        }
        chat_complete_res = self.infer(input_list=[payload])
        content = chat_complete_res[0]["choices"][0]["message"].get("content")
        content = json_repair.loads(content)

        first_key = next(iter(content))
        new_data = {first_key: content[first_key]}
        content = new_data

        if content.get("agent_answer"):
            last_output = content
            if task.get_parent(current_node.id):
                if current_node.id not in [each.id for each in task.get_children(task.get_parent(current_node.id).id)]:
                    self.stm['former_results'] = {}
            former_results = self.stm['former_results']
            former_results[current_node.task] = content
            self.stm['former_results'] = former_results
            current_node.result = content["agent_answer"]
            current_node.status = TaskStatus.SUCCESS
            self.callback.info(agent_id=self.workflow_instance_id, progress=f'Conqueror', message=f'Task "{current_node.task}" agent answer: {content["agent_answer"]}')
            return {"agent_task": task.model_dump(), "switch_case_value": "success", "last_output": last_output, "kwargs": kwargs}

        elif content.get("divide"):
            current_node.result = content["divide"]
            current_node.status = TaskStatus.RUNNING
            last_output = (
                "Task is too complex to complete. Agent provided reason: {}".format(
                    content["divide"]
                )
            )
            self.callback.info(agent_id=self.workflow_instance_id, progress=f'Conqueror', message=f'Task "{current_node.task}" needs to be divided.')
            return {"agent_task": task.model_dump(), "switch_case_value": "complex", "last_output": last_output, "kwargs": kwargs}

        elif content.get("tool_call"):
            self.callback.info(agent_id=self.workflow_instance_id, progress=f'Conqueror', message=f'Task "{current_node.task}" needs to be executed by tool.')
            execution_status, execution_results = self.tool_manager.execute_task(
                content["tool_call"], related_info=self.stm['former_results']
            )
            former_results = self.stm['former_results']
            former_results['tool_call'] = content['tool_call']
            if execution_status == "success":
                last_output = execution_results
                if task.get_parent(current_node.id):
                    if current_node.id not in [each.id for each in task.get_children(task.get_parent(current_node.id).id)]:
                        self.stm['former_results'] = {}
                former_results.pop("tool_call", None)
                former_results[current_node.task] = execution_results
                self.stm['former_results'] = former_results
                current_node.result = execution_results
                current_node.status = TaskStatus.SUCCESS
                toolcall_success_output_structure = {
                    "tool_status": current_node.status,
                    "tool_result": current_node.result,
                }
                self.callback.info(agent_id=self.workflow_instance_id, progress=f'Conqueror', message=f'Tool call success.')
                return {"agent_task": task.model_dump(), "switch_case_value": "success", "last_output": last_output, "kwargs": kwargs}
            else:
                current_node.result = execution_results
                current_node.status = TaskStatus.FAILED
                former_results['tool_call_error'] = f"tool_call {content['tool_call']} raise error: {current_node.result}"
                self.stm['former_results'] = former_results
                self.callback.info(agent_id=self.workflow_instance_id, progress=f'Conqueror', message=f'Tool call failed.')
                return {"agent_task": task.model_dump(), "switch_case_value": "failed", "last_output": last_output, "kwargs": kwargs}

        else:
            raise ValueError("LLM generation is not valid.")
        
