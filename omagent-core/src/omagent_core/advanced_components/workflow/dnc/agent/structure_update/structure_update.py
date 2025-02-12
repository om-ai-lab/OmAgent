from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.registry import registry


@registry.register_worker()
class StructureUpdate(BaseWorker):
    def _run(self, dnc_structure: dict, last_output: str=None, *args, **kwargs):
        stm_data = self.stm(self.workflow_instance_id)
        stm_dnc_structure = stm_data.get("dnc_structure", None)
        stm_last_output = stm_data.get("last_output", None)
        if stm_dnc_structure is None:
            stm_dnc_structure = dnc_structure
            stm_data["dnc_structure"] = stm_dnc_structure
            self.stm(self.workflow_instance_id)["dnc_structure"] = stm_dnc_structure
        if stm_last_output is None:
            stm_last_output = last_output
            stm_data["last_output"] = stm_last_output
            self.stm(self.workflow_instance_id)["last_output"] = stm_last_output

        return {"dnc_structure": stm_dnc_structure, "last_output": stm_last_output}
