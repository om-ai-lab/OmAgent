from pathlib import Path
from omagent_core.services.connectors.redis import RedisConnector
from omagent_core.utils.container import container
container.register_connector(name='redis_stream_client', connector=RedisConnector)
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.utils.build import build_from_file
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.utils.registry import registry
from omagent_core.clients.devices.app.input import AppInput
from omagent_core.clients.devices.cli.callback import DefaultCallback
from colorama import Fore, Style
from omagent_core.utils.container import container
from omagent_core.utils.logger import logging

registry.import_module()

# container.register_stm(stm='RedisSTM')
container.register_callback(callback=DefaultCallback)
container.register_input(input=AppInput)

class DefaultClient:
    def __init__(
        self,
        interactor: ConductorWorkflow = None,
        processor: ConductorWorkflow = None,
        config_path: str = "./config",
        workers: list = [],
        input_prompt: str = None
    ) -> None:
        self._interactor = interactor
        self._processor = processor
        self._config_path = config_path
        self._workers = workers
        self._input_prompt = input_prompt        
        worker_config = build_from_file(self._config_path)
        self.initialization(workers, worker_config)

    def initialization(self, workers, worker_config):        
        self.workers = {}
        for worker in workers:
            self.workers[type(worker).__name__] = worker            
        
        for config in worker_config:
            worker_cls = registry.get_worker(config['name'])        
            self.workers[config['name']] = worker_cls(**config)                    

    def start_processor_with_input(self, workflow_input: dict):                          
        self._interactor.start_workflow_with_input(workflow_input=workflow_input, workers=self.workers)

    def start_interaction(self):
        """
        This function takes keyboard input from the user and runs the workflow 
        using the `start_workflow_with_input` method.
        """
        while True:
            try:
                # Prompt the user for input
                user_input = input(f"\n{Fore.GREEN}Enter your query (or type 'exit' to quit): ")

                # Exit the interaction loop if the user types 'exit'
                if user_input.lower() == "exit":
                    print("Exiting the interaction. Goodbye!")
                    break

                # Prepare the workflow input as a dictionary
                workflow_input = {"query": user_input}

                # Pass the input to start_workflow_with_input
                self.start_processor_with_input(workflow_input)
            
            except KeyboardInterrupt:
                print("\nInteraction interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"An error occurred: {e}")
    
        
    def is_file(self, path: str) -> bool:
        """
        Determine if the given string is a file

        :param path: File path string
        :return: Returns True if it is a file, otherwise returns False
        """
        import os
        try:
            return os.path.isfile(path)
        except Exception as e:
            logging.error(f"Error checking if path is a file: {e}")
            return False
        
    def is_url(self, url: str) -> bool:
        """
        Determine if the given string is a URL
        """
        import re
        return bool(re.match(r'^https?://', url))
    
    def first_input(self, workflow_instance_id: str, input_prompt = ""):
        contents = []
        while True:
            print(f"{Fore.GREEN}{input_prompt}(Waiting for input. Your input can only be text or image path each time, you can press Enter once to input multiple times. Press Enter twice to finish the entire input.):{Style.RESET_ALL}")
            user_input_lines = []
            while True:
                line = input(f"{Fore.GREEN}>>>{Style.RESET_ALL}")
                if line == "":
                    break
                user_input_lines.append(line)
            logging.info(f"User input lines: {user_input_lines}")
            
        
            for user_input in user_input_lines:
                if self.is_url(user_input) or self.is_file(user_input):
                    contents.append({
                        "type": "image_url",
                        "data": user_input
                    })
                else:
                    contents.append({
                        "type": "text",
                        "data": user_input
                    })
            if len(contents) > 0:
                break
        result = {
            "agent_id": workflow_instance_id,
            "messages": [
                {
                    "role": "user",
                    "content": contents
                }
            ],
            "kwargs": {}    
        }
        return result

