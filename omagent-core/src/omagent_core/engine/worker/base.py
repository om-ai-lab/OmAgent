from abc import ABC, abstractmethod
import dataclasses
import inspect
import logging
import socket
import time
import traceback
from copy import deepcopy
from typing import Any, Callable, Union

from typing_extensions import Self

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

DEFAULT_POLLING_INTERVAL = 100

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
    def __init__(
        self, poll_interval: float = None, domain: str = None, worker_id: str = None
    ) -> Self:
        super().__init__()
        self.task_definition_name = self.name
        self.next_task_index = 0
        self._task_definition_name_cache = None
        self._domain = domain
        self._poll_interval = (
            DEFAULT_POLLING_INTERVAL
            if poll_interval is None
            else deepcopy(poll_interval)
        )

        self.api_client = ApiClient()
        if worker_id is None:
            self.worker_id = deepcopy(self.get_identity())
        else:
            self.worker_id = deepcopy(worker_id)

    @abstractmethod
    def _run(self) -> Any:
        """Run the Node."""

    async def _arun(self) -> Any:
        """Run the Node."""
        raise NotImplementedError(
            f"Async run not implemented for {type(self).__name__} Node."
        )

    def execute(self, task: Task) -> TaskResult:
        task_input = {}
        task_output = None
        task_result: TaskResult = self.get_task_result_from_task(task)

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

            task_result.logs = [
                TaskExecLog(
                    traceback.format_exc(), task_result.task_id, int(time.time())
                )
            ]
            task_result.status = TaskResultStatus.FAILED
            if len(ne.args) > 0:
                task_result.reason_for_incompletion = ne.args[0]

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
        return (
            self.poll_interval if self.poll_interval else DEFAULT_POLLING_INTERVAL
        ) / 1000

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
        )

    def get_domain(self) -> str:
        return self.domain

    def paused(self) -> bool:
        return False

    @property
    def domain(self):
        return self._domain

    @domain.setter
    def domain(self, value):
        self._domain = value

    @property
    def poll_interval(self):
        return self._poll_interval

    @poll_interval.setter
    def poll_interval(self, value):
        self._poll_interval = value