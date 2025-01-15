from omagent_core.advanced_components.workflow.dnc.schemas.dnc_structure import \
    TaskTree
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.registry import registry


@registry.register_worker()
class ConstructDncPayload(BaseWorker):
    def _run(self, query: str):
        tree = TaskTree()
        tree.add_node({"task": query})
        return {"dnc_structure": tree.model_dump()}
