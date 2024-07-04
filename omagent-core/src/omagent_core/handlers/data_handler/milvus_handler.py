from uuid import uuid4
from typing import Any
import numpy as np
from pymilvus import Collection, DataType, connections, utility
from pymilvus.client import types
from pydantic import BaseModel

from ...utils.env import EnvVar
from ...utils.registry import registry
from ..error_handler.error import VQLError


@registry.register_handler()
class MilvusHandler(BaseModel):
    # todo: host_url, port, alias configuration use config json
    host_url: str
    port: str
    alias: str
    primary_field: Any = None
    vector_field: Any = None
    index_id: str

    def __init__(self, **data: Any):
        super().__init__(**data)
        connections.connect(host=self.host_url, port=self.port, alias=self.alias)

    def is_collection_in(self, collection_name):
        """
        Check if a collection exists in Milvus.

        Args:
            collection_name (str): The name of the collection to check.

        Returns:
            bool: True if the collection exists, False otherwise.
        """
        return utility.has_collection(collection_name)

    def make_collection(self, collection_name, schema):
        """
        Create a new collection in Milvus.

        This method will first check if a collection with the given name already exists.
        If it does, it will print a message and do nothing.
        If it doesn't, it will create a new collection with the given name and schema,
        and then create an index for the vector field in the collection.

        Args:
            collection_name (str): The name of the collection to create.
            schema (CollectionSchema): The schema of the collection to create.

        Raises:
            VQLError: If the schema does not have exactly one primary key.
        """
        self.vector_field = [
            each.name
            for each in schema.fields
            if each.dtype == DataType.FLOAT_VECTOR
            or each.dtype == DataType.BINARY_VECTOR
        ]
        primary_candidate = [each.name for each in schema.fields if each.is_primary]
        if len(primary_candidate) > 0:
            self.primary_field = primary_candidate[0]
        else:
            raise VQLError(500, detail="The number of primary key is not one!")

        if self.is_collection_in(collection_name):
            print(f"{collection_name} collection already exists")
        else:
            Collection(name=collection_name, schema=schema, using=self.alias)
            self.create_index(collection_name, self.vector_field)
            print(f"Create collection {collection_name} successfully")

    def drop_collection(self, collection_name):
        """
        Drop a collection in Milvus.

        This method will first check if a collection with the given name exists.
        If it does, it will drop the collection and print a success message.
        If it doesn't, it will print a message indicating that the collection does not exist.

        Args:
            collection_name (str): The name of the collection to drop.
        """
        if self.is_collection_in(collection_name):
            collection = Collection(name=collection_name, using=self.alias)
            collection.drop()
            print(f"Drop collection {collection_name} successfully")
        else:
            print(f"{collection_name} collection does not exist")

    def do_add(self, collection_name, vectors):
        """
        Add vectors to a collection in Milvus.

        This method will first check if a collection with the given name exists.
        If it does, it will add the vectors to the collection and return the IDs of the added vectors.
        If it doesn't, it will raise a VQLError.

        Args:
            collection_name (str): The name of the collection to add vectors to.
            vectors (list): The vectors to add to the collection.

        Returns:
            list: The IDs of the added vectors.

        Raises:
            VQLError: If the collection does not exist.
        """
        if self.is_collection_in(collection_name):
            loaded_collection = Collection(collection_name)
            ids = loaded_collection.insert(vectors)
            loaded_collection.flush()
            return ids
        else:
            raise VQLError(500, detail=f"{collection_name} collection does not exist")

    def create_index(self, collection_name, vector_fields):
        """
        Create an index for the specified vector fields in a collection in Milvus.

        This method will first check if a collection with the given name exists.
        If it does, it will create an index for each of the specified vector fields in the collection.
        If it doesn't, it will raise a VQLError.

        Args:
            collection_name (str): The name of the collection to create an index in.
            vector_fields (list): The list of vector fields to create an index for.

        Raises:
            VQLError: If the collection does not exist.
        """
        if self.is_collection_in(collection_name):
            loaded_collection = Collection(collection_name)
            for vector_field in vector_fields:
                index = {
                    "index_type": "IVF_FLAT",
                    "metric_type": "COSINE",
                    "params": {"nlist": 128},
                }
                loaded_collection.create_index(vector_field, index)
                print(f"{vector_field} of {collection_name} index created")
        else:
            raise VQLError(500, detail=f"{collection_name} collection does not exist")

    def match(
        self,
        collection_name,
        query_vectors: list,
        query_field,
        output_fields: list,
        res_size,
        filter_expr,
        threshold,
    ):
        """
        Perform a vector similarity search in a specified collection in Milvus.

        This method will first check if a collection with the given name exists.
        If it does, it will perform a vector similarity search using the provided query vectors,
        and return the search results.
        If it doesn't, it will raise a VQLError.

        Args:
            collection_name (str): The name of the collection to search in.
            query_vectors (list): The vectors to use as query for the search.
            query_field (str): The field to perform the search on.
            output_fields (list): The fields to include in the search results.
            res_size (int): The maximum number of search results to return.
            filter_expr (str): The filter expression to apply during the search.
            threshold (float): The threshold for the similarity search.

        Returns:
            list: The search results.

        Raises:
            VQLError: If the collection does not exist.
        """
        if self.is_collection_in(collection_name):
            loaded_collection = Collection(collection_name)
            if utility.load_state(collection_name) != types.LoadState.Loaded:
                loaded_collection.load()
            search_params = {
                "metric_type": "COSINE",
                "ignore_growing": False,
                "params": {
                    "nprobe": 10,
                    "radius": 2 * threshold - 1,
                    "range_filter": 1,
                },
            }
            hits = loaded_collection.search(
                data=query_vectors,
                anns_field=query_field,
                param=search_params,
                limit=res_size,
                output_fields=output_fields,
                expr=filter_expr,
            )
            return hits
        else:
            raise VQLError(500, detail=f"{collection_name} collection does not exist")

    def delete_doc_by_ids(self, collection_name, ids):
        """
        Delete specific documents in a collection in Milvus by their IDs.

        This method will first check if a collection with the given name exists.
        If it does, it will delete the documents with the provided IDs from the collection.
        If it doesn't, it will raise a VQLError.

        Args:
            collection_name (str): The name of the collection to delete documents from.
            ids (list): The IDs of the documents to delete.

        Raises:
            VQLError: If the collection does not exist.
        """
        if self.is_collection_in(collection_name):
            loaded_collection = Collection(collection_name)
            delete_expr = f"{self.primary_field} in {ids}"
            loaded_collection.delete(delete_expr)
        else:
            raise VQLError(500, detail=f"{collection_name} collection does not exist")

    def delete_doc_by_expr(self, collection_name, expr):
        """
        Delete specific documents in a collection in Milvus by an expression.

        This method will first check if a collection with the given name exists.
        If it does, it will delete the documents that match the provided expression from the collection.
        If it doesn't, it will raise a VQLError.

        Args:
            collection_name (str): The name of the collection to delete documents from.
            expr (str): The expression to match the documents to delete.

        Raises:
            VQLError: If the collection does not exist.
        """
        if self.is_collection_in(collection_name):
            loaded_collection = Collection(collection_name)
            loaded_collection.delete(expr)
        else:
            raise VQLError(500, detail=f"{collection_name} collection does not exist")


# todo: 根据其他信息找primary key


if __name__ == "__main__":
    from pymilvus import CollectionSchema, DataType, FieldSchema

    milvus_handler = MilvusHandler()
    rng = np.random.default_rng()
    pk = FieldSchema(
        name="pk",
        dtype=DataType.VARCHAR,
        is_primary=True,
        auto_id=False,
        max_length=100,
    )
    bot_id = FieldSchema(name="bot_id", dtype=DataType.VARCHAR, max_length=50)
    vector = FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=512)
    schema = CollectionSchema(
        fields=[pk, bot_id, vector],
        description="this is test",
    )

    data = [
        [str(uuid4())] * 1,
        [str(uuid4())] * 1,
        # rng.random((1, 512))
        [[1, 2] * 256],
    ]
    # milvus_handler.drop_collection('test1')
    # milvus_handler.make_collection('test1', schema)
    add_detail = milvus_handler.do_add("test1", data)
    print(add_detail)
    # test_data =
    # match_result = milvus_handler.match('test1', [test_data], 'vector', ['pk'], 10, '', 0.65)
    # print(match_result)
    milvus_handler.primary_field = "pk"
    milvus_handler.delete_doc_by_ids("test1", "5b50a621-7745-41fc-87d8-726f7e1e51cf")
