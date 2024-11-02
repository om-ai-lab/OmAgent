from typing_extensions import Self

from omagent_core.engine.workflow.task.task import TaskInterface
from omagent_core.engine.workflow.task.task_type import TaskType


class SimpleTask(TaskInterface):
    def __init__(self, task_def_name: str, task_reference_name: str) -> Self:
        super().__init__(
            task_reference_name=task_reference_name,
            task_type=TaskType.SIMPLE,
            task_name=task_def_name
        )


def simple_task(task_def_name: str, task_reference_name: str, inputs: dict[str, object] = {}) -> TaskInterface:
    task = SimpleTask(task_def_name=task_def_name, task_reference_name=task_reference_name)
    task.input_parameters.update(inputs)
    return task
