import asyncio
import dataclasses
import inspect
import logging
import socket
import time
import traceback
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Any, Callable, Optional, Union

from omagent_core.base import BotBase
from omagent_core.engine.automator import utils
from omagent_core.engine.automator.utils import convert_from_dict_or_list
from omagent_core.engine.configuration.configuration import Configuration
from omagent_core.engine.http.api_client import ApiClient
from omagent_core.engine.http.models import TaskExecLog
from omagent_core.engine.http.models.task import Task
from omagent_core.engine.http.models.task_result import TaskResult
from omagent_core.engine.http.models.task_result_status import TaskResultStatus
from omagent_core.engine.worker.exception import NonRetryableException
from pydantic import Field
from typing_extensions import Self

ExecuteTaskFunction = Callable[[Union[Task, object]], Union[TaskResult, object]]

logger = logging.getLogger(Configuration.get_logging_formatted_name(__name__))


def is_callable_input_parameter_a_task(
    callable: ExecuteTaskFunction, object_type: Any
) -> bool:
    parameters = inspect.signature(callable).parameters
    if len(parameters) != 1:
        return False
    parameter = parameters[list(parameters.keys())[0]]
    return (
        parameter.annotation == object_type
        or parameter.annotation == parameter.empty
        or parameter.annotation == object
    )


def is_callable_return_value_of_type(
    callable: ExecuteTaskFunction, object_type: Any
) -> bool:
    return_annotation = inspect.signature(callable).return_annotation
    return return_annotation == object_type


class BaseWorker(BotBase, ABC):
    poll_interval: float = Field(
        default=100, description="Worker poll interval in millisecond"
    )
    domain: Optional[str] = Field(default=None, description="The domain of workflow")
    concurrency: int = Field(default=5, description="The concurrency of worker")
    _task_type: Optional[str] = None

    def model_post_init(self, __context: Any) -> None:
        self.task_definition_name = self.id or self.name
        self.next_task_index = 0
        self._task_definition_name_cache = None

        self.api_client = ApiClient()
        self.worker_id = deepcopy(self.get_identity())

        self._workflow_instance_id = None
        self._task_type = None
        for _, attr_value in self.__dict__.items():
            if isinstance(attr_value, BotBase):
                attr_value._parent = self

    @property
    def task_type(self) -> str:
        return self._task_type

    @task_type.setter
    def task_type(self, value: str):
        self._task_type = value

    @property
    def workflow_instance_id(self) -> Optional[str]:
        return self._workflow_instance_id

    @workflow_instance_id.setter
    def workflow_instance_id(self, value: Optional[str]):
        self._workflow_instance_id = value

    @abstractmethod
    def _run(self, *args, **kwargs) -> Any:
        """Run the Node."""

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        print ("__call__")
        return self._run(*args, **kwds)

    def execute(self, task: Task) -> TaskResult:
        task_input = {}
        task_output = None
        task_result: TaskResult = self.get_task_result_from_task(task)
        if task.conversation_info:
            self.workflow_instance_id = '|'.join([
                task.workflow_instance_id,
                task.conversation_info.get('agentId', ''),
                task.conversation_info.get('conversationId', ''),
                task.conversation_info.get('chatId', ''),
            ])
        else:
            self.workflow_instance_id = task.workflow_instance_id
            
        try:
            if is_callable_input_parameter_a_task(
                callable=self._run,
                object_type=Task,
            ):
                task_output = self._run(task)
            else:
                params = inspect.signature(self._run).parameters
                for input_name in params:
                    typ = params[input_name].annotation
                    default_value = params[input_name].default
                    if input_name in task.input_data:
                        if typ in utils.simple_types:
                            task_input[input_name] = task.input_data[input_name]
                        else:
                            task_input[input_name] = convert_from_dict_or_list(
                                typ, task.input_data[input_name]
                            )
                    else:
                        if default_value is not inspect.Parameter.empty:
                            task_input[input_name] = default_value
                        else:
                            task_input[input_name] = None
                if inspect.iscoroutinefunction(self._run):
                    try:
                        loop = asyncio.get_running_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                    task_output = loop.run_until_complete(
                        asyncio.gather(self._run(**task_input), return_exceptions=True)
                    )[0]
                else:
                    task_output = self._run(**task_input)
            if type(task_output) == TaskResult:
                task_output.task_id = task.task_id
                task_output.workflow_instance_id = task.workflow_instance_id
                return task_output
            else:
                task_result.status = TaskResultStatus.COMPLETED
                task_result.output_data = task_output

        except NonRetryableException as ne:
            task_result.status = TaskResultStatus.FAILED_WITH_TERMINAL_ERROR
            if len(ne.args) > 0:
                task_result.reason_for_incompletion = ne.args[0]

        except Exception as ne:
            logger.error(
                f"Error executing task {task.task_def_name} with id {task.task_id}.  error = {traceback.format_exc()}"
            )
            self.callback.error(self.workflow_instance_id, error_code=500, error_info=f"ERROR:The '{task.task_def_name}' task execution failed.")

            task_result.logs = [
                TaskExecLog(
                    traceback.format_exc(), task_result.task_id, int(time.time())
                )
            ]
            task_result.status = TaskResultStatus.FAILED
            if len(ne.args) > 0:
                task_result.reason_for_incompletion = ne.args[0]
        self.workflow_instance_id = None

        if dataclasses.is_dataclass(type(task_result.output_data)):
            task_output = dataclasses.asdict(task_result.output_data)
            task_result.output_data = task_output
            return task_result
        if not isinstance(task_result.output_data, dict):
            task_output = task_result.output_data
            task_result.output_data = self.api_client.sanitize_for_serialization(
                task_output
            )
            if not isinstance(task_result.output_data, dict):
                task_result.output_data = {"result": task_result.output_data}
        return task_result

    def get_identity(self) -> str:
        return self.worker_id if hasattr(self, "worker_id") else socket.gethostname()

    def get_polling_interval_in_seconds(self) -> float:
        return self.poll_interval / 1000

    def get_task_definition_name(self) -> str:
        return self.task_definition_name_cache

    @property
    def task_definition_names(self):
        if isinstance(self.task_definition_name, list):
            return self.task_definition_name
        else:
            return [self.task_definition_name]

    @property
    def task_definition_name_cache(self):
        if self._task_definition_name_cache is None:
            self._task_definition_name_cache = self.compute_task_definition_name()
        return self._task_definition_name_cache

    def clear_task_definition_name_cache(self):
        self._task_definition_name_cache = None

    def compute_task_definition_name(self):
        if isinstance(self.task_definition_name, list):
            task_definition_name = self.task_definition_name[self.next_task_index]
            self.next_task_index = (self.next_task_index + 1) % len(
                self.task_definition_name
            )
            return task_definition_name
        return self.task_definition_name

    def get_task_result_from_task(self, task: Task) -> TaskResult:
        return TaskResult(
            task_id=task.task_id,
            workflow_instance_id=task.workflow_instance_id,
            worker_id=self.get_identity(),
            biz_meta=task.biz_meta,
            callback_url=task.callback_url,
        )

    def get_domain(self) -> str:
        return self.domain

    def paused(self) -> bool:
        return False
