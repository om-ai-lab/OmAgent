from typing import List, Optional

from omagent_core.engine.configuration.configuration import Configuration
from omagent_core.engine.http.models.save_schedule_request import \
    SaveScheduleRequest
from omagent_core.engine.http.models.search_result_workflow_schedule_execution_model import \
    SearchResultWorkflowScheduleExecutionModel
from omagent_core.engine.http.models.workflow_schedule import WorkflowSchedule
from omagent_core.engine.orkes.models.metadata_tag import MetadataTag
from omagent_core.engine.orkes.orkes_base_client import OrkesBaseClient
from omagent_core.engine.scheduler_client import SchedulerClient


class OrkesSchedulerClient(OrkesBaseClient, SchedulerClient):
    def __init__(self, configuration: Configuration):
        super(OrkesSchedulerClient, self).__init__(configuration)

    def save_schedule(self, save_schedule_request: SaveScheduleRequest):
        self.schedulerResourceApi.save_schedule(save_schedule_request)

    def get_schedule(self, name: str) -> WorkflowSchedule:
        return self.schedulerResourceApi.get_schedule(name)

    def get_all_schedules(
        self, workflow_name: Optional[str] = None
    ) -> List[WorkflowSchedule]:
        kwargs = {}
        if workflow_name:
            kwargs.update({"workflow_name": workflow_name})

        return self.schedulerResourceApi.get_all_schedules(**kwargs)

    def get_next_few_schedule_execution_times(
        self,
        cron_expression: str,
        schedule_start_time: Optional[int] = None,
        schedule_end_time: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[int]:
        kwargs = {}
        if schedule_start_time:
            kwargs.update({"schedule_start_time": schedule_start_time})
        if schedule_end_time:
            kwargs.update({"schedule_end_time": schedule_end_time})
        if limit:
            kwargs.update({"limit": limit})
        return self.schedulerResourceApi.get_next_few_schedules(
            cron_expression, **kwargs
        )

    def delete_schedule(self, name: str):
        self.schedulerResourceApi.delete_schedule(name)

    def pause_schedule(self, name: str):
        self.schedulerResourceApi.pause_schedule(name)

    def pause_all_schedules(self):
        self.schedulerResourceApi.pause_all_schedules()

    def resume_schedule(self, name: str):
        self.schedulerResourceApi.resume_schedule(name)

    def resume_all_schedules(self):
        self.schedulerResourceApi.resume_all_schedules()

    def search_schedule_executions(
        self,
        start: Optional[int] = None,
        size: Optional[int] = None,
        sort: Optional[str] = None,
        free_text: Optional[str] = None,
        query: Optional[str] = None,
    ) -> SearchResultWorkflowScheduleExecutionModel:
        kwargs = {}
        if start:
            kwargs.update({"start": start})
        if size:
            kwargs.update({"size": size})
        if sort:
            kwargs.update({"sort": sort})
        if free_text:
            kwargs.update({"freeText": free_text})
        if query:
            kwargs.update({"query": query})
        return self.schedulerResourceApi.search_v21(**kwargs)

    def requeue_all_execution_records(self):
        self.schedulerResourceApi.requeue_all_execution_records()

    def set_scheduler_tags(self, tags: List[MetadataTag], name: str):
        self.schedulerResourceApi.put_tag_for_schedule(tags, name)

    def get_scheduler_tags(self, name: str) -> List[MetadataTag]:
        return self.schedulerResourceApi.get_tags_for_schedule(name)

    def delete_scheduler_tags(
        self, tags: List[MetadataTag], name: str
    ) -> List[MetadataTag]:
        self.schedulerResourceApi.delete_tag_for_schedule(tags, name)
