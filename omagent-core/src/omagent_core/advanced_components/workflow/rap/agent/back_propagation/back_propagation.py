from pathlib import Path
from typing import List
import math
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.models.llms.prompt import PromptTemplate
from omagent_core.utils.registry import registry
from pydantic import Field

CURRENT_PATH = Path(__file__).parents[0]

@registry.register_worker()
class BackPropagation(BaseWorker):
    """Back propagation worker that updates node values"""

    def _run(self, *args, **kwargs):
        path = self.stm(self.workflow_instance_id)['selected_path']
        rewards = []
        cum_reward = -math.inf

        # Update rewards for each node in path
        for node in reversed(path):
            rewards.append(node.reward)
            cum_reward = self.cum_reward(rewards[::-1])
            node.cum_rewards.append(cum_reward)

        return {}

    def cum_reward(self, rewards):
        """Calculate cumulative reward"""
        return sum(rewards) 