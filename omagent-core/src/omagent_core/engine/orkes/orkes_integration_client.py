from __future__ import absolute_import

from typing import List

from omagent_core.engine.configuration.configuration import Configuration
from omagent_core.engine.http.models.integration import Integration
from omagent_core.engine.http.models.integration_api import IntegrationApi
from omagent_core.engine.http.models.integration_api_update import \
    IntegrationApiUpdate
from omagent_core.engine.http.models.integration_update import \
    IntegrationUpdate
from omagent_core.engine.http.models.prompt_template import PromptTemplate
from omagent_core.engine.http.rest import ApiException
from omagent_core.engine.integration_client import IntegrationClient
from omagent_core.engine.orkes.orkes_base_client import OrkesBaseClient


class OrkesIntegrationClient(OrkesBaseClient, IntegrationClient):

    def __init__(self, configuration: Configuration):
        super(OrkesIntegrationClient, self).__init__(configuration)

    def associate_prompt_with_integration(
        self, ai_integration: str, model_name: str, prompt_name: str
    ):
        self.integrationApi.associate_prompt_with_integration(
            ai_integration, model_name, prompt_name
        )

    def delete_integration_api(self, api_name: str, integration_name: str):
        self.integrationApi.delete_integration_api(api_name, integration_name)

    def delete_integration(self, integration_name: str):
        self.integrationApi.delete_integration_provider(integration_name)

    def get_integration_api(
        self, api_name: str, integration_name: str
    ) -> IntegrationApi:
        try:
            return self.integrationApi.get_integration_api(api_name, integration_name)
        except ApiException as e:
            if e.is_not_found():
                return None
            raise e

    def get_integration_apis(self, integration_name: str) -> List[IntegrationApi]:
        return self.integrationApi.get_integration_apis(integration_name)

    def get_integration(self, integration_name: str) -> Integration:
        try:
            return self.integrationApi.get_integration_provider(integration_name)
        except ApiException as e:
            if e.is_not_found():
                return None
            raise e

    def get_integrations(self) -> List[Integration]:
        return self.integrationApi.get_integration_providers()

    def get_prompts_with_integration(
        self, ai_integration: str, model_name: str
    ) -> List[PromptTemplate]:
        return self.integrationApi.get_prompts_with_integration(
            ai_integration, model_name
        )

    def save_integration_api(
        self, integration_name, api_name, api_details: IntegrationApiUpdate
    ):
        self.integrationApi.save_integration_api(
            api_details, integration_name, api_name
        )

    def save_integration(
        self, integration_name, integration_details: IntegrationUpdate
    ):
        self.integrationApi.save_integration_provider(
            integration_details, integration_name
        )

    def get_token_usage_for_integration(self, name, integration_name) -> int:
        return self.integrationApi.get_token_usage_for_integration(
            name, integration_name
        )

    def get_token_usage_for_integration_provider(self, name) -> dict:
        return self.integrationApi.get_token_usage_for_integration_provider(name)

    def register_token_usage(self, body, name, integration_name):
        pass

    # Tags

    def delete_tag_for_integration(self, body, tag_name, integration_name):
        """Delete an integration"""
        pass

    def delete_tag_for_integration_provider(self, body, name):
        pass

    def put_tag_for_integration(self, body, name, integration_name):
        pass

    def put_tag_for_integration_provider(self, body, name):
        pass

    def get_tags_for_integration(self, name, integration_name):
        pass

    def get_tags_for_integration_provider(self, name):
        pass
