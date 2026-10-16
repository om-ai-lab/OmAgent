from pathlib import Path
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.registry import registry
import re

@registry.register_worker()
class Conclude(BaseWorker):
    """Worker that formats and presents the final reasoning output"""

    def _run(self, final_answer: str, *args, **kwargs):
        """Format and present the final reasoning results.
        
        Args:
            final_answer: The final answer from RAP
            
        Returns:
            dict: Contains the extracted short answer
        """
        
        # Extract the short answer using regex pattern
        matches = re.findall(r'the answer is\s+([^.]+)\.', final_answer.lower())
        short_answer = matches[-1] if matches else final_answer
        
        # Send formatted answer through callback
        self.callback.send_answer(
            agent_id=self.workflow_instance_id,
            msg=f"Final conclusion: {short_answer}"
        )

        return {"short_answer": short_answer} 