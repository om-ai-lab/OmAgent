from copy import deepcopy
from typing import List

from omagent_core.engine.http.models.workflow_task import WorkflowTask
from omagent_core.engine.workflow.task.join_task import JoinTask
from omagent_core.engine.workflow.task.task import TaskInterface
from omagent_core.engine.workflow.task.task_type import TaskType
from typing_extensions import Self


def get_join_task(task_reference_name: str) -> str:
    return task_reference_name + "_join"


class ForkTask(TaskInterface):
    def __init__(
        self,
        task_ref_name: str,
        forked_tasks: List[List[TaskInterface]],
        join_on: List[str] = None,
    ) -> Self:
        super().__init__(
            task_reference_name=task_ref_name, task_type=TaskType.FORK_JOIN
        )
        self._forked_tasks = deepcopy(forked_tasks)
        self._join_on = join_on

    def to_workflow_task(self) -> [WorkflowTask]:
        tasks = []
        workflow_task = super().to_workflow_task()
        workflow_task.fork_tasks = []
        workflow_task.join_on = []
        for inner_forked_tasks in self._forked_tasks:
            converted_inner_forked_tasks = []
            for inner_forked_task in inner_forked_tasks:
                converted_inner_forked_tasks.append(
                    inner_forked_task.to_workflow_task()
                )
            workflow_task.fork_tasks.append(converted_inner_forked_tasks)
            workflow_task.join_on.append(
                converted_inner_forked_tasks[-1].task_reference_name
            )
        if self._join_on is not None:
            join_on = self._join_on
            join_task = JoinTask(
                workflow_task.task_reference_name + "_join", join_on=join_on
            )
            tasks.append(workflow_task)
            tasks.append(join_task.to_workflow_task())
            return tasks
        return workflow_task
