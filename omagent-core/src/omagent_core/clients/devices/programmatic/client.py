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
        interactor: ConductorWorkflow = None,
        processor: ConductorWorkflow = None,
        config_path: str = "./config",
        workers: list = [],
        input_prompt: str = None,
    ) -> None:
        self._interactor = interactor
        self._processor = processor
        self._config_path = config_path
        self._workers = workers
        self._input_prompt = input_prompt
        self._task_handler_processor = None

    def start_interactor(self):
        pass

    def stop_interactor(self):
        pass

    def start_processor(self):
        worker_config = build_from_file(self._config_path)
        self._task_handler_processor = TaskHandler(
            worker_config=worker_config, workers=self._workers
        )
        self._task_handler_processor.start_processes()
        self._processor.start_workflow_with_input(workflow_input={})

    def start_processor_with_input(self, workflow_input: dict):
        try:
            if self._task_handler_processor is None:
                worker_config = build_from_file(self._config_path)
                self._task_handler_processor = TaskHandler(
                    worker_config=worker_config, workers=self._workers
                )
                self._task_handler_processor.start_processes()
            self._process_workflow(self._processor, workflow_input)
        except Exception as e:
            logging.error(f"Error in start_processor_with_input: {e}")

    def start_batch_processor(self, workflow_input_list: list[dict]):
        worker_config = build_from_file(self._config_path)
        self._task_handler_processor = TaskHandler(
            worker_config=worker_config, workers=self._workers
        )
        self._task_handler_processor.start_processes()
        processes = []
        for workflow_input in workflow_input_list:
            p = multiprocessing.Process(
                target=self._process_workflow,
                args=(
                    self._processor,
                    workflow_input,
                ),
            )
            p.start()
            processes.append(p)
        for p in processes:
            p.join()

    def stop_processor(self):
        if self._task_handler_processor is not None:
            self._task_handler_processor.stop_processes()

    def _process_workflow(self, workflow: ConductorWorkflow, workflow_input: dict):
        workflow_instance_id = None
        try:
            workflow_instance_id = workflow.start_workflow_with_input(
                workflow_input=workflow_input
            )
            while True:
                status = workflow.get_workflow(workflow_id=workflow_instance_id).status
                if status in terminal_status:
                    break
                sleep(1)
        except KeyboardInterrupt:
            logging.info("\nDetected Ctrl+C, stopping workflow...")
            if workflow_instance_id is not None:
                workflow._executor.terminate(workflow_id=workflow_instance_id)
            raise  # Rethrow the exception to allow the program to exit normally
