from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    WAITING = "waiting"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class TaskNode(BaseModel):
    id: int
    predecessor_ids: List[int] = []
    successor_ids: List[int] = []
    executed: bool = False
    can_be_executed: bool = False
    task: str
    phrase: int = 0
    pre_task_input: Any = None
    original_task_input: Any = ""
    current_task_input: Any = None
    score: float = 0
    scored: bool = False
    

    def copy_as_dict(self, **kwargs):
        new_node = self.model_dump()
        del new_node['id']
        del new_node['predecessor_ids']
        del new_node['successor_ids']
        new_node['successor_ids'] = []
        new_node['executed'] = False
        new_node['score'] = 0
        new_node['scored'] = False
        

        for key, value in kwargs.items():
            try:    
                new_node[key] = value
            except:
                raise ValueError(f"Key {key} not found in TaskNode")

        return new_node




class TaskTree(BaseModel):
    nodes: Dict[int, TaskNode] = Field(default_factory=dict)
    cursor: int = 0
    next_id: int = 0
    leaves: List[int] = []
    roots: List[int] = []
        

    ######
    def is_node_can_be_executed(self, node_id: int)  -> bool:
        """
        Checks if the node can be executed based on its predecessors.

        :return: True if all predecessors have been executed, False otherwise.
        :rtype: bool
        """
        
        return all(self.nodes.get(predecessor_id).executed for predecessor_id in self.nodes.get(node_id).predecessor_ids)
    def get_node_id(self, node: TaskNode) -> int:
        """
        Get the ID of a given TaskNode.

        :param node: The TaskNode to find the ID for
        :return: The ID of the node, or -1 if not found
        :rtype: int
        """
        for id, n in self.nodes.items():
            if n == node:
                return id
        return -1

    def get_node(self, node_id: int) -> TaskNode:
        """
        Get a TaskNode by its ID.

        :param node_id: The ID of the node to retrieve
        :return: The TaskNode object
        :rtype: TaskNode
        """
        return self.nodes.get(node_id)

    def _add_predecessor(self, node_id: int, predecessor_id: int):
        """
        Add a preceding node and update the relationships.

        :param node_id: ID of the target node
        :param predecessor_id: ID of the predecessor node
        """
        self.nodes.get(node_id).predecessor_ids.append(predecessor_id)
        self.nodes.get(predecessor_id).successor_ids.append(node_id)
    
    def _add_successor(self, node_id: int, successor_id: int):
        """
        Add a successor relationship between two nodes.

        :param node_id: ID of the target node
        :param successor_id: ID of the successor node
        """
        self.nodes.get(node_id).successor_ids.append(successor_id)
        self.nodes.get(successor_id).predecessor_ids.append(node_id)
    
    def get_predecessors(self, node_id: int) -> List[TaskNode]:
        """
        Get all predecessor nodes for a given node ID.

        :param node_id: The ID of the node
        :return: List of predecessor TaskNodes
        :rtype: List[TaskNode]
        """
        if len(self.nodes.get(node_id).predecessor_ids) > 0:
            return [node for node in self.nodes.values() if node.id in self.nodes.get(node_id).predecessor_ids]
        return []

    def get_successors(self, node_id: int) -> List[TaskNode]:
        """
        Get all successor nodes for a given node ID.

        :param node_id: The ID of the node
        :return: List of successor TaskNodes
        :rtype: List[TaskNode]
        """
        if len(self.nodes.get(node_id).successor_ids) > 0:
            return [node for node in self.nodes.values() if node.id in self.nodes.get(node_id).successor_ids]
        return []
    
    def get_can_be_executed_nodes(self) -> List[TaskNode]:
        """
        Get all nodes that are ready to be executed.

        :return: List of executable TaskNodes
        :rtype: List[TaskNode]
        """
        return [node for node in self.nodes.values() if node.can_be_executed]
    
    def get_all_nodes(self) -> List[TaskNode]:
        """
        Get all nodes in the task tree.

        :return: List of all TaskNodes
        :rtype: List[TaskNode]
        """
        return list(self.nodes.values())
    
    def get_all_nodes_ids(self) -> List[int]:
        """
        Get IDs of all nodes in the task tree.

        :return: List of all node IDs
        :rtype: List[int]
        """
        return [node.id for node in self.nodes.values()]
    
    def add_node(self, task: dict, predecessor_ids: Optional[int] = []) -> TaskNode:
        """Add a single node to the tree"""
        node = TaskNode(
            id=self.next_id,
            predecessor_ids=predecessor_ids,
            **task
        )

        self.nodes[node.id] = node
        self.next_id += 1
        if len(self.roots) == 0:
            self.roots = [node.id]
            assert (
                len(node.predecessor_ids) == 0
            ), "First operation should have no predecessors"
            if len(node.successor_ids) == 0:
                self.leaves = [node.id]
            else:
                raise ValueError("Successors should only be added to after nodes are added")
        else:
            if len(predecessor_ids) == 0:
                self.roots.append(node.id)
            node_predecessor_ids = predecessor_ids.copy()
            for predecessor_id in node_predecessor_ids:
                if predecessor_id in self.leaves:
                    self.leaves.remove(predecessor_id)
                self.nodes.get(predecessor_id).successor_ids.append(node.id)
            self.leaves.append(node.id) 
         
        return node
    
    def append_node_to_all_leaves(self, task: dict) -> TaskNode:
        """
        Appends an operation to all leaves in the graph and updates the relationships.

        :param operation: The operation to append.
        :type operation: Operation
        """
        leaves = self.leaves
        # node = TaskNode(
        #     id=self.next_id,
        #     predecessor_ids=leaves,
        #     **task
        # )
        # self.nodes[node.id] = node
        # self.next_id += 1
        assert len(leaves) > 0, "Leaves should not be empty"
        self.add_node(task, leaves)
        # if len(self.roots) == 0:
        #     self.add_node(task, leaves)
        #     self.roots = [node.id]
        #     self.leaves = [node.id]
        # else:
        #     self.add_node(task, leaves)
        
        return
    
