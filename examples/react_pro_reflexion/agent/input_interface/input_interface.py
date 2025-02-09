from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.registry import registry
from pydantic import Field

@registry.register_worker()
class InputInterface(BaseWorker):
    """Input interface worker for handling user input"""
    
    def _run(self, *args, **kwargs):
        """Process user input"""
        query = input("Please enter your question: ")
        previous_attempts = input("Please enter previous attempts (or press Enter to skip): ")
        
        return {
            "query": query,
            "previous_attempts": previous_attempts,
            "id": ""  # Optional ID field
        } 