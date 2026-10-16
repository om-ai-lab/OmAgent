from pathlib import Path
from typing import List

from omagent_core.advanced_components.workflow.dnc.schemas.dnc_structure import \
    TaskTree
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
import os

CURRENT_PATH = root_path = Path(__file__).parents[0]

ROOT_PATH = Path(__file__).parents[1]

@registry.register_worker()
class WorkerManager(BaseLLMBackend, BaseWorker):
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_file(CURRENT_PATH.joinpath("worker_system.prompt"), role="system"),
            PromptTemplate.from_file(CURRENT_PATH.joinpath("worker_user.prompt"), role="user")
        ]
    )
    llm: BaseLLM
    def _run(self, *args, **kwargs):    
        print ("CURRENT_PATH",CURRENT_PATH)
        print ("ROOT_PATH",ROOT_PATH)  
        
        workflow_json = json.loads(self.stm(self.workflow_instance_id)["workflow_json"])
        tool_schema =self.stm(self.workflow_instance_id)["tool_schema"]
        folder_path = self.stm(self.workflow_instance_id)["folder_path"]
        workflow_file_name = f"{workflow_json['name']}_workflow.json"
        workflow_path = os.path.join(folder_path, workflow_file_name)
        os.makedirs(folder_path, exist_ok=True)
        with open(workflow_path, 'w') as f:
            json.dump(workflow_json, f, indent=4)

        workflow_path = os.path.join(folder_path, workflow_file_name)
        print ("workflow_path",workflow_path)
        workflow_name = workflow_json["name"]
        workers_section = workflow_json["description"]
        Dic_worker = {}
        for w in workflow_json["tasks"]:
            if w["type"] == "SWITCH":
                for case in w["decisionCases"]:
                    case_data = w["decisionCases"][case]
                    if isinstance(case_data, list):
                        for c in case_data:
                            Dic_worker[c["name"]] = c
                    else:
                        Dic_worker[case_data["name"]] = case_data
            elif w["type"] == "DO_WHILE":
                for c in w["loopOver"]:
                    Dic_worker[c["name"]] = c
            else:
                Dic_worker[w["name"]] = w

        generated_workers = {"workers": [], "name":workflow_name, "workflow_path": workflow_path}
        codes = []
        total_input_parameters = {}
        total_output_parameters = {}
        for worker in workers_section:   
            input_parameters, input_parameters_str = self.get_input_parameters(worker["Worker_Name"], workflow_json)
            output_parameters, output_parameters_str = self.get_output_parameters(worker["Worker_Name"], workflow_json)
        
            total_input_parameters[worker["Worker_Name"]] = input_parameters_str        
            total_output_parameters[worker["Worker_Name"]] = output_parameters_str
            self.callback.info(self.workflow_instance_id, progress=worker["Worker_Name"]+" generating...", message= worker["Role"]+"\n"+json.dumps(Dic_worker[worker["Worker_Name"]], indent=2)+"\n"+input_parameters+"\n    ....\n    "+output_parameters)
            code = self.simple_infer(input_parameters=input_parameters_str, output_parameters=output_parameters_str, tool_schema=tool_schema,workflow_name=worker["Worker_Name"], worker_description=worker["Role"], workflow=workflow_json, previous_codes="\n".join(codes))["choices"][0]["message"].get("content")
            code = self.parse_code(code)
            codes.append("# worker name: "+worker["Worker_Name"]+"\n"+code)
            worker_dir = os.path.join(folder_path, 'agent', worker["Worker_Name"])
            os.makedirs(worker_dir, exist_ok=True)
            worker_file_path = os.path.join(worker_dir, f"{worker['Worker_Name']}.py")
            with open(worker_file_path, 'w') as f:
                f.write(code)
            print ("worker_file_path",worker_file_path)
            print ("code",code)
            self.callback.info(self.workflow_instance_id, progress=worker_file_path.split("/")[-1], message=code)
            generated_workers["workers"].append({"worker_name": worker['Worker_Name'], "worker_file_path": worker_file_path, "code": code })
        
        self.stm(self.workflow_instance_id)["input_parameters"] = total_input_parameters
        self.stm(self.workflow_instance_id)["output_parameters"] = total_output_parameters

        agents_dir = os.path.join(folder_path, "agent")
        for root, dirs, files in os.walk(agents_dir):
            for d in dirs:
                sub_folder_path = os.path.join(root, d)
                init_file = os.path.join(sub_folder_path, "__init__.py")
                if not os.path.isfile(init_file):
                    with open(init_file, "w") as f:
                        f.write("# Auto-generated __init__.py for agents sub-package\n")
                    print(f"Ensured sub-package: {init_file}")
        self.callback.info(self.workflow_instance_id, progress="WORKER MANAGER", message="********ALL WORKERS GENERATED********")
        self.stm(self.workflow_instance_id)["generated_workers"] = generated_workers
    
    def get_input_parameters(self, worker_name, workflow_json):
        tasks = {}
        for task in workflow_json["tasks"]:        
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
        print (worker_name, task)
        if not task:
            return "def _run(self, *args, **kwargs):", "No input parameters. you need to set def _run(self, *args, **kwargs): without any additional parameters"
        if "inputParameters" not in task:
            return "def _run(self, *args, **kwargs):", "No input parameters. you need to set def _run(self, *args, **kwargs): without any additional parameters"
        input_parameters = list(task["inputParameters"].keys())

        if len(input_parameters) == 0:
            return "def _run(self, *args, **kwargs):", "No input parameters. you need to set def _run(self, *args, **kwargs): without any additional parameters"
        else:
            return "def _run(self, "+", ".join(input_parameters)+", *args, **kwargs):", "The input parameters are: "+", ".join(input_parameters)+". You need to set def _run(self, "+", ".join(input_parameters)+", *args, **kwargs):"

    def get_output_parameters(self, worker_name, workflow_json):
        match = re.findall(r'\${(.*?)\.output\.(.*?)}', str(workflow_json))
        class_input_params = {}
        for m in match:            
            if not m[0] in class_input_params:
                class_input_params[m[0]] = []
            class_input_params[m[0]].append(m[1])
            
                
        match = re.findall(r"\$\.(\w+)\['(\w+)'\]", str(workflow_json))
        for m in match:         
            if not m[0] in class_input_params:
                class_input_params[m[0]] = []
            class_input_params[m[0]].append(m[1])
        
        for w in workflow_json["tasks"]:
            if w["name"] == worker_name:
                if w["taskReferenceName"] in class_input_params:
                    return_keys = class_input_params[w["taskReferenceName"]]
                    keys = {}
                    for key in return_keys:
                        keys[key] = "..."
                    return "return "+", ".join(class_input_params[w["taskReferenceName"]])+",", "the output return should be "+", ".join(class_input_params[w["taskReferenceName"]])+"\nreturn should be a dictionary with the following keys: "+json.dumps(keys)
        return "return None", "No output parameters. no return any value"
        

    def parse_code(self, code: str):
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0]
        code = code.replace("<tag>", "{{")
        code = code.replace("</tag>", "}}")
        
        return code


    