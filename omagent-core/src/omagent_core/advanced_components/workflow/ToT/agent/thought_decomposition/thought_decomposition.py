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
    
    

    def _run(self, query: str, tot_parameters: dict):

        if self.stm(self.workflow_instance_id).get('thought_tree', None) is None:
            thought_tree = ThoughtTree()
            thought_tree.add_node(content=query, infer_input=query, parent_id=None)
            self.stm(self.workflow_instance_id)['thought_tree'] = thought_tree
            self.stm(self.workflow_instance_id)['current_depth'] = 0
            self.stm(self.workflow_instance_id)['current_node_id'] = 0
            self.stm(self.workflow_instance_id)['max_depth'] = tot_parameters['decomposition_parameters']['max_depth']
            self.stm(self.workflow_instance_id)['max_steps'] = tot_parameters['decomposition_parameters']['max_steps']
            self.stm(self.workflow_instance_id)['generator_parameters'] = tot_parameters['generator_parameters']
            self.stm(self.workflow_instance_id)['evaluator_parameters'] = tot_parameters['evaluator_parameters']
            self.stm(self.workflow_instance_id)['search_parameters'] = tot_parameters['search_parameters']
        
        # self.print_setting(tot_parameters, query)



    def print_setting(self, tot_parameters: dict, query: str):
        thought_tree = self.stm(self.workflow_instance_id)['thought_tree']
        current_depth = self.stm(self.workflow_instance_id)['current_depth']
        current_node_id = self.stm(self.workflow_instance_id)['current_node_id']
        max_depth = self.stm(self.workflow_instance_id)['max_depth']
        max_steps = self.stm(self.workflow_instance_id)['max_steps']
        generator_parameters = self.stm(self.workflow_instance_id)['generator_parameters']
        evaluator_parameters = self.stm(self.workflow_instance_id)['evaluator_parameters']
        search_parameters = self.stm(self.workflow_instance_id)['search_parameters']
        
        
        print('\n'+'--show--setting--'*10)
        
        print(f'query: {query}')
        print(f'tot_parameters: {tot_parameters}')

        print('\n'+'--show--setting--'*10)
        
        print('\n'+'--show--stm--'*10)

        print(f'thought_tree: {thought_tree}')
        print(f'current_depth: {current_depth}')
        print(f'current_node_id: {current_node_id}')
        print(f'max_depth: {max_depth}')
        print(f'max_steps: {max_steps}')
        print(f'generator_parameters: {generator_parameters}')
        print(f'evaluator_parameters: {evaluator_parameters}')
        print(f'search_parameters: {search_parameters}')

        print('\n'+'--show--stm--'*10)

        # # Check the structure and content of the parameters and query
        # if not isinstance(tot_parameters, dict):
        #     raise ValueError("tot_parameters must be a dictionary")
        # required_keys = ["decomposition_parameters", "generator_parameters", "evaluator_parameters", "search_parameters"]
        # for key in required_keys:
        #     if key not in tot_parameters:
        #         raise ValueError(f"Missing required key: {key} in tot_parameters")
        
        # if not isinstance(query, str):
        #     raise ValueError("query must be a string")
        # if not query:
        #     raise ValueError("query cannot be empty")



        




