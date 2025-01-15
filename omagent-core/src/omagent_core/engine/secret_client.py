from abc import ABC, abstractmethod
from typing import List

from omagent_core.engine.orkes.models.metadata_tag import MetadataTag


class SecretClient(ABC):
    @abstractmethod
    def put_secret(self, key: str, value: str):
        pass

    @abstractmethod
    def get_secret(self, key: str) -> str:
        pass

    @abstractmethod
    def list_all_secret_names(self) -> set[str]:
        pass

    @abstractmethod
    def list_secrets_that_user_can_grant_access_to(self) -> List[str]:
        pass

    @abstractmethod
    def delete_secret(self, key: str):
        pass

    @abstractmethod
    def secret_exists(self, key: str) -> bool:
        pass

    @abstractmethod
    def set_secret_tags(self, tags: List[MetadataTag], key: str):
        pass

    @abstractmethod
    def get_secret_tags(self, key: str) -> List[MetadataTag]:
        pass

    @abstractmethod
    def delete_secret_tags(
        self, tags: List[MetadataTag], key: str
    ) -> List[MetadataTag]:
        pass
