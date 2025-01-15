from abc import ABC
from typing import Any, Dict

from omagent_core.engine.event.queue.queue_worker_configuration import \
    QueueWorkerConfiguration


class QueueConfiguration(ABC):
    WORKER_CONSUMER_KEY = "consumer"
    WORKER_PRODUCER_KEY = "producer"

    def __init__(self, queue_name: str, queue_type: str):
        self.queue_name = queue_name
        self.queue_type = queue_type
        self.worker_configuration = {}

    def add_consumer(self, worker_configuration: QueueWorkerConfiguration) -> None:
        self.worker_configuration[self.WORKER_CONSUMER_KEY] = worker_configuration

    def add_producer(self, worker_configuration: QueueWorkerConfiguration) -> None:
        self.worker_configuration[self.WORKER_PRODUCER_KEY] = worker_configuration

    def get_worker_configuration(self) -> Dict[str, Any]:
        raise NotImplementedError
