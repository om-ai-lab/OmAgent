import json
import re
from pathlib import Path
from typing import List, Tuple

from colorama import Fore, Style
from omagent_core.core.node.dnc import TaskConqueror
from omagent_core.core.node.dnc.schemas import AgentTask, TaskStatus
from omagent_core.core.prompt.prompt import PromptTemplate
from omagent_core.core.tool_system.manager import ToolManager
from omagent_core.handlers.data_handler.ltm import LTM
from omagent_core.schemas.base import BaseInterface
from omagent_core.utils.env import EnvVar
from omagent_core.utils.registry import registry
from pydantic import Field
from tenacity import (retry, retry_if_exception_message, stop_after_attempt,
                      stop_after_delay)

CURRENT_PATH = Path(__file__).parents[0]


@registry.register_node()
class VideoConqueror(TaskConqueror):
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

    @retry(
        stop=(
            stop_after_delay(EnvVar.STOP_AFTER_DELAY)
            | stop_after_attempt(EnvVar.STOP_AFTER_ATTEMPT)
        ),
        retry=retry_if_exception_message(message="LLM generation is not valid."),
        reraise=True,
    )
    def _run(self, args: BaseInterface, ltm: LTM) -> Tuple[BaseInterface, str]:
        task: AgentTask = args.task
        task.status = TaskStatus.RUNNING

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
        self.callback.send_block(chat_structure)
        chat_complete_body = {
            "video_meta": {"video_duration_seconds(s)": self.stm.video.stream.duration.get_seconds(), "frame_rate": self.stm.video.stream.frame_rate},
            "video_summary": self.stm.video_summary,
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
            "former_results": self.stm.former_results,
            "img_placeholders": "".join(list(self.stm.image_cache.keys())),
        }
        chat_complete_res = self.infer(
            input_list=[chat_complete_body], images=self.stm.image_cache.values()
        )[0]
        content = chat_complete_res["choices"][0]["message"].get("content")
        content = self._extract_from_result(content)

        first_key = next(iter(content))
        new_data = {first_key: content[first_key]}
        content = new_data

        self.callback.send_block(content)
        if content.get("agent_answer"):
            args.last_output = content
            if task.parent:
                if task.id not in [
                    each_child.id for each_child in task.parent.children
                ]:
                    self.stm.former_results = {}
            self.stm.former_results[task.task] = content
            task.result = content["agent_answer"]
            task.status = TaskStatus.SUCCESS
            direct_output_structure = {
                "tool_status": task.status,
                "tool_result": task.result,
            }
            self.callback.send_block(direct_output_structure)
            return args, "success"
        elif content.get("impossible_to_accomplish"):
            task.result = content["impossible_to_accomplish"]
            task.status = TaskStatus.FAILED
            args.last_output = "failed: Task is impossible to accomplish. Agent provided reason: {}".format(
                content["impossible_to_accomplish"]
            )
            direct_output_structure = {
                "tool_status": task.status,
                "tool_result": task.result,
            }
            self.callback.send_block(direct_output_structure)
            return args, "failed"

        elif content.get("divide"):
            task.result = content["divide"]
            task.status = TaskStatus.RUNNING
            args.last_output = (
                "Task is too complex to complete. Agent provided reason: {}".format(
                    content["divide"]
                )
            )
            direct_output_structure = {
                "tool_status": task.status,
                "tool_result": task.result,
            }
            self.callback.send_block(direct_output_structure)
            return args, "complex"

        elif content.get("tool_call"):
            execution_status, execution_results = self.tool_manager.execute_task(
                content["tool_call"], related_info=self.stm.former_results
            )
            if execution_status == "success":
                args.last_output = execution_results
                if task.parent:
                    if task.id not in [
                        each_child.id for each_child in task.parent.children
                    ]:
                        self.stm.former_results = {}
                self.stm.former_results[task.task] = execution_results
                task.result = execution_results
                task.status = TaskStatus.SUCCESS
                toolcall_success_output_structure = {
                    "tool_status": task.status,
                    "tool_result": task.result,
                }
                self.callback.send_block(toolcall_success_output_structure)
                return args, "success"
            else:
                # todo: retry if tool call failed, read failed reason from execution_results
                task.result = execution_results
                task.status = TaskStatus.FAILED
                self.stm.former_results["failed_detail"] = task.result
                self.stm.former_results["tool_call"] = content["tool_call"]
                return args, "failed"

        else:
            raise ValueError("LLM generation is not valid.")

    @retry(
        stop=(
            stop_after_delay(EnvVar.STOP_AFTER_DELAY)
            | stop_after_attempt(EnvVar.STOP_AFTER_ATTEMPT)
        ),
        retry=retry_if_exception_message(message="LLM generation is not valid."),
        reraise=True,
    )
    async def _arun(self, args: BaseInterface, ltm: LTM) -> Tuple[BaseInterface, str]:
        task: AgentTask = args.task
        task.status = TaskStatus.RUNNING

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
        self.callback.send_block(
            f'{Fore.WHITE}\n{"-=" * 5}Current task{"=-" * 5}{Style.RESET_ALL}\n'
            f"{Fore.BLUE}{json.dumps(chat_structure, indent=2, ensure_ascii=False)}{Style.RESET_ALL}"
        )
        chat_complete_res = await self.simple_ainfer(
            task=task.task,
            tools=self.tool_manager.generate_prompt(),
            sibling_tasks=task.sibling_info(),
            parent_task=task.parent.task_info() if task.parent else None,
            former_results=args.last_output,
        )
        content = chat_complete_res["choices"][0]["message"].get("content")
        content = self._extract_from_result(content)

        self.callback.send_block(content)
        if content.get("agent_answer"):
            args.last_output = content
            task.result = content["agent_answer"]
            task.status = TaskStatus.SUCCESS
            direct_output_structure = {
                "tool_status": task.status,
                "tool_result": task.result,
            }
            self.callback.send_block(direct_output_structure)
            return args, "success"
        elif content.get("impossible_to_accomplish"):
            task.result = content["impossible_to_accomplish"]
            task.status = TaskStatus.FAILED
            args.last_output = "failed: Task is impossible to accomplish. Agent provided reason: {}".format(
                content["impossible_to_accomplish"]
            )
            direct_output_structure = {
                "tool_status": task.status,
                "tool_result": task.result,
            }
            self.callback.send_block(direct_output_structure)
            return args, "failed"

        elif content.get("divide"):
            task.result = content["divide"]
            task.status = TaskStatus.FAILED
            args.last_output = (
                "Task is too complex to complete. Agent provided reason: {}".format(
                    content["divide"]
                )
            )
            direct_output_structure = {
                "tool_status": task.status,
                "tool_result": task.result,
            }
            self.callback.send_block(direct_output_structure)
            return args, "complex"

        elif content.get("tool_call"):
            execution_status, execution_results = await self.tool_manager.aexecute_task(
                content["tool_call"]
            )
            if execution_status == "success":
                args.last_output = execution_results
                task.result = execution_results
                task.status = TaskStatus.SUCCESS
                return args, "success"
            else:
                task.result = execution_results
                task.status = TaskStatus.FAILED
                args.last_output = "This task cannot be solved directly and all at once using a tool. Agent provided reason: {}".format(
                    execution_results
                )
                direct_output_structure = {
                    "tool_status": task.status,
                    "tool_result": task.result,
                }
                self.callback.send_block(direct_output_structure)
                return args, "complex"

        else:
            raise ValueError("LLM generation is not valid.")

    def _extract_from_result(self, result: str) -> dict:
        try:
            pattern = r'```json\s*(\{(?:.|\s)*?\})\s*```'
            result = result.replace('\n', '')
            match = re.search(pattern, result, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            else:
                return json.loads(result)
        except Exception as error:
            raise ValueError("LLM generation is not valid.")
