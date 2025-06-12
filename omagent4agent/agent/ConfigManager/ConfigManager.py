from pathlib import Path

from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.general import read_image
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry
import os
import json
import shutil
CURRENT_PATH = Path(__file__).parents[0]


@registry.register_worker()
class ConfigManager(BaseWorker):
    def _run(self, *args, **kwargs):
        generated_workers = self.stm(self.workflow_instance_id)["generated_workers"]
        folder_path = self.stm(self.workflow_instance_id)["folder_path"]
        name = generated_workers["name"]
        source = os.path.join("configs","llms")
        target = os.path.join(folder_path, "configs","llms" )
        if not os.path.exists(target):
            shutil.copytree(source, target)
        else:
            print ("llms folder already exists")
        source = os.path.join("configs","tools")
        target = os.path.join(folder_path, "configs","tools" )
        if not os.path.exists(target):
            shutil.copytree(source, target) 
        else:
            print ("tools folder already exists")

        for worker in generated_workers["workers"]:
            worker_folder = os.path.join(folder_path, "configs", "workers")
            if not os.path.exists(worker_folder):
                os.makedirs(worker_folder)
            config_path = os.path.join(worker_folder, worker["worker_name"].lower() + ".yaml")
            if not os.path.exists(config_path):
                with open(config_path, 'w') as f:
                    f.write("name: "+worker["worker_name"]+"\n")
                    if "llm:" in worker["code"] and "image" in worker["code"]:
                        f.write("llm: ${sub|vlm}\n")
                    if "llm:" in worker["code"] and not "image" in worker["code"]:
                        f.write("llm: ${sub|llm_text}\n")
                    if "tool_manager:" in worker["code"]:
                        f.write("tool_manager: ${sub|all_tools}\n") 
            else:
                print (f"worker config file {config_path} already exists")
