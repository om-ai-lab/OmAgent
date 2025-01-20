from omagent_core.advanced_components.workflow.ToT.schemas.ToT_structure import ThoughtTree
from omagent_core.utils.registry import registry
from omagent_core.engine.worker.base import BaseWorker

@registry.register_worker()
class ThoughtDecomposition(BaseWorker):
    """
    最基础的任务设置，
    
    尝试模型直接分解任务
    
    """
    
    def _run(self, qid: str, requirements: str, problem: str):
        try:
            record = {
                "qid": qid,
                "problem": problem,
                "last_output": None,
                "prompt_tokens": 0,
                "completion_tokens": 0,
            }
            self.stm(self.workflow_instance_id)['record'] = record
            
            if self.stm(self.workflow_instance_id).get('thought_tree', None) is None:
                thought_tree = ThoughtTree()
                thought_tree.add_node(thought="", parent_id=None)
                
                self.stm(self.workflow_instance_id)['requirements'] = requirements
                self.stm(self.workflow_instance_id)['problem'] = problem
                
                self.stm(self.workflow_instance_id)['thought_tree'] = thought_tree
                self.stm(self.workflow_instance_id)['current_depth'] = 0
                self.stm(self.workflow_instance_id)['current_step'] = 0
                self.stm(self.workflow_instance_id)['current_node_id'] = 0
                
                self.stm(self.workflow_instance_id)['search_type'] = self.params['search_type']
                self.stm(self.workflow_instance_id)['dfs_best'] = {"id": 0, "score": 0} 
                self.stm(self.workflow_instance_id)['max_depth'] = int(self.params['max_depth'])
                self.stm(self.workflow_instance_id)['max_steps'] = int(self.params['max_steps'])
                self.stm(self.workflow_instance_id)['b'] = int(self.params['b'])
                
            self.callback.info(
                agent_id=self.workflow_instance_id,
                progress=f"Thought Decomposition",
                message=f"\nrecord: {record}\nsearch_type: {self.params['search_type']}\nmax_depth: {self.params['max_depth']}\nmax_steps: {self.params['max_steps']}\nb: {self.params['b']}",
            )
            
        except Exception as e:
            self.callback.error(
                agent_id=self.workflow_instance_id,
                message=f"Error occurred: {str(e)}"
            )
            







        