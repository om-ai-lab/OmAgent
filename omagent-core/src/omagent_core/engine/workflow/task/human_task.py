from enum import Enum

from omagent_core.engine.workflow.task.task import TaskInterface
from omagent_core.engine.workflow.task.task_type import TaskType
from typing_extensions import Self


class AssignmentCompletionStrategy(str, Enum):
    LEAVE_OPEN = ("LEAVE_OPEN",)
    TERMINATE = "TERMINATE"

    def __str__(self) -> str:
        return self.name.__str__()


class TriggerType(str, Enum):
    ASSIGNED = ("ASSIGNED",)
    PENDING = ("PENDING",)
    IN_PROGRESS = ("IN_PROGRESS",)
    COMPLETED = ("COMPLETED",)
    TIMED_OUT = ("TIMED_OUT",)
    ASSIGNEE_CHANGED = ("ASSIGNEE_CHANGED",)

    def __str__(self) -> str:
        return self.name.__str__()


class HumanTask(TaskInterface):
    def __init__(
        self,
        task_ref_name: str,
        display_name: str = None,
        form_template: str = None,
        form_version: int = 0,
        assignment_completion_strategy: AssignmentCompletionStrategy = AssignmentCompletionStrategy.LEAVE_OPEN,
    ) -> Self:
        super().__init__(task_reference_name=task_ref_name, task_type=TaskType.HUMAN)
        self.input_parameters.update(
            {
                "__humanTaskDefinition": {
                    "assignmentCompletionStrategy": assignment_completion_strategy.name,
                    "displayName": display_name,
                    "userFormTemplate": {
                        "name": form_template,
                        "version": form_version,
                    },
                }
            }
        )
