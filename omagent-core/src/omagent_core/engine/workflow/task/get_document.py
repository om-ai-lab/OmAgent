from omagent_core.engine.workflow.task.task import TaskInterface
from omagent_core.engine.workflow.task.task_type import TaskType
from typing_extensions import Self


class GetDocument(TaskInterface):
    def __init__(
        self, task_name: str, task_ref_name: str, url: str, media_type: str
    ) -> Self:
        super().__init__(
            task_name=task_name,
            task_reference_name=task_ref_name,
            task_type=TaskType.GET_DOCUMENT,
            input_parameters={"url": url, "mediaType": media_type},
        )
