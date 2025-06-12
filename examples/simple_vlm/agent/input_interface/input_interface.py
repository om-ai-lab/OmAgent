from pathlib import Path

from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.general import read_image
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry

CURRENT_PATH = Path(__file__).parents[0]


@registry.register_worker()
class InputInterface(BaseWorker):

    def _run(self, *args, **kwargs):
        # Read user input through configured input interface
        user_instruction = "test mcp"

        return {"user_instruction": user_instruction}
