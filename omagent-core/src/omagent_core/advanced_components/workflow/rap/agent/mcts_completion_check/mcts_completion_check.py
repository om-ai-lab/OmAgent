from pathlib import Path
from typing import List
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.models.llms.prompt import PromptTemplate
from omagent_core.utils.registry import registry
from pydantic import Field

CURRENT_PATH = Path(__file__).parents[0]

@registry.register_worker()
class MCTSCompletionCheck(BaseWorker):
    """MCTS completion check worker that determines when to stop MCTS"""

    def _run(self, *args, **kwargs):
        mcts_iter_num = kwargs.get('mcts_iter_num', 10)

        # Initialize or increment loop counter
        if self.stm(self.workflow_instance_id).get("loop_index", None) is None:
            self.stm(self.workflow_instance_id)["loop_index"] = 0
            self.stm(self.workflow_instance_id)['candidates_path'] = []
            
        self.stm(self.workflow_instance_id)["loop_index"] += 1

        # Store current path as candidate if it exists and ends in a terminal state
        path = self.stm(self.workflow_instance_id)['selected_path']
        if path and path[-1].is_terminal:
            if path not in self.stm(self.workflow_instance_id)['candidates_path']:
                self.stm(self.workflow_instance_id)['candidates_path'] = self.stm(self.workflow_instance_id)['candidates_path'] + [path]

        # Check if we've reached max iterations
        finish = (self.stm(self.workflow_instance_id)["loop_index"] >= mcts_iter_num or 
                 len(self.stm(self.workflow_instance_id)['candidates_path']) > 0)

        return {"finish": finish} 