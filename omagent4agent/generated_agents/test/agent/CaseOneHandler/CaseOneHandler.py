from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.registry import registry
from omagent_core.utils.logger import logging

@registry.register_worker()
class CaseOneHandler(BaseWorker):
    """
    Worker to handle the first case of the SWITCH statement.
    """

    def _run(self, *args, **kwargs) -> None:
        # Logic for handling the first case
        logging.info("Handling the first case of the SWITCH statement.")
