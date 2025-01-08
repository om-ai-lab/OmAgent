from pathlib import Path
from typing import List
import json
from omagent_core.advanced_components.workflow.ToT.schemas.ToT_structure import ThoughtTree

from omagent_core.utils.registry import registry
from omagent_core.engine.worker.base import BaseWorker


@registry.register_worker()
class ThoughtDecomposition(BaseWorker):
    """
    最基础的任务设置，
    
    尝试模型直接分解任务
    
    """
    
    def _run(self, query: str):
        # print(self.params)
        if self.stm(self.workflow_instance_id).get('thought_tree', None) is None:
            thought_tree = ThoughtTree()
            thought_tree.add_node(content=query, infer_input=query, parent_id=None)
            self.stm(self.workflow_instance_id)['thought_tree'] = thought_tree
            self.stm(self.workflow_instance_id)['current_depth'] = 0
            self.stm(self.workflow_instance_id)['current_node_id'] = 0
            self.stm(self.workflow_instance_id)['search_type'] = self.params['search_type']
            self.stm(self.workflow_instance_id)['max_depth'] = self.params['max_depth']
            self.stm(self.workflow_instance_id)['max_steps'] = self.params['max_steps']

        # print('-----'*10+'tot_decompose'+'-----'*10)
        # print(f'thought_tree: {self.stm(self.workflow_instance_id)["thought_tree"]}')
        # print(f'current_depth: {self.stm(self.workflow_instance_id)["current_depth"]}')
        # print(f'current_node_id: {self.stm(self.workflow_instance_id)["current_node_id"]}')
        # print(f'max_depth: {self.stm(self.workflow_instance_id)["max_depth"]}')
        # print(f'max_steps: {self.stm(self.workflow_instance_id)["max_steps"]}')
        # print('-----'*10+'tot_decompose'+'-----'*10)
        message = ''
        for key, value in self.params.items():
            message += f'{key}: {value}\n'
        self.callback.info(
            agent_id=self.workflow_instance_id,
            progress=f"Thought Decomposition",
            message='\n'+message,
        )





        




