from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel


class TaskStatus(str, Enum):
    WAITING = "waiting"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class AgentTask(BaseModel):
    id: int
    parent: Optional["AgentTask"] = None
    children: List["AgentTask"] = []

    task: str
    criticism: str = "None"
    milestones: List[str] = []
    status: TaskStatus = TaskStatus.WAITING
    result: Any = None

    def add_subtasks(self, subtasks: List[dict]):
        """Add subtasks to current task as children tasks.

        Args:
            subtasks (List[dict]): List of subtasks in dict, arranged in execution order.
        """
        for index, subtask in enumerate(subtasks):
            self.children.append(
                self.__class__(parent=self, id=self.task_depth() + index, **subtask)
            )

    def find_sibling_tasks(self) -> List["AgentTask"]:
        """Return the subtasks from same parent task.

        Returns:
            List[AgentTask]: Sibling tasks of current task.
        """
        if self.parent is None:
            return [self]
        else:
            return self.parent.children

    def find_origin_task(self) -> "AgentTask":
        """Retrun the original task.

        Returns:
            AgentTask: The original task from user.
        """
        current = self
        while current.id != 0:
            current = current.parent
        return current

    def task_info(self) -> dict:
        """Retrun the task information of current task.

        Returns:
            dict: The task information of current task.
        """
        return self.model_dump(exclude={"parent", "children"}, exclude_none=True)

    def sibling_info(self) -> List[dict]:
        """Get information of all sibling tasks (including current task).

        Returns:
            List[dict]: Task informations.
        """
        return [item.task_info() for item in self.find_sibling_tasks()]

    def children_info(self) -> List[dict]:
        """Get information of all childen tasks.

        Returns:
            List[dict]: Task informations.
        """
        return [item.task_info() for item in self.children]

    def task_depth(self) -> int:
        """Get the level depth of this task. Depth start from 1.

        Returns:
            int: The depth of current task.
        """
        depth = 1
        current = self
        while current.id != 0:
            current = current.parent
            depth += 1
        return depth

    def next_sibling_task(self) -> Optional["AgentTask"]:
        """Get the next sibling task of current task.

        Returns:
            Optional[AgentTask]: The next sibling task of current task.
        """
        siblings = self.find_sibling_tasks()
        for index, sib in enumerate(siblings):
            if sib.id == self.id:
                break
        if index + 1 < len(siblings):
            return siblings[index + 1]
        else:
            return None

    def previous_sibling_task(self) -> Optional["AgentTask"]:
        """Get the previous sibling task of current task.

        Returns:
            Optional[AgentTask]: The previous sibling task of current task.
        """
        siblings = self.find_sibling_tasks()
        for index, sib in enumerate(siblings):
            if sib.id == self.id:
                break
        if index - 1 >= 0:
            return siblings[index - 1]
        else:
            return None

    def find_root_task(self) -> "AgentTask":
        """Get the root task of current task.

        Returns:
            AgentTask: The root task of current task.
        """
        current = self
        while current.parent is not None:
            current = current.parent
        return current
