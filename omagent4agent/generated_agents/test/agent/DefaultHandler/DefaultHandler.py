from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.registry import registry

@registry.register_worker()
class DefaultHandler(BaseWorker):
    """
    Worker to handle the default case of the SWITCH statement.
    """

    def _run(self, *args, **kwargs) -> None:
        # Logic for handling the default case
        print("Handling the default case of the SWITCH statement.")

        # Since there are no specific output requirements for DefaultHandler in the workflow,
        # we do not need to return any output here.
        pass