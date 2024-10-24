from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from omagent_core.memories.ltms.ltm_base import LTMVecotrBase
from omagent_core.models.encoders.base import EncoderBase
from omagent_core.utils.error import VQLError
import uuid

class VectorPineconeLTM(LTMVecotrBase):
    def __init__(self, index_id: str, pinecone_client):
        self.encoders: Dict[str, EncoderBase] = {}
        self.dim: Optional[int] = None
        self.index_id: str = index_id
        # Pinecone client is injected
        self.pinecone_client = pinecone_client
        self.index = None  # Will be initialized in init_memory

    def encoder_register(self, modality: str, encoder: EncoderBase):
        self.encoders[modality] = encoder
        if self.dim is None:
            self.dim = encoder.dim
        elif self.dim != encoder.dim:
            raise VQLError(500, detail="All encoders must have the same dimension")

    def init_memory(self, spec=None, metric="cosine", deletion_protection='disabled', **kwargs) -> None:
        """
        Initialize the Pinecone index for storing vectors.

        Args:
            spec (Optional): Specification for the index. Can be ServerlessSpec or PodSpec.
            metric (str, optional): Similarity metric. Defaults to "cosine".
            deletion_protection (str, optional): Whether deletion protection is enabled. Defaults to 'disabled'.
            **kwargs: Additional parameters for Pinecone index creation.
        """
        print(f"Initializing index with vector dimension: {self.dim}")
        # Create Pinecone index if it doesn't exist
        existing_indexes = [idx['name'] for idx in self.pinecone_client.list_indexes()]
        if self.index_id not in existing_indexes:
            self.pinecone_client.create_index(
                name=self.index_id,
                dimension=self.dim,
                metric=metric,
                deletion_protection=deletion_protection,
                spec=spec,
                **kwargs
            )
            print(f"Index '{self.index_id}' created.")
        else:
            print(f"Index '{self.index_id}' already exists.")
        # Get index description to obtain the host
        index_description = self.pinecone_client.describe_index(self.index_id)
        print (index_description)
        index_host = index_description['host']
        # Initialize index object
        self.index = self.pinecone_client.Index(host=index_host)

    def add_data(
        self,
        data: List[Dict[str, Any]],
        encode_data: Optional[List[Any]] = None,
        modality: Optional[str] = None,
        target_field: Optional[str] = None,
        src_type: Optional[str] = None,
        namespace: Optional[str] = None,
    ) -> int:
        """
        Add data to the Pinecone index.

        Args:
            data (List[Dict[str, Any]]): List of dictionaries containing the data to be added.
            encode_data (Optional[List[Any]]): Data to be encoded if not pre-encoded.
            modality (Optional[str]): Modality of the data for encoding.
            target_field (Optional[str]): Field name containing pre-encoded vectors.
            src_type (Optional[str]): Source type for encoding.
            namespace (Optional[str]): Namespace for the data.

        Returns:
            int: Number of inserted records.

        Raises:
            VQLError: If there's a mismatch in data or missing required fields.
        """
        if encode_data:
            records = self._prepare_encode_data(data, encode_data, modality, src_type)
        elif target_field:
            records = self._prepare_target_field_data(data, target_field)
        else:
            records = data

        # Prepare data for Pinecone upsert
        # Each record should be a tuple: (id, vector, metadata)
        vectors = []
        for idx, record in enumerate(records):
            vector = record.get("vector")
            if vector is None:
                raise VQLError(500, detail="Missing 'vector' in record")
            # Use provided ID or generate one
            id = record.get("id", str(uuid.uuid4()))
            # Remove 'vector' and 'id' from metadata
            metadata = {k: v for k, v in record.items() if k not in ["vector", "id"]}
            vectors.append((id, vector, metadata))

        # Upsert data into Pinecone
        upsert_response = self.index.upsert(
            vectors=vectors,
            namespace=namespace
        )
        return upsert_response['upserted_count']

    def _prepare_encode_data(self, data, encode_data, modality, src_type):
        """Prepare data that needs to be encoded."""
        encoder = self.encoders.get(modality)
        if not encoder:
            raise VQLError(500, detail=f'Missing encoder for modality "{modality}"')

        vectors = encoder.infer(encode_data, src_type=src_type)
        if len(vectors) != len(data):
            raise VQLError(500, detail='Mismatch between data and encoded vectors')

        return [{"vector": vector, **item} for vector, item in zip(vectors, data)]

    def _prepare_target_field_data(self, data, target_field):
        """Prepare data where vectors are already in a target field."""
        records = []
        for item in data:
            if target_field not in item:
                raise VQLError(500, detail=f'Missing target_field:{target_field} in {item}')
            vector = item[target_field]
            record = {"vector": vector}
            record.update(item)
            records.append(record)
        return records

    def match_data(
        self,
        query_data: Any,
        modality: str,
        filters: Dict[str, Any] = {},
        threshold: float = -1.0,
        size: int = 10,
        src_type: Optional[str] = None,
        namespace: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        # Encode query data
        encoder = self.encoders.get(modality)
        if not encoder:
            raise VQLError(500, detail=f'Missing encoder for modality "{modality}"')
        vector = encoder.infer([query_data], src_type=src_type)[0]

        # Perform search
        query_response = self.index.query(
            vector=vector,
            top_k=size,
            filter=filters if filters else None,
            include_values=True,
            include_metadata=True,
            namespace=namespace
        )

        results = []
        for match in query_response['matches']:
            score = match['score']
            if score >= threshold:
                results.append({
                    "id": match["id"],
                    "score": score,
                    "vector": match.get("values"),
                    "metadata": match.get("metadata")
                })
        return results

    def delete_data(self, ids: List[str], namespace: Optional[str] = None):
        # Delete data
        delete_response = self.index.delete(ids=ids, namespace=namespace)
        print(f"Deleted IDs: {ids}")
        return delete_response

    def fetch_data(self, ids: List[str], namespace: Optional[str] = None):
        # Fetch data
        fetch_response = self.index.fetch(ids=ids, namespace=namespace)
        return fetch_response

    def update_data(self, id: str, values: Optional[List[float]] = None,
                    set_metadata: Optional[Dict[str, Any]] = None,
                    namespace: Optional[str] = None):
        # Update data
        update_response = self.index.update(
            id=id,
            values=values,
            set_metadata=set_metadata,
            namespace=namespace
        )
        return update_response

if __name__ == "__main__":
    # Import pinecone here
    from pinecone import Pinecone
    from pinecone import ServerlessSpec
    from omagent_core.models.encoders.openai_encoder import OpenaiTextEmbeddingV3
    import os

    # Initialize Pinecone
    pinecone_api_key = os.getenv('PINECONE_API_KEY')
    pc = Pinecone(api_key=pinecone_api_key)

    ltm = VectorPineconeLTM(index_id="test-index", pinecone_client=pc)
    # Register an encoder (ensure your encoder implements EncoderBase)
    openai_api_key = os.getenv('OPENAI_API_KEY')
    encoder = OpenaiTextEmbeddingV3(api_key=openai_api_key, endpoint="https://api.openai.com/v1/")
    ltm.encoder_register(modality="text", encoder=encoder)

    # Initialize knowledge base
    # Create a serverless index
    spec = ServerlessSpec(cloud='aws', region='us-east-1')
    ltm.init_memory(spec=spec)

    # Add data
    data = [
        {"color": "red", "content": "Hello World"},
        {"color": "blue", "content": "Hi there"},
        {"color": "green", "content": "Greetings"},
    ]
    encode_data = ["Hello World", "Hi there", "Greetings"]
    ltm.add_data(data=data, encode_data=encode_data, modality="text")
    print("Data added to Pinecone index.")

    # Match data
    results = ltm.match_data(
        query_data="Hello",
        modality="text",
        size=3,
        threshold=0.0,
        filters={"color": {"$in": ["red"]}}
    )
    print("Match Results:", results)

    # Delete data (use the IDs from the match results or your own IDs)
    ids_to_delete = [result['id'] for result in results]
    ltm.delete_data(ids=ids_to_delete)
