from pathlib import Path
from typing import List

from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.registry import registry
from omagent_core.models.llms.prompt.prompt import PromptTemplate
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.tool_system.manager import ToolManager
from pydantic import Field


CURRENT_PATH = Path(__file__).parents[0]


@registry.register_worker()
class ScenicSpotRecommendation(BaseWorker, BaseLLMBackend):
    """Scenic spot recommendation processor that generates personalized suggestions for traveling.
    
    This processor:
    1. Retrieves user instructions and scenic spot information from the workflow context.
    2. Loads system and user prompts from template files.
    3. Uses LLM to generate contextual recommendations based on scenic spot and preferences.
    4. Returns recommendations and sends them via callback.
    
    Attributes:
        llm (OpenaiGPTLLM): LLM model for generating recommendations.
        prompts (List[PromptTemplate]): System and user prompts loaded from files.
    """
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
    tool_manager: ToolManager
    def _run(self, *args, **kwargs):
        """Process user input and generate scenic spot recommendations.
        
        Retrieves user instructions and optional weather information from the workflow context,
        generates recommendations using the LLM model, and returns the recommendations while also sending them via callback.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
            
        Returns:
            str: Generated scenic spot recommendations.
        """
        # Retrieve user instruction and optional weather info from workflow context
        user_instruct = self.stm(self.workflow_instance_id).get("user_instruction")
        search_info = self.stm(self.workflow_instance_id)["search_info"] if "search_info" in self.stm(self.workflow_instance_id) else None

        # Generate scenic spot recommendations using LLM with weather and user input
        chat_complete_res = self.simple_infer(weather=str(search_info), instruction=user_instruct, image='<image_0>')

        # Extract recommendations from LLM response
        scenic_spot_recommendation = chat_complete_res["choices"][0]["message"]["content"]
        execution_status, execution_results = self.tool_manager.execute_task(
                scenic_spot_recommendation+'\nYou should use write file to complete this task.'
            )
        self.callback.send_block(agent_id=self.workflow_instance_id, msg=execution_results)
        
        # Send recommendations via callback and return
        self.callback.send_answer(agent_id=self.workflow_instance_id, msg=scenic_spot_recommendation)
        
        self.stm(self.workflow_instance_id).clear()
        return scenic_spot_recommendation

