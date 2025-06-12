from pathlib import Path

from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.general import read_image
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry
import os
import glob2
import json
CURRENT_PATH = Path(__file__).parents[0]

ROOT_PATH = Path(__file__).parents[2]

@registry.register_worker()
class TestInput(BaseWorker):

    def _run(self, *args, **kwargs):
        # Read user input through configured input interface
        input_keys = {}
        folders = {}
        for i, agent in enumerate(glob2.glob(os.path.join(ROOT_PATH, "generated_agents", "**","*.json"))):
            with open(agent, "r") as f:
                try:
                    agent_json = json.load(f)   
                except:
                    continue
                
                keys = agent_json["tasks"][0]["inputParameters"].keys()
                _id = agent.split("/")[-2]       
                folders[str(i+1)] = _id                      
                self.callback.info(agent_id=self.workflow_instance_id, progress=f"", message=f"{i+1}. {agent_json['name']}, folders: generated_agents/{_id}")
                input_keys[_id] = keys

        while True:
            input = self.input.read_input(workflow_instance_id=self.workflow_instance_id, input_prompt=f"Please select the number [1-{len(folders)}] to test the agent.")
            content = input['messages'][-1]['content']
            print ("content",content)
            folder_path = None
            for content_item in content:
                if content_item['type'] == 'text' and content_item['data'] in folders:
                    folder_path = folders[content_item['data']]
                    break
            if folder_path:
                break
            else:
                self.callback.info(agent_id=self.workflow_instance_id, progress="", message="Invalid selection. Please select a valid number.")

        print("folder_path", folder_path)

        example_input = {}
        for key in input_keys[folder_path]:            
            input = self.input.read_input(workflow_instance_id=self.workflow_instance_id, input_prompt=key)
            content = input['messages'][-1]['content']
            for content_item in content:                
                example_input[key] = content_item['data']

        print ("example_input",example_input)
        self.stm(self.workflow_instance_id)["folder_path"] = "generated_agents/"+folder_path
        self.stm(self.workflow_instance_id)["example_input"] = example_input      
        return {"folder_path": "generated_agents/"+folder_path, "example_inputs": example_input}
