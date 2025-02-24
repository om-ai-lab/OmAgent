from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.registry import registry

@registry.register_worker()
class ReactOutput(BaseWorker):
    """Simple worker that passes through the final action output for React workflow"""
    
    def _run(self, action_output: str,*args, **kwargs):
        """Simply return the action output with any necessary state"""
        
        # state = self.stm(self.workflow_instance_id)
        state = self.stm(self.workflow_instance_id)
        query = state.get('query', '')
        id = state.get('id', '')
        token_usage = state.get('token_usage', {})
        context = state.get('context', '')
        is_final = action_output.get('is_final', False)
        state['output'] = action_output
        return {
            'output': action_output,
            'context': context,
            'query': query,
            'id': id,
            'token_usage': token_usage,
            'is_final': is_final
        } 