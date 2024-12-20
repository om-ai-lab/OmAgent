import re
from pathlib import Path
from typing import List

import json_repair
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.models.llms.prompt.parser import StrParser
from omagent_core.models.llms.prompt.prompt import PromptTemplate
from omagent_core.tool_system.manager import ToolManager
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry
from pydantic import Field

CURRENT_PATH = Path(__file__).parents[0]


@registry.register_worker()
class OutfitQA(BaseLLMBackend, BaseWorker):
    """Outfit Q&A processor that handles interactive dialogue with users about outfit recommendations.

    This processor manages a multi-turn conversation with users to gather outfit preferences and requirements:
    1. Takes user instructions, search info, and feedback from workflow context
    2. Uses LLM to analyze context and either:
       - Generate follow-up questions to clarify user needs
       - Make tool calls to search for relevant information (e.g. weather)
    3. Handles user responses and tool execution results
    4. Updates workflow context with new information for downstream processors

    Attributes:
        output_parser (StrParser): Parser for LLM output strings
        llm (OpenaiGPTLLM): LLM model for generating questions and analyzing responses
        prompts (List[PromptTemplate]): System and user prompts loaded from template files
        tool_manager (ToolManager): Tool manager instance for executing web searches
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
        """Run the outfit Q&A processor to gather outfit requirements through conversation.

        Manages an interactive dialogue loop that:
        1. Retrieves current context (user instructions, search results, feedback)
        2. Uses LLM to analyze context and determine next action
        3. Either asks user a follow-up question or executes a web search
        4. Updates context with new information

        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments containing workflow context

        Returns:
            None - Updates workflow context with new user responses or search results

        Raises:
            ValueError: If LLM output is invalid or web search fails
        """
        # Retrieve conversation context from memory, initializing empty if not present
        if self.stm(self.workflow_instance_id).get("user_instruction"):
            user_instruct = self.stm(self.workflow_instance_id).get("user_instruction")
        else:
            user_instruct = []

        if self.stm(self.workflow_instance_id).get("search_info"):
            search_info = self.stm(self.workflow_instance_id).get("search_info")
        else:
            search_info = []

        if self.stm(self.workflow_instance_id).get("feedback"):
            feedback = self.stm(self.workflow_instance_id).get("feedback")
        else:
            feedback = []

        # Log current conversation state for debugging
        chat_structure = {
            "search_info": search_info,
            "user_instruct": user_instruct,
            "feedback": feedback,
        }
        logging.info(chat_structure)

        # Generate next conversation action using LLM
        chat_complete_res = self.simple_infer(
            instruction=str(user_instruct),
            previous_search=str(search_info),
            feedback=str(feedback),
        )
        content = chat_complete_res["choices"][0]["message"].get("content")
        content = self._extract_from_result(content)

        # Handle follow-up question flow
        if content.get("conversation"):
            question = content["conversation"]
            # self.callback.send_block(self.workflow_instance_id, msg=question)
            user_input = self.input.read_input(
                workflow_instance_id=self.workflow_instance_id,
                input_prompt=question + "\n",
            )
            content = user_input["messages"][-1]["content"]
            for content_item in content:
                if content_item["type"] == "text":
                    answer = content_item["data"]

            # Store Q&A exchange in conversation history
            user_instruct.append("Question: " + question + "\n" + "Answer: " + answer)
            self.stm(self.workflow_instance_id)["user_instruction"] = user_instruct
            return

        # Handle web search flow for gathering contextual info
        elif content.get("tool_call"):
            self.callback.info(
                self.workflow_instance_id,
                progress="Outfit QA",
                message="Search for weather information",
            )
            execution_status, execution_results = self.tool_manager.execute_task(
                content["tool_call"]
                + "\nYou should use web search to complete this task."
            )
            if execution_status == "success":
                search_info.append(str(execution_results))
                self.stm(self.workflow_instance_id)["search_info"] = search_info
                feedback.append(
                    "The weather information is provided detailly and specifically, and satisfied the requirement, dont need to ask for more weather information."
                )
                self.stm(self.workflow_instance_id)["feedback"] = feedback
                return
            else:
                raise ValueError("Web search tool execution failed.")

        else:
            raise ValueError("LLM generation is not valid.")

    def _extract_from_result(self, result: str) -> dict:
        try:
            pattern = r"```json\s+(.*?)\s+```"
            match = re.search(pattern, result, re.DOTALL)
            if match:
                return json_repair.loads(match.group(1))
            else:
                return json_repair.loads(result)
        except Exception as error:
            raise ValueError("LLM generation is not valid.")