if __name__ == "__main__":
    import json
    # Test code
    tree = TaskTree()
    
    # Add root task
    root = tree.add_node({"task": "search hangzhou weather tomorrow and save the result into a file"})
    id = tree.get_node_id(root)
    # Add subtasks
    subtasks = [
        {"task": "search hangzhou weather tomorrow"},
        {"task": "analyze the weather data"},
        {"task": "save the result into a file"}
    ]

    for task in subtasks:
        tree.add_node(task, [id])

    print(tree.nodes)
    print(tree.roots)
    print(tree.leaves)
    print(tree.get_node_id(root))   


    node1 = tree.nodes[1]
    node2 = tree.nodes[2]
    node3 = tree.nodes[3]

    print(node1.predecessor_ids)
    print(node2.predecessor_ids)
    print(node3.predecessor_ids)



    print(tree.get_node_id(node1))
    print(tree.get_node_id(node2))
    print(tree.get_node_id(node3))

    print(tree.is_node_can_be_executed(node1.id))

    print("############")
    for node in tree.get_all_nodes():
        print(node.id, tree.get_predecessors(node.id))

    print("############")
    for node in tree.get_all_nodes():
        print(node.id, tree.get_successors(node.id))

    print(tree.get_can_be_executed_nodes())
    print(tree.get_all_nodes_ids())
    print(tree.get_all_nodes())

    task4 = {"task": "search hangzhou weather tomorrow"}
    tree.append_node_to_all_leaves(task4)
    print(tree.get_all_nodes_ids())
    print(tree.get_all_nodes()) 
    print(tree.leaves)
    print(tree.roots)

    for id in tree.leaves:
        node = tree.get_node(id)



