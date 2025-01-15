from typing import Any
from uuid import uuid4

import numpy as np
from omagent_core.utils.error import VQLError
from omagent_core.utils.registry import registry
from pydantic import BaseModel
from pymilvus import Collection, DataType, MilvusClient, connections, utility
from pymilvus.client import types


@registry.register_component()
class MilvusHandler(BaseModel):
    host_url: str = "./memory.db"
    user: str = ""
    password: str = ""
    db_name: str = "default"
    primary_field: Any = None
    vector_field: Any = None

    class Config:
        """Configuration for this pydantic object."""

        extra = "allow"
        arbitrary_types_allowed = True

    def __init__(self, **data: Any):
        super().__init__(**data)
        self.milvus_client = MilvusClient(
            uri=self.host_url,
            user=self.user,
            password=self.password,
            db_name=self.db_name,
        )

    def is_collection_in(self, collection_name):
        """
        Check if a collection exists in Milvus.

        Args:
            collection_name (str): The name of the collection to check.

        Returns:
            bool: True if the collection exists, False otherwise.
        """
        return self.milvus_client.has_collection(collection_name)

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

        index_params = self.milvus_client.prepare_index_params()
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
                print(f"{field.name} of {collection_name} index created")

        if self.is_collection_in(collection_name):
            print(f"{collection_name} collection already exists")
        else:
            self.milvus_client.create_collection(
                collection_name, schema=schema, index_params=index_params
            )
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
            self.milvus_client.drop_collection(collection_name)
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
            res = self.milvus_client.insert(
                collection_name=collection_name, data=vectors
            )
            return res["ids"]
        else:
            raise VQLError(500, detail=f"{collection_name} collection does not exist")

    def match(
        self,
        collection_name,
        query_vectors: list,
        query_field,
        output_fields: list = None,
        res_size=10,
        filter_expr="",
        threshold=0,
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
            search_params = {
                "metric_type": "COSINE",
                "ignore_growing": False,
                "params": {
                    "nprobe": 10,
                    "radius": 2 * threshold - 1,
                    "range_filter": 1,
                },
            }
            hits = self.milvus_client.search(
                collection_name=collection_name,
                data=query_vectors,
                anns_field=query_field,
                search_params=search_params,
                limit=res_size,
                output_fields=output_fields,
                filter=filter_expr,
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
            delete_expr = f"{self.primary_field} in {ids}"
            res = self.milvus_client.delete(
                collection_name=collection_name, filter=delete_expr
            )
            return res
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
            self.milvus_client.delete(collection_name=collection_name, filter=expr)
        else:
            raise VQLError(500, detail=f"{collection_name} collection does not exist")


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
        {
            "pk": str(uuid4()),
            "bot_id": str(uuid4()),
            # rng.random((1, 512))
            "vector": [1.0, 2.0] * 256,
        }
    ]
    milvus_handler.drop_collection("test1")
    milvus_handler.make_collection("test1", schema)
    add_detail = milvus_handler.do_add("test1", data)
    print(add_detail)
    print(milvus_handler.milvus_client.describe_index("test1", "vector"))
    test_data = [[1.0, 2.0] * 256, [100, 400] * 256]
    match_result = milvus_handler.match(
        "test1", test_data, "vector", ["pk"], 10, "", 0.65
    )
    print(match_result)
    # milvus_handler.primary_field = "pk"
    # milvus_handler.delete_doc_by_ids("test1", ["1f764837-b80b-4788-ad8c-7a89924e343b"])
