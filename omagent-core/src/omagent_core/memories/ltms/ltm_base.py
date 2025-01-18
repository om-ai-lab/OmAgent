from abc import ABC, abstractmethod
from typing import Any, Iterable, Tuple

from omagent_core.base import BotBase


class LTMBase(BotBase):
    @abstractmethod
    def __getitem__(self, key: Any) -> Any:
        """
        Retrieve an item from the short-term memory by its key.

        Args:
            key (Any): The key of the item to retrieve.

        Returns:
            Any: The value associated with the given key.

        Raises:
            KeyError: If the key is not found in the short-term memory.
        """
        pass

    @abstractmethod
    def __setitem__(self, key: Any, value: Any) -> None:
        """
        Set an item in the short-term memory.

        Args:
            key (Any): The key of the item to set.
            value (Any): The value to associate with the key.
        """
        pass

    @abstractmethod
    def __delitem__(self, key: Any) -> None:
        """
        Delete an item from the short-term memory.

        Args:
            key (Any): The key of the item to delete.

        Raises:
            KeyError: If the key is not found in the short-term memory.
        """
        pass

    @abstractmethod
    def __contains__(self, key: Any) -> bool:
        """
        Check if a key exists in the short-term memory.

        Args:
            key (Any): The key to check for.

        Returns:
            bool: True if the key exists, False otherwise.
        """
        pass

    @abstractmethod
    def __len__(self) -> int:
        """
        Get the number of items in the short-term memory.

        Returns:
            int: The number of items in the short-term memory.
        """
        pass

    @abstractmethod
    def keys(self) -> Iterable[Any]:
        """
        Get an iterable of all keys in the short-term memory.

        Returns:
            Iterable[Any]: An iterable containing all keys.
        """
        pass

    @abstractmethod
    def values(self) -> Iterable[Any]:
        """
        Get an iterable of all values in the short-term memory.

        Returns:
            Iterable[Any]: An iterable containing all values.
        """
        pass

    @abstractmethod
    def items(self) -> Iterable[Tuple[Any, Any]]:
        """
        Get an iterable of all key-value pairs in the short-term memory.

        Returns:
            Iterable[Tuple[Any, Any]]: An iterable containing all key-value pairs.
        """
        pass

    @abstractmethod
    def get(self, key: Any, default: Any = None) -> Any:
        """
        Get an item from the short-term memory.

        Args:
            key (Any): The key of the item to retrieve.
            default (Any, optional): The default value to return if the key is not found. Defaults to None.

        Returns:
            Any: The value associated with the key, or the default value if the key is not found.
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """
        Remove all items from the short-term memory.
        """
        pass

    @abstractmethod
    def pop(self, key: Any, default: Any = None) -> Any:
        """
        Remove and return an item from the short-term memory.

        Args:
            key (Any): The key of the item to remove.
            default (Any, optional): The default value to return if the key is not found. Defaults to None.

        Returns:
            Any: The value associated with the key, or the default value if the key is not found.

        Raises:
            KeyError: If the key is not found and no default value is provided.
        """
        pass

    @abstractmethod
    def update(self, other: Iterable[Tuple[Any, Any]]) -> None:
        """
        Update the short-term memory with key-value pairs from another iterable.

        Args:
            other (Iterable[Tuple[Any, Any]]): An iterable of key-value pairs to update the short-term memory with.
        """
        pass
