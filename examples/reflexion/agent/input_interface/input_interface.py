from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.registry import registry
from pydantic import Field

@registry.register_worker()
class InputInterface(BaseWorker):
    """Input interface worker for handling user input"""
    
    def _run(self, *args, **kwargs):
        """Process user input"""
        query = input("Please enter your question: ")
        
        return {
            "query": query,
            "id": ""  # Optional ID field
        } 