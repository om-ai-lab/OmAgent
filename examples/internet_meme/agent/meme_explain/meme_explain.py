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
class MemeExplain(BaseWorker, BaseLLMBackend):
    llm: OpenaiGPTLLM

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

    def _run(self, *args, **kwargs):
        """Process user input and generate outfit recommendations.
        
        Retrieves user instruction and weather information from workflow context,
        generates outfit recommendations using the LLM model, and returns the 
        recommendations while also sending them via callback.

        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Returns:
            str: Generated outfit recommendations
        """
        # Retrieve user instruction and optional weather info from workflow context
        user_instruct = self.stm(self.workflow_instance_id).get("user_instruction")
        search_info = self.stm(self.workflow_instance_id)["search_info"] if "search_info" in self.stm(self.workflow_instance_id) else None
        # Generate outfit recommendations using LLM with weather and user input
        chat_complete_res = self.simple_infer(info=str(search_info), name=user_instruct)

        # Extract recommendations from LLM response
        outfit_recommendation = chat_complete_res["choices"][0]["message"]["content"]
        
        # Send recommendations via callback and return
        self.callback.send_answer(agent_id=self.workflow_instance_id, msg=outfit_recommendation)
        
        self.stm(self.workflow_instance_id).clear()
        return outfit_recommendation
