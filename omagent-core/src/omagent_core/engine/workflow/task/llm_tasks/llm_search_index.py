from omagent_core.engine.workflow.task.task import TaskInterface
from omagent_core.engine.workflow.task.task_type import TaskType
from typing_extensions import Self


class LlmSearchIndex(TaskInterface):
    def __init__(
        self,
        task_ref_name: str,
        vector_db: str,
        namespace: str,
        index: str,
        embedding_model_provider: str,
        embedding_model: str,
        query: str,
        task_name: str = None,
        max_results: int = 1,
    ) -> Self:
        if task_name is None:
            task_name = "llm_search_index"

        super().__init__(
            task_name=task_name,
            task_reference_name=task_ref_name,
            task_type=TaskType.LLM_SEARCH_INDEX,
            input_parameters={
                "vectorDB": vector_db,
                "namespace": namespace,
                "index": index,
                "embeddingModelProvider": embedding_model_provider,
                "embeddingModel": embedding_model,
                "query": query,
                "maxResults": max_results,
            },
        )
