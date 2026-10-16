from omagent_core.engine.worker.base import BaseWorker
from omagent_core.models.llms.prompt import prompt
from omagent_core.utils.registry import registry
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.models.llms.schemas import Message, Content
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.utils.logger import logging
import ast
from typing import List
from pathlib import Path
from omagent_core.models.llms.prompt.prompt import PromptTemplate
from pydantic import Field

CURRENT_PATH = Path(__file__).parents[0]

@registry.register_worker()
class COTExtract(BaseLLMBackend, BaseWorker):


    """ 
    COTExtract class for handling extraction tasks using OpenaiGPTLLM.
    It manages the prompts and interacts with the base worker architecture.
    """

    llm: OpenaiGPTLLM

    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("user_prompt.prompt"), role="user"
            ),
        ]
    )

    def _run(self,  reasoning_result:List[str], *args, **kwargs):

        """
        Executes the reasoning process based on the final answers and question provided.

        Args:
            reasoning_result (List[str]): A list of reasoning results to be processed.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            dict: A dictionary containing the final answer.
        """
        final_answer = []
        for item in reasoning_result:
            reasoning_result = self.simple_infer(reasoning_step=item)
            reasoning_result = reasoning_result["choices"][0]["message"]["content"]
            final_answer.append(reasoning_result)
        self.stm(self.workflow_instance_id)['reasoning_result'] = final_answer
        self.callback.send_answer(self.workflow_instance_id, msg=",".join(final_answer))
        return {'final_answer': final_answer}