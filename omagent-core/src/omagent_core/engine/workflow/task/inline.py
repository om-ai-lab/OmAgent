from omagent_core.engine.workflow.task.task import TaskInterface
from omagent_core.engine.workflow.task.task_type import TaskType
from typing_extensions import Self


class InlineTask(TaskInterface):
    def __init__(
        self, task_ref_name: str, script: str, bindings: dict[str, str] = None
    ) -> Self:
        super().__init__(
            task_reference_name=task_ref_name,
            task_type=TaskType.INLINE,
            input_parameters={
                "evaluatorType": "graaljs",
                "expression": script,
            },
        )
        if bindings is not None:
            self.input_parameters.update(bindings)
