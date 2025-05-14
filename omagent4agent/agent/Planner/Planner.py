from pathlib import Path
from typing import List

from omagent_core.advanced_components.workflow.dnc.schemas.dnc_structure import TaskTree
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.memories.ltms.ltm import LTM
from omagent_core.models.llms.base import BaseLLMBackend, BaseLLM
from omagent_core.models.llms.prompt import PromptTemplate
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry
from openai import Stream
from pydantic import Field
from collections.abc import Iterator
from omagent_core.models.llms.prompt.parser import *
from omagent_core.tool_system.manager import ToolManager

CURRENT_PATH = Path(__file__).parents[0]

@registry.register_worker()
class Planner(BaseLLMBackend, BaseWorker):
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_file(CURRENT_PATH.joinpath("planner_system.prompt"), role="system"),
            PromptTemplate.from_file(CURRENT_PATH.joinpath("planner_user.prompt"), role="user"),
        ]
    )
    llm: BaseLLM
    output_parser: StrParser = StrParser()
    tool_manager: ToolManager
    
    def _run(self, initial_description: str, *args, **kwargs):
        print("Input description:", initial_description)
        # Generate the initial plan.
        tool_schema = []
        for name, tool in self.tool_manager.tools.items():            
            tool_schema.append(str(tool.generate_schema()))

        tool_schema_str = "\n".join(tool_schema)
        self.stm(self.workflow_instance_id)["tool_schema"] = tool_schema_str
        plan_text = self.simple_infer(prompt=initial_description, tool_schema=tool_schema_str)["choices"][0]["message"].get("content")
        self.callback.info(agent_id=self.workflow_instance_id, progress="Planner", message=plan_text)
        state = self.stm(self.workflow_instance_id)
        state["plan"] = plan_text
        state["initial_description"] = initial_description

        # Enter a loop for user confirmation/suggestion.
        """
        while True:
            user_response = self.input.read_input(
                workflow_instance_id=self.workflow_instance_id,
                input_prompt="Is the generated plan acceptable? "
                             "Reply 'good' or 'yes' if it is fine. "
                             "Otherwise, provide your suggestion to improve it."
            )
            suggestion = user_response['messages'][-1]['content']
            for content_item in suggestion:
                if content_item['type'] == 'text':
                    suggestion = content_item['data']
            # If the user confirms or provides an empty response, we consider it acceptable.
            if suggestion.lower() in ("good", "yes", ""):
                self.callback.info(
                    agent_id=self.workflow_instance_id,
                    progress="Planner",
                    message="Final plan confirmed."
                )
                break
            else:
                # Generate a new plan using the original description, the current plan, and the user's suggestion.
                new_prompt = (
                    f"Initial description: {initial_description}\n"
                    f"Previous plan: {plan_text}\n"
                    f"User suggestion: {suggestion}\n"
                    f"Generate a revised plan based on the above."
                )
                plan_text = self.simple_infer(prompt=new_prompt)["choices"][0]["message"].get("content")
                self.callback.info(agent_id=self.workflow_instance_id, progress="Planner", message=plan_text)
                state["plan"] = plan_text
        """
        print("FinalPlan:", plan_text)

        return {"plan": plan_text}

