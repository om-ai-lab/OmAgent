from pathlib import Path
from typing import List

from omagent_core.advanced_components.workflow.dnc.schemas.dnc_structure import TaskTree
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.memories.ltms.ltm import LTM
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.models.llms.prompt import PromptTemplate
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry
from openai import Stream
from pydantic import Field
from collections.abc import Iterator

CURRENT_PATH = root_path = Path(__file__).parents[0]


@registry.register_worker()
class Conclude(BaseLLMBackend, BaseWorker):

    def _run(self, dnc_structure: dict, last_output: str, *args, **kwargs):
        """A conclude node that summarizes and completes the root task.

        This component acts as the final node that:
        - Takes the root task and its execution results
        - Generates a final conclusion/summary of the entire task execution
        - Formats and presents the final output in a clear way
        - Cleans up any temporary state/memory used during execution

        The conclude node is responsible for providing a coherent final response that
        addresses the original root task objective based on all the work done by
        previous nodes.

        Args:
            agent_task (dict): The task tree containing the root task and results
            last_output (str): The final output from previous task execution
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            dict: Final response containing the conclusion/summary
        """
        task = TaskTree(**dnc_structure)
        self.callback.info(
            agent_id=self.workflow_instance_id,
            progress=f"Conclude",
            message=f"{task.get_current_node().task}",
        )
        chat_complete_res = self.simple_infer(
            task=task.get_root().task,
            result=str(last_output),
            img_placeholders=self.stm(self.workflow_instance_id).get("image_cache"),
        )
        if isinstance(chat_complete_res, Iterator):
            # Invoke the DeepSeek model via API to stream the reasoning process and results.
            if hasattr(next(chat_complete_res).choices[0].delta, "reasoning_content"):
                last_output = "Reasoning: \n"
                self.callback.send_incomplete(
                    agent_id=self.workflow_instance_id, msg="Reasoning: \n"
                )
                flag = False
                for chunk in chat_complete_res:
                    if len(chunk.choices) > 0:
                        if not flag and chunk.choices[0].delta.content is not None:
                            last_output += "\nAnswer: "
                            self.callback.send_incomplete(
                                agent_id=self.workflow_instance_id,
                                msg="\nAnswer: ",
                            )
                            flag = True
                        current_msg = (
                            chunk.choices[0].delta.content
                            if chunk.choices[0].delta.content is not None
                            else (
                                chunk.choices[0].delta.reasoning_content
                                if chunk.choices[0].delta.reasoning_content is not None
                                else ""
                            )
                        )
                        self.callback.send_incomplete(
                            agent_id=self.workflow_instance_id,
                            msg=f"{current_msg}",
                        )
                        last_output += current_msg
                self.callback.send_answer(agent_id=self.workflow_instance_id, msg="")
            # Invoke the DeepSeek model via ollama API to stream the reasoning process and results.
            elif "deepseek" in self.llm.model_id:
                last_output = "Reasoning: \n "
                self.callback.send_incomplete(
                    agent_id=self.workflow_instance_id, msg="Reasoning: \n"
                )
                for chunk in chat_complete_res:
                    if len(chunk.choices) > 0:
                        current_msg = (
                            chunk.choices[0].delta.content
                            if chunk.choices[0].delta.content is not None
                            else ""
                        )
                        if current_msg == "</think>":
                            current_msg = "\nAnswer:"
                        self.callback.send_incomplete(
                            agent_id=self.workflow_instance_id,
                            msg=f"{current_msg}",
                        )
                        last_output += current_msg
                self.callback.send_answer(agent_id=self.workflow_instance_id, msg="")
            # Invoke models that typically do not have a reasoning process, and stream the results.
            else:
                last_output = "Answer: "
                self.callback.send_incomplete(
                    agent_id=self.workflow_instance_id, msg="Answer: "
                )
                for chunk in chat_complete_res:
                    if len(chunk.choices) > 0:
                        current_msg = (
                            chunk.choices[0].delta.content
                            if chunk.choices[0].delta.content is not None
                            else ""
                        )
                        self.callback.send_incomplete(
                            agent_id=self.workflow_instance_id,
                            msg=f"{current_msg}",
                        )
                        last_output += current_msg
                self.callback.send_answer(agent_id=self.workflow_instance_id, msg="")
        else:
            last_output = chat_complete_res["choices"][0]["message"]["content"]
            self.callback.send_answer(
                agent_id=self.workflow_instance_id,
                msg=f'Answer: {chat_complete_res["choices"][0]["message"]["content"]}',
            )
        self.callback.send_answer(
            agent_id=self.workflow_instance_id, msg=f"Token usage: {self.token_usage}"
        )
        self.stm(self.workflow_instance_id).clear()
        return {"last_output": last_output}
