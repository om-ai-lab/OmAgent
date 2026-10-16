import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, List, Tuple

import json_repair
from colorama import Fore, Style
from omagent_core.advanced_components.workflow.dnc.schemas.dnc_structure import (
    TaskStatus, TaskTree)
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.memories.ltms.ltm import LTM
from omagent_core.models.llms.base import BaseLLMBackend, StrParser
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.models.llms.prompt.prompt import PromptTemplate
from omagent_core.tool_system.manager import ToolManager
from omagent_core.utils.registry import registry
from pydantic import Field
from tenacity import (retry, retry_if_exception_message, stop_after_attempt,
                      stop_after_delay)
from omagent_core.utils.logger import logging

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

    def _run(self, dnc_structure: dict, last_output: str, *args, **kwargs):
        """A task conqueror that executes and manages complex task trees.

        This component acts as a task conqueror that:
        - Takes a hierarchical task tree and processes each task node
        - Maintains context and state between task executions
        - Leverages LLM to determine next actions and generate responses
        - Manages task dependencies and relationships between parent/sibling tasks
        - Tracks task completion status and progression through the tree

        The conqueror is responsible for breaking down complex tasks into manageable
        subtasks and ensuring they are executed in the correct order while maintaining
        overall context and goal alignment.

        Args:
            dnc_structure (dict): The task tree definition and current state
            last_output (str): The output from previous task execution
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            dict: Processed response containing next actions or task completion results
        """
        task = TaskTree(**dnc_structure)
        current_node = task.get_current_node()
        current_node.status = TaskStatus.RUNNING

        # Initialize former_results in shared memory if not present
        # former_results is used to store the results of the tasks which are in the same depth that have been executed
        if not self.stm(self.workflow_instance_id).get("former_results"):
            self.stm(self.workflow_instance_id)["former_results"] = {}
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
            "former_results": self.stm(self.workflow_instance_id)["former_results"],
            "extra_info": self.stm(self.workflow_instance_id).get("extra"),
            "img_placeholders": self.stm(self.workflow_instance_id).get("image_cache"),
        }

        # Call LLM to get next actions or task completion results
        chat_complete_res = self.infer(input_list=[payload])
        logging.info(f"Conqueror chat_complete_res: {chat_complete_res}")
        content = chat_complete_res[0]["choices"][0]["message"].get("content")
        content = json_repair.loads(content)

        # Handle the case where the LLM returns a dictionary with multiple keys
        first_key = next(iter(content))
        new_data = {first_key: content[first_key]}
        content = new_data

        # LLM returns the direct answer of the task
        if content.get("agent_answer"):
            last_output = content
            if task.get_parent(current_node.id):
                if current_node.id not in [
                    each.id
                    for each in task.get_children(task.get_parent(current_node.id).id)
                ]:
                    self.stm(self.workflow_instance_id)["former_results"] = {}
            former_results = self.stm(self.workflow_instance_id)["former_results"]
            former_results[current_node.task] = content
            self.stm(self.workflow_instance_id)["former_results"] = former_results
            current_node.result = content["agent_answer"]
            current_node.status = TaskStatus.SUCCESS
            self.callback.info(
                agent_id=self.workflow_instance_id,
                progress=f"Conqueror",
                message=f'Task "{current_node.task}"\nAgent answer: {content["agent_answer"]}',
            )
            self.stm(self.workflow_instance_id)["dnc_structure"] = task.model_dump()
            self.stm(self.workflow_instance_id)["last_output"] = last_output
            return {
                "dnc_structure": task.model_dump(),
                "switch_case_value": "success",
                "last_output": last_output,
                "kwargs": kwargs,
            }

        # LLM returns the reason why the task needs to be divided
        elif content.get("divide"):
            current_node.result = content["divide"]
            current_node.status = TaskStatus.RUNNING
            last_output = (
                "Task is too complex to complete. Agent provided reason: {}".format(
                    content["divide"]
                )
            )
            self.callback.info(
                agent_id=self.workflow_instance_id,
                progress=f"Conqueror",
                message=f'Task "{current_node.task}" needs to be divided.',
            )
            self.stm(self.workflow_instance_id)["dnc_structure"] = task.model_dump()
            self.stm(self.workflow_instance_id)["last_output"] = last_output
            return {
                "dnc_structure": task.model_dump(),
                "switch_case_value": "complex",
                "last_output": last_output,
                "kwargs": kwargs,
            }

        # LLM returns the tool call information
        elif content.get("tool_call"):
            self.callback.info(
                agent_id=self.workflow_instance_id,
                progress=f"Conqueror",
                message=f'Task "{current_node.task}" needs to be executed by tool.',
            )

            # Call tool_manager to decide which tool to use and execute the tool
            execution_status, execution_results = self.tool_manager.execute_task(
                content["tool_call"],
                related_info=self.stm(self.workflow_instance_id)["former_results"],
            )
            former_results = self.stm(self.workflow_instance_id)["former_results"]
            former_results["tool_call"] = content["tool_call"]

            # Handle the case where the tool call is successful
            if execution_status == "success":
                last_output = execution_results
                if task.get_parent(current_node.id):
                    if current_node.id not in [
                        each.id
                        for each in task.get_children(
                            task.get_parent(current_node.id).id
                        )
                    ]:
                        self.stm(self.workflow_instance_id)["former_results"] = {}
                former_results.pop("tool_call", None)
                former_results[current_node.task] = execution_results
                self.stm(self.workflow_instance_id)["former_results"] = former_results
                current_node.result = execution_results
                current_node.status = TaskStatus.SUCCESS
                toolcall_success_output_structure = {
                    "tool_status": current_node.status,
                    "tool_result": current_node.result,
                }
                self.callback.info(
                    agent_id=self.workflow_instance_id,
                    progress=f"Conqueror",
                    message=f"Tool call success. {toolcall_success_output_structure}",
                )
                self.stm(self.workflow_instance_id)["dnc_structure"] = task.model_dump()
                self.stm(self.workflow_instance_id)["last_output"] = last_output
                return {
                    "dnc_structure": task.model_dump(),
                    "switch_case_value": "success",
                    "last_output": last_output,
                    "kwargs": kwargs,
                }
            # Handle the case where the tool call is failed
            else:
                current_node.result = execution_results
                current_node.status = TaskStatus.FAILED
                former_results["tool_call_error"] = (
                    f"tool_call {content['tool_call']} raise error: {current_node.result}"
                )
                self.stm(self.workflow_instance_id)["former_results"] = former_results
                self.callback.info(
                    agent_id=self.workflow_instance_id,
                    progress=f"Conqueror",
                    message=f'Tool call failed. {former_results["tool_call_error"]}',
                )
                self.stm(self.workflow_instance_id)["dnc_structure"] = task.model_dump()
                self.stm(self.workflow_instance_id)["last_output"] = last_output
                return {
                    "dnc_structure": task.model_dump(),
                    "switch_case_value": "failed",
                    "last_output": last_output,
                    "kwargs": kwargs,
                }
        # Handle the case where the LLM generation is not valid
        else:
            raise ValueError("LLM generation is not valid.")
