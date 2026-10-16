
from pathlib import Path

from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.general import read_image
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry
import glob
import os
import sys
import json
import traceback

CURRENT_PATH = Path(__file__).parents[0]


@registry.register_worker()
class ExecuteAgent(BaseWorker):
    def _run(self, folder_path, example_inputs,*args, **kwargs):
            mode = os.getenv("OMAGENT_MODE")            
            os.environ["OMAGENT_MODE"] = "lite"  
            if folder_path == None:
                folder_path = self.stm(self.workflow_instance_id)["folder_path"]
            if example_inputs == None:
                example_inputs = self.stm(self.workflow_instance_id)["example_input"]

            from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
            from omagent_core.clients.devices.programmatic.lite_client import ProgrammaticClient
            logging.init_logger("omagent", "omagent", level="INFO")
            
            if type(example_inputs) == str:
                example_inputs = json.loads(example_inputs)

            workflow_path = glob.glob(os.path.join(folder_path, "*_workflow.json"))[0]
            
            target_folder = os.path.abspath(folder_path)
            if target_folder not in sys.path:
                sys.path.insert(0, target_folder)
            print(f"Added {target_folder} to sys.path")
            os.environ["OMAGENT_MODE"] = "lite"  
            #self.clear_modules(folder_path)
            with open(workflow_path) as f:
                workflow_json = json.load(f)

            try:
                registry.import_module(os.path.join(target_folder, "agent"))
            except Exception as e:
                print ("error ",e)
                print ("traceback ",traceback.format_exc())
                self.stm(self.workflow_instance_id)["error_message"] = str(e)
                self.stm(self.workflow_instance_id)["traceback"] = str(traceback.format_exc())
                self.stm(self.workflow_instance_id)["workflow_json"] = workflow_json
                self.stm(self.workflow_instance_id)["input"] = example_inputs
                self.callback.info(agent_id=self.workflow_instance_id, progress="EXECUTE OUTPUT", message="Finished")
                return {"outputs": None, "class": None, "error": str(e), "traceback": str(traceback.format_exc()), "has_error": True, "input":None}


            workflow = ConductorWorkflow(name=workflow_json["name"], lite_version=True)
            workflow.load(workflow_path)
            print ("/".join(workflow_path.split("/")[:-1])+"/configs")
            self.callback.info(agent_id=self.workflow_instance_id, progress="EXECUTING", message="Loading workflow...")
            print ("before")
            try:
                client = ProgrammaticClient(
                    processor=workflow,
                    config_path="/".join(workflow_path.split("/")[:-1])+"/configs",
                )
            except Exception as e:
                print ("error",e)
                self.stm(self.workflow_instance_id)["error_message"] = str(e)
                self.stm(self.workflow_instance_id)["traceback"] = str(traceback.format_exc())
                self.stm(self.workflow_instance_id)["workflow_json"] = workflow_json
                self.stm(self.workflow_instance_id)["input"] = example_inputs
                self.callback.info(agent_id=self.workflow_instance_id, progress="EXECUTE OUTPUT", message="Finished")
                return {"outputs": None, "class": None, "error": str(e), "traceback": str(traceback.format_exc()), "has_error": True, "input":None}

            self.stm(self.workflow_instance_id)["example_input"] = example_inputs
            output = client.start_processor_with_input(example_inputs)
            print ("output",output)
            
            if output and "last_output" in output:
                self.stm(self.workflow_instance_id)["error_message"] = "no error"
                self.stm(self.workflow_instance_id)["traceback"] = "None"
                self.stm(self.workflow_instance_id)["workflow_json"] = "" 
                self.stm(self.workflow_instance_id)["input"] = ""
                self.callback.info(agent_id=self.workflow_instance_id, progress="EXECUTE OUTPUT", message=output["last_output"])
            else:
                self.callback.info(agent_id=self.workflow_instance_id, progress="EXECUTE OUTPUT", message="Finished")
            
            if output and "error" in output:
                self.stm(self.workflow_instance_id)["error_message"] = output["error"]
                self.stm(self.workflow_instance_id)["traceback"] = output["traceback"]
                self.stm(self.workflow_instance_id)["workflow_json"] = workflow_json 
                self.stm(self.workflow_instance_id)["input"] = output["input"]
                os.environ["OMAGENT_MODE"] = mode
                return {"outputs": None, "class": output["class"], "error": output["error"], "traceback": output["traceback"], "has_error": True, "input":output["input"]}
            else:
                self.stm(self.workflow_instance_id)["error_message"] = None
                self.stm(self.workflow_instance_id)["traceback"] = None
                self.stm(self.workflow_instance_id)["workflow_json"] = workflow_json            
                os.environ["OMAGENT_MODE"] = mode
                return {"outputs": output, "error": None, "traceback": None, "has_error": False}
        
    def clear_modules(self, folder: str):        
        agents_dir = os.path.join(folder, "agent")
        for module_name in list(sys.modules.keys()):
            module = sys.modules[module_name]
            if module_name.startswith("agent") or (hasattr(module, '__file__') and module.__file__ and agents_dir in module.__file__):
                del sys.modules[module_name]
                # Extract the class name from the module name
                class_name = module_name.split('.')[-1]
                try:
                    registry.unregister("worker", class_name)
                except KeyError:
                    print(f"Module {class_name} not found in registry, skipping unregistration.")
