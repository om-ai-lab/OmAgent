from pathlib import Path

from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.general import read_image
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry
import uuid
import json

CURRENT_PATH = Path(__file__).parents[0]


@registry.register_worker()
class InputInterface(BaseWorker):
    """Input interface processor that handles user instructions and image input.

    This processor:
    1. Reads user input containing question and image via input interface
    2. Extracts text instruction and image path from the input
    3. Loads and caches the image in workflow storage
    4. Returns the user instruction for next steps
    """

    def _run(self, *args, **kwargs):
        # Read user input through configured input interface

        #self.callback.info_image(self.workflow_instance_id, progress="AGENT ID", image="https://www.crystalmountainresort.com/-/media/crystal/images/2425-images/hero-images/lift-tickets-hero.jpg")
        #self.callback.show_image(self.workflow_instance_id, progress="AGENT ID", image="https://www.crystalmountainresort.com/-/media/crystal/images/2425-images/hero-images/lift-tickets-hero.jpg")
        input = self.input.read_input(workflow_instance_id=self.workflow_instance_id, input_prompt="Describe the agent you want to create.")
        content = input['messages'][-1]['content']
        for content_item in content:
            if content_item['type'] == 'text':
                initial_description = content_item['data']

        print ("initial_description",initial_description)
        
   
        folder_path = "generated_agents/"+str(uuid.uuid4())
        self.callback.info(self.workflow_instance_id, progress="AGENT ID", message=folder_path.split("/")[-1])
        is_valid_json = False
        while not is_valid_json:
            input = self.input.read_input(workflow_instance_id=self.workflow_instance_id, input_prompt="Give me an example input for the agent.(e.g., {'image_path': '/path/to/image.jpg'})")
            content = input['messages'][-1]['content']
            for content_item in content:
                if content_item['type'] == 'text':
                    example_input = content_item['data']
                    try:
                        example_input = self.clean_json(example_input)
                        print ("example_input",example_input)
                        json.loads(example_input)
                        is_valid_json = True
                        break
                    except json.JSONDecodeError:
                        print("Invalid JSON format. Please input a valid JSON.")
                

        print ("example_input",example_input)
        self.stm(self.workflow_instance_id)["initial_description"] = initial_description
        self.stm(self.workflow_instance_id)["folder_path"] = folder_path
        self.stm(self.workflow_instance_id)["example_input"] = example_input      
        print (initial_description)  
        return {"initial_description": initial_description}

    def clean_json(self, json_str):
        json_str = json_str.replace('”', '"').replace('”', '"')
        return json_str.strip()
