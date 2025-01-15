from copy import deepcopy
from typing import List

from omagent_core.engine.http.models.workflow_task import WorkflowTask
from omagent_core.engine.workflow.task.task import TaskInterface
from omagent_core.engine.workflow.task.task_type import TaskType
from typing_extensions import Self


class JoinTask(TaskInterface):
    def __init__(
        self, task_ref_name: str, join_on: List[str] = None, join_on_script: str = None
    ) -> Self:
        super().__init__(task_reference_name=task_ref_name, task_type=TaskType.JOIN)
        self._join_on = deepcopy(join_on)
        if join_on_script is not None:
            self.evaluator_type = "js"
            self.expression = join_on_script

    def to_workflow_task(self) -> WorkflowTask:
        workflow = super().to_workflow_task()
        workflow.join_on = self._join_on
        return workflow
