from typing import Any, Optional

from omagent_core.utils.registry import registry
from pydantic import Field
from redis import ConnectionPool, Redis

from .base import ConnectorBase


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
            decode_responses=False,
        )
        self._client = Redis(connection_pool=pool)

    def check_connection(self) -> bool:
        """Check if Redis connection is valid by executing a simple ping command"""
        self._client.ping()
