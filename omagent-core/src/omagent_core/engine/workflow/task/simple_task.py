from typing_extensions import Self
from typing import Type

from omagent_core.engine.workflow.task.task import TaskInterface
from omagent_core.engine.workflow.task.task_type import TaskType
from omagent_core.engine.worker.base import BaseWorker


class SimpleTask(TaskInterface):
    def __init__(self, task_def_name: str, task_reference_name: str) -> Self:
        super().__init__(
            task_reference_name=task_reference_name,
            task_type=TaskType.SIMPLE,
            task_name=task_def_name
        )


def simple_task(task_def_name: str|Type[BaseWorker], task_reference_name: str, inputs: dict[str, object] = {}) -> TaskInterface:
    if isinstance(task_def_name, type) and issubclass(task_def_name, BaseWorker):
        task_def_name = task_def_name.name
    task = SimpleTask(task_def_name=task_def_name, task_reference_name=task_reference_name)
    task.input_parameters.update(inputs)
    return task
