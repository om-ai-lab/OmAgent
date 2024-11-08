import os
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.utils.build import build_from_file
from omagent_core.utils.compile import compile
from omagent_core.engine.automator.task_handler import TaskHandler
import yaml
from omagent_core.utils.container import container
from omagent_core.utils.registry import registry


class AppClient:
    def __init__(
        self,
        interactor: ConductorWorkflow,
        processor: ConductorWorkflow = None,
        config_path: str = "./config",
    ) -> None:
        self._interactor = interactor
        self._processor = processor
        self._config_path = config_path

    def start_interactor(self):
        worker_config = build_from_file(self._config_path + "/step1_simpleVQA/configs")
        self._task_handler_interactor = TaskHandler(worker_config=worker_config)
        self._task_handler_interactor.start_processes()
        workflow_execution_id = self._interactor.start_workflow_with_input(workflow_input={})

    def stop_interactor(self):
        self._task_handler_interactor.stop_processes()
        
    def start_processor(self):
        worker_config = yaml.load(
            open(self._config_path + "/processor/worker.yaml", "r"),
            Loader=yaml.FullLoader,
        )
        self._task_handler_processor = TaskHandler(worker_config=worker_config)
        self._task_handler_processor.start_processes()

    def stop_processor(self):
        self._task_handler_processor.stop_processes()

