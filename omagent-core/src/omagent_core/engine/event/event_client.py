from omagent_core.engine.event.queue.queue_configuration import \
    QueueConfiguration
from omagent_core.engine.http.api.event_resource_api import EventResourceApi
from omagent_core.engine.http.api_client import ApiClient


class EventClient:
    def __init__(self, api_client: ApiClient):
        self.client = EventResourceApi(api_client)

    def delete_queue_configuration(
        self, queue_configuration: QueueConfiguration
    ) -> None:
        return self.client.delete_queue_config(
            queue_name=queue_configuration.queue_name,
            queue_type=queue_configuration.queue_type,
        )

    def get_kafka_queue_configuration(self, queue_topic: str) -> QueueConfiguration:
        return self.get_queue_configuration(
            queue_type="kafka",
            queue_name=queue_topic,
        )

    def get_queue_configuration(self, queue_type: str, queue_name: str):
        return self.client.get_queue_config(queue_type, queue_name)

    def put_queue_configuration(self, queue_configuration: QueueConfiguration):
        return self.client.put_queue_config(
            body=queue_configuration.get_worker_configuration(),
            queue_name=queue_configuration.queue_name,
            queue_type=queue_configuration.queue_type,
        )
