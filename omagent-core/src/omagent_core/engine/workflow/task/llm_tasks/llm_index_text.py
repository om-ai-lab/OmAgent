from omagent_core.engine.workflow.task.llm_tasks.utils.embedding_model import \
    EmbeddingModel
from omagent_core.engine.workflow.task.task import TaskInterface
from omagent_core.engine.workflow.task.task_type import TaskType
from typing_extensions import Self


class LlmIndexText(TaskInterface):
    """
    Stores the text as ebmeddings in the vector database
    Inputs:
    embedding_model.provider: AI provider to use for generating embeddings e.g. OpenAI
    embedding_model.model: Model to be used to generate embeddings e.g. text-embedding-ada-002
    url: URL to read the document from.  Can be HTTP(S), S3 or other blob store that the server can access
    media_type: content type for the document. e.g. application/pdf, text/html, text/plain, application/json, text/json
    namespace: (optional) namespace to separate the data inside the index - if supported by vector store (e.g. Pinecone)
    index: Index or classname (in case of Weaviate)
    doc_id: ID of the stored document in the vector db
    metadata: a dictionary of optional metadata to be added to thd indexed doc
    """

    def __init__(
        self,
        task_ref_name: str,
        vector_db: str,
        index: str,
        embedding_model: EmbeddingModel,
        text: str,
        doc_id: str,
        namespace: str = None,
        task_name: str = None,
        metadata: dict = {},
    ) -> Self:
        if task_name is None:
            task_name = "llm_index_doc"

        super().__init__(
            task_name=task_name,
            task_reference_name=task_ref_name,
            task_type=TaskType.LLM_INDEX_TEXT,
            input_parameters={
                "vectorDB": vector_db,
                "index": index,
                "embeddingModelProvider": embedding_model.provider,
                "embeddingModel": embedding_model.model,
                "text": text,
                "docId": doc_id,
                "metadata": metadata,
            },
        )
        if namespace is not None:
            self.input_parameter("namespace", namespace)
