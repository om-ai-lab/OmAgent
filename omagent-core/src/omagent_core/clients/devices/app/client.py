from time import sleep
from omagent_core.utils.container import container
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.utils.build import build_from_file
from omagent_core.engine.automator.task_handler import TaskHandler
from omagent_core.clients.devices.app.callback import AppCallback
from omagent_core.clients.devices.app.input import AppInput
import yaml
from omagent_core.utils.container import container
from omagent_core.utils.registry import registry
from omagent_core.services.connectors.redis import RedisConnector

registry.import_module()

container.register_connector(name='redis_stream_client', connector=RedisConnector)
# container.register_stm(stm='RedisSTM')
container.register_callback(callback=AppCallback)
container.register_input(input=AppInput)


class AppClient:
    def __init__(
        self,
        interactor: ConductorWorkflow = None,
        processor: ConductorWorkflow = None,
        config_path: str = "./config",
        workers: list = [],
    ) -> None:
        self._interactor = interactor
        self._processor = processor
        self._config_path = config_path
        self._workers = workers
        
    def start_interactor(self):
        worker_config = build_from_file(self._config_path)
        self._task_handler_interactor = TaskHandler(worker_config=worker_config, workers=self._workers)
        self._task_handler_interactor.start_processes()
        # workflow_execution_id = self._interactor.start_workflow_with_input(workflow_input={})

    def stop_interactor(self):
        self._task_handler_interactor.stop_processes()
        
    def start_processor(self):
        worker_config = build_from_file(self._config_path)
        self._task_handler_processor = TaskHandler(worker_config=worker_config, workers=self._workers)
        self._task_handler_processor.start_processes()
        workflow_instance_id = self._processor.start_workflow_with_input(workflow_input={})
        while True:
            status = self._processor.get_workflow(workflow_id=workflow_instance_id).status
            if status == 'COMPLETED':
                workflow_instance_id = self._processor.start_workflow_with_input(workflow_input={})

            sleep(1)

    def stop_processor(self):
        self._task_handler_processor.stop_processes()

