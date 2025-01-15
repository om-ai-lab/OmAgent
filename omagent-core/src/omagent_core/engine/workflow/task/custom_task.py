from typing import List, Type, Union

from omagent_core.engine.worker.base import BaseWorker
from omagent_core.engine.workflow.task.set_variable_task import SetVariableTask
from omagent_core.engine.workflow.task.task import TaskInterface
from omagent_core.engine.workflow.task.task_type import TaskType
from typing_extensions import Self
from omagent_core.utils.registry import registry


class CustomTask(TaskInterface):
    def __init__(self, task_def_name: str, task_reference_name: str) -> Self:
        super().__init__(
            task_reference_name=task_reference_name,
            task_type=TaskType.CUSTOM,
            task_name=task_def_name,
        )


def custom_task(
    task_def_name: str | Type[BaseWorker],
    task_reference_name: str,
    inputs: dict[str, object] = {},
) -> TaskInterface:
    if isinstance(task_def_name, type) and issubclass(task_def_name, BaseWorker):
        worker_class = task_def_name
        task_def_name = task_def_name.__name__
        worker_class.task_type = TaskType.CUSTOM
    else:
        worker_class = registry.get_worker(task_def_name)
        if worker_class:
            worker_class.task_type = TaskType.CUSTOM
    
    task = CustomTask(
        task_def_name=task_def_name, task_reference_name=task_reference_name
    )
    task.input_parameters.update(inputs)
    return task
