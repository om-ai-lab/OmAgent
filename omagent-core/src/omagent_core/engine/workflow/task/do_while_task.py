from copy import deepcopy
from typing import Any, Dict, List
import os
from omagent_core.engine.http.models.workflow_task import WorkflowTask
from omagent_core.engine.workflow.task.task import (
    TaskInterface, get_task_interface_list_as_workflow_task_list)
from omagent_core.engine.workflow.task.task_type import TaskType
from typing_extensions import Self
from omagent_core.engine.workflow.task.simple_task import simple_task


def get_for_loop_condition(task_ref_name: str, iterations: int) -> str:
    return f"if ( $.{task_ref_name}.iteration < {iterations} ) {{ true; }} else {{ false; }}"


def get_dnc_loop_condition(task_ref_name: str) -> str:

    return (
        f" if ( $.{task_ref_name}['exit_flag'] == true) {{ false; }} else {{ true; }}"
    )

class DoWhileTask(TaskInterface):
    # termination_condition is a Javascript expression that evaluates to True or False
    def __init__(
        self, task_ref_name: str, termination_condition: str, tasks: List[TaskInterface], inputs: Dict[str, Any] = None
    ) -> Self:
        super().__init__(
            task_reference_name=task_ref_name,
            task_type=TaskType.DO_WHILE,
            input_parameters=inputs,
        )
        self._loop_condition = deepcopy(termination_condition)
        if isinstance(tasks, List):
            self._loop_over = deepcopy(tasks)
        else:
            self._loop_over = [deepcopy(tasks)]

    def to_workflow_task(self) -> WorkflowTask:
        workflow = super().to_workflow_task()
        workflow.loop_condition = self._loop_condition
        workflow.loop_over = get_task_interface_list_as_workflow_task_list(
            *self._loop_over,
        )
        return workflow


class LoopTask(DoWhileTask):
    def __init__(
        self, task_ref_name: str, iterations: int, tasks: List[TaskInterface]
    ) -> Self:
        super().__init__(
            task_ref_name=task_ref_name,
            termination_condition=get_for_loop_condition(
                task_ref_name,
                iterations,
            ),
            tasks=tasks,
        )


class ForEachTask(DoWhileTask):
    def __init__(
        self,
        task_ref_name: str,
        tasks: List[TaskInterface],
        iterate_over: str,
        variables: List[str] = None,
    ) -> Self:
        super().__init__(
            task_ref_name=task_ref_name,
            termination_condition=get_for_loop_condition(
                task_ref_name,
                0,
            ),
            tasks=tasks,
        )
        super().input_parameter("items", iterate_over)


class InfiniteLoopTask(DoWhileTask):
    def __init__(self, task_ref_name: str, tasks: List[TaskInterface]) -> Self:
        super().__init__(
            task_ref_name=task_ref_name,
            termination_condition="true",
            tasks=tasks,
        )


class DnCLoopTask(DoWhileTask):
    def __init__(
        self,
        task_ref_name: str,
        tasks: List[TaskInterface],
        pre_loop_exit: TaskInterface = None,
        post_loop_exit: List[TaskInterface] = None,
    ) -> Self:
        if pre_loop_exit is not None and post_loop_exit is not None:
            real_tasks = pre_loop_exit + tasks + post_loop_exit
        elif pre_loop_exit is not None:
            real_tasks = pre_loop_exit + tasks
        elif post_loop_exit is not None:
            real_tasks = tasks + post_loop_exit
        else:
            real_tasks = tasks
        flatten_tasks = []
        for each in real_tasks:
            if isinstance(each, list):
                flatten_tasks.extend(each)
            else:
                flatten_tasks.append(each)
        super().__init__(
            task_ref_name=task_ref_name,
            termination_condition=get_dnc_loop_condition(
                post_loop_exit[0].task_reference_name
            ),
            tasks=flatten_tasks,
        )
