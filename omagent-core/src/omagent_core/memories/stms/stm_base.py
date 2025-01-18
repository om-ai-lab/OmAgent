from abc import ABC, abstractmethod
from typing import Any

from omagent_core.base import BotBase


class STMBase(BotBase):
    @abstractmethod
    def __call__(self, workflow_instance_id: str):
        """
        Return a WorkflowInstanceProxy for the given workflow instance ID.

        Args:
            workflow_instance_id (str): The ID of the workflow instance.

        Returns:
            WorkflowInstanceProxy: A proxy object for accessing the workflow instance data.
        """
        pass

    @abstractmethod
    def __getitem__(self, key: tuple | str) -> Any:
        """
        Retrieve an item or all items from storage.

        Args:
            key (tuple | str): Either a tuple containing (workflow_instance_id, key) or just workflow_instance_id

        Returns:
            Any: The value associated with the given key, or a dictionary of all key-value pairs for the workflow_instance_id.

        Raises:
            KeyError: If the key is not found in storage.
        """
        pass

    @abstractmethod
    def __setitem__(self, key: tuple, value: Any) -> None:
        """
        Set an item in storage.

        Args:
            key (tuple): A tuple containing (workflow_instance_id, key)
            value (Any): The value to associate with the key.
        """
        pass

    @abstractmethod
    def __delitem__(self, workflow_instance_id: str, key: str) -> None:
        """
        Delete an item from storage.

        Args:
            workflow_instance_id (str): The ID of the workflow instance.
            key (str): The key of the item to delete.

        Raises:
            KeyError: If the key is not found in storage.
        """
        pass

    @abstractmethod
    def __contains__(self, key: tuple) -> bool:
        """
        Check if a key exists in storage.

        Args:
            key (tuple): A tuple containing (workflow_instance_id, key)

        Returns:
            bool: True if the key exists, False otherwise.
        """
        pass

    @abstractmethod
    def keys(self, workflow_instance_id: str) -> list:
        """
        Get a list of all keys in storage for a workflow instance.

        Args:
            workflow_instance_id (str): The ID of the workflow instance.

        Returns:
            list: A list containing all keys.
        """
        pass

    @abstractmethod
    def values(self, workflow_instance_id: str) -> list:
        """
        Get a list of all values in storage for a workflow instance.

        Args:
            workflow_instance_id (str): The ID of the workflow instance.

        Returns:
            list: A list containing all values.
        """
        pass

    @abstractmethod
    def items(self, workflow_instance_id: str) -> list:
        """
        Get a list of all key-value pairs in storage for a workflow instance.

        Args:
            workflow_instance_id (str): The ID of the workflow instance.

        Returns:
            list: A list containing all key-value pairs.
        """
        pass

    @abstractmethod
    def get(self, workflow_instance_id: str, key: str, default: Any = None) -> Any:
        """
        Get an item from storage.

        Args:
            workflow_instance_id (str): The ID of the workflow instance.
            key (str): The key of the item to retrieve.
            default (Any, optional): The default value to return if the key is not found. Defaults to None.

        Returns:
            Any: The value associated with the given key, or the default value if the key is not found.
        """
        pass

    @abstractmethod
    def clear(self, workflow_instance_id: str) -> None:
        """
        Remove all items from storage for a workflow instance.

        Args:
            workflow_instance_id (str): The ID of the workflow instance.
        """
        pass

    @abstractmethod
    def pop(self, workflow_instance_id: str, key: str, default: Any = None) -> Any:
        """
        Remove and return an item from storage.

        Args:
            workflow_instance_id (str): The ID of the workflow instance.
            key (str): The key of the item to remove.
            default (Any, optional): The default value to return if the key is not found. Defaults to None.

        Returns:
            Any: The value associated with the given key, or the default value if the key is not found.
        """
        pass

    @abstractmethod
    def update(self, workflow_instance_id: str, other: dict) -> None:
        """
        Update storage with the key-value pairs from another dictionary.

        Args:
            workflow_instance_id (str): The ID of the workflow instance.
            other (dict): A dictionary containing the key-value pairs to update with.
        """
        pass

    @abstractmethod
    def __len__(self, workflow_instance_id: str) -> int:
        """
        Get the number of items in storage for a workflow instance.

        Args:
            workflow_instance_id (str): The ID of the workflow instance.

        Returns:
            int: The number of items in storage.
        """
        pass


class WorkflowInstanceProxy:
    def __init__(self, stm: STMBase, workflow_instance_id: str):
        self.stm = stm
        self.workflow_instance_id = workflow_instance_id

    def __getitem__(self, key: str) -> Any:
        return self.stm[self.workflow_instance_id, key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.stm[self.workflow_instance_id, key] = value

    def __delitem__(self, key: str) -> None:
        self.stm.__delitem__(self.workflow_instance_id, key)

    def __contains__(self, key: str) -> bool:
        return (self.workflow_instance_id, key) in self.stm

    def keys(self) -> list:
        return self.stm.keys(self.workflow_instance_id)

    def values(self) -> list:
        return self.stm.values(self.workflow_instance_id)

    def items(self) -> list:
        return self.stm.items(self.workflow_instance_id)

    def get(self, key: str, default: Any = None) -> Any:
        return self.stm.get(self.workflow_instance_id, key, default)

    def clear(self) -> None:
        self.stm.clear(self.workflow_instance_id)

    def pop(self, key: str, default: Any = None) -> Any:
        return self.stm.pop(self.workflow_instance_id, key, default)

    def update(self, other: dict) -> None:
        self.stm.update(self.workflow_instance_id, other)

    def __len__(self) -> int:
        return self.stm.__len__(self.workflow_instance_id)
