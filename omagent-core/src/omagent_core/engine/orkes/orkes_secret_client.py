from typing import List

from omagent_core.engine.configuration.configuration import Configuration
from omagent_core.engine.orkes.models.metadata_tag import MetadataTag
from omagent_core.engine.orkes.orkes_base_client import OrkesBaseClient
from omagent_core.engine.secret_client import SecretClient


class OrkesSecretClient(OrkesBaseClient, SecretClient):
    def __init__(self, configuration: Configuration):
        super(OrkesSecretClient, self).__init__(configuration)

    def put_secret(self, key: str, value: str):
        self.secretResourceApi.put_secret(value, key)

    def get_secret(self, key: str) -> str:
        return self.secretResourceApi.get_secret(key)

    def list_all_secret_names(self) -> set[str]:
        return set(self.secretResourceApi.list_all_secret_names())

    def list_secrets_that_user_can_grant_access_to(self) -> List[str]:
        return self.secretResourceApi.list_secrets_that_user_can_grant_access_to()

    def delete_secret(self, key: str):
        self.secretResourceApi.delete_secret(key)

    def secret_exists(self, key: str) -> bool:
        return self.secretResourceApi.secret_exists(key)

    def set_secret_tags(self, tags: List[MetadataTag], key: str):
        self.secretResourceApi.put_tag_for_secret(tags, key)

    def get_secret_tags(self, key: str) -> List[MetadataTag]:
        return self.secretResourceApi.get_tags(key)

    def delete_secret_tags(
        self, tags: List[MetadataTag], key: str
    ) -> List[MetadataTag]:
        self.secretResourceApi.delete_tag_for_secret(tags, key)
