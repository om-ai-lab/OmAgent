from omagent_core.memories.ltms.ltm_base import LTMBase
import pickle
from omagent_core.utils.registry import registry
from omagent_core.services.connectors.milvus import MilvusConnector
from typing import Any, Iterable, Tuple, List, Optional
from pymilvus import CollectionSchema, FieldSchema, DataType, Collection, utility
import base64
import pickle
from typing import Any, Iterable, Tuple, List, Optional


@registry.register_component()
class MilvusLTM(LTMBase):
    def __init__(self, milvus_ltm_client: MilvusConnector, storage_name: str = 'default', dim: int = 128):
        super().__init__()
        self.milvus_ltm_client = milvus_ltm_client
        self.storage_name = storage_name
        self.dim = dim
        self.connection_alias = self.milvus_ltm_client.alias

        # Check if collection exists
        if not utility.has_collection(self.storage_name, using=self.connection_alias):
            # Define field schemas
            key_field = FieldSchema(
                name="key", dtype=DataType.VARCHAR, is_primary=True, max_length=256
            )
            value_field = FieldSchema(
                name="value", dtype=DataType.VARCHAR, description="Serialized value", max_length=65535
            )
            embedding_field = FieldSchema(
                name="embedding", dtype=DataType.FLOAT_VECTOR, description="Embedding vector", dim=self.dim
            )

            # Create collection schema
            schema = CollectionSchema(
                fields=[key_field, value_field, embedding_field],
                description="Key-Value storage with embeddings",
            )
            # Create collection
            self.collection = Collection(
                name=self.storage_name,
                schema=schema,
                using=self.connection_alias
            )

            # Create index separately after collection creation
            index_params = {
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128}
            }
            self.collection.create_index(
                field_name="embedding",
                index_params=index_params
            )
            self.collection.load()
            print(f"Created collection {self.storage_name} successfully")
        else:
            # Load the existing collection
            self.collection = Collection(
                name=self.storage_name,
                using=self.connection_alias
            )
            self.collection.load()
            print(f"{self.storage_name} collection already exists")

    def __getitem__(self, key: Any) -> Any:
        key_str = str(key)
        expr = f'key == "{key_str}"'
        res = self.collection.query(expr, output_fields=["value"])
        if res:
            value_base64 = res[0]['value']
            value_bytes = base64.b64decode(value_base64)
            value = pickle.loads(value_bytes)
            return value
        else:
            raise KeyError(f"Key {key} not found")
    
    def __setitem__(self, key: Any, value: Any) -> None:
        key_str = str(key)

        # Check if value is a dictionary containing 'value' and 'embedding'
        if isinstance(value, dict) and 'value' in value and 'embedding' in value:
            actual_value = value['value']
            embedding = value['embedding']
        else:
            raise ValueError("When setting an item, value must be a dictionary containing 'value' and 'embedding' keys.")

        # Serialize the actual value and encode it to base64
        value_bytes = pickle.dumps(actual_value)
        value_base64 = base64.b64encode(value_bytes).decode('utf-8')

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
                "value": value_base64,
                "embedding": embedding,
            }
        ]

        # Insert the new record
        self.collection.insert(data)

    def __setitem2__(self, key: Any, value: Any, embedding: Optional[List[float]] = None) -> None:
        key_str = str(key)
        value_bytes = pickle.dumps(value)
        value_base64 = base64.b64encode(value_bytes).decode('utf-8')

        if embedding is None:
            raise ValueError("An embedding vector must be provided.")

        if key_str in self:
            self.__delitem__(key_str)

        data = [
            {
                "key": key_str,
                "value": value_base64,
                "embedding": embedding,
            }
        ]

        self.collection.insert(data)

    def __delitem__(self, key: Any) -> None:
        key_str = str(key)
        if key_str in self:
            expr = f'key == "{key_str}"'
            self.collection.delete(expr)
        else:
            raise KeyError(f"Key {key} not found")

    def __contains__(self, key: Any) -> bool:
        key_str = str(key)
        expr = f'key == "{key_str}"'
        res = self.collection.query(expr, output_fields=["key"])
        return len(res) > 0
    """
    def __len__(self) -> int:
        milvus_ltm.collection.flush()
        return self.collection.num_entities
    """
    def __len__(self) -> int:
        expr = 'key != ""'  # Expression to match all entities
        self.collection.load(refresh=True)
        results = self.collection.query(expr, output_fields=["key"], consistency_level="Strong")
        return len(results)

    def keys(self,limit=10) -> Iterable[Any]:
        expr = ""
        res = self.collection.query(expr, output_fields=["key"], limit=limit)
        return (item['key'] for item in res)

    def values(self) -> Iterable[Any]:
        expr = 'key != ""'  # Expression to match all active entities
        self.collection.load(refresh=True)
        res = self.collection.query(expr, output_fields=["value"], consistency_level="Strong")
        for item in res:
            value_base64 = item['value']
            value_bytes = base64.b64decode(value_base64)
            value = pickle.loads(value_bytes)
            yield value

    def items(self) -> Iterable[Tuple[Any, Any]]:
        expr = 'key != ""'
        res = self.collection.query(expr, output_fields=["key", "value"])
        for item in res:
            key = item['key']
            value_base64 = item['value']
            value_bytes = base64.b64decode(value_base64)
            value = pickle.loads(value_bytes)
            yield (key, value)

    def get(self, key: Any, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def clear(self) -> None:
        expr = 'key != ""'  # This expression matches all records where 'key' is not empty
        self.collection.delete(expr)
        # Optionally, flush and wait for the deletion to complete
        self.collection.flush()
        #utility.wait_for_flushed(collection_name=self.collection.name)

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

    def get_by_vector(self, embedding: List[float], top_k: int = 10, threshold: float = 0.0) -> List[Tuple[Any, Any, float]]:
        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10},
        }
        results = self.collection.search(
            data=[embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["key", "value"],
            consistency_level="Strong",
        )

        items = []
        for match in results[0]:
            key = match.entity.get('key')
            value_base64 = match.entity.get('value')
            value_bytes = base64.b64decode(value_base64)
            value = pickle.loads(value_bytes)
            distance = match.distance
            if distance >= threshold:
                items.append((key, value, distance))

        return items


if __name__ == "__main__":
    milvus_ltm_client = MilvusConnector()
    milvus_ltm = MilvusLTM(milvus_ltm_client=milvus_ltm_client, dim=128, storage_name='test3')
    #print(milvus_ltm["key"])
    #milvus_ltm.clear()
    embedding_vector = [0.1] * 128  # Replace with actual 128-dimensional vector
    milvus_ltm['0'] = {"value": {"abc":"abc"}, "embedding": embedding_vector}
    
    print(len(milvus_ltm))
    print (milvus_ltm["1"])

    for key in milvus_ltm.keys():
        print(key)
    for value in milvus_ltm.items():
        print (value)
    
    # Set an item with an embedding
    embedding_vector = [0.1] * 128  # Replace with actual 128-dimensional vector
    #milvus_ltm.__setitem__('key', 'value', embedding=embedding_vector)

    # Search for similar items
    query_embedding = [0.15] * 128  # Replace with actual 128-dimensional vector
    similar_items = milvus_ltm.get_by_vector(query_embedding, top_k=5)
    for key, value, distance in similar_items:
        print(f"Key: {key}, Value: {value}, Distance: {distance}")