from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    WAITING = "waiting"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class TaskNode(BaseModel):
    id: int
    parent_id: Optional[int] = None
    task: str
    criticism: str = "None"
    milestones: List[str] = []
    status: TaskStatus = TaskStatus.WAITING
    result: Any = None


class TaskTree(BaseModel):
    nodes: Dict[int, TaskNode] = Field(default_factory=dict)
    cursor: int = 0
    next_id: int = 0

    def add_node(self, task: dict, parent_id: Optional[int] = None) -> TaskNode:
        """添加单个节点到树中"""
        node = TaskNode(id=self.next_id, parent_id=parent_id, **task)
        self.nodes[node.id] = node
        self.next_id += 1
        return node

    def add_subtasks(self, parent_id: int, subtasks: List[dict]) -> List[TaskNode]:
        """为指定节点添加子任务"""
        if parent_id not in self.nodes:
            raise ValueError(f"Parent node {parent_id} not found")

        added_nodes = []
        for subtask in subtasks:
            node = self.add_node(subtask, parent_id=parent_id)
            added_nodes.append(node)
        return added_nodes

    def get_children(self, node_id: int) -> List[TaskNode]:
        """获取指定节点的所有子节点"""
        return [node for node in self.nodes.values() if node.parent_id == node_id]

    def get_parent(self, node_id: int) -> Optional[TaskNode]:
        """获取指定节点的父节点"""
        node = self.nodes.get(node_id)
        if node and node.parent_id is not None:
            return self.nodes.get(node.parent_id)
        return None

    def get_siblings(self, node_id: int) -> List[TaskNode]:
        """获取指定节点的兄弟节点（不包括自己）"""
        node = self.nodes.get(node_id)
        if not node:
            return []
        if node.parent_id is None:
            return []
        return [
            n
            for n in self.nodes.values()
            if n.parent_id == node.parent_id and n.id != node_id
        ]

    def get_next_sibling(self, node_id: int) -> Optional[TaskNode]:
        """获取下一个兄弟节点"""
        siblings = self.get_siblings(node_id)
        siblings.sort(key=lambda x: x.id)
        for i, sibling in enumerate(siblings):
            if sibling.id == node_id + 1 and i <= len(siblings) - 1:
                return siblings[i]
        return None

    def get_previous_sibling(self, node_id: int) -> Optional[TaskNode]:
        """获取上一个兄弟节点"""
        siblings = self.get_siblings(node_id)
        siblings.sort(key=lambda x: x.id)
        for i, sibling in enumerate(siblings):
            if sibling.id == node_id - 1 and i >= 0:
                return siblings[i]
        return None

    def get_root(self) -> Optional[TaskNode]:
        """获取根节点"""
        for node in self.nodes.values():
            if node.parent_id is None:
                return node
        return None

    def get_depth(self, node_id: int) -> int:
        """获取节点的深度（从1开始）"""
        depth = 1
        current = self.nodes.get(node_id)
        while current and current.parent_id is not None:
            current = self.nodes.get(current.parent_id)
            depth += 1
        return depth

    def get_current_node(self) -> Optional[TaskNode]:
        """获取当前光标所在的节点"""
        return self.nodes.get(self.cursor)

    def set_cursor(self, node_id: int):
        """设置光标位置"""
        if node_id in self.nodes:
            self.cursor = node_id
        else:
            raise ValueError(f"Node {node_id} not found")


if __name__ == "__main__":
    import json

    # 测试代码
    tree = TaskTree()

    # 添加根任务
    root = tree.add_node(
        {"task": "search hangzhou weather tomorrow and save the result into a file"}
    )

    # 添加子任务
    subtasks = [
        {"task": "search hangzhou weather tomorrow"},
        {"task": "analyze the weather data"},
        {"task": "save the result into a file"},
    ]
    children = tree.add_subtasks(root.id, subtasks)

    sub_task1 = tree.get_children(root.id)[1]
    sub_task0 = tree.get_previous_sibling(sub_task1.id)
    sub_task2 = tree.get_next_sibling(sub_task1.id)
    tree.get_next_sibling(0)
    tree.get_root()
    print()
