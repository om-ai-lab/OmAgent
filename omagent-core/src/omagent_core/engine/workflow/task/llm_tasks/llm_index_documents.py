from typing import Optional

from omagent_core.engine.workflow.task.llm_tasks.utils.embedding_model import \
    EmbeddingModel
from omagent_core.engine.workflow.task.task import TaskInterface
from omagent_core.engine.workflow.task.task_type import TaskType
from typing_extensions import Self


class LlmIndexDocument(TaskInterface):
    """
    Indexes the document specified by a URL
    Inputs:
    embedding_model.provider: AI provider to use for generating embeddings e.g. OpenAI
    embedding_model.model: Model to be used to generate embeddings e.g. text-embedding-ada-002
    url: URL to read the document from.  Can be HTTP(S), S3 or other blob store that the server can access
    media_type: content type for the document. e.g. application/pdf, text/html, text/plain, application/json, text/json
    namespace: (optional) namespace to separate the data inside the index - if supported by vector store (e.g. Pinecone)
    index: Index or classname (in case of Weaviate)

    Optional fields
    chunk_size: size of the chunk so the document is split into the chunks and stored
    chunk_overlap: how much the chunks should overlap
    doc_id: by default the indexed document is given an id based on the URL, use doc_id to override this
    metadata: a dictionary of optional metadata to be added to thd indexed doc
    """

    def __init__(
        self,
        task_ref_name: str,
        vector_db: str,
        namespace: str,
        embedding_model: EmbeddingModel,
        index: str,
        url: str,
        media_type: str,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        doc_id: str = None,
        task_name: str = None,
        metadata: dict = {},
    ) -> Self:
        input_params = {
            "vectorDB": vector_db,
            "namespace": namespace,
            "index": index,
            "embeddingModelProvider": embedding_model.provider,
            "embeddingModel": embedding_model.model,
            "url": url,
            "mediaType": media_type,
            "metadata": metadata,
        }

        optional_input_params = {}

        if chunk_size:
            optional_input_params.update({"chunkSize": chunk_size})

        if chunk_overlap:
            optional_input_params.update({"chunkOverlap": chunk_overlap})

        if doc_id:
            optional_input_params.update({"docId": doc_id})

        input_params.update(optional_input_params)
        if task_name is None:
            task_name = "llm_index_document"

        super().__init__(
            task_name=task_name,
            task_reference_name=task_ref_name,
            task_type=TaskType.LLM_INDEX_DOCUMENT,
            input_parameters=input_params,
        )
