from abc import ABC

from omagent_core.engine.workflow.task.task import TaskInterface
from omagent_core.engine.workflow.task.task_type import TaskType
from typing_extensions import Self


class WaitTask(TaskInterface, ABC):

    def __init__(
        self, task_ref_name: str, wait_until: str = None, wait_for_seconds: int = None
    ) -> Self:
        """
        wait_until: Specific date/time to wait for e.g. 2023-12-25 05:25 PST
        wait_for_seconds: time to block for - e.g. specifying 60 will wait for 60 seconds
        """
        super().__init__(task_reference_name=task_ref_name, task_type=TaskType.WAIT)
        if wait_until is not None and wait_for_seconds is not None:
            raise Exception(
                "both wait_until and wait_for_seconds are provided.  ONLY one is allowed"
            )
        if wait_until:
            self.input_parameters = {"wait_until": wait_until}
        if wait_for_seconds:
            self.input_parameters = {"duration": str(wait_for_seconds) + "s"}


class WaitForDurationTask(WaitTask):
    def __init__(self, task_ref_name: str, duration_time_seconds: int) -> Self:
        super().__init__(task_ref_name)
        self.input_parameters = {"duration": str(duration_time_seconds) + "s"}


class WaitUntilTask(WaitTask):
    def __init__(self, task_ref_name: str, date_time: str) -> Self:
        super().__init__(task_ref_name)
        self.input_parameters = {"until": date_time}
