from typing import List, Optional

from omagent_core.engine.configuration.configuration import Configuration
from omagent_core.engine.http.models import (
    ScrollableSearchResultWorkflowSummary, SkipTaskRequest, WorkflowStatus)
from omagent_core.engine.http.models.correlation_ids_search_request import \
    CorrelationIdsSearchRequest
from omagent_core.engine.http.models.rerun_workflow_request import \
    RerunWorkflowRequest
from omagent_core.engine.http.models.start_workflow_request import \
    StartWorkflowRequest
from omagent_core.engine.http.models.workflow import Workflow
from omagent_core.engine.http.models.workflow_run import WorkflowRun
from omagent_core.engine.http.models.workflow_state_update import \
    WorkflowStateUpdate
from omagent_core.engine.http.models.workflow_test_request import \
    WorkflowTestRequest
from omagent_core.engine.orkes.orkes_base_client import OrkesBaseClient
from omagent_core.engine.workflow_client import WorkflowClient
from omagent_core.utils.container import container
import os

class OrkesWorkflowClient(OrkesBaseClient, WorkflowClient):
    def __init__(self, configuration: Configuration):
        super(OrkesWorkflowClient, self).__init__(configuration)

    def check_connection(self) -> bool:
        """Check if the connection to Conductor server is valid"""
        self.metadataResourceApi.get_all_workflows()

    def start_workflow_by_name(
        self,
        name: str,
        input: dict[str, object],
        version: Optional[int] = None,
        **kwargs
    ) -> str:
        start_workflow_request = StartWorkflowRequest(
            name=name, version=version, input=input, **kwargs
        )

        return self.start_workflow(start_workflow_request)

    def start_workflow(self, start_workflow_request: StartWorkflowRequest) -> str:
        return self.workflowResourceApi.start_workflow(start_workflow_request)

    def execute_workflow(
        self,
        start_workflow_request: StartWorkflowRequest,
        request_id: str = None,
        wait_until_task_ref: Optional[str] = None,
        wait_for_seconds: int = 30,
    ) -> WorkflowRun:

        return self.workflowResourceApi.execute_workflow(
            body=start_workflow_request,
            request_id=request_id,
            version=start_workflow_request.version,
            name=start_workflow_request.name,
            wait_until_task_ref=wait_until_task_ref,
            wait_for_seconds=wait_for_seconds,
        )

    def pause_workflow(self, workflow_id: str):
        self.workflowResourceApi.pause_workflow(workflow_id)

    def resume_workflow(self, workflow_id: str):
        self.workflowResourceApi.resume_workflow(workflow_id)

    def restart_workflow(
        self, workflow_id: str, use_latest_def: Optional[bool] = False
    ):
        kwargs = {}
        if use_latest_def:
            kwargs["use_latest_definitions"] = use_latest_def
        self.workflowResourceApi.restart(workflow_id, **kwargs)

    def rerun_workflow(
        self, workflow_id: str, rerun_workflow_request: RerunWorkflowRequest
    ) -> str:
        rerun_workflow_request.re_run_from_workflow_id = workflow_id
        return self.workflowResourceApi.rerun(rerun_workflow_request, workflow_id)

    def retry_workflow(
        self, workflow_id: str, resume_subworkflow_tasks: Optional[bool] = False
    ):
        kwargs = {}
        if resume_subworkflow_tasks:
            kwargs["resume_subworkflow_tasks"] = resume_subworkflow_tasks
        self.workflowResourceApi.retry(workflow_id, **kwargs)

    def terminate_workflow(
        self,
        workflow_id: str,
        reason: Optional[str] = None,
        trigger_failure_workflow: bool = False,
    ):
        kwargs = {}
        if reason:
            kwargs["reason"] = reason
        if trigger_failure_workflow:
            kwargs["trigger_failure_workflow"] = trigger_failure_workflow
        self.workflowResourceApi.terminate(workflow_id, **kwargs)

    def get_workflow(
        self, workflow_id: str, include_tasks: Optional[bool] = True
    ) -> Workflow:
        kwargs = {}
        if include_tasks:
            kwargs["include_tasks"] = include_tasks
        return self.workflowResourceApi.get_execution_status(workflow_id, **kwargs)

    def get_workflow_status(
        self,
        workflow_id: str,
        include_output: bool = None,
        include_variables: bool = None,
    ) -> WorkflowStatus:
        if os.getenv("OMAGENT_MODE") == "lite":
            return WorkflowStatus(status="RUNNING")
        kwargs = {}
        if include_output is not None:
            kwargs["include_output"] = include_output
        if include_variables is not None:
            kwargs["include_variables"] = include_variables
        return self.workflowResourceApi.get_workflow_status_summary(
            workflow_id, **kwargs
        )

    def delete_workflow(
        self, workflow_id: str, archive_workflow: Optional[bool] = True
    ):
        self.workflowResourceApi.delete(workflow_id, archive_workflow=archive_workflow)

    def skip_task_from_workflow(
        self, workflow_id: str, task_reference_name: str, request: SkipTaskRequest
    ):
        self.workflowResourceApi.skip_task_from_workflow(
            workflow_id, task_reference_name, request
        )

    def test_workflow(self, test_request: WorkflowTestRequest) -> Workflow:
        return self.workflowResourceApi.test_workflow(test_request)

    def search(
        self,
        start: int = 0,
        size: int = 100,
        free_text: str = "*",
        query: str = None,
        query_id: str = None,
    ) -> ScrollableSearchResultWorkflowSummary:
        args = {
            "start": start,
            "size": size,
            "free_text": free_text,
            "query": query,
            "query_id": query_id,
        }
        return self.workflowResourceApi.search(**args)

    def get_by_correlation_ids_in_batch(
        self,
        batch_request: CorrelationIdsSearchRequest,
        include_completed: bool = False,
        include_tasks: bool = False,
    ) -> dict[str, List[Workflow]]:
        """Given the list of correlation ids and list of workflow names, find and return workflows
        Returns a map with key as correlationId and value as a list of Workflows
        When IncludeClosed is set to true, the return value also includes workflows that are completed otherwise only running workflows are returned
        """
        kwargs = {}

        kwargs["body"] = batch_request
        if include_tasks:
            kwargs["include_tasks"] = include_tasks
        if include_completed:
            kwargs["include_closed"] = include_completed
        return self.workflowResourceApi.get_workflows_by_correlation_id_in_batch(
            **kwargs
        )

    def get_by_correlation_ids(
        self,
        workflow_name: str,
        correlation_ids: List[str],
        include_completed: bool = False,
        include_tasks: bool = False,
    ) -> dict[str, List[Workflow]]:
        """Lists workflows for the given correlation id list"""
        kwargs = {}
        if include_tasks:
            kwargs["include_tasks"] = include_tasks
        if include_completed:
            kwargs["include_closed"] = include_completed

        return self.workflowResourceApi.get_workflows(
            body=correlation_ids, name=workflow_name, **kwargs
        )

    def remove_workflow(self, workflow_id: str):
        self.workflowResourceApi.delete(workflow_id)

    def update_variables(
        self, workflow_id: str, variables: dict[str, object] = {}
    ) -> None:
        self.workflowResourceApi.update_workflow_state(variables, workflow_id)

    def update_state(
        self,
        workflow_id: str,
        update_requesst: WorkflowStateUpdate,
        wait_until_task_ref_names: List[str] = None,
        wait_for_seconds: int = None,
    ) -> WorkflowRun:
        kwargs = {}
        if wait_until_task_ref_names is not None:
            kwargs["wait_until_task_ref"] = ",".join(wait_until_task_ref_names)
        if wait_for_seconds is not None:
            kwargs["wait_for_seconds"] = wait_for_seconds

        return self.workflowResourceApi.update_workflow_and_task_state(
            update_requesst=update_requesst, workflow_id=workflow_id, **kwargs
        )


workflow_client = OrkesWorkflowClient(container.conductor_config)
