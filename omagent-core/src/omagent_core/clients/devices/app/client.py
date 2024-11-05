from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.utils.compile import compile
from omagent_core.engine.automator.task_handler import TaskHandler
import yaml
from omagent_core.utils.container import container

container.register_component(
    component="RedisStreamHandler",
    key="redis_stream_handler_2",
    component_category="handler",
)


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

        container.register_component("RedisStreamHandler")

    def compile(self):
        compile(self._interactor, self._config_path + "/interactor")
        if self._processor:
            compile(self._processor, self._config_path + "/processor")

    def start_interactor(self):
        worker_config = yaml.load(
            open(self._config_path + "/interactor/worker.yaml", "r"),
            Loader=yaml.FullLoader,
        )
        self._task_handler_interactor = TaskHandler(worker_config=worker_config)
        self._task_handler_interactor.start_processes()

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

