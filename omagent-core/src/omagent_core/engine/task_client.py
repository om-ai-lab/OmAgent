from abc import ABC, abstractmethod
from typing import List, Optional

from omagent_core.engine.http.models import PollData
from omagent_core.engine.http.models.task import Task
from omagent_core.engine.http.models.task_exec_log import TaskExecLog
from omagent_core.engine.http.models.task_result import TaskResult
from omagent_core.engine.http.models.task_result_status import TaskResultStatus
from omagent_core.engine.http.models.workflow import Workflow


class TaskClient(ABC):
    @abstractmethod
    def poll_task(
        self,
        task_type: str,
        worker_id: Optional[str] = None,
        domain: Optional[str] = None,
    ) -> Optional[Task]:
        pass

    @abstractmethod
    def batch_poll_tasks(
        self,
        task_type: str,
        worker_id: Optional[str] = None,
        count: Optional[int] = None,
        timeout_in_millisecond: Optional[int] = None,
        domain: Optional[str] = None,
    ) -> List[Task]:
        pass

    @abstractmethod
    def get_task(self, task_id: str) -> Task:
        pass

    @abstractmethod
    def update_task(self, task_result: TaskResult) -> str:
        pass

    @abstractmethod
    def update_task_by_ref_name(
        self,
        workflow_id: str,
        task_ref_name: str,
        status: TaskResultStatus,
        output: object,
        worker_id: Optional[str] = None,
    ) -> str:
        pass

    @abstractmethod
    def update_task_sync(
        self,
        workflow_id: str,
        task_ref_name: str,
        status: TaskResultStatus,
        output: object,
        worker_id: Optional[str] = None,
    ) -> Workflow:
        pass

    @abstractmethod
    def get_queue_size_for_task(self, task_type: str) -> int:
        pass

    @abstractmethod
    def add_task_log(self, task_id: str, log_message: str):
        pass

    @abstractmethod
    def get_task_logs(self, task_id: str) -> List[TaskExecLog]:
        pass

    @abstractmethod
    def get_task_poll_data(self, task_type: str) -> List[PollData]:
        pass
