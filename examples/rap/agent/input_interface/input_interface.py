from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.registry import registry

# Define supported tasks
SUPPORTED_TASKS = {
    'math': "Please input your math problem:"
}

@registry.register_worker()
class InputInterface(BaseWorker):
    """Input interface processor that handles user queries."""

    def _run(self, query=None, *args, **kwargs):
        # Get task selection from user
        task = input(f'\nWelcome to OmAgent RAP! Please select a task type: {list(SUPPORTED_TASKS.keys())} ')
        
        if task not in SUPPORTED_TASKS:
            raise ValueError(f"Unsupported task type: {task}. Must be one of {list(SUPPORTED_TASKS.keys())}")
        
        self.stm(self.workflow_instance_id)['task'] = task 

        # Use query parameter if provided, otherwise get user input
        data_input = query if query else input(SUPPORTED_TASKS[task])
        
        # Store input in STM and return
        self.stm(self.workflow_instance_id)['data_input'] = data_input
        return {"query": data_input} 