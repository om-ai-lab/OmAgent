from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class ThoughtNode(BaseModel):
    id: int
    parent_id: Optional[int] = None
    thought: Any
    value: float = 0.0
    depth: int
    children: List[int] = Field(default_factory=list)

class ThoughtTree(BaseModel):
    nodes: Dict[int, ThoughtNode] = Field(default_factory=dict)
    next_id: int = 0

    def add_node(self, thought: Any, parent_id: Optional[int] = None, value: float = 0.0) -> ThoughtNode:
        """Add a thought node to the tree"""
        # Calculate depth: if there's a parent node, depth = parent's depth + 1; otherwise 0
        depth = 0
        if parent_id is not None:
            parent_node = self.nodes.get(parent_id)
            if parent_node:
                depth = parent_node.depth + 1

        node = ThoughtNode(
            id=self.next_id,
            parent_id=parent_id,
            thought=thought,
            depth=depth,
            value=value
        )
        self.nodes[node.id] = node
        if parent_id is not None:
            self.nodes[parent_id].children.append(node.id)
        self.next_id += 1
        return node

    def get_nodes_at_depth(self, depth: int, return_ids: bool = False):
        """Get all nodes at specified depth"""
        if return_ids:
            return [node.id for node in self.nodes.values() if node.depth == depth]
        return [node for node in self.nodes.values() if node.depth == depth]
                
    def get_childrens(self, node_id: int, return_ids: bool = False):
        """Get all child nodes of the specified node"""
        if node_id in self.nodes:
            if return_ids:
                return self.nodes[node_id].children
            return [self.nodes[child_id] for child_id in self.nodes[node_id].children]
        return []
    
    def get_parent(self, node_id: int, return_ids: bool = False):
        """Get the parent node of the specified node"""
        if node_id in self.nodes:
            if return_ids:
                return self.nodes[node_id].parent_id
            return self.nodes.get(self.nodes[node_id].parent_id)
        return None
    
    def prune(self, node_id: int):
        """Prune the specified node and all its children"""
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
                
    def get_top_n_score_nodes(self, node_id: int = None, depth: int = None, sort_region: str = 'children', n: int = 1, return_ids: bool = False):
        """
        Return the top n nodes or their IDs with the highest scores among children of specified depth or node.
        sort_region: 'children' or 'depth'
        """
        if sort_region == 'children':
            nodes = self.get_childrens(node_id)
        elif sort_region == 'depth':
            nodes = self.get_nodes_at_depth(depth)
        else:
            raise ValueError("Invalid sort_region. It must be 'children' or 'depth'.")
        
        key = lambda node: node.value
        
        top_n_score_nodes = sorted(nodes, key=key, reverse=True)
        print(n, len(top_n_score_nodes))
        if n > len(top_n_score_nodes):
            n = len(top_n_score_nodes)
        top_n_score_nodes = top_n_score_nodes[:n]
        
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
        
    def get_current_thought_chain(self, node_id: int):
        """Get the thought content of nodes in the current path"""
        current_path = self.get_current_path(node_id)
        thought_chain = ""
        for node in current_path:
            thought_chain += f"{node.thought}\n"
        return thought_chain

    def get_current_path_score(self, node_id: int):
        """Get the score of nodes in the current path"""
        current_path = self.get_current_path(node_id)
        score = 0
        for node in current_path:
            score += node.value
        return score

    def get_root_node(self, return_ids: bool = False):
        """Get the root node ID"""
        for node in self.nodes.values():
            if node.parent_id is None:
                if return_ids:
                    return node.id
                return node
        return None
    
    def thought_tree_to_dict(self):
        """Convert thought tree to dictionary"""
        return {node.id: node.model_dump() for node in self.nodes.values()}

        
    