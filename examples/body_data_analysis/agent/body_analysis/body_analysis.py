from pathlib import Path
from typing import List

from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.registry import registry
from omagent_core.models.llms.prompt.prompt import PromptTemplate
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM

from pydantic import Field


CURRENT_PATH = Path(__file__).parents[0]


@registry.register_worker()
class BodyAnalysis(BaseWorker, BaseLLMBackend):

    llm: OpenaiGPTLLM

    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("sys_prompt_en.prompt"), role="system"
            ),
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("user_prompt_en.prompt"), role="user"
            ),
        ]
    )

    def _run(self, *args, **kwargs):

        # Retrieve user instruction and optional weather info from workflow context
        user_body_data = self.stm(self.workflow_instance_id).get("user_body_data")
        
        chat_complete_res = self.simple_infer(bodydata=str(user_body_data))

        # Extract recommendations from LLM response
        body_analysis = chat_complete_res["choices"][0]["message"]["content"]
        
        # Send recommendations via callback and return
        self.callback.send_answer(agent_id=self.workflow_instance_id, msg=body_analysis)
        
        self.stm(self.workflow_instance_id).clear()
        return body_analysis

