from typing import Any

from omagent_core.base import BotBase


class ConnectorBase(BotBase):
    @property
    def client(self) -> Any:
        return self._client
