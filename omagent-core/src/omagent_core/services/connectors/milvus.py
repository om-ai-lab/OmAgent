from .base import ConnectorBase
from pymilvus import Collection, DataType, MilvusClient, connections, utility
from pymilvus.client import types
from typing import Any, Optional
from pydantic import Field
from omagent_core.utils.registry import registry


@registry.register_connector()
class MilvusConnector(ConnectorBase):
    host: str = Field(default="./db.db")
    port: int = Field(default=19530)
    password: str = Field(default="")
    username: Optional[str] = Field(default="default")
    db: Optional[str] = Field(default="default")
    alias: Optional[str] = Field(default="alias")

    def model_post_init(self, __context: Any) -> None:                
        self._client = MilvusClient(
            uri=self.host,
            user=self.username,
            password=self.password,
            db_name=self.db,
        ) 
        