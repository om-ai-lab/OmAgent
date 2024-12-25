from omagent_core.engine.authorization_client import AuthorizationClient
from omagent_core.engine.configuration.configuration import Configuration
from omagent_core.engine.integration_client import IntegrationClient
from omagent_core.engine.metadata_client import MetadataClient
from omagent_core.engine.orkes.orkes_authorization_client import \
    OrkesAuthorizationClient
from omagent_core.engine.orkes.orkes_integration_client import \
    OrkesIntegrationClient
from omagent_core.engine.orkes.orkes_metadata_client import OrkesMetadataClient
from omagent_core.engine.orkes.orkes_prompt_client import OrkesPromptClient
from omagent_core.engine.orkes.orkes_scheduler_client import \
    OrkesSchedulerClient
from omagent_core.engine.orkes.orkes_secret_client import OrkesSecretClient
from omagent_core.engine.orkes.orkes_task_client import OrkesTaskClient
from omagent_core.engine.orkes.orkes_workflow_client import OrkesWorkflowClient
from omagent_core.engine.prompt_client import PromptClient
from omagent_core.engine.scheduler_client import SchedulerClient
from omagent_core.engine.secret_client import SecretClient
from omagent_core.engine.task_client import TaskClient
from omagent_core.engine.workflow.executor.workflow_executor import \
    WorkflowExecutor
from omagent_core.engine.workflow_client import WorkflowClient
from omagent_core.utils.container import container


class OrkesClients:
    def __init__(self, configuration: Configuration = None):
        if configuration is None:
            configuration = container.conductor_config
        self.configuration = configuration

    def get_workflow_client(self) -> WorkflowClient:
        return OrkesWorkflowClient(self.configuration)

    def get_authorization_client(self) -> AuthorizationClient:
        return OrkesAuthorizationClient(self.configuration)

    def get_metadata_client(self) -> MetadataClient:
        return OrkesMetadataClient(self.configuration)

    def get_scheduler_client(self) -> SchedulerClient:
        return OrkesSchedulerClient(self.configuration)

    def get_secret_client(self) -> SecretClient:
        return OrkesSecretClient(self.configuration)

    def get_task_client(self) -> TaskClient:
        return OrkesTaskClient(self.configuration)

    def get_integration_client(self) -> IntegrationClient:
        return OrkesIntegrationClient(self.configuration)

    def get_workflow_executor(self) -> WorkflowExecutor:
        return WorkflowExecutor(self.configuration)

    def get_prompt_client(self) -> PromptClient:
        return OrkesPromptClient(self.configuration)
