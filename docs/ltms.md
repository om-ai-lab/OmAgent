# **VectorMilvusLTM**

The `VectorMilvusLTM` class provides an interface for storing and retrieving vector embeddings using the [Milvus](https://milvus.io/) vector database. It acts as a Long-Term Memory (LTM) component in applications that require vector-based storage and retrieval, such as similarity search, recommendation systems, and AI applications involving embeddings.

## **Overview**

The `VectorMilvusLTM` class manages vector data storage and retrieval using Milvus. It supports:

- Registering encoders for different data modalities.
- Initializing a Milvus collection with specified dimensions.
- Adding data with or without encoding.
- Querying similar vectors based on a query vector.
- Deleting vectors from the collection.

## **Initialization**

```python
def __init__(self, index_id: str, milvus_client):
```

- `index_id` (str): The name of the Milvus collection to use.
- `milvus_client`: An instance of the Milvus client.

**Example:**

```python
from pymilvus import Milvus

milvus_client = Milvus()
ltm = VectorMilvusLTM(index_id="my_collection", milvus_client=milvus_client)
```

## **Methods**

### **encoder_register**

```python
def encoder_register(self, modality: str, encoder: EncoderBase):
```

Registers an encoder for a specific data modality.

- `modality` (str): The modality of the data (e.g., "text", "image").
- `encoder` (EncoderBase): An encoder instance that implements `EncoderBase`.

**Usage:**

```python
encoder = OpenaiTextEmbeddingV3(api_key=api_key)
ltm.encoder_register(modality="text", encoder=encoder)
```

### **init_memory**

```python
def init_memory(self, auto_id=True, schema=None, index_params=None) -> None:
```

Initializes the Milvus collection.

- `auto_id` (bool, optional): If `True`, Milvus auto-generates IDs. Defaults to `True`.
- `schema` (optional): Custom schema for the collection.
- `index_params` (dict, optional): Parameters for creating an index.

**Usage:**

```python
ltm.init_memory()
```

### **add_data**

```python
def add_data(
    self,
    data: List[Dict[str, Any]],
    encode_data: Optional[List[Any]] = None,
    modality: Optional[str] = None,
    target_field: Optional[str] = None,
) -> int:
```

Adds data to the Milvus collection.

- `data` (List[Dict[str, Any]]): List of records to add.
- `encode_data` (Optional[List[Any]]): Data to be encoded.
- `modality` (Optional[str]): Modality for encoding.
- `target_field` (Optional[str]): Field to be encoded.

**Returns:**

- `int`: Number of records inserted.

**Usage:**

```python
data = [{"color": "red", "content": "Hello World"}]
encode_data = ["Hello World"]
ltm.add_data(data=data, encode_data=encode_data, modality="text")
```

### **match_data**

```python
def match_data(
    self,
    query_data: Any,
    modality: str,
    filters: Dict[str, Any] = {},
    threshold: float = -1.0,
    size: int = 10,
) -> List[Dict[str, Any]]:
```

Queries the Milvus collection for similar vectors.

- `query_data` (Any): Data to query.
- `modality` (str): Modality of the data.
- `filters` (Dict[str, Any], optional): Filters to apply.
- `threshold` (float, optional): Similarity threshold.
- `size` (int, optional): Number of results to return.

**Returns:**

- `List[Dict[str, Any]]`: List of matching records.

**Usage:**

```python
results = ltm.match_data(
    query_data="Hello",
    modality="text",
    size=3,
    threshold=0.0,
    filters={"color": "red"}
)
```

### **get_all_data**

```python
def get_all_data(self, output_fields=["*"]):
```

Retrieves all data from the collection.

- `output_fields` (List[str], optional): Fields to include in the output.

**Returns:**

- Data retrieved from Milvus.

**Usage:**

```python
all_data = ltm.get_all_data(output_fields=["color", "id"])
```

### **delete_data**

```python
def delete_data(self, ids: List[str]):
```

Deletes data from the collection by IDs.

- `ids` (List[str]): List of IDs to delete.

**Usage:**

```python
ltm.delete_data(ids=["1", "2", "3"])
```

## **Usage Example**

```python
from omagent_core.models.encoders.openai_encoder import OpenaiTextEmbeddingV3
from pymilvus import Milvus
import os

# Initialize Milvus client
milvus_client = Milvus()
ltm = VectorMilvusLTM(index_id="my_collection", milvus_client=milvus_client)

# Register an encoder
api_key = os.getenv('OPENAI_API_KEY')
encoder = OpenaiTextEmbeddingV3(api_key=api_key)
ltm.encoder_register(modality="text", encoder=encoder)

# Initialize the memory (collection)
ltm.init_memory()

# Add data
data = [
    {"color": "red", "content": "Hello World"},
    {"color": "blue", "content": "Hi there"},
    {"color": "green", "content": "Greetings"},
]
encode_data = ["Hello World", "Hi there", "Greetings"]
ltm.add_data(data=data, encode_data=encode_data, modality="text")

# Query data
results = ltm.match_data(
    query_data="Hello",
    modality="text",
    size=3,
    threshold=0.0,
    filters={"color": "red"}
)
print("Match Results:", results)

# Get all data
all_data = ltm.get_all_data(output_fields=["color", "id"])
print("All Data:", all_data)

# Delete data
ltm.delete_data(ids=[result["id"] for result in results])
```

## **Notes**

- **Encoders:** Ensure that the encoder you use implements the `EncoderBase` interface and has an `infer` method.
- **Milvus Client:** The `milvus_client` must be an instance of the Milvus client, properly configured to connect to your Milvus server.
- **Data Consistency:** When adding data, make sure that the length of `encode_data` matches the length of `data`.

---

# **VectorPineconeLTM**

The `VectorPineconeLTM` class provides an interface for storing and retrieving vector embeddings using the [Pinecone](https://www.pinecone.io/) vector database. It acts as a Long-Term Memory (LTM) component in applications that require vector-based storage and retrieval.


## **Overview**

The `VectorPineconeLTM` class manages vector data storage and retrieval using Pinecone. It supports:

- Registering encoders for different data modalities.
- Initializing a Pinecone index with specified configurations.
- Adding data with or without encoding.
- Querying similar vectors based on a query vector.
- Deleting, fetching, and updating vectors in the index.

## **Initialization**

```python
def __init__(self, index_id: str, pinecone_client):
```

- `index_id` (str): The name of the Pinecone index to use.
- `pinecone_client`: An instance of the Pinecone client (`Pinecone` class).

**Example:**

```python
from pinecone import Pinecone

pc = Pinecone(api_key='YOUR_API_KEY')
ltm = VectorPineconeLTM(index_id="my_index", pinecone_client=pc)
```

## **Methods**

### **encoder_register**

```python
def encoder_register(self, modality: str, encoder: EncoderBase):
```

Registers an encoder for a specific data modality.

- `modality` (str): The modality of the data (e.g., "text", "image").
- `encoder` (EncoderBase): An encoder instance that implements `EncoderBase`.

**Usage:**

```python
encoder = OpenaiTextEmbeddingV3(api_key=api_key)
ltm.encoder_register(modality="text", encoder=encoder)
```

### **init_memory**

```python
def init_memory(self, spec=None, metric="cosine", deletion_protection='disabled', **kwargs) -> None:
```

Initializes the Pinecone index.

- `spec` (Optional): Specification for the index (e.g., `ServerlessSpec`, `PodSpec`).
- `metric` (str, optional): Similarity metric. Defaults to `"cosine"`.
- `deletion_protection` (str, optional): Deletion protection setting (`'enabled'` or `'disabled'`). Defaults to `'disabled'`.
- `**kwargs`: Additional parameters for index creation.

**Usage:**

```python
from pinecone import ServerlessSpec

spec = ServerlessSpec(cloud='aws', region='us-west-2')
ltm.init_memory(spec=spec)
```

### **add_data**

```python
def add_data(
    self,
    data: List[Dict[str, Any]],
    encode_data: Optional[List[Any]] = None,
    modality: Optional[str] = None,
    target_field: Optional[str] = None,
    namespace: Optional[str] = None,
) -> int:
```

Adds data to the Pinecone index.

- `data` (List[Dict[str, Any]]): List of records to add.
- `encode_data` (Optional[List[Any]]): Data to be encoded.
- `modality` (Optional[str]): Modality for encoding.
- `target_field` (Optional[str]): Field containing pre-encoded vectors.
- `namespace` (Optional[str]): Namespace for organizing data.

**Returns:**

- `int`: Number of records inserted.

**Usage:**

```python
data = [{"color": "red", "content": "Hello World"}]
encode_data = ["Hello World"]
ltm.add_data(data=data, encode_data=encode_data, modality="text")
```

### **match_data**

```python
def match_data(
    self,
    query_data: Any,
    modality: str,
    filters: Dict[str, Any] = {},
    threshold: float = -1.0,
    size: int = 10,
    namespace: Optional[str] = None,
) -> List[Dict[str, Any]]:
```

Queries the Pinecone index for similar vectors.

- `query_data` (Any): Data to query.
- `modality` (str): Modality of the data.
- `filters` (Dict[str, Any], optional): Filters to apply.
- `threshold` (float, optional): Similarity threshold.
- `size` (int, optional): Number of results to return.
- `namespace` (Optional[str]): Namespace of the data.

**Returns:**

- `List[Dict[str, Any]]`: List of matching records.

**Usage:**

```python
results = ltm.match_data(
    query_data="Hello",
    modality="text",
    size=3,
    threshold=0.0,
    filters={"color": {"$in": ["red"]}}
)
```

### **delete_data**

```python
def delete_data(self, ids: List[str], namespace: Optional[str] = None):
```

Deletes data from the index by IDs.

- `ids` (List[str]): List of IDs to delete.
- `namespace` (Optional[str]): Namespace of the data.

**Usage:**

```python
ltm.delete_data(ids=["id1", "id2"], namespace="my_namespace")
```

### **fetch_data**

```python
def fetch_data(self, ids: List[str], namespace: Optional[str] = None):
```

Fetches data from the index by IDs.

- `ids` (List[str]): List of IDs to fetch.
- `namespace` (Optional[str]): Namespace of the data.

**Returns:**

- Fetch response from Pinecone.

**Usage:**

```python
fetch_response = ltm.fetch_data(ids=["id1", "id2"])
```

### **update_data**

```python
def update_data(
    self,
    id: str,
    values: Optional[List[float]] = None,
    set_metadata: Optional[Dict[str, Any]] = None,
    namespace: Optional[str] = None
):
```

Updates a vector in the index.

- `id` (str): ID of the vector to update.
- `values` (Optional[List[float]]): New vector values.
- `set_metadata` (Optional[Dict[str, Any]]): Metadata to update.
- `namespace` (Optional[str]): Namespace of the data.

**Usage:**

```python
ltm.update_data(
    id="id1",
    values=[0.1, 0.2, 0.3],
    set_metadata={"color": "yellow"}
)
```

## **Usage Example**

```python
from pinecone import Pinecone, ServerlessSpec
from omagent_core.models.encoders.openai_encoder import OpenaiTextEmbeddingV3
import os

# Initialize Pinecone client
pinecone_api_key = os.getenv('PINECONE_API_KEY')
pc = Pinecone(api_key=pinecone_api_key)

# Initialize the LTM
ltm = VectorPineconeLTM(index_id="test_index", pinecone_client=pc)

# Register an encoder
openai_api_key = os.getenv('OPENAI_API_KEY')
encoder = OpenaiTextEmbeddingV3(api_key=openai_api_key)
ltm.encoder_register(modality="text", encoder=encoder)

# Initialize the index
spec = ServerlessSpec(cloud='aws', region='us-west-2')
ltm.init_memory(spec=spec)

# Add data
data = [
    {"color": "red", "content": "Hello World"},
    {"color": "blue", "content": "Hi there"},
    {"color": "green", "content": "Greetings"},
]
encode_data = ["Hello World", "Hi there", "Greetings"]
ltm.add_data(data=data, encode_data=encode_data, modality="text")

# Perform a match
results = ltm.match_data(
    query_data="Hello",
    modality="text",
    size=3,
    threshold=0.0,
    filters={"color": {"$in": ["red"]}}
)
print("Match Results:", results)

# Delete data
ids_to_delete = [result['id'] for result in results]
ltm.delete_data(ids=ids_to_delete)
```

## **Notes**

- **Pinecone Client:** The `pinecone_client` must be an instance of the `Pinecone` class, properly initialized with your API key.
- **Index Specifications:** You can specify the index type (`ServerlessSpec` or `PodSpec`) and configurations during initialization.
- **Encoders:** Ensure that the encoder implements the `EncoderBase` interface and provides an `infer` method.
- **Filters:** When using filters in `match_data`, make sure the filter syntax matches Pinecone's filtering capabilities.
- **Thresholds:** Adjust the `threshold` parameter based on the similarity metric used. For example, with the cosine metric, scores range from `-1` to `1`.

---
