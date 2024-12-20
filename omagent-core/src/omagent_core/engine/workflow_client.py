from abc import ABC, abstractmethod
from typing import List, Optional

from omagent_core.engine.http.models import (
    ScrollableSearchResultWorkflowSummary, SkipTaskRequest, WorkflowRun,
    WorkflowStatus)
from omagent_core.engine.http.models.correlation_ids_search_request import \
    CorrelationIdsSearchRequest
from omagent_core.engine.http.models.rerun_workflow_request import \
    RerunWorkflowRequest
from omagent_core.engine.http.models.start_workflow_request import \
    StartWorkflowRequest
from omagent_core.engine.http.models.workflow import Workflow
from omagent_core.engine.http.models.workflow_state_update import \
    WorkflowStateUpdate
from omagent_core.engine.http.models.workflow_test_request import \
    WorkflowTestRequest


class WorkflowClient(ABC):
    @abstractmethod
    def start_workflow(self, start_workflow_request: StartWorkflowRequest) -> str:
        pass

    @abstractmethod
    def get_workflow(
        self, workflow_id: str, include_tasks: Optional[bool] = True
    ) -> Workflow:
        pass

    @abstractmethod
    def get_workflow_status(
        self,
        workflow_id: str,
        include_output: bool = None,
        include_variables: bool = None,
    ) -> WorkflowStatus:
        pass

    @abstractmethod
    def delete_workflow(
        self, workflow_id: str, archive_workflow: Optional[bool] = True
    ):
        pass

    @abstractmethod
    def terminate_workflow(
        self,
        workflow_id: str,
        reason: Optional[str] = None,
        trigger_failure_workflow: bool = False,
    ):
        pass

    @abstractmethod
    def execute_workflow(
        self,
        start_workflow_request: StartWorkflowRequest,
        request_id: str = None,
        wait_until_task_ref: Optional[str] = None,
        wait_for_seconds: int = 30,
    ) -> WorkflowRun:
        pass

    @abstractmethod
    def pause_workflow(self, workflow_id: str):
        pass

    @abstractmethod
    def resume_workflow(self, workflow_id: str):
        pass

    @abstractmethod
    def restart_workflow(
        self, workflow_id: str, use_latest_def: Optional[bool] = False
    ):
        pass

    @abstractmethod
    def retry_workflow(
        self, workflow_id: str, resume_subworkflow_tasks: Optional[bool] = False
    ):
        pass

    @abstractmethod
    def rerun_workflow(
        self, workflow_id: str, rerun_workflow_request: RerunWorkflowRequest
    ):
        pass

    @abstractmethod
    def skip_task_from_workflow(
        self, workflow_id: str, task_reference_name: str, request: SkipTaskRequest
    ):
        pass

    @abstractmethod
    def test_workflow(self, test_request: WorkflowTestRequest) -> Workflow:
        pass

    @abstractmethod
    def search(
        self, start: int = 0, size: int = 100, free_text: str = "*", query: str = None
    ) -> ScrollableSearchResultWorkflowSummary:
        pass

    @abstractmethod
    def get_by_correlation_ids_in_batch(
        self,
        batch_request: CorrelationIdsSearchRequest,
        include_completed: bool = False,
        include_tasks: bool = False,
    ) -> dict[str, List[Workflow]]:
        pass

    @abstractmethod
    def get_by_correlation_ids(
        self,
        workflow_name: str,
        correlation_ids: List[str],
        include_completed: bool = False,
        include_tasks: bool = False,
    ) -> dict[str, List[Workflow]]:
        pass

    @abstractmethod
    def remove_workflow(self, workflow_id: str):
        pass

    @abstractmethod
    def update_variables(
        self, workflow_id: str, variables: dict[str, object] = {}
    ) -> None:
        pass

    @abstractmethod
    def update_state(
        self,
        workflow_id: str,
        update_requesst: WorkflowStateUpdate,
        wait_until_task_ref_names: List[str] = None,
        wait_for_seconds: int = None,
    ) -> WorkflowRun:
        pass
