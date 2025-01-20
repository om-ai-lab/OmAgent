
from omagent_core.utils.container import container
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.utils.build import build_from_file
from omagent_core.utils.registry import registry
from omagent_core.clients.devices.cli.callback import DefaultCallback
from colorama import Fore
from omagent_core.utils.container import container
from omagent_core.utils.logger import logging
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.registry import registry
        
registry.import_module()

container.register_callback(callback=DefaultCallback)

class ProgrammaticClient:
    def __init__(
        self,
        processor: ConductorWorkflow = None,
        config_path: str = "./config",
        workers: list = [],
        input_prompt: str = None
    ) -> None:
        self._interactor = processor
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

    
    def start_batch_processor(self, workflow_input_list: list, max_tasks=1):
        results = []
        for workflow_input in workflow_input_list:
            print ("workflow_input:",workflow_input)
            result = self._interactor.start_workflow_with_input(workflow_input=workflow_input, workers=self.workers)
            print ("result:",result)
            results.append(result)
        return results
    
    def stop_processor(self):
        print ("stop_processor")