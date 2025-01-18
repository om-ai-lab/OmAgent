from __future__ import absolute_import

import re  # noqa: F401
from abc import ABC, abstractmethod
from typing import List

# python 2 and python 3 compatibility library
import six
from omagent_core.engine.http.api_client import ApiClient
from omagent_core.engine.http.models.prompt_template import PromptTemplate
from omagent_core.engine.orkes.models.metadata_tag import MetadataTag


class PromptClient(ABC):

    @abstractmethod
    def save_prompt(self, prompt_name: str, description: str, prompt_template: str):
        pass

    @abstractmethod
    def get_prompt(self, prompt_name: str) -> PromptTemplate:
        pass

    @abstractmethod
    def get_prompts(self):
        pass

    @abstractmethod
    def delete_prompt(self, prompt_name: str):
        pass

    @abstractmethod
    def get_tags_for_prompt_template(self, prompt_name: str) -> List[MetadataTag]:
        pass

    @abstractmethod
    def update_tag_for_prompt_template(self, prompt_name: str, tags: List[MetadataTag]):
        pass

    @abstractmethod
    def delete_tag_for_prompt_template(self, prompt_name: str, tags: List[MetadataTag]):
        pass

    @abstractmethod
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
        pass
