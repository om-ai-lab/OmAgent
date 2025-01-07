from omagent_core.engine.workflow.task.kafka_publish_input import \
    KafkaPublishInput
from omagent_core.engine.workflow.task.task import TaskInterface
from omagent_core.engine.workflow.task.task_type import TaskType
from typing_extensions import Self


class KafkaPublishTask(TaskInterface):
    def __init__(
        self, task_ref_name: str, kafka_publish_input: KafkaPublishInput = None
    ) -> Self:
        super().__init__(
            task_reference_name=task_ref_name,
            task_type=TaskType.KAFKA_PUBLISH,
            input_parameters={"kafka_request": kafka_publish_input},
        )
