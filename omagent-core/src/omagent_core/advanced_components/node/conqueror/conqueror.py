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
from ....engine.task.agent_task import AgentTask, TaskStatus
from ....engine.worker.base import BaseWorker
from ....models.llms.base import StrParser
import json_repair
from ....models.llms.openai_gpt import OpenaiGPTLLM
from ....utils.container import container
from collections import defaultdict
import pickle

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

    def _run(self, agent_task: dict, last_output: str, workflow_instance_id: str, *args, **kwargs):
        # task: AgentTask = task
        if self.stm.get('agent_task'):
            task = self.stm['agent_task']
        else:
            task = AgentTask(**agent_task)
        task.status = TaskStatus.RUNNING
        if not self.stm.get('former_results'):
            self.stm['former_results'] = {}
        llm_detail = {
            "api_keys": {
                self.llm.model_id: [
                    {
                        "llm_key": self.llm.api_key,
                        "endpoint": self.llm.endpoint,
                        "max_token": self.llm.max_tokens,
                        "temperature": self.llm.temperature,
                        "response_format": self.llm.response_format,
                    }
                ]
            }
        }
        chat_structure = {
            "current_stage": self.__class__.__name__,
            "task": task.task,
            "task_depth": task.task_depth(),
            "llm_detail": llm_detail,
        }
        # self.callback.send_block(agent_id=workflow_instance_id, msg=chat_structure)
        payload = {
            "task": task.task,
            "tools": self.tool_manager.generate_prompt(),
            "sibling_tasks": [
                (
                    {
                        "task": each["task"],
                        "criticism": each["criticism"],
                        "milestones": each["milestones"],
                    }
                    if each["id"] > task.id
                    else None
                )
                for each in task.sibling_info()[1:]
            ],
            "parent_task": (
                [
                    {
                        "task": each["task"],
                        "criticism": each["criticism"],
                        "milestones": each["milestones"],
                    }
                    for each in [task.parent.task_info()]
                ][0]
                if task.parent
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

        # self.callback.send_block(agent_id=workflow_instance_id, msg=content)
        if content.get("agent_answer"):
            last_output = content
            if task.parent:
                if task.id not in [
                    each_child.id for each_child in task.parent.children
                ]:
                    self.stm['former_results'] = {}
            former_results = self.stm['former_results']
            former_results[task.task] = content
            self.stm['former_results'] = former_results
            task.result = content["agent_answer"]
            task.status = TaskStatus.SUCCESS
            direct_output_structure = {
                "tool_status": task.status,
                "tool_result": task.result,
            }
            self.callback.send_block(agent_id=workflow_instance_id, msg=f'Current task "{task.task}" has direct output: \n{content["agent_answer"]}')
            self.stm['agent_task'] = task
            return {"agent_task": task.task_info(), "switch_case_value": "success", "last_output": last_output, "kwargs": kwargs}

        elif content.get("divide"):
            task.result = content["divide"]
            task.status = TaskStatus.RUNNING
            last_output = (
                "Task is too complex to complete. Agent provided reason: {}".format(
                    content["divide"]
                )
            )
            direct_output_structure = {
                "tool_status": task.status,
                "tool_result": task.result,
            }
            self.callback.send_block(agent_id=workflow_instance_id, msg=f'Current task "{task.task}" needs to be divided: \n{content["divide"]}')
            self.stm['agent_task'] = task
            return {"agent_task": task.task_info(), "switch_case_value": "complex", "last_output": last_output, "kwargs": kwargs}

        elif content.get("tool_call"):
            self.callback.send_block(agent_id=workflow_instance_id, msg=f'Current tool call task: \n{content["tool_call"]}')
            execution_status, execution_results = self.tool_manager.execute_task(
                content["tool_call"], related_info=self.stm['former_results']
            )
            former_results = self.stm['former_results']
            former_results['tool_call'] = content['tool_call']
            if execution_status == "success":
                last_output = execution_results
                if task.parent:
                    if task.id not in [
                        each_child.id for each_child in task.parent.children
                    ]:
                        self.stm['former_results'] = {}
                former_results.pop("tool_call", None)
                former_results[task.task] = execution_results
                self.stm['former_results'] = former_results
                task.result = execution_results
                task.status = TaskStatus.SUCCESS
                toolcall_success_output_structure = {
                    "tool_status": task.status,
                    "tool_result": task.result,
                }
                self.callback.send_block(agent_id=workflow_instance_id, msg=toolcall_success_output_structure)
                self.stm['agent_task'] = task
                return {"agent_task": task.task_info(), "switch_case_value": "success", "last_output": last_output, "kwargs": kwargs}
            else:
                task.result = execution_results
                task.status = TaskStatus.FAILED
                former_results['tool_call_error'] = f"tool_call {content['tool_call']} raise error: {task.result}"
                self.stm['former_results'] = former_results
                self.stm['agent_task'] = task
                return {"agent_task": task.task_info(), "switch_case_value": "failed", "last_output": last_output, "kwargs": kwargs}

        else:
            raise ValueError("LLM generation is not valid.")
        
