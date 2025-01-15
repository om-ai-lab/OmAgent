from typing import Any, Optional

from omagent_core.utils.registry import registry
from pydantic import Field
from pymilvus import MilvusClient

from .base import ConnectorBase


@registry.register_connector()
class MilvusConnector(ConnectorBase):
    host: str = Field(default="./db.db")
    port: int = Field(default=19530)
    password: str = Field(default="")
    username: Optional[str] = Field(default="default")
    db: Optional[str] = Field(default="default")
    alias: Optional[str] = Field(default="alias")

    def model_post_init(self, __context: Any) -> None:
        try:
            self._client = MilvusClient(
                uri=self.host,
                user=self.username,
                password=self.password,
                db_name=self.db,
            )
        except Exception as e:
            raise ConnectionError(
                f"Connection to Milvus failed. Please check your connector config in container.yaml. \n Error Message: {e}"
            )

    def check_connection(self) -> bool:
        """Check if the connection to Milvus is valid."""
        # Try to list collections to verify connection
        self._client.list_collections()
