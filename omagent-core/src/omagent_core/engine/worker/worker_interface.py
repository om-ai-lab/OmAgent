import abc
import socket
from typing import Union

from omagent_core.engine.http.models.task import Task
from omagent_core.engine.http.models.task_result import TaskResult

DEFAULT_POLLING_INTERVAL = 100  # ms


class WorkerInterface(abc.ABC):
    def __init__(self, task_definition_name: Union[str, list]):
        self.task_definition_name = task_definition_name
        self.next_task_index = 0
        self._task_definition_name_cache = None
        self._domain = None
        self._poll_interval = DEFAULT_POLLING_INTERVAL

    @abc.abstractmethod
    def execute(self, task: Task) -> TaskResult:
        """
        Executes a task and returns the updated task.

        :param Task: (required)
        :return: TaskResult
                 If the task is not completed yet, return with the status as IN_PROGRESS.
        """
        pass

    def get_identity(self) -> str:
        """
        Retrieve the hostname of the instance that the worker is running.

        :return: str
        """
        return socket.gethostname()

    def get_polling_interval_in_seconds(self) -> float:
        """
        Retrieve interval in seconds at which the server should be polled for worker tasks.

        :return: float
                 Default: 100ms
        """
        return (self.poll_interval if self.poll_interval else DEFAULT_POLLING_INTERVAL) / 1000

    def get_task_definition_name(self) -> str:
        """
        Retrieve the name of the task definition the worker is currently working on.

        :return: TaskResult
        """
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
            self.next_task_index = (self.next_task_index + 1) % len(self.task_definition_name)
            return task_definition_name
        return self.task_definition_name

    def get_task_result_from_task(self, task: Task) -> TaskResult:
        """
        Retrieve the TaskResult object from given task.

        :param Task: (required)
        :return: TaskResult
        """
        return TaskResult(
            task_id=task.task_id,
            workflow_instance_id=task.workflow_instance_id,
            worker_id=self.get_identity()
        )

    def get_domain(self) -> str:
        """
        Retrieve the domain of the worker.

        :return: str
        """
        return self.domain

    def paused(self) -> bool:
        """
        Override this method to pause the worker from polling.
        """
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
