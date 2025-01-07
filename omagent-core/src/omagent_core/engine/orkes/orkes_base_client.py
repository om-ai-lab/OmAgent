import logging

from omagent_core.engine.configuration.configuration import Configuration
from omagent_core.engine.http.api.application_resource_api import \
    ApplicationResourceApi
from omagent_core.engine.http.api.authorization_resource_api import \
    AuthorizationResourceApi
from omagent_core.engine.http.api.group_resource_api import GroupResourceApi
from omagent_core.engine.http.api.integration_resource_api import \
    IntegrationResourceApi
from omagent_core.engine.http.api.metadata_resource_api import \
    MetadataResourceApi
from omagent_core.engine.http.api.prompt_resource_api import PromptResourceApi
from omagent_core.engine.http.api.scheduler_resource_api import \
    SchedulerResourceApi
from omagent_core.engine.http.api.secret_resource_api import SecretResourceApi
from omagent_core.engine.http.api.task_resource_api import TaskResourceApi
from omagent_core.engine.http.api.user_resource_api import UserResourceApi
from omagent_core.engine.http.api.workflow_resource_api import \
    WorkflowResourceApi
from omagent_core.engine.http.api_client import ApiClient
from omagent_core.engine.orkes.api.tags_api import TagsApi


class OrkesBaseClient(object):
    def __init__(self, configuration: Configuration):
        self.api_client = ApiClient(configuration)
        self.logger = logging.getLogger(
            Configuration.get_logging_formatted_name(__name__)
        )
        self.metadataResourceApi = MetadataResourceApi(self.api_client)
        self.taskResourceApi = TaskResourceApi(self.api_client)
        self.workflowResourceApi = WorkflowResourceApi(self.api_client)
        self.applicationResourceApi = ApplicationResourceApi(self.api_client)
        self.secretResourceApi = SecretResourceApi(self.api_client)
        self.userResourceApi = UserResourceApi(self.api_client)
        self.groupResourceApi = GroupResourceApi(self.api_client)
        self.authorizationResourceApi = AuthorizationResourceApi(self.api_client)
        self.schedulerResourceApi = SchedulerResourceApi(self.api_client)
        self.tagsApi = TagsApi(self.api_client)
        self.integrationApi = IntegrationResourceApi(self.api_client)
        self.promptApi = PromptResourceApi(self.api_client)
