from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.registry import registry

@registry.register_worker()
class ReactOutput(BaseWorker):
    """Simple worker that passes through the final action output for React workflow"""
    
    def _run(self, action_output: str, workflow_id: str, *args, **kwargs):
        """Simply return the action output with any necessary state"""
        
        state = self.stm(workflow_id)
        query = state.get('query', '')
        id = state.get('id', '')
        token_usage = state.get('token_usage', {})
        
        return {
            'output': action_output,
            'query': query,
            'id': id,
            'token_usage': token_usage
        } 