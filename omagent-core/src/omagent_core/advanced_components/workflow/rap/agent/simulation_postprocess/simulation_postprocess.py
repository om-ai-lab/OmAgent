from pathlib import Path
from typing import List
import numpy as np
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.models.llms.prompt import PromptTemplate
from omagent_core.utils.registry import registry
from pydantic import Field

CURRENT_PATH = Path(__file__).parents[0]

@registry.register_worker()
class SimulationPostProcess(BaseWorker):
    """Simulation post-process worker that handles simulation results"""

    def _run(self, *args, **kwargs):
        depth_limit = kwargs.get('depth_limit', 5)

        node = self.stm(self.workflow_instance_id)['selected_path'][-1]
        
        # Check if we should finish simulation
        if node.depth >= depth_limit or node.children is None:
            self.stm(self.workflow_instance_id)['in_simulation'] = False
            self.callback.send_answer(
                self.workflow_instance_id, 
                msg=f'Done.{node.action}\n{node.state}'
            )
            return {"finish": True}

        # Select next node based on fast rewards
        fast_rewards = [child.fast_reward for child in node.children]
        
        # Log rewards for debugging
        for c, r in zip(node.children, fast_rewards):
            self.callback.send_answer(
                self.workflow_instance_id, 
                msg=f'{c.action}\n{r}'
            )

        # Select node with highest reward
        node = node.children[np.argmax(fast_rewards)]
        self.callback.send_answer(
            self.workflow_instance_id, 
            msg=f'Choose node: {node.action}'
        )

        # Update selected path
        self.stm(self.workflow_instance_id)['selected_path'] = \
            self.stm(self.workflow_instance_id)['selected_path'] + [node]

        return {"finish": False} 