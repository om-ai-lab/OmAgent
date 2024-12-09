from typing import Dict, Any
from typing_extensions import Self

from omagent_core.engine.workflow.task.task import TaskInterface
from omagent_core.engine.workflow.task.task_type import TaskType


class SetVariableTask(TaskInterface):
    def __init__(self, task_ref_name: str, input_parameters: Dict[str, Any]) -> Self:
        super().__init__(
            task_reference_name=task_ref_name,
            task_type=TaskType.SET_VARIABLE,
            input_parameters=input_parameters
        )
