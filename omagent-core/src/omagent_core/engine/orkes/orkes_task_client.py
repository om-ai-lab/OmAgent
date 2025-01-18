from typing import List, Optional

from omagent_core.engine.configuration.configuration import Configuration
from omagent_core.engine.http.models import PollData
from omagent_core.engine.http.models.task import Task
from omagent_core.engine.http.models.task_exec_log import TaskExecLog
from omagent_core.engine.http.models.task_result import TaskResult
from omagent_core.engine.http.models.workflow import Workflow
from omagent_core.engine.orkes.orkes_base_client import OrkesBaseClient
from omagent_core.engine.task_client import TaskClient


class OrkesTaskClient(OrkesBaseClient, TaskClient):
    def __init__(self, configuration: Configuration):
        super(OrkesTaskClient, self).__init__(configuration)

    def poll_task(
        self,
        task_type: str,
        worker_id: Optional[str] = None,
        domain: Optional[str] = None,
    ) -> Optional[Task]:
        kwargs = {}
        if worker_id:
            kwargs.update({"workerid": worker_id})
        if domain:
            kwargs.update({"domain": domain})

        return self.taskResourceApi.poll(task_type, **kwargs)

    def batch_poll_tasks(
        self,
        task_type: str,
        worker_id: Optional[str] = None,
        count: Optional[int] = None,
        timeout_in_millisecond: Optional[int] = None,
        domain: Optional[str] = None,
    ) -> List[Task]:
        kwargs = {}
        if worker_id:
            kwargs.update({"workerid": worker_id})
        if count:
            kwargs.update({"count": count})
        if timeout_in_millisecond:
            kwargs.update({"timeout": timeout_in_millisecond})
        if domain:
            kwargs.update({"domain": domain})

        return self.taskResourceApi.batch_poll(task_type, **kwargs)

    def get_task(self, task_id: str) -> Task:
        return self.taskResourceApi.get_task(task_id)

    def update_task(self, task_result: TaskResult) -> str:
        return self.taskResourceApi.update_task(task_result)

    def update_task_by_ref_name(
        self,
        workflow_id: str,
        task_ref_name: str,
        status: str,
        output: object,
        worker_id: Optional[str] = None,
    ) -> str:
        body = {"result": output}
        kwargs = {}
        if worker_id:
            kwargs.update({"workerid": worker_id})
        return self.taskResourceApi.update_task1(
            body, workflow_id, task_ref_name, status, **kwargs
        )

    def update_task_sync(
        self,
        workflow_id: str,
        task_ref_name: str,
        status: str,
        output: object,
        worker_id: Optional[str] = None,
    ) -> Workflow:
        if not isinstance(output, dict):
            output = {"result": output}
        body = output
        kwargs = {}
        if worker_id:
            kwargs.update({"workerid": worker_id})
        return self.taskResourceApi.update_task_sync(
            body, workflow_id, task_ref_name, status, **kwargs
        )

    def get_queue_size_for_task(self, task_type: str) -> int:
        queueSizesByTaskType = self.taskResourceApi.size(task_type=[task_type])
        queueSize = queueSizesByTaskType.get(task_type, 0)
        return queueSize

    def add_task_log(self, task_id: str, log_message: str):
        self.taskResourceApi.log(log_message, task_id)

    def get_task_logs(self, task_id: str) -> List[TaskExecLog]:
        return self.taskResourceApi.get_task_logs(task_id)

    def get_task_poll_data(self, task_type: str) -> List[PollData]:
        return self.taskResourceApi.get_poll_data(task_type=task_type)
