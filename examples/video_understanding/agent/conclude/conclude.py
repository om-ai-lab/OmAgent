from pathlib import Path
from typing import List

from omagent_core.advanced_components.workflow.dnc.schemas.dnc_structure import \
    TaskTree
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.memories.ltms.ltm import LTM
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.models.llms.prompt import PromptTemplate
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry
from collections.abc import Iterator
from pydantic import Field

CURRENT_PATH = root_path = Path(__file__).parents[0]


@registry.register_worker()
class Conclude(BaseLLMBackend, BaseWorker):
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
            img_placeholders="".join(
                list(self.stm(self.workflow_instance_id).get("image_cache", {}).keys())
            ),
        )
        if isinstance(chat_complete_res, Iterator):
            last_output = "Answer: "
            self.callback.send_incomplete(
                agent_id=self.workflow_instance_id, msg="Answer: "
            )
            for chunk in chat_complete_res:
                if len(chunk.choices) > 0:
                    current_msg = chunk.choices[0].delta.content if chunk.choices[0].delta.content is not None else ''
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
        self.stm(self.workflow_instance_id).clear()
        return {"last_output": last_output}
