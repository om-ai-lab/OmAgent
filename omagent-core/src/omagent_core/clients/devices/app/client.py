from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow

class AppClient:
    def __init__(self, interactor: ConductorWorkflow, processor: ConductorWorkflow) -> None:
        self._interactor = interactor
        self._processor = processor
        
    