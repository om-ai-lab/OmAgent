from abc import ABC, abstractmethod
from typing import List, Optional

from omagent_core.engine.http.models.save_schedule_request import \
    SaveScheduleRequest
from omagent_core.engine.http.models.search_result_workflow_schedule_execution_model import \
    SearchResultWorkflowScheduleExecutionModel
from omagent_core.engine.http.models.workflow_schedule import WorkflowSchedule
from omagent_core.engine.orkes.models.metadata_tag import MetadataTag


class SchedulerClient(ABC):
    @abstractmethod
    def save_schedule(self, save_schedule_request: SaveScheduleRequest):
        pass

    @abstractmethod
    def get_schedule(self, name: str) -> (Optional[WorkflowSchedule], str):
        pass

    @abstractmethod
    def get_all_schedules(
        self, workflow_name: Optional[str] = None
    ) -> List[WorkflowSchedule]:
        pass

    @abstractmethod
    def get_next_few_schedule_execution_times(
        self,
        cron_expression: str,
        schedule_start_time: Optional[int] = None,
        schedule_end_time: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[int]:
        pass

    @abstractmethod
    def delete_schedule(self, name: str):
        pass

    @abstractmethod
    def pause_schedule(self, name: str):
        pass

    @abstractmethod
    def pause_all_schedules(self):
        pass

    @abstractmethod
    def resume_schedule(self, name: str):
        pass

    @abstractmethod
    def resume_all_schedules(self):
        pass

    @abstractmethod
    def search_schedule_executions(
        self,
        start: Optional[int] = None,
        size: Optional[int] = None,
        sort: Optional[str] = None,
        free_text: Optional[str] = None,
        query: Optional[str] = None,
    ) -> SearchResultWorkflowScheduleExecutionModel:
        pass

    @abstractmethod
    def requeue_all_execution_records(self):
        pass

    @abstractmethod
    def set_scheduler_tags(self, tags: List[MetadataTag], name: str):
        pass

    @abstractmethod
    def get_scheduler_tags(self, name: str) -> List[MetadataTag]:
        pass

    @abstractmethod
    def delete_scheduler_tags(
        self, tags: List[MetadataTag], name: str
    ) -> List[MetadataTag]:
        pass
