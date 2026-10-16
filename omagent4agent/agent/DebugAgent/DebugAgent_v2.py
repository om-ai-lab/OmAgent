import os
import sys
import json
import glob2
import difflib
from pathlib import Path
from typing import List
from pprint import pprint

from omagent_core.engine.worker.base import BaseWorker
from omagent_core.models.llms.base import BaseLLMBackend, BaseLLM
from omagent_core.models.llms.prompt import PromptTemplate
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry
from pydantic import Field
from omagent_core.models.llms.prompt.parser import *

CURRENT_PATH = Path(__file__).parents[0]


@registry.register_worker()
class DebugAgent2(BaseLLMBackend, BaseWorker):
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_file(CURRENT_PATH.joinpath("debug_agent_system.prompt"), role="system"),
            PromptTemplate.from_file(CURRENT_PATH.joinpath("debug_agent_user.prompt"), role="user"),
        ]
    )
    llm: BaseLLM

    def _run(self, *args, **kwargs):
        # Retrieve necessary state once.
        state = self.stm(self.workflow_instance_id)
        error_message = state.get("error_message", "")

        # If the same error repeats, regenerate or exit early.
        prev_error = state.get("previous_error_message", None)
        if prev_error == error_message and error_message not in ("no error", ""):
            self.callback.info(
                agent_id=self.workflow_instance_id,
                progress="REGENERATING",
                message="Same error repeated, regenerating the code..."
            )
            # Completely regenerate the code, or whatever logic you need here:
            # e.g., ...
            # self._completely_regenerate_code()
            return {"finished": True}
        else:
            state["previous_error_message"] = error_message

        traceback = state.get("traceback", "")
        workflow = state.get("workflow_json", {})
        example_input = state.get("example_input", {})
        folder_path = state.get("folder_path", "")

        # Log the retrieved state.
        logging.info(f"Error: {error_message}")
        logging.info(f"Traceback: {traceback}")
        logging.info(f"Workflow: {workflow}")
        logging.info(f"Example Input: {example_input}")

        # Exit early if there's nothing to fix.
        if error_message == "no error" or not workflow:
            return {"finished": True}

        # Load all .py files (ignoring __init__.py) from the agent folder.
        file_paths = glob2.glob(os.path.join(folder_path, "agent", "**", "*.py"))
        full_code = ""
        code_by_file = {}

        for file_path in file_paths:
            if "__init__.py" in file_path:
                continue
            try:
                with open(file_path, "r") as f:
                    content = f.read()
            except Exception as e:
                logging.error(f"Error reading {file_path}: {e}")
                continue
            full_code += f"# File_path: {file_path}\n{content}\n\n"
            code_by_file[file_path] = content

        # Inform callback about debugging start.
        self.callback.info(
            agent_id=self.workflow_instance_id,
            progress="DEBUGGING",
            message=error_message
        )

        # Initialize fix suggestion as an empty string.
        fix_suggestion = ""

        # Begin suggestion loop.
        while True:
            # Call the LLM to get code suggestions.
            if not fix_suggestion == "":
                error_message = ""
                traceback = ""

            suggestions_response = self.simple_infer(
                fix_suggestion=fix_suggestion,
                traceback=traceback,
                error_message=error_message,
                workflow=workflow,
                code=full_code,
                input=example_input
            )
            suggestions_content = suggestions_response["choices"][0]["message"].get("content")
            try:
                suggestions = self.parse(suggestions_content)
            except Exception as e:
                logging.error(f"Error parsing suggestions: {e}")
                return {"finished": False}

            # Iterate over each suggestion returned.
            suggestion_applied = False
            for suggestion in suggestions:
                file_path = suggestion.get("file_path")
                new_code = suggestion.get("code")
                if file_path not in code_by_file:
                    logging.warning(f"Suggestion provided for unknown file: {file_path}")
                    continue

                # Generate a diff between the old and new code.
                diff_code = self.diff(code_by_file[file_path], new_code)
                self.callback.info(
                    agent_id=self.workflow_instance_id,
                    progress=f"Suggestion for {file_path}",
                    message=diff_code
                )
                # Ask user whether to apply the fix.
                user_response = self.input.read_input(
                    workflow_instance_id=self.workflow_instance_id,
                    input_prompt="Do you want to apply this fix? (yes/no) "
                                 "Or provide an alternative suggestion if you have any:"
                )
                # Assume the latest message's content is a string.
                user_input = user_response['messages'][-1]['content']
                for content_item in user_input:
                    if content_item['type'] == 'text':
                        user_input = content_item['data'].lower()

                if user_input == "yes":
                    try:
                        with open(file_path, "w") as f:
                            f.write(new_code)
                    except Exception as e:
                        logging.error(f"Error writing to {file_path}: {e}")
                        continue
                    self.clear_modules(folder_path)
                    return {"finished": False}
                elif user_input == "no":
                    self.callback.info(
                        agent_id=self.workflow_instance_id,
                        progress=f"Suggestion for {file_path}",
                        message="User declined to apply the fix."
                    )
                    # Continue to the next suggestion.
                    continue
                else:
                    # Update fix_suggestion with the user's alternative input and break to get new suggestions.
                    fix_suggestion = user_input
                    suggestion_applied = True
                    break

            if suggestion_applied:
                # Restart loop with the new suggestion.
                continue
            # If no suggestion was applied and no new suggestion provided, exit loop.
            break

        return {"finished": False}

    def parse(self, code: str):
        """
        Parses the provided string by removing markdown wrappers and loading JSON.
        """
        cleaned_code = code.replace("```json", "").replace("```", "")
        return json.loads(cleaned_code)

    def diff(self, code_a: str, code_b: str):
        """
        Compares two code snippets and returns a unified diff as a string.
        """
        code_a_lines = code_a.splitlines()
        code_b_lines = code_b.splitlines()
        diff_generator = difflib.unified_diff(code_a_lines, code_b_lines, lineterm='')
        return '\n'.join(diff_generator)

    def clear_modules(self, folder: str):
        """
        Clears loaded modules under the agent directory and unregisters them.
        """
        agents_dir = os.path.join(folder, "agent")
        for module_name in list(sys.modules.keys()):
            module = sys.modules[module_name]
            if module_name.startswith("agent") or (hasattr(module, '__file__') and module.__file__ and agents_dir in module.__file__):
                del sys.modules[module_name]
                class_name = module_name.split('.')[-1]
                try:
                    registry.unregister("worker", class_name)
                except KeyError:
                    logging.info(f"Module {class_name} not found in registry, skipping unregistration.")
