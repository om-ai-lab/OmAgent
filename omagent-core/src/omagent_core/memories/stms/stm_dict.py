from .stm_base import STMBase
from omagent_core.utils.registry import registry
from typing import Any
from multiprocessing import Manager

@registry.register_component()
class DictSTM(STMBase):
    def model_post_init(self, __context: Any) -> None:
        self._storage = Manager().dict()

    def __getitem__(self, key):
        """
        Retrieve an item from the short-term memory by its key.

        Args:
            key (Any): The key of the item to retrieve.

        Returns:
            Any: The value associated with the given key.

        Raises:
            KeyError: If the key is not found in the short-term memory.
        """
        return self._storage[key]

    def __setitem__(self, key, value):
        """
        Set an item in the short-term memory.

        Args:
            key (Any): The key of the item to set.
            value (Any): The value to associate with the key.
        """
        self._storage[key] = value

    def __delitem__(self, key):
        """
        Delete an item from the short-term memory.

        Args:
            key (Any): The key of the item to delete.

        Raises:
            KeyError: If the key is not found in the short-term memory.
        """
        del self._storage[key]

    def __contains__(self, key):
        """
        Check if a key exists in the short-term memory.

        Args:
            key (Any): The key to check for.

        Returns:
            bool: True if the key exists, False otherwise.
        """
        return key in self._storage

    def __len__(self):
        """
        Get the number of items in the short-term memory.

        Returns:
            int: The number of items in the short-term memory.
        """
        return len(self._storage)

    def keys(self):
        """
        Get an iterable of all keys in the short-term memory.

        Returns:
            Iterable[Any]: An iterable containing all keys.
        """
        return self._storage.keys()

    def values(self):
        """
        Get an iterable of all values in the short-term memory.

        Returns:
            Iterable[Any]: An iterable containing all values.
        """
        return self._storage.values()

    def items(self):
        """
        Get an iterable of all key-value pairs in the short-term memory.

        Returns:
            Iterable[Tuple[Any, Any]]: An iterable containing all key-value pairs.
        """
        return self._storage.items()

    def get(self, key, default=None):
        """
        Get an item from the short-term memory.

        Args:
            key (Any): The key of the item to retrieve.
            default (Any, optional): The default value to return if the key is not found. Defaults to None.

        Returns:
            Any: The value associated with the given key, or the default value if the key is not found.
        """
        return self._storage.get(key, default)

    def clear(self):
        """
        Remove all items from the short-term memory.
        """
        self._storage.clear()
    
    def pop(self, key, default=None):
        """
        Remove and return an item from the short-term memory.

        Args:
            key (Any): The key of the item to remove.
            default (Any, optional): The default value to return if the key is not found. Defaults to None.

        Returns:
            Any: The value associated with the given key, or the default value if the key is not found.
        """
        return self._storage.pop(key, default)

    def update(self, other):
        """
        Update the short-term memory with the key-value pairs from another dictionary-like object.

        Args:
            other (dict): A dictionary-like object containing the key-value pairs to update with.
        """
        self._storage.update(other)
