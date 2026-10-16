import os
import re
import json
from pathlib import Path
from typing import List

from omagent_core.engine.worker.base import BaseWorker
from omagent_core.models.llms.base import BaseLLMBackend, BaseLLM
from omagent_core.models.llms.prompt import PromptTemplate
from omagent_core.utils.registry import registry
from pydantic import Field

CURRENT_PATH = Path(__file__).parents[0]

@registry.register_worker()
class RuleBasedVerifier(BaseLLMBackend, BaseWorker):
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_file(CURRENT_PATH.joinpath("worker_verifier_system.prompt"), role="system"),
            PromptTemplate.from_file(CURRENT_PATH.joinpath("rule_based_verifier_user.prompt"), role="user"),
        ]
    )
    llm: BaseLLM

    def _run(self, *args, **kwargs):
        state = self.stm(self.workflow_instance_id)
        generated_workers = state.get("generated_workers", {})
        workflow_json = state.get("workflow_json")
        folder = state.get("folder_path")
        results = {}

        # Loop over workers to verify input parameters and for forbidden patterns.
        for worker in generated_workers.get("workers", []):
            worker_name = worker["worker_name"]
            worker_file_path = worker["worker_file_path"]
            code = worker["code"]

            # Check for forbidden patterns.
            if "kwargs.get(" in code:
                results.setdefault(worker_name, []).append({
                    "is_correct": False,
                    "error_message": "The worker has kwargs.get. This is not allowed. Please use input parameters instead."
                })

            # Verify input parameters.
            output = self.verify_input_parameters(code, workflow_json, worker_name)
            if not output["is_correct"]:
                results.setdefault(worker_name, []).append(output)
                print("The input parameters are not correct.", worker_name, worker_file_path)
            else:
                print("The input parameters are correct.", worker_name, worker_file_path)

        # Verify import correctness.
        for worker in generated_workers.get("workers", []):
            worker_name = worker["worker_name"]
            worker_file_path = worker["worker_file_path"]
            output = self.test_import(worker["code"])
            if not output["is_correct"]:
                results.setdefault(worker_name, []).append(output)
                print("The import is not correct.", worker_name, worker_file_path)
            else:
                print("The import is correct.", worker_name, worker_file_path)

        # Verify output parameters.
        results = self.verify_output_parameters(generated_workers.get("workers", []), workflow_json, results)

        # For each worker with errors, allow user to review a proposed fix before applying it.
        for w in generated_workers.get("workers", []):
            worker_name = w["worker_name"]
            if worker_name in results:
                error_messages = " ".join([x["error_message"] for x in results[worker_name]])
                fix_suggestion = ""
                # Enter a loop for user confirmation.
                while True:
                    # Generate a candidate fix.
                    output = self.simple_infer(
                        code=w["code"],
                        workflow_json=workflow_json,
                        error_messages=error_messages,
                        fix_suggestion=fix_suggestion
                    )["choices"][0]["message"].get("content")
                    new_code = self.parser(output)
                    self.callback.info(
                        agent_id=self.workflow_instance_id,
                        progress="RuleBasedVerifier",
                        message=f"Proposed correction for {worker_name}:\n{new_code}"
                    )

                    # Ask the user for confirmation or alternative suggestion.
                    user_response = self.input.read_input(
                        workflow_instance_id=self.workflow_instance_id,
                        input_prompt=f"Do you want to apply this fix for {worker_name}? (yes/no) "
                                     f"Or provide an alternative suggestion if any:"
                    )
                    print ("user_response",user_response)
                    content = user_response['messages'][-1]['content']
                    for content_item in content:
                        if content_item['type'] == 'text':
                            user_input = content_item['data']
                    if user_input == "yes":
                        w["code"] = new_code
                        task_name = w["worker_name"]
                        code_path = os.path.join(folder, "agent", task_name, f"{task_name}.py")
                        with open(code_path, "w") as f:
                            f.write(w["code"])
                        self.callback.info(
                            agent_id=self.workflow_instance_id,
                            progress="RuleBasedVerifier",
                            message=f"The code is corrected for {worker_name}."
                        )
                        break
                    elif user_input == "no":
                        self.callback.info(
                            agent_id=self.workflow_instance_id,
                            progress="RuleBasedVerifier",
                            message=f"No fix applied for {worker_name}."
                        )
                        break
                    else:
                        # Use the user's alternative suggestion for the next iteration.
                        fix_suggestion = user_input

    def parser(self, output):
        if "```python" in output:
            output = output.split("```python")[1].split("```")[0]
        return output

    def get_returns(self, code):
        # Regex to find the dictionary inside the return statement.
        match = re.search(r'return\s*{([^}]*)}', code, re.DOTALL)
        if not match:
            return []
        dict_content = match.group(1)
        # Regex to capture all keys in the dictionary.
        keys = re.findall(r'"(\w+)"\s*:', dict_content)
        return keys

    def verify_input_parameters(self, code, workflow_json, worker_name):
        print(code)
        # Extract function parameters from the _run method.
        function_parameters = re.findall(r"def _run\(self,\s*([^)]*)\)", code)
        if function_parameters:
            function_parameters = function_parameters[0].split(",")
        # Remove any asterisk parameters and extract parameter names.
        function_parameters = [x.strip().split(":")[0] for x in function_parameters if not x.strip().startswith("*")]
        print(function_parameters)

        tasks = {}
        for task in json.loads(workflow_json)["tasks"]:
            print(task)
            if task["type"] == "SWITCH":
                for case in task["decisionCases"]:
                    case_data = task["decisionCases"][case]
                    if isinstance(case_data, list):
                        for c in case_data:
                            tasks[c["name"]] = c
                    else:
                        c = case_data
                        tasks[c["name"]] = c
            elif task["type"] == "DO_WHILE":
                for c in task["loopOver"]:
                    tasks[c["name"]] = c
            else:
                tasks[task["name"]] = task

        task = tasks.get(worker_name)
        #if not task:
        #    return {"is_correct": False, "error_message": "Task not found in workflow."}
        print ("task",task)
        if not task:
            return {"is_correct": True, "error_message": ""}
        if "inputParameters" not in task:
            return {"is_correct": True, "error_message": ""}
        if task["inputParameters"]:
            input_parameters = task["inputParameters"].keys()
            if set(input_parameters) != set(function_parameters):
                print(input_parameters, function_parameters)
                return {"is_correct": False, "error_message": "The input parameters are not correct. Input parameters should contain: " + ", ".join(input_parameters)}
            else:
                return {"is_correct": True, "error_message": ""}
        else:
            if function_parameters:
                return {"is_correct": False, "error_message": "The input parameters are not correct. Task defines empty input parameters, but function parameters have values: " + ", ".join(function_parameters)}
            else:
                return {"is_correct": True, "error_message": ""}

    def verify_output_parameters(self, workers, workflow_json, results):
        match = re.findall(r'\${(.*?)\.output\.(.*?)}', str(workflow_json))
        workers_codes = {}
        workers_names = {}
        class_input_params = {}
        for m in match:            
            class_input_params[m[0]] = m[1]
        """
        match = re.findall(r"\$\.(\w+)\['(\w+)'\]",str(workflow_json))
        for m in match:            
            class_input_params[m[0]] = m[1]
        """
        print ("class_input_params",class_input_params)

        if isinstance(workflow_json, str):
            workflow_json = json.loads(workflow_json)
        Dic = {}
        for w in workflow_json["tasks"]:
            if w["type"] == "SWITCH":
                for case in w["decisionCases"]:
                    for c in w["decisionCases"][case]:
                        Dic[c["name"]] = c["taskReferenceName"]
                        workers_names[c["taskReferenceName"]] = c["name"]
            elif w["type"] == "DO_WHILE":
                for c in w["loopOver"]:
                    Dic[c["name"]] = c["taskReferenceName"]
                    workers_names[c["taskReferenceName"]] = c["name"]
            else:
                Dic[w["name"]] = w["taskReferenceName"]
                workers_names[w["taskReferenceName"]] = w["name"]

        for w in workers:
            try:
                workers_codes[Dic[w["worker_name"]]] = w["code"]
            except Exception:
                pass

        for ref_name in class_input_params:                
            output_param = class_input_params[ref_name]
            print ("output params in workflow",output_param)
            out_return = self.get_returns(workers_codes[ref_name])
            print ("output params in code",out_return)
            if set(output_param) == set(out_return):
                continue
            else:
                if workers_names.get(ref_name) not in results:
                    results[workers_names.get(ref_name)] = []
                results[workers_names.get(ref_name)].append({"is_correct": False, "error_message": "The output parameter is not in the return statement."})
        print(results)
        return results

    def test_import(self, code):
        import_code_only = []
        for line in code.split("\n"):
            if "@registry.register_worker()" in line:
                break
            import_code_only.append(line)
        try:
            exec("\n".join(import_code_only))
        except ImportError as e:
            return {"is_correct": False, "error_message": str(e)}
        return {"is_correct": True, "error_message": ""}
