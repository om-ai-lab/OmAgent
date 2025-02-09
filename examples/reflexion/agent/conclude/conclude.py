from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.registry import registry

@registry.register_worker()
class ConcludeTask(BaseWorker):
    """Conclude the workflow by summarizing all attempts"""
    def _run(self):
        last_output = self.input.get('last_output', {})
        iteration = self.input.get('iteration', 1)
        
        return {
            "final_output": last_output,
            "total_iterations": iteration,
            "status": "success" if not last_output.get('needs_another_attempt', False) else "max_iterations_reached"
        } 