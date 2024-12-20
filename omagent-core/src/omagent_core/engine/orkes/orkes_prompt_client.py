from __future__ import absolute_import

import re  # noqa: F401
from typing import List

from omagent_core.engine.configuration.configuration import Configuration
from omagent_core.engine.http.models.prompt_template import PromptTemplate
from omagent_core.engine.http.models.prompt_test_request import \
    PromptTemplateTestRequest
from omagent_core.engine.http.rest import ApiException
from omagent_core.engine.orkes.models.metadata_tag import MetadataTag
from omagent_core.engine.orkes.orkes_base_client import OrkesBaseClient
from omagent_core.engine.prompt_client import PromptClient

# python 2 and python 3 compatibility library


class OrkesPromptClient(OrkesBaseClient, PromptClient):

    def __init__(self, configuration: Configuration):
        super(OrkesPromptClient, self).__init__(configuration)

    def save_prompt(self, prompt_name: str, description: str, prompt_template: str):
        self.promptApi.save_message_template(prompt_template, description, prompt_name)

    def get_prompt(self, prompt_name: str) -> PromptTemplate:
        try:
            return self.promptApi.get_message_template(prompt_name)
        except ApiException as e:
            if e.is_not_found():
                return None
            raise e

    def get_prompts(self):
        return self.promptApi.get_message_templates()

    def delete_prompt(self, prompt_name: str):
        self.promptApi.delete_message_template(prompt_name)

    def get_tags_for_prompt_template(self, prompt_name: str) -> List[MetadataTag]:
        self.promptApi.get_tags_for_prompt_template(prompt_name)

    def update_tag_for_prompt_template(self, prompt_name: str, tags: List[MetadataTag]):
        self.promptApi.put_tag_for_prompt_template(tags, prompt_name)

    def delete_tag_for_prompt_template(self, prompt_name: str, tags: List[MetadataTag]):
        self.promptApi.delete_tag_for_prompt_template(tags, prompt_name)

    def test_prompt(
        self,
        prompt_text: str,
        variables: dict,
        ai_integration: str,
        text_complete_model: str,
        temperature: float = 0.1,
        top_p: float = 0.9,
        stop_words: List[str] = None,
    ) -> str:
        request = PromptTemplateTestRequest()
        request.prompt = prompt_text
        request.llm_provider = ai_integration
        request.model = text_complete_model
        request.prompt_variables = variables
        request.temperature = temperature
        request.top_p = top_p
        if stop_words is not None:
            request.stop_words = stop_words
        return self.promptApi.test_message_template(request)
