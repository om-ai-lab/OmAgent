from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class ThoughtNode(BaseModel):
    id: int
    parent_id: Optional[int] = None
    content: Any
    bfs_value: float = 0.0
    dfs_value: Any = None
    depth: int
    children: List[int] = Field(default_factory=list)

class ThoughtTree(BaseModel):
    nodes: Dict[int, ThoughtNode] = Field(default_factory=dict)
    next_id: int = 0

    def add_node(self, content: str, parent_id: Optional[int] = None, bfs_value: float = 0.0, dfs_value: Any = None) -> ThoughtNode:
        """添加思维节点到树中"""
        # 计算深度：如果有父节点，则深度为父节点深度+1；否则为0
        depth = 0
        if parent_id is not None:
            parent_node = self.nodes.get(parent_id)
            if parent_node:
                depth = parent_node.depth + 1

        node = ThoughtNode(
            id=self.next_id,
            parent_id=parent_id,
            content=content,
            depth=depth,
            bfs_value=bfs_value,
            dfs_value=dfs_value
        )
        self.nodes[node.id] = node
        if parent_id is not None:
            self.nodes[parent_id].children.append(node.id)
        self.next_id += 1
        return node

    def get_nodes_at_depth(self, depth: int, return_ids: bool = False):
        """获取指定深度的所有节点"""
        if return_ids:
            return [node.id for node in self.nodes.values() if node.depth == depth]
        return [node for node in self.nodes.values() if node.depth == depth]
    
    def update_node_value(self, node_id: int, bfs_value: float, dfs_value: Any):
        """更新指定节点的值"""
        if node_id in self.nodes:
            if bfs_value is not None:
                self.nodes[node_id].bfs_value = bfs_value 
            if dfs_value is not None:
                self.nodes[node_id].dfs_value = dfs_value
    def get_childrens(self, node_id: int, return_ids: bool = False):
        """获取指定节点的所有子节点"""
        if node_id in self.nodes:
            if return_ids:
                return self.nodes[node_id].children
            return [self.nodes[child_id] for child_id in self.nodes[node_id].children]
        return []
    
    def get_parent(self, node_id: int, return_ids: bool = False):
        """获取指定节点的父节点"""
        if node_id in self.nodes:
            if return_ids:
                return self.nodes[node_id].parent_id
            return self.nodes.get(self.nodes[node_id].parent_id)
        return None
    
    def prune(self, node_id: int):
        """剪枝指定节点及其所有子节点"""
        if node_id in self.nodes:
            # 从父节点中移除当前节点
            parent_id = self.nodes[node_id].parent_id
            if parent_id is not None and parent_id in self.nodes:
                self.nodes[parent_id].children.remove(node_id)
            # 删除子节点
            children = self.nodes[node_id].children.copy()
            for child_id in children:
                self.prune(child_id)
            # 删除当前节点
            del self.nodes[node_id]
    
    def tot_bfs(self, depth: int, b: int):
        """基于广度遍历获取指定深度的所有节点"""
        root_id = self.get_root_id()
        if root_id is None:
            return []
        nodes_at_depth = self.get_nodes_at_depth(depth)
        sorted_nodes_at_depth_top_b = sorted(nodes_at_depth, key=lambda node: node.bfs_value, reverse=True)[:b]
        
        top_b_ids = [node.id for node in sorted_nodes_at_depth_top_b]
        
        for node in nodes_at_depth:
            if node.id not in top_b_ids:
                self.prune(node.id)
                
    def get_highest_bfs_score_node_at_depth(self, depth: int, return_ids: bool = False):
        """返回指定深度的最高分节点或其ID"""
        nodes_at_depth = self.get_nodes_at_depth(depth)
        highest_score_nodes = sorted(nodes_at_depth, key=lambda node: node.bfs_value, reverse=True)
        highest_score_node = highest_score_nodes[0] if highest_score_nodes else None
        
        if highest_score_node:
            if return_ids:
                return highest_score_node.id
            return highest_score_node
        return None
    
    def get_highest_bfs_score_node_in_childerens(self, node_id: int, return_ids: bool = False):
        children_nodes = self.get_childrens(node_id)
        highest_score_nodes = sorted(children_nodes, key=lambda node: node.bfs_value, reverse=True)
        highest_score_node = highest_score_nodes[0] if highest_score_nodes else None
        
        if highest_score_node:
            if return_ids:
                return highest_score_node.id
            return highest_score_node
        return None
                
    def get_current_path(self, node_id: int, return_ids: bool = False):
        result = []
        

        node = self.nodes.get(node_id)
        while node:
            result.append(node)
            node = self.get_parent(node.id)
        result.reverse()  # Reverse the result to get the path from leaf to root
        if return_ids:
            return [node.id for node in result]
        return result
        
        





    def get_root_node(self, return_ids: bool = False):
        """获取根节点的 ID"""
        for node in self.nodes.values():
            if node.parent_id is None:
                if return_ids:
                    return node.id
                return node
        return None
    
    def thought_tree_to_dict(self):
        """将思维树转换为字典"""
        return {node.id: node.model_dump() for node in self.nodes.values()}

if __name__ == "__main__":
    # 测试代码
    # 测试代码
    tree = ThoughtTree()

    # 添加根思维节点（深度 0）
    root = tree.add_node("Root Thought")

    # 添加子思维节点（深度 1）
    child1 = tree.add_node("Child Thought 1", parent_id=root.id, bfs_value=0.1)
    child2 = tree.add_node("Child Thought 2", parent_id=root.id, bfs_value=0.2)

    # 添加孙子思维节点（深度 2）
    grandchild1 = tree.add_node("Grandchild Thought 1", parent_id=child1.id, bfs_value=0.11)
    grandchild2 = tree.add_node("Grandchild Thought 2", parent_id=child1.id, bfs_value=1.12)
    grandchild3 = tree.add_node("Grandchild Thought 3", parent_id=child1.id, bfs_value=2.13)

    
    # # tree.prune(grandchild1.id)
    # print(tree.nodes)
    # tree.tot_bfs(depth=2, b=2)
    # print(tree.nodes)
    
    print(tree.nodes[1].children)
    # # 获取深度为 1 的所有节点
    # depth_1_nodes = tree.get_nodes_at_depth(1)
    # print("Nodes at depth 1:")
    # for node in depth_1_nodes:
    #     print(f"Node ID: {node.id}, Content: {node.content}")

    # # 获取深度为 2 的所有节点
    # depth_2_nodes = tree.get_nodes_at_depth(2)
    # sorted_depth_2_nodes = sorted(depth_2_nodes, key=lambda node: node.value, reverse=True)[:2]
    # print(sorted_depth_2_nodes)
    
    # print("\nNodes at depth 2:")
    # for node in depth_2_nodes:
    #     print(f"Node ID: {node.id}, Content: {node.content}")
        
    