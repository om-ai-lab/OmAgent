import json
from pathlib import Path
from typing import List, Tuple

from colorama import Fore, Style
from ....engine.task.agent_task import TaskStatus
from pydantic import Field
from tenacity import (
    retry,
    retry_if_exception_message,
    stop_after_attempt,
    stop_after_delay,
)

from ....models.llms.base import BaseLLMBackend
from ....engine.node.decider import BaseDecider
from ....engine.workflow.context import BaseWorkflowContext
from ....models.llms.prompt import PromptTemplate
from ....memories.ltms.ltm import LTM
from ....utils.env import EnvVar
from ....utils.registry import registry
from ....tool_system.manager import ToolManager

CURRENT_PATH = root_path = Path(__file__).parents[0]


@registry.register_node()
class TaskRescue(BaseLLMBackend, BaseDecider):
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
    def _run(self, args: BaseWorkflowContext, ltm: LTM) -> Tuple[BaseWorkflowContext, str]:
        toolcall_content = self.stm.former_results.get("tool_call", None)
        if toolcall_content is not None:
            del self.stm.former_results["tool_call"]
            chat_complete_res = self.simple_infer(
                task=args.task.task,
                failed_detail=self.stm.former_results["failed_detail"],
            )
            self.stm.former_results["failed_detail"] = chat_complete_res["choices"][0][
                "message"
            ]["content"]

            rescue_execution_status, rescue_execution_results = (
                self.tool_manager.execute_task(
                    toolcall_content, related_info=self.stm.former_results
                )
            )
            if rescue_execution_status == "success":
                toolcall_rescue_output_structure = {
                    "tool_status": rescue_execution_status,
                    "tool_result": rescue_execution_results,
                }
                self.callback.send_block(
                    f'{Fore.WHITE}\n{"-=" * 5}Tool Call {Fore.RED}Rescue{Style.RESET_ALL} Output{"=-" * 5}{Style.RESET_ALL}\n'
                    f"{Fore.BLUE}{json.dumps(toolcall_rescue_output_structure, indent=2, ensure_ascii=False)}{Style.RESET_ALL}"
                )
                del self.stm.former_results["failed_detail"]
                self.stm.former_results["rescue_detail"] = rescue_execution_results
                return args, "success"

            else:
                args.task.status = TaskStatus.RUNNING
                return args, "failure"
        else:
            return args, "failure"

    async def _arun(self, args: BaseWorkflowContext, ltm: LTM) -> Tuple[BaseWorkflowContext, str]:
        toolcall_content = self.stm.former_results.get("tool_call", None)
        if toolcall_content is not None:
            del self.stm.former_results["tool_call"]
            chat_complete_res = await self.simple_ainfer(
                task=args.task.task,
                failed_detail=self.stm.former_results["failed_detail"],
            )
            self.stm.former_results["failed_detail"] = chat_complete_res["choices"][0][
                "message"
            ]["content"]

            rescue_execution_status, rescue_execution_results = (
                await self.tool_manager.aexecute_task(
                    toolcall_content, related_info=self.stm.former_results
                )
            )
            if rescue_execution_status == "success":
                toolcall_rescue_output_structure = {
                    "tool_status": rescue_execution_status,
                    "tool_result": rescue_execution_results,
                }
                self.callback.send_block(
                    f'{Fore.WHITE}\n{"-=" * 5}Tool Call {Fore.RED}Rescue{Style.RESET_ALL} Output{"=-" * 5}{Style.RESET_ALL}\n'
                    f"{Fore.BLUE}{json.dumps(toolcall_rescue_output_structure, indent=2, ensure_ascii=False)}{Style.RESET_ALL}"
                )
                del self.stm.former_results["failed_detail"]
                self.stm.former_results["rescue_detail"] = rescue_execution_results
                return args, "success"

            else:
                args.task.status = TaskStatus.RUNNING
                return args, "failure"
        else:
            return args, "failure"