from enum import Enum

from omagent_core.engine.workflow.task.task import TaskInterface
from omagent_core.engine.workflow.task.task_type import TaskType
from typing_extensions import Self


class WorkflowStatus(str, Enum):
    COMPLETED = ("COMPLETED",)
    FAILED = ("FAILED",)
    PAUSED = ("PAUSED",)
    RUNNING = ("RUNNING",)
    TERMINATED = ("TERMINATED",)
    TIMEOUT_OUT = ("TIMED_OUT",)


class TerminateTask(TaskInterface):
    def __init__(
        self, task_ref_name: str, status: WorkflowStatus, termination_reason: str
    ) -> Self:
        super().__init__(
            task_reference_name=task_ref_name,
            task_type=TaskType.TERMINATE,
            input_parameters={
                "terminationStatus": status,
                "terminationReason": termination_reason,
            },
        )
