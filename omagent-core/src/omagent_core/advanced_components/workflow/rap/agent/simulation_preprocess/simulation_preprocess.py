from pathlib import Path
from typing import List
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.models.llms.prompt import PromptTemplate
from omagent_core.utils.registry import registry
from pydantic import Field

CURRENT_PATH = Path(__file__).parents[0]

@registry.register_worker()
class SimulationPreProcess(BaseWorker):
    """Simulation pre-process worker that prepares for simulation phase"""

    def _run(self, *args, **kwargs):
        # Mark that we're entering simulation phase
        self.stm(self.workflow_instance_id)['in_simulation'] = True
        self.callback.send_answer(self.workflow_instance_id, msg='start simulation')
        return {} 