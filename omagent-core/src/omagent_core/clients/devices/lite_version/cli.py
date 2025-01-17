
from omagent_core.utils.container import container
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.utils.build import build_from_file
from omagent_core.utils.registry import registry
from omagent_core.clients.devices.cli.callback import DefaultCallback
from colorama import Fore
from omagent_core.utils.container import container
from omagent_core.utils.logger import logging

registry.import_module()

container.register_callback(callback=DefaultCallback)

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

    def start_interactor(self):
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
    
        