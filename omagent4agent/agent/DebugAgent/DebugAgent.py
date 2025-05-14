import os
import sys
import json
import glob2
import difflib
from pathlib import Path
from typing import List
import re
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.models.llms.base import BaseLLMBackend, BaseLLM
from omagent_core.models.llms.prompt import PromptTemplate
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry
from pydantic import Field
from omagent_core.models.llms.prompt.parser import *
import demjson3
import traceback
from omagent_core.models.llms.schemas import Message


CURRENT_PATH = Path(__file__).parent


@registry.register_worker()
class DebugAgent(BaseLLMBackend, BaseWorker):
    """
    DebugAgent applies iterative debugging by generating and applying code fixes.
    It loops until the workflow executes with no errors or the same error is seen three times.
    """
    prompts: List[PromptTemplate] = Field(default=[
        PromptTemplate.from_file(CURRENT_PATH.joinpath("../WorkerManager/worker_user.prompt"), role="system"),
        PromptTemplate.from_file(CURRENT_PATH.joinpath("debug_agent_user.prompt"), role="user"),
    ])
    llm: BaseLLM
    output_parser: DictParser = DictParser()
    def _run(self, folder_path, example_inputs, *args, **kwargs):
        print ("folder_path 1111111111111",folder_path)
        if not folder_path:
            folder_path = self.stm(self.workflow_instance_id).get("folder_path", "")
        if not example_inputs:
            example_inputs = self.stm(self.workflow_instance_id).get("example_input", "")
        count = 0
        while True:
            state = self.execute_workflow(folder_path=folder_path, example_inputs=example_inputs)
            print ("state 2222222222222",state)
            if not state.get("status", 'fail') == 'fail':
                self.callback.info(
                agent_id=self.workflow_instance_id,
                progress="DEBUGGING",
                message="No error detected. Exiting debug loop."
            )
                return {"finished": True}
            else:
                print ("state 3333333333333",state)
                self.debug(folder_path, state)
                print ("debug finished")
                count += 1
                print ("count 6666666666666",count)
                if count >= 5:
                    return {"finished": False}
    
    def extract_file_paths(self, error_message):
        pattern = r'File \"([^<>\"]+)\"'
        paths =  [z for z in re.findall(pattern, error_message) if z.endswith(".py") and "generated_agents" in z ]
        codes = {}
        for path in paths:
            with open(path, "r") as f:
                codes[path] = f.read()
        return codes

    def debug(self, folder_path, state):
        error_message = state.get("error_message", "")
        traceback = state.get("traceback", "")
        workflow = state.get("workflow_json", {})
        example_input = state.get("example_input", {})
        tool_schema = state.get("tool_schema", {})

        # Load all agent code (ignoring __init__.py).
        code_by_file, full_code = self.load_agent_code(folder_path)

        # Generate debugging suggestions using the LLM.
        target_codes = self.extract_file_paths(traceback)
        print ("target_codes 1111111111111",target_codes)
        if target_codes == {}:
            if os.path.exists(os.path.join(folder_path, "agent", state["class"], state["class"] + ".py")):
                target_codes = {os.path.join(folder_path, "agent", state["class"], state["class"] + ".py"): open(os.path.join(folder_path, "agent", state["class"], state["class"] + ".py"), "r").read()}
        try:            
            print ("target_codes 2222222222222",target_codes)
            suggestions = self.get_suggestions(traceback, error_message, workflow, target_codes, example_input, tool_schema)
            print ("suggestions 4444444444444",suggestions)
        except Exception as e:
            logging.error(f"Error getting suggestions: {e}")
            return

        # Apply each suggestion to update the code.
        for suggestion in suggestions:
            if type(suggestion) == str:
                suggestion = suggestion.replace("```json", "").replace("```", "")
                print ("suggestion 5555555555555",suggestion)
                suggestion = demjson3.decode(suggestion)
            file_path = suggestion.get("file_path")
            if not os.path.exists(file_path):
                file_path = os.path.join(folder_path, file_path)
            if not os.path.exists(file_path):
                logging.warning(f"Suggestion provided for unknown file: {file_path}")
                continue
            new_code = suggestion.get("code")
            try:
                with open(file_path, "w") as f:
                    f.write(new_code.replace("<tag>", "{{").replace("</tag>", "}}"))
            except Exception as e:
                logging.error(f"Error writing to {file_path}: {e}")
                continue

        self.clear_modules(folder_path)
        

    def load_agent_code(self, folder_path: str):
        """
        Loads all Python files under the 'agent' directory (ignoring __init__.py).

        Returns:
            code_by_file (dict): Mapping of file paths to file content.
            full_code (str): Concatenated string of all file contents with headers.
        """
        code_by_file = {}
        full_code = ""
        file_paths = glob2.glob(os.path.join(folder_path, "agent", "**", "*.py"))
        for file_path in file_paths:
            if "__init__.py" in file_path:
                continue
            try:
                with open(file_path, "r") as f:
                    content = f.read()
                full_code += f"# File_path: {file_path}\n{content}\n\n"
                code_by_file[file_path] = content
            except Exception as e:
                logging.error(f"Error reading {file_path}: {e}")
        return code_by_file, full_code

    def get_suggestions(self, traceback: str, error_message: str, workflow: dict, code: str, example_input: dict, tool_schema: dict):
        """
        Uses the LLM to generate debugging suggestions based on the error details.

        Returns:
            suggestions (list): A list of suggestions parsed from the LLM output,
                                or None if parsing fails.
        """
        print ("traceback 1111111111111",traceback)
        print ("error_message 1111111111111",error_message)    
        input_parameters = self.stm(self.workflow_instance_id).get("input_parameters","N/A")
        output_parameters = self.stm(self.workflow_instance_id).get("output_parameters","N/A")
        suggestions_response = self.simple_infer(
            traceback=traceback,
            error_message=error_message,
            workflow=workflow,
            code=code,
            input=example_input,
            tool_schema=tool_schema,
            input_parameters=input_parameters,
            output_parameters=output_parameters
        )
        print (suggestions_response)
        suggestions_content = suggestions_response["choices"][0]["message"].get("content")
        print (suggestions_content )
        if type(suggestions_content) == dict:
            print ("suggestions_content is a dict")
            print (suggestions_content)
            return [suggestions_content]
        elif type(suggestions_content) == list:
            print ("suggestions_content is a list")
            print (suggestions_content)
            return suggestions_content
        else:
            try:
                suggestions = self.output_parser.parse(suggestions_content)
                print ("suggestions 2222222222222",suggestions)
                return suggestions
            except Exception as e:
                logging.error(f"Error parsing suggestions: {e}")
                return None

    def parse(self, code: str):
        """
        Parses a string by removing markdown wrappers and loading it as JSON.
        """
        cleaned_code = code.replace("```json", "").replace("```", "")
        return json.loads(cleaned_code)

    def diff(self, code_a: str, code_b: str) -> str:
        """
        Returns a unified diff of two code snippets.
        """
        diff_generator = difflib.unified_diff(
            code_a.splitlines(), code_b.splitlines(), lineterm=''
        )
        return '\n'.join(diff_generator)

    def clear_modules(self, folder: str):
        """
        Clears loaded modules under the 'agent' directory and unregisters them.
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

    def execute_workflow(self, folder_path: str, example_inputs):
        """
        Executes the workflow using the ProgrammaticClient. This method updates the state
        with the result of the execution.

        Returns:
            A dict containing workflow execution outputs, or error details if execution fails.
        """
        
        mode = os.getenv("OMAGENT_MODE")
        os.environ["OMAGENT_MODE"] = "lite"
        state = self.stm(self.workflow_instance_id)
        if not folder_path:
            folder_path = state.get("folder_path")
        if not example_inputs:
            example_inputs = state.get("example_input")

        from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
        from omagent_core.clients.devices.programmatic.lite_client import ProgrammaticClient

        logging.init_logger("omagent", "omagent", level="INFO")

        if isinstance(example_inputs, str):
            example_inputs = json.loads(example_inputs)

        workflow_files = glob2.glob(os.path.join(folder_path, "*_workflow.json"))
        if not workflow_files:
            logging.error("No workflow JSON file found.")
            return {"outputs": None, "error": "Workflow JSON not found", "traceback": "", "status": "fail"}
        workflow_path = workflow_files[0]

        target_folder = os.path.abspath(folder_path)
        if target_folder not in sys.path:
            sys.path.insert(0, target_folder)
        os.environ["OMAGENT_MODE"] = "lite"
        try:
            registry.import_module(os.path.join(target_folder, "agent"))
        except Exception as e:
            logging.error(f"Error importing modules: {e}")
            return {"outputs": None, "error": str(e), "traceback": traceback.format_exc(), "status": "fail"}

        with open(workflow_path) as f:
            workflow_json = json.load(f)

        workflow = ConductorWorkflow(name=workflow_json["name"], lite_version=True)
        print ("workflow 5555555555555",workflow)
        workflow.load(workflow_path)
        config_path = os.path.join(os.path.dirname(workflow_path), "configs")
        self.callback.info(
            agent_id=self.workflow_instance_id,
            progress="EXECUTING",
            message="Loading workflow..."
        )
        client = ProgrammaticClient(
            processor=workflow,
            config_path=config_path,
        )
        state["example_input"] = example_inputs

        output = client.start_processor_with_input(example_inputs)
        print("Workflow execution output:", output)

        if output and "last_output" in output:
            state["error_message"] = "no error"
            state["traceback"] = "None"
            state["workflow_json"] = ""
            state["input"] = ""
            self.callback.info(
                agent_id=self.workflow_instance_id,
                progress="EXECUTE OUTPUT",
                message=output["last_output"]
            )
        else:
            self.callback.info(
                agent_id=self.workflow_instance_id,
                progress="EXECUTE OUTPUT",
                message="Finished"
            )

        if output and "error" in output:
            state["error_message"] = output["error"]
            state["traceback"] = output["traceback"]
            state["workflow_json"] = workflow_json
            state["input"] = output["input"]
            os.environ["OMAGENT_MODE"] = mode
            return {
                "outputs": None,
                "class": output.get("class"),
                "error": output["error"],
                "traceback": output["traceback"],
                "has_error": True,
                "input": output["input"],
                "status": "fail"
            }
        else:
            state["error_message"] = None
            state["traceback"] = None
            state["workflow_json"] = workflow_json
            os.environ["OMAGENT_MODE"] = mode
            return {"outputs": output, "error": None, "traceback": None, "has_error": False, "status": "success"}

