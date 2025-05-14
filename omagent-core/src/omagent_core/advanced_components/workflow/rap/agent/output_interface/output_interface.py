from pathlib import Path
from typing import List
import random
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.models.llms.prompt import PromptTemplate
from omagent_core.utils.registry import registry
from pydantic import Field

CURRENT_PATH = Path(__file__).parents[0]

@registry.register_worker()
class OutputInterface(BaseWorker):
    """Output interface worker that formats and returns final results"""

    def format_output_math(self, path):
        """Format output for math problems"""
        question = self.stm(self.workflow_instance_id)['tree'].data_input
        question_info = f"Question: {question}\n"
        
        for i, n in enumerate(path):
            if i == 0:  # Skip root node
                continue
            question_info += f"Question 1.{i}: {n.action}\n"
            question_info += f"Answer 1.{i}: {n.state}\n"
            
        return question_info

    def _run(self, *args, **kwargs):
        candidates_path = self.stm(self.workflow_instance_id)['candidates_path']
        
        if not candidates_path:
            error_msg = "No valid reasoning paths found. Please try again."
            self.callback.send_answer(self.workflow_instance_id, msg=error_msg)
            return {"final_answer": error_msg}
        
        # Select path with highest cumulative reward
        path = max(candidates_path, 
                  key=lambda p: max((n.cum_rewards if n.cum_rewards else [0]) for n in p))
        
        # Get task-specific output formatter
        task = self.stm(self.workflow_instance_id)['task']
        format_output = getattr(self, f"format_output_{task}", None)
        
        # Format and send output
        output = format_output(path)
        self.callback.send_answer(self.workflow_instance_id, msg=output)

        return {"final_answer": output} 