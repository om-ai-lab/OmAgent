from pathlib import Path
from typing import List

from ....models.llms.base import BaseLLMBackend
from ....engine.worker.base import BaseWorker
from ....engine.workflow.context import BaseWorkflowContext
from ....models.llms.prompt import PromptTemplate
from ....memories.ltms.ltm import LTM
from ....utils.registry import registry
from pydantic import Field
from ....engine.task.agent_task import TaskTree

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

    def _run(self, agent_task: dict, last_output: str, *args, **kwargs):
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
        task = TaskTree(**agent_task)
        self.callback.info(agent_id=self.workflow_instance_id, progress=f'Conclude', message=f'{task.get_current_node().task}')
        chat_complete_res = self.simple_infer(
            task=task.get_root().task,
            result=str(last_output),
            img_placeholders="".join(list(self.stm(self.workflow_instance_id).get('image_cache', {}).keys())),
        )
        self.callback.send_answer(agent_id=self.workflow_instance_id, msg=f'Answer: {chat_complete_res["choices"][0]["message"]["content"]}')
        last_output = chat_complete_res["choices"][0]["message"]["content"]
        for key, value in self.token_usage.items():
            print(f"Usage of {key}: {value}")
        self.stm(self.workflow_instance_id).clear()
        return {'last_output': last_output}