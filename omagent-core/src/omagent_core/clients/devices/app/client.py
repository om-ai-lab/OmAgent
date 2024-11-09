from omagent_core.utils.container import container
from omagent_core.engine.configuration.configuration import Configuration
container.register_connector(name='conductor_config', connector=Configuration)

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
container.register_stm(stm='RedisSTM')
container.register_callback(callback=AppCallback)
container.register_input(input=AppInput)


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
        worker_config = build_from_file(self._config_path)
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

