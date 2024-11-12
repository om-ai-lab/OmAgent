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
from ....engine.worker.base import BaseWorker
from ....engine.task.agent_task import TaskTree


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
        """A task rescue node that attempts to recover from tool execution failures.

        This component acts as a rescue mechanism that:
        - Takes a failed tool execution and its error details
        - Analyzes the failure reason (e.g. missing dependencies, invalid arguments)
        - Attempts to fix the issue by retrying with corrected parameters
        - Maintains context about the original task and failure
        - Provides detailed feedback about rescue attempts

        The rescue node is responsible for:
        1. Retrieving the original failed tool call and error details
        2. Using LLM to understand the failure and generate fixes
        3. Re-executing the tool with corrections
        4. Tracking rescue attempts and results
        5. Determining if rescue was successful or needs further handling

        Args:
            agent_task (dict): The task tree containing the failed task
            last_output (str): The output from previous failed execution
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            dict: Contains updated task status, rescue results, and next actions
        """
        toolcall_content = self.stm(self.workflow_instance_id).get("former_results", {}).pop("tool_call", None)
        # Get the tool call information from the former results
        if toolcall_content is not None:
            former_results = self.stm(self.workflow_instance_id)['former_results']
            tool_call_error = former_results.pop("tool_call_error", None)
            task = TaskTree(**agent_task)
            current_node = task.get_current_node()

            # Call LLM to understand the failure and generate fixes
            chat_complete_res = self.simple_infer(
                task=current_node.task,
                failed_detail=tool_call_error,
            )
            former_results['failed_detail'] = chat_complete_res["choices"][0]["message"]["content"]
            
            # Re-execute the tool call with the corrected parameters
            rescue_execution_status, rescue_execution_results = (
                self.tool_manager.execute_task(
                    toolcall_content, related_info=former_results
                )
            )

            # Handle the case where the rescue execution is successful
            if rescue_execution_status == "success":
                former_results.pop("failed_detail", None)
                former_results['rescue_detail'] = rescue_execution_results
                self.stm(self.workflow_instance_id)['former_results'] = former_results
                self.callback.info(agent_id=self.workflow_instance_id, progress=f'Rescue', message=f'Rescue tool call success.')
                return {"agent_task": task.model_dump(), "switch_case_value": "success", "last_output": last_output, "kwargs": kwargs}
            # Handle the case where the rescue execution is failed
            else:
                self.stm(self.workflow_instance_id)['former_results'] = former_results
                current_node.status = TaskStatus.RUNNING
                self.callback.info(agent_id=self.workflow_instance_id, progress=f'Rescue', message=f'Rescue tool call failed.')
                return {"agent_task": task.model_dump(), "switch_case_value": "failed", "last_output": last_output, "kwargs": kwargs}
        
        # Handle the case where there is no tool call to rescue
        else:
            self.callback.info(agent_id=self.workflow_instance_id, progress=f'Rescue', message=f'No tool call to rescue.')
            return {"agent_task": task.model_dump(), "switch_case_value": "failed", "last_output": last_output, "kwargs": kwargs}
