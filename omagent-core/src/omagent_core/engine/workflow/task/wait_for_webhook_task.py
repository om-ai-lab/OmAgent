from abc import ABC

from omagent_core.engine.workflow.task.task import TaskInterface
from omagent_core.engine.workflow.task.task_type import TaskType
from typing_extensions import Self


class WaitForWebHookTask(TaskInterface, ABC):

    def __init__(self, task_ref_name: str, matches: dict[str, object]) -> Self:
        """
        matches: dictionary of matching payload that acts as correction between the incoming webhook payload and a
        running workflow task - amongst all the running workflows.

        example:
        if the matches is specified as below:

        {
            "$['type']": "customer_created",
            "$['customer_id']": "${workflow.input.customer_id}"
        }

        for an incoming webhook request with the payload like:
        {
         "type": "customer_created",
         "customer_id": "customer_123"
        }

        The system will find a matching workflow task that is in progress matching the type and customer id and complete
        the task.
        """
        super().__init__(
            task_reference_name=task_ref_name, task_type=TaskType.WAIT_FOR_WEBHOOK
        )
        self.input_parameters["matches"] = matches


def wait_for_webhook(
    task_ref_name: str, matches: dict[str, object], task_def_name: str = None
) -> TaskInterface:
    task = WaitForWebHookTask(task_ref_name=task_ref_name, matches=matches)
    if task_def_name is not None:
        task.name = task_def_name
    return task
