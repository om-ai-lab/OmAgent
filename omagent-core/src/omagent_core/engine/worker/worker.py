import dataclasses
import inspect
import logging
import time
import traceback
from copy import deepcopy
from typing import Any, Callable, Union

from typing_extensions import Self

from omagent_core.engine.automator import utils
from omagent_core.engine.automator.utils import convert_from_dict_or_list
from omagent_core.engine.configuration.configuration import Configuration
from omagent_core.engine.http.api_client import ApiClient
from omagent_core.engine.http.models import TaskExecLog
from omagent_core.engine.http.models.task import Task
from omagent_core.engine.http.models.task_result import TaskResult
from omagent_core.engine.http.models.task_result_status import TaskResultStatus
from omagent_core.engine.worker.exception import NonRetryableException
from omagent_core.engine.worker.worker_interface import WorkerInterface, DEFAULT_POLLING_INTERVAL

ExecuteTaskFunction = Callable[
    [
        Union[Task, object]
    ],
    Union[TaskResult, object]
]

logger = logging.getLogger(
    Configuration.get_logging_formatted_name(
        __name__
    )
)


def is_callable_input_parameter_a_task(callable: ExecuteTaskFunction, object_type: Any) -> bool:
    parameters = inspect.signature(callable).parameters
    if len(parameters) != 1:
        return False
    parameter = parameters[list(parameters.keys())[0]]
    return parameter.annotation == object_type or parameter.annotation == parameter.empty or parameter.annotation == object


def is_callable_return_value_of_type(callable: ExecuteTaskFunction, object_type: Any) -> bool:
    return_annotation = inspect.signature(callable).return_annotation
    return return_annotation == object_type


class Worker(WorkerInterface):
    def __init__(self,
                 task_definition_name: str,
                 execute_function: ExecuteTaskFunction,
                 poll_interval: float = None,
                 domain: str = None,
                 worker_id: str = None,
                 ) -> Self:
        super().__init__(task_definition_name)
        self.api_client = ApiClient()
        if poll_interval is None:
            self.poll_interval = DEFAULT_POLLING_INTERVAL
        else:
            self.poll_interval = deepcopy(poll_interval)
        self.domain = deepcopy(domain)
        if worker_id is None:
            self.worker_id = deepcopy(super().get_identity())
        else:
            self.worker_id = deepcopy(worker_id)
        self.execute_function = deepcopy(execute_function)

    def execute(self, task: Task) -> TaskResult:
        task_input = {}
        task_output = None
        task_result: TaskResult = self.get_task_result_from_task(task)

        try:

            if self._is_execute_function_input_parameter_a_task:
                task_output = self.execute_function(task)
            else:
                params = inspect.signature(self.execute_function).parameters
                for input_name in params:
                    typ = params[input_name].annotation
                    default_value = params[input_name].default
                    if input_name in task.input_data:
                        if typ in utils.simple_types:
                            task_input[input_name] = task.input_data[input_name]
                        else:
                            task_input[input_name] = convert_from_dict_or_list(typ, task.input_data[input_name])
                    else:
                        if default_value is not inspect.Parameter.empty:
                            task_input[input_name] = default_value
                        else:
                            task_input[input_name] = None
                task_output = self.execute_function(**task_input)

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
                f'Error executing task {task.task_def_name} with id {task.task_id}.  error = {traceback.format_exc()}')

            task_result.logs = [TaskExecLog(
                traceback.format_exc(), task_result.task_id, int(time.time()))]
            task_result.status = TaskResultStatus.FAILED
            if len(ne.args) > 0:
                task_result.reason_for_incompletion = ne.args[0]

        if dataclasses.is_dataclass(type(task_result.output_data)):
            task_output = dataclasses.asdict(task_result.output_data)
            task_result.output_data = task_output
            return task_result
        if not isinstance(task_result.output_data, dict):
            task_output = task_result.output_data
            task_result.output_data = self.api_client.sanitize_for_serialization(task_output)
            if not isinstance(task_result.output_data, dict):
                task_result.output_data = {'result': task_result.output_data}

        return task_result

    def get_identity(self) -> str:
        return self.worker_id

    @property
    def execute_function(self) -> ExecuteTaskFunction:
        return self._execute_function

    @execute_function.setter
    def execute_function(self, execute_function: ExecuteTaskFunction) -> None:
        self._execute_function = execute_function
        self._is_execute_function_input_parameter_a_task = is_callable_input_parameter_a_task(
            callable=execute_function,
            object_type=Task,
        )
        self._is_execute_function_return_value_a_task_result = is_callable_return_value_of_type(
            callable=execute_function,
            object_type=TaskResult,
        )
