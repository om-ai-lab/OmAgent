from typing import Any, Dict

from omagent_core.engine.event.queue.queue_configuration import \
    QueueConfiguration
from omagent_core.engine.event.queue.queue_worker_configuration import \
    QueueWorkerConfiguration


class KafkaQueueConfiguration(QueueConfiguration):
    def __init__(self, queue_topic_name: str):
        super().__init__(queue_topic_name, "kafka")

    def get_worker_configuration(self) -> Dict[str, Any]:
        worker_configuration = {}
        for required_key in ["consumer", "producer"]:
            if required_key not in self.worker_configuration:
                raise RuntimeError(f"required key not present: {required_key}")
        for key, value in self.worker_configuration.items():
            worker_configuration[key] = value.configuration
        return worker_configuration


class KafkaConsumerConfiguration(QueueWorkerConfiguration):
    def __init__(self, bootstrap_servers_config: str):
        super().__init__()
        super().add_configuration(
            key="bootstrap.servers", value=bootstrap_servers_config
        )


class KafkaProducerConfiguration(QueueWorkerConfiguration):
    def __init__(self, bootstrap_servers_config: str):
        super().__init__()
        super().add_configuration(
            key="bootstrap.servers", value=bootstrap_servers_config
        )
