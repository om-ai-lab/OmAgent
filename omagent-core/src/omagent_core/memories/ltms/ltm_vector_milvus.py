from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel

from omagent_core.memories.ltms.ltm_base import LTMVecotrBase
from omagent_core.models.encoders.base import EncoderBase
from omagent_core.utils.error import VQLError


class VectorMilvusLTM(LTMVecotrBase):
    def __init__(self, index_id: str, milvus_client):
        self.encoders: Dict[str, EncoderBase] = {}
        self.dim: Optional[int] = None
        self.index_id: str = index_id
        # Initialize Milvus client
        self.milvus_client = milvus_client 

    def encoder_register(self, modality: str, encoder: EncoderBase):
        self.encoders[modality] = encoder
        if self.dim is None:
            self.dim = encoder.dim
        elif self.dim != encoder.dim:
            raise VQLError(500, detail="All encoders must have the same dimension")

    def init_memory(self, auto_id=False, schema=None, index_params=None) -> None:
        # Create collection
        """
        Initialize the Milvus collection for storing vectors.

        Args:
            auto_id (bool, optional): If True, Milvus will automatically generate IDs for inserted entities. 
                                      Defaults to True.
            schema (CollectionSchema, optional): Custom schema for the collection. If None, a default schema is used.
            index_params (dict, optional): Parameters for creating an index. If None, no index is created initially.

        Note:
            - The 'dimension' parameter is set based on the encoder's dimension (self.dim).
            - 'schema' and 'index_params' are currently not used in this implementation but can be 
              added for more advanced configurations.
        """
        # Print the dimension of vectors to be stored
        print(f"Initializing collection with vector dimension: {self.dim}")
        self.milvus_client.create_collection(
            collection_name=self.index_id,
            schema=schema,
            index_params=index_params,
            auto_id=auto_id,            
            dimension=self.dim
        )

    def add_data(
        self,
        data: List[Dict[str, Any]],
        encode_data: Optional[List[Any]] = None,
        modality: Optional[str] = None,
        target_field: Optional[str] = None,
    ) -> int:
        """
        Add data to the Milvus collection.

        Args:
            data (List[Dict[str, Any]]): List of dictionaries containing the data to be added.
            encode_data (Optional[List[Any]]): Data to be encoded if not pre-encoded.
            modality (Optional[str]): Modality of the data for encoding.
            target_field (Optional[str]): Field name containing pre-encoded vectors.

        Returns:
            int: Number of inserted records.

        Raises:
            VQLError: If there's a mismatch in data or missing required fields.
        """
        if encode_data:
            records = self._prepare_encode_data(data, encode_data, modality)
        elif target_field:
            records = self._prepare_target_field_data(data, target_field)
        else:
            records = data

        # Insert data into Milvus
        res = self.milvus_client.insert(
            collection_name=self.index_id,
            data=records
        )
        #res = {'insert_count': 3, 'ids': [453417917787420124, 453417917787420125, 453417917787420126]}
        return res

    def _prepare_encode_data(self, data, encode_data, modality):
        """Prepare data that needs to be encoded."""
        encoder = self.encoders.get(modality)
        if not encoder:
            raise VQLError(500, detail=f'Missing encoder for modality "{modality}"')
        
        vectors = encoder.infer(encode_data)
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
    ) -> List[Dict[str, Any]]:
        # Encode query data
        encoder = self.encoders.get(modality)
        if not encoder:
            raise VQLError(500, detail=f'Missing encoder for modality "{modality}"')
        vector = encoder.infer([query_data])[0]
        
        # Build search parameters
        search_params = {
            "metric_type": "COSINE",
            "params": {}
        }
        
        # Build filter expression
        filter_expr = ""
        if filters:
            filter_expr = " and ".join(f"{k} == '{v}'" for k, v in filters.items())
        
        # Perform search
        res = self.milvus_client.search(
            collection_name=self.index_id,
            data=[vector],
            limit=size,
            filter=filter_expr if filter_expr else None,
            search_params=search_params
        )
        
        results = []
        for hit in res[0]:
            if hit["distance"] >= threshold:
                results.append({
                    "id": hit["id"],
                    "score": hit["distance"],
                    "entity": hit["entity"]
                })
        return results

    def get_all_data(self, output_fields=["*"]):
        # Query all data
        res = self.milvus_client.query(
            collection_name=self.index_id,
            filter="",
            limit=10,
            output_fields=output_fields,            
        )
        return res

    def delete_data(self, ids: List[str]):
        # Delete data
        expr = f"id in [" + ", ".join(f"{id}" for id in ids) + "]"
        res = self.milvus_client.delete(
            collection_name=self.index_id,
            filter=expr
        )
        return res

if __name__ == "__main__":
    from omagent_core.models.encoders.openai_encoder import OpenaiTextEmbeddingV3
    import os
    from pymilvus import MilvusClient    
    milvus_client = MilvusClient(
            uri="http://localhost:19530",
            token=""
        )
    ltm = VectorMilvusLTM(index_id="test_collection5", milvus_client=milvus_client)
    api_key = os.getenv('OPENAI_API_KEY')
    # Register an encoder (ensure your encoder implements EncoderBase)
    
    encoder = OpenaiTextEmbeddingV3(api_key=api_key, endpoint="https://api.openai.com/v1/")
    ltm.encoder_register(modality="text", encoder=encoder)

    # Initialize knowledge base
    ltm.init_memory()

    # Add data
    data = [
    {"id":1, "color": "red", "content":"Hello World"},
    {"id":2, "color": "blue",  "content":"Hi there"},
    {"id":3, "color": "green",   "content": "Greetings"},
    ]
    encode_data = ["Hello World", "Hi there", "Greetings"]
    ltm.add_data(data=data, encode_data=encode_data, modality="text")
    all_data = ltm.get_all_data(output_fields=["color","id"])
    print("All Data:", all_data)
    # Match data    
    results = ltm.match_data(
        query_data="Hello",
        modality="text",
        size=3,
        threshold=0.0,
        filters={"color": "red"}
    )
    print("Match Results:", results)

    # Get all data
    all_data = ltm.get_all_data()
    print("All Data:", all_data)

    # Delete data
    ltm.delete_data(ids=[1])
