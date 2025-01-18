import uuid
from typing import Any, Dict, List

from omagent_core.engine.http.api.metadata_resource_api import \
    MetadataResourceApi
from omagent_core.engine.http.api.task_resource_api import TaskResourceApi
from omagent_core.engine.http.api_client import ApiClient
from omagent_core.engine.http.models import *
from omagent_core.engine.http.models.correlation_ids_search_request import \
    CorrelationIdsSearchRequest
from omagent_core.engine.orkes.orkes_workflow_client import workflow_client
from omagent_core.utils.container import container
from typing_extensions import Optional, Self


class WorkflowExecutor:
    def __init__(self) -> Self:
        self.metadata_client = MetadataResourceApi(
            ApiClient(container.conductor_config)
        )
        self.task_client = TaskResourceApi(ApiClient(container.conductor_config))
        self.workflow_client = workflow_client

    def register_workflow(
        self, workflow: WorkflowDef, overwrite: bool = None
    ) -> object:
        """Create a new workflow definition"""
        kwargs = {}
        if overwrite is not None:
            kwargs["overwrite"] = overwrite
        return self.metadata_client.update1(body=[workflow], **kwargs)

    def start_workflow(self, start_workflow_request: StartWorkflowRequest) -> str:
        """Start a new workflow with StartWorkflowRequest, which allows task to be executed in a domain"""
        return self.workflow_client.start_workflow(
            start_workflow_request=start_workflow_request,
        )

    def start_workflows(
        self, *start_workflow_request: StartWorkflowRequest
    ) -> List[str]:
        """Start multiple instances of workflows.  Note, there is no parallelism implemented in starting so giving a
        very large number can impact the latencies and performance
        """
        workflow_id_list = [""] * len(start_workflow_request)
        for i in range(len(start_workflow_request)):
            workflow_id_list[i] = self.start_workflow(
                start_workflow_request=start_workflow_request[i]
            )
        return workflow_id_list

    def execute_workflow(
        self,
        request: StartWorkflowRequest,
        wait_until_task_ref: str,
        wait_for_seconds: int = 10,
        request_id: str = None,
    ) -> WorkflowRun:
        """Executes a workflow with StartWorkflowRequest and waits for the completion of the workflow or until a
        specific task in the workflow"""
        if request_id is None:
            request_id = str(uuid.uuid4())

        return self.workflow_client.execute_workflow(
            start_workflow_request=request,
            request_id=request_id,
            wait_until_task_ref=wait_until_task_ref,
            wait_for_seconds=wait_for_seconds,
        )

    def execute(
        self,
        name: str,
        version: Optional[int] = None,
        workflow_input: Any = {},
        wait_until_task_ref: str = None,
        wait_for_seconds: int = 10,
        request_id: str = None,
        correlation_id: str = None,
        domain: str = None,
    ) -> WorkflowRun:
        """Executes a workflow with StartWorkflowRequest and waits for the completion of the workflow or until a
        specific task in the workflow"""
        if request_id is None:
            request_id = str(uuid.uuid4())

        request = StartWorkflowRequest()
        request.name = name
        if version:
            request.version = version
        request.input = workflow_input
        request.correlation_id = correlation_id
        if domain is not None:
            request.task_to_domain = {"*": domain}

        return self.workflow_client.execute_workflow(
            start_workflow_request=request,
            request_id=request_id,
            wait_until_task_ref=wait_until_task_ref,
            wait_for_seconds=wait_for_seconds,
        )

    def remove_workflow(self, workflow_id: str, archive_workflow: bool = None) -> None:
        """Removes the workflow permanently from the system"""
        kwargs = {}
        if archive_workflow is not None:
            kwargs["archive_workflow"] = archive_workflow
        return self.workflow_client.delete_workflow(workflow_id=workflow_id, **kwargs)

    def get_workflow(self, workflow_id: str, include_tasks: bool = None) -> Workflow:
        """Gets the workflow by workflow id"""
        kwargs = {}
        if include_tasks is not None:
            kwargs["include_tasks"] = include_tasks
        return self.workflow_client.get_workflow(workflow_id=workflow_id, **kwargs)

    def get_workflow_status(
        self,
        workflow_id: str,
        include_output: bool = None,
        include_variables: bool = None,
    ) -> WorkflowStatus:
        """Gets the workflow by workflow id"""
        kwargs = {}
        if include_output is not None:
            kwargs["include_output"] = include_output
        if include_variables is not None:
            kwargs["include_variables"] = include_variables
        return self.workflow_client.get_workflow_status(
            workflow_id=workflow_id,
            include_output=include_output,
            include_variables=include_variables,
        )

    def search(
        self,
        query_id: str = None,
        start: int = None,
        size: int = None,
        sort: str = None,
        free_text: str = None,
        query: str = None,
        skip_cache: bool = None,
    ) -> ScrollableSearchResultWorkflowSummary:
        """Search for workflows based on payload and other parameters"""
        return self.workflow_client.search(
            start=start, size=size, free_text=free_text, query=query
        )

    def get_by_correlation_ids(
        self,
        workflow_name: str,
        correlation_ids: List[str],
        include_closed: bool = None,
        include_tasks: bool = None,
    ) -> dict[str, List[Workflow]]:
        """Lists workflows for the given correlation id list"""
        return self.workflow_client.get_by_correlation_ids(
            correlation_ids=correlation_ids,
            workflow_name=workflow_name,
            include_tasks=include_tasks,
            include_completed=include_closed,
        )

    def get_by_correlation_ids_and_names(
        self,
        batch_request: CorrelationIdsSearchRequest,
        include_closed: bool = None,
        include_tasks: bool = None,
    ) -> Dict[str, List[Workflow]]:
        """
        Given the list of correlation ids and list of workflow names, find and return workflows Returns a map with
        key as correlationId and value as a list of Workflows When IncludeClosed is set to true, the return value
        also includes workflows that are completed otherwise only running workflows are returned
        """
        return self.workflow_client.get_by_correlation_ids_in_batch(
            batch_request=batch_request,
            include_closed=include_closed,
            include_tasks=include_tasks,
        )

    def pause(self, workflow_id: str) -> None:
        """Pauses the workflow"""
        return self.workflow_client.pause_workflow(workflow_id=workflow_id)

    def resume(self, workflow_id: str) -> None:
        """Resumes the workflow"""
        return self.workflow_client.resume_workflow(workflow_id=workflow_id)

    def terminate(
        self,
        workflow_id: str,
        reason: str = None,
        trigger_failure_workflow: bool = None,
    ) -> None:
        """Terminate workflow execution"""
        return self.workflow_client.terminate_workflow(
            workflow_id=workflow_id,
            reason=reason,
            trigger_failure_workflow=trigger_failure_workflow,
        )

    def restart(self, workflow_id: str, use_latest_definitions: bool = None) -> None:
        """Restarts a completed workflow"""
        return self.workflow_client.restart_workflow(
            workflow_id=workflow_id, use_latest_def=use_latest_definitions
        )

    def retry(self, workflow_id: str, resume_subworkflow_tasks: bool = None) -> None:
        """Retries the last failed task"""
        return self.workflow_client.retry_workflow(
            workflow_id=workflow_id, resume_subworkflow_tasks=resume_subworkflow_tasks
        )

    def rerun(
        self, rerun_workflow_request: RerunWorkflowRequest, workflow_id: str
    ) -> str:
        """Reruns the workflow from a specific task"""
        return self.workflow_client.rerun_workflow(
            rerun_workflow_request=rerun_workflow_request,
            workflow_id=workflow_id,
        )

    def skip_task_from_workflow(
        self,
        workflow_id: str,
        task_reference_name: str,
        skip_task_request: SkipTaskRequest = None,
    ) -> None:
        """Skips a given task from a current running workflow"""
        return self.workflow_client.skip_task_from_workflow(
            workflow_id=workflow_id,
            task_reference_name=task_reference_name,
            request=skip_task_request,
        )

    def update_task(
        self, task_id: str, workflow_id: str, task_output: Dict[str, Any], status: str
    ) -> str:
        """Update a task"""
        task_result = self.__get_task_result(task_id, workflow_id, task_output, status)
        return self.task_client.update_task(
            body=task_result,
        )

    def update_task_by_ref_name(
        self,
        task_output: Dict[str, Any],
        workflow_id: str,
        task_reference_name: str,
        status: str,
    ) -> str:
        """Update a task By Ref Name"""
        return self.task_client.update_task1(
            body=task_output,
            workflow_id=workflow_id,
            task_ref_name=task_reference_name,
            status=status,
        )

    def update_task_by_ref_name_sync(
        self,
        task_output: Dict[str, Any],
        workflow_id: str,
        task_reference_name: str,
        status: str,
    ) -> Workflow:
        """Update a task By Ref Name"""
        return self.task_client.update_task_sync(
            body=task_output,
            workflow_id=workflow_id,
            task_ref_name=task_reference_name,
            status=status,
        )

    def get_task(self, task_id: str) -> str:
        """Get task by Id"""
        return self.task_client.get_task(task_id=task_id)

    def __get_task_result(
        self, task_id: str, workflow_id: str, task_output: Dict[str, Any], status: str
    ) -> TaskResult:
        return TaskResult(
            workflow_instance_id=workflow_id,
            task_id=task_id,
            output_data=task_output,
            status=status,
        )
