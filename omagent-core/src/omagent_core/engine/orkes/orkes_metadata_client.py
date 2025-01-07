from typing import List, Optional

from omagent_core.engine.configuration.configuration import Configuration
from omagent_core.engine.http.models.tag_string import TagString
from omagent_core.engine.http.models.task_def import TaskDef
from omagent_core.engine.http.models.workflow_def import WorkflowDef
from omagent_core.engine.metadata_client import MetadataClient
from omagent_core.engine.orkes.models.metadata_tag import MetadataTag
from omagent_core.engine.orkes.models.ratelimit_tag import RateLimitTag
from omagent_core.engine.orkes.orkes_base_client import OrkesBaseClient


class OrkesMetadataClient(OrkesBaseClient, MetadataClient):
    def __init__(self, configuration: Configuration):
        super(OrkesMetadataClient, self).__init__(configuration)

    def register_workflow_def(
        self, workflow_def: WorkflowDef, overwrite: Optional[bool] = True
    ):
        self.metadataResourceApi.create(workflow_def, overwrite=overwrite)

    def update_workflow_def(
        self, workflow_def: WorkflowDef, overwrite: Optional[bool] = True
    ):
        self.metadataResourceApi.update1([workflow_def], overwrite=overwrite)

    def unregister_workflow_def(self, name: str, version: int):
        self.metadataResourceApi.unregister_workflow_def(name, version)

    def get_workflow_def(self, name: str, version: Optional[int] = None) -> WorkflowDef:
        workflow = None
        if version:
            workflow = self.metadataResourceApi.get(name, version=version)
        else:
            workflow = self.metadataResourceApi.get(name)

        return workflow

    def get_all_workflow_defs(self) -> List[WorkflowDef]:
        return self.metadataResourceApi.get_all_workflows()

    def register_task_def(self, task_def: TaskDef):
        self.metadataResourceApi.register_task_def([task_def])

    def update_task_def(self, task_def: TaskDef):
        self.metadataResourceApi.update_task_def(task_def)

    def unregister_task_def(self, task_type: str):
        self.metadataResourceApi.unregister_task_def(task_type)

    def get_task_def(self, task_type: str) -> TaskDef:
        return self.metadataResourceApi.get_task_def(task_type)

    def get_all_task_defs(self) -> List[TaskDef]:
        return self.metadataResourceApi.get_task_defs()

    def add_workflow_tag(self, tag: MetadataTag, workflow_name: str):
        self.tagsApi.add_workflow_tag(tag, workflow_name)

    def delete_workflow_tag(self, tag: MetadataTag, workflow_name: str):
        tagStr = TagString(tag.key, tag.type, tag.value)
        self.tagsApi.delete_workflow_tag(tagStr, workflow_name)

    def get_workflow_tags(self, workflow_name: str) -> List[MetadataTag]:
        return self.tagsApi.get_workflow_tags(workflow_name)

    def set_workflow_tags(self, tags: List[MetadataTag], workflow_name: str):
        self.tagsApi.set_workflow_tags(tags, workflow_name)

    def addTaskTag(self, tag: MetadataTag, taskName: str):
        self.tagsApi.add_task_tag(tag, taskName)

    def deleteTaskTag(self, tag: MetadataTag, taskName: str):
        tagStr = TagString(tag.key, tag.type, tag.value)
        self.tagsApi.delete_task_tag(tagStr, taskName)

    def getTaskTags(self, taskName: str) -> List[MetadataTag]:
        return self.tagsApi.get_task_tags(taskName)

    def setTaskTags(self, tags: List[MetadataTag], taskName: str):
        self.tagsApi.set_task_tags(tags, taskName)

    def setWorkflowRateLimit(self, rateLimit: int, workflowName: str):
        self.removeWorkflowRateLimit(workflowName)
        rateLimitTag = RateLimitTag(workflowName, rateLimit)
        self.tagsApi.add_workflow_tag(rateLimitTag, workflowName)

    def getWorkflowRateLimit(self, workflowName: str) -> Optional[int]:
        tags = self.tagsApi.get_workflow_tags(workflowName)
        for tag in tags:
            if tag.type == "RATE_LIMIT" and tag.key == workflowName:
                return tag.value

        return None

    def removeWorkflowRateLimit(self, workflowName: str):
        current_rate_limit = self.getWorkflowRateLimit(workflowName)
        if current_rate_limit:
            rateLimitTag = RateLimitTag(workflowName, current_rate_limit)
            self.tagsApi.delete_workflow_tag(rateLimitTag, workflowName)
