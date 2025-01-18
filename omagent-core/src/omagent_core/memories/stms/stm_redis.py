import pickle
from typing import Any

from omagent_core.memories.stms.stm_base import STMBase, WorkflowInstanceProxy
from omagent_core.services.connectors.redis import RedisConnector
from omagent_core.utils.registry import registry


@registry.register_component()
class RedisSTM(STMBase):
    redis_stm_client: RedisConnector

    def __call__(self, workflow_instance_id: str):
        """
        Return a WorkflowInstanceProxy for the given workflow instance ID.

        Args:
            workflow_instance_id (str): The ID of the workflow instance.

        Returns:
            WorkflowInstanceProxy: A proxy object for accessing the workflow instance data.
        """
        return WorkflowInstanceProxy(self, workflow_instance_id)

    def __getitem__(self, key: tuple | str) -> Any:
        """
        Retrieve an item or all items from the Redis storage.

        Args:
            key (tuple | str): Either a tuple containing (workflow_instance_id, key) or just workflow_instance_id

        Returns:
            Any: The value associated with the given key, or a dictionary of all key-value pairs for the workflow_instance_id.

        Raises:
            KeyError: If the key is not found in the Redis storage.
        """
        if isinstance(key, tuple):
            workflow_instance_id, key = key
            value = self.redis_stm_client._client.hget(workflow_instance_id, key)
            if value is not None:
                return pickle.loads(value)
            raise KeyError(key)
        else:
            workflow_instance_id = key
            all_items = self.redis_stm_client._client.hgetall(workflow_instance_id)
            if not all_items:
                return {}
            return {k.decode("utf-8"): pickle.loads(v) for k, v in all_items.items()}

    def __setitem__(self, key: tuple, value: Any) -> None:
        """
        Set an item in the Redis storage.

        Args:
            key (tuple): A tuple containing (workflow_instance_id, key)
            value (Any): The value to associate with the key.
        """
        workflow_instance_id, key = key
        self.redis_stm_client._client.hset(
            workflow_instance_id, key, pickle.dumps(value)
        )

    def __delitem__(self, workflow_instance_id: str, key: str) -> None:
        """
        Delete an item from the Redis storage.

        Args:
            workflow_instance_id (str): The ID of the workflow instance.
            key (str): The key of the item to delete.

        Raises:
            KeyError: If the key is not found in the Redis storage.
        """
        if not self.redis_stm_client._client.hdel(workflow_instance_id, key):
            raise KeyError(key)

    def __contains__(self, key: tuple) -> bool:
        """
        Check if a key exists in the Redis storage.

        Args:
            key (tuple): A tuple containing (workflow_instance_id, key)

        Returns:
            bool: True if the key exists, False otherwise.
        """
        workflow_instance_id, key = key
        return self.redis_stm_client._client.hexists(workflow_instance_id, key)

    def keys(self, workflow_instance_id: str) -> list:
        """
        Get a list of all keys in the Redis storage for a workflow instance.

        Args:
            workflow_instance_id (str): The ID of the workflow instance.

        Returns:
            list: A list containing all keys.
        """
        return [
            k.decode("utf-8")
            for k in self.redis_stm_client._client.hkeys(workflow_instance_id)
        ]

    def values(self, workflow_instance_id: str) -> list:
        """
        Get a list of all values in the Redis storage for a workflow instance.

        Args:
            workflow_instance_id (str): The ID of the workflow instance.

        Returns:
            list: A list containing all values.
        """
        return [
            pickle.loads(v)
            for v in self.redis_stm_client._client.hvals(workflow_instance_id)
        ]

    def items(self, workflow_instance_id: str) -> list:
        """
        Get a list of all key-value pairs in the Redis storage for a workflow instance.

        Args:
            workflow_instance_id (str): The ID of the workflow instance.

        Returns:
            list: A list containing all key-value pairs.
        """
        items = self.redis_stm_client._client.hgetall(workflow_instance_id)
        return [(k.decode("utf-8"), pickle.loads(v)) for k, v in items.items()]

    def get(self, workflow_instance_id: str, key: str, default: Any = None) -> Any:
        """
        Get an item from the Redis storage.

        Args:
            workflow_instance_id (str): The ID of the workflow instance.
            key (str): The key of the item to retrieve.
            default (Any, optional): The default value to return if the key is not found. Defaults to None.

        Returns:
            Any: The value associated with the given key, or the default value if the key is not found.
        """
        try:
            return self[workflow_instance_id, key]
        except KeyError:
            return default

    def clear(self, workflow_instance_id: str) -> None:
        """
        Remove all items from the Redis storage for a workflow instance.

        Args:
            workflow_instance_id (str): The ID of the workflow instance.
        """
        self.redis_stm_client._client.delete(workflow_instance_id)

    def pop(self, workflow_instance_id: str, key: str, default: Any = None) -> Any:
        """
        Remove and return an item from the Redis storage.

        Args:
            workflow_instance_id (str): The ID of the workflow instance.
            key (str): The key of the item to remove.
            default (Any, optional): The default value to return if the key is not found. Defaults to None.

        Returns:
            Any: The value associated with the given key, or the default value if the key is not found.
        """
        try:
            value = self[workflow_instance_id, key]
            self.redis_stm_client._client.hdel(workflow_instance_id, key)
            return value
        except KeyError:
            return default

    def update(self, workflow_instance_id: str, other: dict) -> None:
        """
        Update the Redis storage with the key-value pairs from another dictionary-like object.

        Args:
            workflow_instance_id (str): The ID of the workflow instance.
            other (dict): A dictionary-like object containing the key-value pairs to update with.
        """
        pipeline = self.redis_stm_client._client.pipeline()
        for key, value in other.items():
            pipeline.hset(workflow_instance_id, key, pickle.dumps(value))
        pipeline.execute()

    def __len__(self, workflow_instance_id: str) -> int:
        """
        Get the number of items in the Redis storage for a workflow instance.

        Args:
            workflow_instance_id (str): The ID of the workflow instance.

        Returns:
            int: The number of items in the Redis storage.
        """
        return self.redis_stm_client._client.hlen(workflow_instance_id)


if __name__ == "__main__":
    # Create Redis client
    redis_client = RedisConnector()

    # Create RedisSTM instance
    stm = RedisSTM(redis_stm_client=redis_client)

    # Test workflow instance ID
    workflow_id = "test_workflow"

    # Get workflow instance proxy
    workflow = stm(workflow_id)

    # Test basic operations
    print("Testing basic operations...")

    # Set items
    workflow["key1"] = "value1"
    workflow["key2"] = {"nested": "value2"}

    # Get items
    print(f"Get key1: {workflow['key1']}")
    print(f"Get key2: {workflow['key2']}")

    # Test contains
    print(f"Contains key1: {'key1' in workflow}")

    # Test keys, values, items
    print(f"Keys: {workflow.keys()}")
    print(f"Values: {workflow.values()}")
    print(f"Items: {workflow.items()}")

    # Test length
    print(f"Length: {len(workflow)}")

    # Test pop
    popped = workflow.pop("key1")
    print(f"Popped value: {popped}")

    # Test update
    workflow.update({"key3": "value3", "key4": "value4"})
    print(f"After update - keys: {workflow.keys()}")

    # Test clear
    workflow.clear()
    print(f"After clear - length: {len(workflow)}")
