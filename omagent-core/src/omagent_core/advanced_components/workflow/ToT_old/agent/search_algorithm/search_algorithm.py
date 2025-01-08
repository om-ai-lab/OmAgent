from pathlib import Path
from typing import List

from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.utils.registry import registry
from omagent_core.models.llms.schemas import Message, Content
from omagent_core.utils.general import encode_image
from omagent_core.models.llms.prompt.parser import StrParser
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.container import container
from omagent_core.models.llms.prompt.prompt import PromptTemplate
from pydantic import Field
from typing import List
# from .prompts import *
# from .utils import *

CURRENT_PATH = Path(__file__).parents[0]

# def completion_check(workflow_instance_id: str):

'''
加一个判断任务是否结束

'''
@registry.register_worker()
class SearchAlgorithm(BaseWorker):
    
    
    
    
    def _run(self, *args, **kwargs):
        thought_tree = self.stm(self.workflow_instance_id).get('thought_tree', None)
        current_depth = self.stm(self.workflow_instance_id).get('current_depth', None)

        max_depth = self.stm(self.workflow_instance_id).get('max_depth', None)
        max_step = self.stm(self.workflow_instance_id).get('max_step', None)
        
        current_node_id = self.stm(self.workflow_instance_id).get('current_node_id', None)
        
        search_parameters = self.stm(self.workflow_instance_id).get('search_parameters', None)
        search_type = search_parameters.get('search_type', None)
        
        
        if search_type == "bfs":
            b = search_parameters.get('b', None)
            current_nodes_ids = thought_tree.get_nodes_at_depth(current_depth, return_ids=True)
            top_b_nodes_ids = thought_tree.get_top_n_score_nodes(depth=current_depth, sort_region='depth', score_type='evaluation', n=b, return_ids=True)
            for node_id in current_nodes_ids:
                if node_id not in top_b_nodes_ids:
                    thought_tree.prune(node_id)
        elif search_type == "dfs":
            current_node_score = thought_tree.nodes[current_node_id].evaluation_value
            if current_node_score < 0:
                prune_id = current_node_id
                parent_id = thought_tree.get_parent(current_node_id, return_ids=True)
                thought_tree.prune(prune_id)
                while thought_tree.get_childrens(parent_id) == []:
                    prune_id = parent_id
                    parent_id = thought_tree.get_parent(parent_id, return_ids=True)
                    thought_tree.prune(prune_id)
                    current_depth -= 1
                current_node_id = thought_tree.get_top_n_score_nodes(node_id=parent_id, sort_region='children', score_type='evaluation', n=1, return_ids=True)
                
    
                
            
            
        print('-'*100)
        print(thought_tree.nodes)
        print('-'*100)
        
        self.stm(self.workflow_instance_id)['thought_tree'] = thought_tree
        self.stm(self.workflow_instance_id)['current_node_id'] = current_node_id
        self.stm(self.workflow_instance_id)['current_depth'] = current_depth
        
        if current_depth >= max_depth:
            best_node_id = thought_tree.get_top_n_score_nodes(depth=current_depth, sort_region='depth', score_type='evaluation', n=1, return_ids=True)
            print('-'*100)
            print(best_node_id)
            print('-'*100)
            current_path = thought_tree.get_current_path(node_id=best_node_id[0])
            self.callback.send_answer(self.workflow_instance_id, msg=current_path)
            return {
                "finish": True,
                "best_path": current_path
                }
        else:
            return {
                "finish": False,
                }
            
            
            
    