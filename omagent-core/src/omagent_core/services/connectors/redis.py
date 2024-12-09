from .base import ConnectorBase
from redis import ConnectionPool, Redis
from typing import Any, Optional
from pydantic import Field
from omagent_core.utils.registry import registry

@registry.register_connector()
class RedisConnector(ConnectorBase):
    host: str = Field(default="localhost")
    port: int = Field(default=6379)
    password: Optional[str] = Field(default=None)
    username: Optional[str] = Field(default=None)
    db: int = Field(default=0)

    def model_post_init(self, __context: Any) -> None:
        pool = ConnectionPool(
            host=self.host,
            port=self.port,
            password=self.password,
            username=self.username,
            db=self.db,
            decode_responses=False
        )
        self._client = Redis(connection_pool=pool)