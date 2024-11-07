import os
from omagent_core.engine.http.models.task_result_status import TaskResultStatus
from omagent_core.engine.http.models.workflow_status import terminal_status
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.utils.compile import compile
from omagent_core.engine.automator.task_handler import TaskHandler
import yaml
from time import sleep
import json
from colorama import Fore, Style
from omagent_core.utils.container import container
from omagent_core.utils.registry import registry
from omagent_core.utils.logger import logging


class DefaultClient:
    def __init__(
        self,
        interactor: ConductorWorkflow,
        processor: ConductorWorkflow = None,
        config_path: str = "./config",
    ) -> None:
        self._interactor = interactor
        self._processor = processor
        self._config_path = config_path

    def _is_redis_stream_listener_running(self, workflow):
        try:
            for task in workflow.tasks:
                # print(task.task_def_name, task.status)
                if task.task_def_name == 'RedisStreamListener' and task.status in [TaskResultStatus.IN_PROGRESS]:
                    return True
            return False
        except Exception as e:
            logging.error(f"Error while checking RedisStreamListener status: {e}")
            return False

    def compile(self):
        output_path = self._config_path + "/interactor"
        os.makedirs(output_path, exist_ok=True)
        compile(self._interactor, output_path)
        if self._processor:
            compile(self._processor, self._config_path + "/processor")

    def start_interactor(self):
        worker_config = yaml.load(
            open(self._config_path + "/interactor/worker.yaml", "r"),
            Loader=yaml.FullLoader,
        )
        self._task_handler_interactor = TaskHandler(worker_config=worker_config)
        self._task_handler_interactor.start_processes()
        workflow_execution_id = self._interactor.start_workflow_with_input(workflow_input={})

        while True:
            workflow = self._interactor.get_workflow(workflow_id=workflow_execution_id)
            workflow_status = workflow.status
            if workflow_status in terminal_status:
                break
            if self._is_redis_stream_listener_running(workflow):
                # print("RedisStreamListener is running.")
                user_input = input((Fore.BLUE + "Please enter:\n" + Style.RESET_ALL))
                data = {
                    "agent_id": workflow_execution_id,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "data": user_input
                                }
                            ]
                        }
                    ],
                    "kwargs": {}    
                }
                container.get_component("RedisStreamHandler").redis_stream_client._client.xadd(f"{workflow_execution_id}_input", {"payload":json.dumps(data, ensure_ascii=False) })
                sleep(5)
            else:
                # print("RedisStreamListener is not running.")
                sleep(1)
        self.stop_interactor()

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

