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
from ....engine.workflow.context import BaseWorkflowContext
from ....models.llms.prompt import PromptTemplate
from ....memories.ltms.ltm import LTM
from ....utils.env import EnvVar
from ....utils.registry import registry
from ....tool_system.manager import ToolManager
from omagent_core.engine.worker.base import BaseWorker


CURRENT_PATH = root_path = Path(__file__).parents[0]


@registry.register_worker()
class TaskRescue(BaseLLMBackend, BaseWorker):
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

    def _run(self, agent_task: dict, last_output: str, *args, **kwargs) -> Tuple[BaseWorkflowContext, str]:
        toolcall_content = self.stm['former_results'].pop("tool_call", None)
        if toolcall_content is not None:
            former_results = self.stm['former_results']
            tool_call_error = former_results.pop("tool_call_error", None)
            task = self.stm['agent_task']
            chat_complete_res = self.simple_infer(
                task=task.task,
                failed_detail=tool_call_error,
            )
            former_results['failed_detail'] = chat_complete_res["choices"][0]["message"]["content"]
            # self.stm['former_results'] = former_results

            rescue_execution_status, rescue_execution_results = (
                self.tool_manager.execute_task(
                    toolcall_content, related_info=former_results
                )
            )
            if rescue_execution_status == "success":
                # toolcall_rescue_output_structure = {
                #     "tool_status": rescue_execution_status,
                #     "tool_result": rescue_execution_results,
                # }
                # former_results = self.stm['former_results']
                former_results.pop("failed_detail", None)
                former_results['rescue_detail'] = rescue_execution_results
                self.stm['former_results'] = former_results
                return args, "success"
            else:
                self.stm['former_results'] = former_results
                task.status = TaskStatus.RUNNING
                return args, "failure"
        else:
            return args, "failure"
