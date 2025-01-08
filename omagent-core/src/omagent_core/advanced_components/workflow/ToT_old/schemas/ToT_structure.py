from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class ThoughtNode(BaseModel):
    id: int
    parent_id: Optional[int] = None
    content: Any
    next_step_input: Any
    generation_value: float = 0.0
    evaluation_value: float = 0.0
    depth: int
    children: List[int] = Field(default_factory=list)

class ThoughtTree(BaseModel):
    nodes: Dict[int, ThoughtNode] = Field(default_factory=dict)
    next_id: int = 0

    def add_node(self, content: Any, next_step_input: Any, parent_id: Optional[int] = None, evaluation_value: float = 0.0, generation_value: float = 0.0) -> ThoughtNode:
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
            next_step_input=next_step_input,
            depth=depth,
            evaluation_value=evaluation_value,
            generation_value=generation_value
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
                
    def get_top_n_score_nodes(self, node_id: int = None, depth: int = None, sort_region: str = 'children', score_type: str = 'evaluation', n: int = 1, return_ids: bool = False):
        """
        返回指定深度或节点的子节点中最高分数的前n个节点或其ID。
        sort_region: 'children' or 'depth'
        score_type: 'evaluation' or 'generation'
        """
        if sort_region == 'children':
            nodes = self.get_childrens(node_id)
        elif sort_region == 'depth':
            nodes = self.get_nodes_at_depth(depth)
        else:
            raise ValueError("Invalid sort_region. It must be 'children' or 'depth'.")
        
        if score_type == 'evaluation':
            key = lambda node: node.evaluation_value
        elif score_type == 'generation':
            key = lambda node: node.generation_value
        else:
            raise ValueError("Invalid score_type. It must be 'evaluation' or 'generation'.")
        
        top_n_score_nodes = sorted(nodes, key=key, reverse=True)[:n]
        
        if return_ids:
            return [node.id for node in top_n_score_nodes]
        return top_n_score_nodes
                
    def get_current_path(self, node_id: int, return_ids: bool = False):
        result = []
        
        node = self.nodes[node_id]
        while node:
            result.append(node)
            node = self.get_parent(node.id)
        result.reverse()  # Reverse the result to get the path from leaf to root
        if return_ids:
            return [node.id for node in result]
        return result
        
    def get_current_path_contents(self, node_id: int):
        """获取指定节点的当前路径的节点内容"""
        current_path = self.get_current_path(node_id)
        contents = ""
        for node in current_path:
            contents += f"{node.content}\n"
        return contents





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
    root = tree.add_node("Root Thought", infer_input="Root Thought", parent_id=None, evaluation_value=0.0)

    # 添加子思维节点（深度 1）
    child1 = tree.add_node("Child Thought 1", infer_input="Child Thought 1", parent_id=root.id, evaluation_value=0.1)
    child2 = tree.add_node("Child Thought 2", infer_input="Child Thought 2", parent_id=root.id, evaluation_value=0.2)

    # 添加孙子思维节点（深度 2）
    grandchild1 = tree.add_node("Grandchild Thought 1", infer_input="Grandchild Thought 1", parent_id=child1.id, evaluation_value=0.11)
    grandchild2 = tree.add_node("Grandchild Thought 2", infer_input="Grandchild Thought 2", parent_id=child1.id, evaluation_value=1.12)
    grandchild3 = tree.add_node("Grandchild Thought 3", infer_input="Grandchild Thought 3", parent_id=child1.id, evaluation_value=2.13)

    
    # # tree.prune(grandchild1.id)
    # print(tree.nodes)
    # tree.tot_bfs(depth=2, b=2)
    # print(tree.nodes)
    
    print(tree.nodes[1].children)
    best_node_id = tree.get_top_n_score_nodes(depth=2, sort_region='depth', score_type='evaluation', n=1, return_ids=True)
    print('-'*100)
    print(best_node_id)
    print('-'*100)
    current_path = tree.get_current_path(node_id=best_node_id[0], return_ids=True)
    print(current_path)
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
        
    