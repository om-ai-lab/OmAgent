from copy import deepcopy
from typing import Any, Dict

from typing_extensions import Self


class KafkaPublishInput:
    def __init__(self,
                 bootstrap_servers: str = None,
                 key: str = None,
                 key_serializer: str = None,
                 value: str = None,
                 request_timeout_ms: str = None,
                 max_block_ms: str = None,
                 headers: Dict[str, Any] = None,
                 topic: str = None) -> Self:
        self._bootstrap_servers = deepcopy(bootstrap_servers)
        self._key = deepcopy(key)
        self._key_serializer = deepcopy(key_serializer)
        self._value = deepcopy(value)
        self._request_timeout_ms = deepcopy(request_timeout_ms)
        self._max_block_ms = deepcopy(max_block_ms)
        self._headers = deepcopy(headers)
        self._topic = deepcopy(topic)
