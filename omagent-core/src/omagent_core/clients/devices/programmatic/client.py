import multiprocessing
from time import sleep

from omagent_core.engine.automator.task_handler import TaskHandler
from omagent_core.engine.http.models.workflow_status import terminal_status
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.utils.build import build_from_file
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry

registry.import_module()


class ProgrammaticClient:
    def __init__(
        self,
        processor: ConductorWorkflow = None,
        config_path: str = "./config",
        workers: list = []
    ) -> None:
        self._processor = processor
        self._config_path = config_path
        self._workers = workers
        self._task_handler_processor = None
        self._task_to_domain = {}

    def start_processor(self):
        worker_config = build_from_file(self._config_path)
        self._task_handler_processor = TaskHandler(
            worker_config=worker_config, workers=self._workers
        )
        self._task_handler_processor.start_processes()
        self._processor.start_workflow_with_input(workflow_input={}, task_to_domain=self._task_to_domain)

    def start_processor_with_input(self, workflow_input: dict):
        try:
            if self._task_handler_processor is None:
                worker_config = build_from_file(self._config_path)
                self._task_handler_processor = TaskHandler(
                    worker_config=worker_config, workers=self._workers, task_to_domain=self._task_to_domain
                )
                self._task_handler_processor.start_processes()
            return self._process_workflow(self._processor, workflow_input)
        except Exception as e:
            logging.error(f"Error in start_processor_with_input: {e}")

    def start_batch_processor(self, workflow_input_list: list[dict], max_tasks: int = 10):
        results = [None] * len(workflow_input_list)
        worker_config = build_from_file(self._config_path)
        if self._task_handler_processor is None:
            self._task_handler_processor = TaskHandler(worker_config=worker_config, workers=self._workers, task_to_domain=self._task_to_domain)
            self._task_handler_processor.start_processes()
        
        result_queue = multiprocessing.Queue()
        active_processes = []
        
        for idx, workflow_input in enumerate(workflow_input_list):
            while len(active_processes) >= max_tasks:
                for p in active_processes[:]:
                    if not p.is_alive():
                        p.join()
                        active_processes.remove(p)
                        if not result_queue.empty():
                            task_idx, result = result_queue.get()
                            results[task_idx] = result
                sleep(0.1)
            
            p = multiprocessing.Process(
                target=self._process_workflow_with_queue, 
                args=(self._processor, workflow_input, result_queue, idx)
            )
            p.start()
            active_processes.append(p)

        for p in active_processes:
            p.join()
        
        while not result_queue.empty():
            task_idx, result = result_queue.get()
            results[task_idx] = result
            
        return results

    def stop_processor(self):
        if self._task_handler_processor is not None:
            self._task_handler_processor.stop_processes()

    def _process_workflow(self, workflow: ConductorWorkflow, workflow_input: dict):
        workflow_instance_id = None
        try:
            workflow_instance_id = workflow.start_workflow_with_input(
                workflow_input=workflow_input, task_to_domain=self._task_to_domain
            )
            while True:
                status = workflow.get_workflow(workflow_id=workflow_instance_id).status
                if status in terminal_status:
                    break
                sleep(1)
            return workflow.get_workflow(workflow_id=workflow_instance_id).output
        except KeyboardInterrupt:
            logging.info("\nDetected Ctrl+C, stopping workflow...")
            if workflow_instance_id is not None:
                workflow._executor.terminate(workflow_id=workflow_instance_id)
            raise  # Rethrow the exception to allow the program to exit normally

    def _process_workflow_with_queue(self, workflow: ConductorWorkflow, workflow_input: dict, 
                                   queue: multiprocessing.Queue, task_idx: int):
        try:
            result = self._process_workflow(workflow, workflow_input)
            queue.put((task_idx, result))
        except Exception as e:
            logging.error(f"Error in process workflow: {e}")
            queue.put((task_idx, None))
