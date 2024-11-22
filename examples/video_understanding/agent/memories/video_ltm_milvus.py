from omagent_core.memories.ltms.ltm_base import LTMBase
import pickle
from omagent_core.utils.registry import registry
from omagent_core.services.connectors.milvus import MilvusConnector
from typing import Any, Iterable, Tuple, List, Optional
from pymilvus import CollectionSchema, FieldSchema, DataType, Collection, utility
import base64
import pickle
from typing import Any, Iterable, Tuple, List, Optional
from pydantic import Field


@registry.register_component()
class VideoMilvusLTM(LTMBase):
    milvus_ltm_client: MilvusConnector
    storage_name: str = Field(default='default')
    dim: int = Field(default=128)
    
    def model_post_init(self, __context: Any) -> None:        
        pass
    
    def _create_collection(self) -> None:  
        # Check if collection exists
        if not self.milvus_ltm_client._client.has_collection(self.storage_name):
            index_params = self.milvus_ltm_client._client.prepare_index_params()
            # Define field schemas
            key_field = FieldSchema(
                name="key", dtype=DataType.VARCHAR, is_primary=True, max_length=256
            )
            value_field = FieldSchema(
                name="value", dtype=DataType.JSON, description="Json value"
            )
            embedding_field = FieldSchema(
                name="embedding", dtype=DataType.FLOAT_VECTOR, description="Embedding vector", dim=self.dim
            )
            index_params = self.milvus_ltm_client._client.prepare_index_params()            

            # Create collection schema
            schema = CollectionSchema(
                fields=[key_field, value_field, embedding_field],
                description="Key-Value storage with embeddings",
            )
            for field in schema.fields:
                if (
                    field.dtype == DataType.FLOAT_VECTOR
                    or field.dtype == DataType.BINARY_VECTOR
                ):
                    index_params.add_index(
                        field_name=field.name,
                        index_name=field.name,
                        index_type="FLAT",
                        metric_type="COSINE",
                        params={"nlist": 128},
                    )
            self.milvus_ltm_client._client.create_collection(self.storage_name, schema=schema, index_params=index_params)            

            # Create index separately after collection creation                        
            print(f"Created storage {self.storage_name} successfully")

    def __getitem__(self, key: Any) -> Any:
        key_str = str(key)
        expr = f'key == "{key_str}"'
        res = self.milvus_ltm_client._client.query(self.storage_name, expr, output_fields=["value"])
        if res:
            value = res[0]['value']
            # value_bytes = base64.b64decode(value_base64)
            # value = pickle.loads(value_bytes)
            return value
        else:
            raise KeyError(f"Key {key} not found")
    
    def __setitem__(self, key: Any, value: Any) -> None:
        self._create_collection()

        key_str = str(key)

        # Check if value is a dictionary containing 'value' and 'embedding'
        if isinstance(value, dict) and 'value' in value and 'embedding' in value:
            actual_value = value['value']
            embedding = value['embedding']
        else:
            raise ValueError("When setting an item, value must be a dictionary containing 'value' and 'embedding' keys.")

        # Serialize the actual value and encode it to base64
        # value_bytes = pickle.dumps(actual_value)
        # value_base64 = base64.b64encode(value_bytes).decode('utf-8')

        # Ensure the embedding is provided
        if embedding is None:
            raise ValueError("An embedding vector must be provided.")

        # Check if the key exists and delete it if it does
        if key_str in self:
            self.__delitem__(key_str)

        # Prepare data for insertion (as a list of dictionaries)
        data = [
            {
                "key": key_str,
                "value": actual_value,
                "embedding": embedding,
            }
        ]

        # Insert the new record
        self.milvus_ltm_client._client.insert(collection_name=self.storage_name, data=data)


    def __delitem__(self, key: Any) -> None:
        key_str = str(key)
        if key_str in self:
            expr = f'key == "{key_str}"'
            self.milvus_ltm_client._client.delete(self.storage_name, expr)
        else:
            raise KeyError(f"Key {key} not found")

    def __contains__(self, key: Any) -> bool:
        key_str = str(key)
        expr = f'key == "{key_str}"'
        # Adjust the query call to match the expected signature
        res = self.milvus_ltm_client._client.query(
            self.storage_name,  # Pass the collection name as the first argument
            filter=expr,
            output_fields=["key"]
        )
        return len(res) > 0
    """
    def __len__(self) -> int:
        milvus_ltm.collection.flush()
        return self.collection.num_entities
    """
    def __len__(self) -> int:
        expr = 'key != ""'  # Expression to match all entities
        #self.milvus_ltm_client._client.load(refresh=True)
        results = self.milvus_ltm_client._client.query(self.storage_name, expr, output_fields=["key"], consistency_level="Strong")
        return len(results)

    def keys(self,limit=10) -> Iterable[Any]:
        expr = ""
        res = self.milvus_ltm_client._client.query(self.storage_name, expr, output_fields=["key"], limit=limit)
        return (item['key'] for item in res)

    def values(self) -> Iterable[Any]:
        expr = 'key != ""'  # Expression to match all active entities
        self.milvus_ltm_client._client.load(refresh=True)
        res = self.milvus_ltm_client._client.query(self.storage_name, expr, output_fields=["value"], consistency_level="Strong")
        for item in res:
            value_base64 = item['value']
            value_bytes = base64.b64decode(value_base64)
            value = pickle.loads(value_bytes)
            yield value

    def items(self) -> Iterable[Tuple[Any, Any]]:
        expr = 'key != ""'
        res = self.milvus_ltm_client._client.query(self.storage_name, expr, output_fields=["key", "value"])
        for item in res:
            key = item['key']
            value = item['value']
            # value_bytes = base64.b64decode(value_base64)
            # value = pickle.loads(value_bytes)
            yield (key, value)

    def get(self, key: Any, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def clear(self) -> None:
        expr = 'key != ""'  # This expression matches all records where 'key' is not empty
        self.milvus_ltm_client._client.delete(self.storage_name, filter=expr)

    def pop(self, key: Any, default: Any = None) -> Any:
        try:
            value = self[key]
            self.__delitem__(key)
            return value
        except KeyError:
            if default is not None:
                return default
            else:
                raise

    def update(self, other: Iterable[Tuple[Any, Any]]) -> None:
        for key, value in other:
            self[key] = value

    def get_by_vector(self, embedding: List[float], top_k: int = 10, threshold: float = 0.0, filter: str = "") -> List[Tuple[Any, Any, float]]:
        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10, "range_filter": 1, "radius": threshold},
        }
        results = self.milvus_ltm_client._client.search(
            self.storage_name,
            data=[embedding],
            anns_field="embedding",
            search_params=search_params,
            limit=top_k,
            output_fields=["key", "value"],
            consistency_level="Strong",
            filter=filter
        )

        items = []
        for match in results[0]:
            key = match.get("entity").get('key')
            value = match.get("entity").get('value')            
            items.append((key, value))

        return items