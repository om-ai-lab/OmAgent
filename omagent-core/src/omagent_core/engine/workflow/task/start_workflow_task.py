from omagent_core.engine.http.models.start_workflow_request import \
    StartWorkflowRequest
from omagent_core.engine.workflow.task.task import TaskInterface
from omagent_core.engine.workflow.task.task_type import TaskType
from typing_extensions import Self


class StartWorkflowTask(TaskInterface):
    def __init__(
        self,
        task_ref_name: str,
        workflow_name: str,
        start_workflow_request: StartWorkflowRequest,
        version: int = None,
    ) -> Self:
        super().__init__(
            task_reference_name=task_ref_name,
            task_type=TaskType.START_WORKFLOW,
            input_parameters={
                "startWorkflow": {
                    "name": workflow_name,
                    "version": version,
                    "input": start_workflow_request.input,
                    "correlationId": start_workflow_request.correlation_id,
                },
            },
        )
