from omagent_core.engine.http.models import WorkflowTask
from omagent_core.engine.workflow.task.task import TaskInterface
from omagent_core.engine.workflow.task.task_type import TaskType
from typing_extensions import Self


class DynamicTask(TaskInterface):
    def __init__(
        self,
        dynamic_task: str,
        task_reference_name: str,
        dynamic_task_param: str = "taskToExecute",
    ) -> Self:
        super().__init__(
            task_reference_name=task_reference_name,
            task_type=TaskType.DYNAMIC,
            task_name="dynamic_task",
        )
        self.input_parameters[dynamic_task_param] = dynamic_task
        self._dynamic_task_param = dynamic_task_param

    def to_workflow_task(self) -> WorkflowTask:
        wf_task = super().to_workflow_task()
        wf_task.dynamic_task_name_param = self._dynamic_task_param
        return wf_task
