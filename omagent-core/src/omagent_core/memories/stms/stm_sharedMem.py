import hashlib
import pickle
from multiprocessing import shared_memory
from typing import Any
import atexit
import os

import numpy as np
from omagent_core.memories.stms.stm_base import STMBase, WorkflowInstanceProxy
from omagent_core.utils.registry import registry


@registry.register_component()
class SharedMemSTM(STMBase):
    def __init__(self, id=None):
        super().__init__()
        self.id = id
        self.main_pid = os.getpid()
        self._cleaned_up = False
        
        # Use shared memory to store workflow_instance_ids
        if os.getpid() == self.main_pid:
            try:
                self._ids_shm = shared_memory.SharedMemory(name='workflow_ids', size=1024*1024)
            except FileNotFoundError:
                self._ids_shm = shared_memory.SharedMemory(create=True, name='workflow_ids', size=1024*1024)
                self._save_ids(set())
        else:
            try:
                self._ids_shm = shared_memory.SharedMemory(name='workflow_ids')
            except FileNotFoundError:
                # if not found, create a new one
                self._ids_shm = shared_memory.SharedMemory(create=True, name='workflow_ids', size=1024*1024)
                self._save_ids(set())

        if os.getpid() == self.main_pid:
            atexit.register(self.cleanup)

    def _save_ids(self, ids_set):
        """Save ids set to shared memory"""
        pickled_data = pickle.dumps(ids_set)
        self._ids_shm.buf[:len(pickled_data)] = pickled_data

    def _load_ids(self):
        """Load ids set from shared memory"""
        try:
            return pickle.loads(bytes(self._ids_shm.buf).strip(b'\x00'))
        except (pickle.UnpicklingError, EOFError):
            return set()

    def _add_workflow_id(self, workflow_id):
        """Add workflow id to shared set"""
        ids = self._load_ids()
        ids.add(workflow_id)
        self._save_ids(ids)

    def __call__(self, workflow_instance_id: str):
        self._add_workflow_id(workflow_instance_id)
        return WorkflowInstanceProxy(self, workflow_instance_id)
    
    def cleanup(self):
        if os.getpid() == self.main_pid and not self._cleaned_up:
            try:
                workflow_ids = self._load_ids()
                for workflow_instance_id in list(workflow_ids):
                    try:
                        self.clear(workflow_instance_id)
                    except Exception as e:
                        print(f"Error cleaning up {workflow_instance_id}: {e}")
            finally:
                self._cleaned_up = True
                # clear workflow_ids shared memory
                if hasattr(self, '_ids_shm'):
                    self._ids_shm.close()
                    if os.getpid() == self.main_pid:
                        try:
                            self._ids_shm.unlink()
                        except Exception:
                            pass

    def __del__(self):
        if not self._cleaned_up:
            self.cleanup()
    

    def _create_shm(self, workflow_instance_id: str, size: int = 1024 * 1024 * 100):
        """Create a new shared memory block"""
        shortened_id = hashlib.md5(workflow_instance_id.encode()).hexdigest()[:8]
        shm = shared_memory.SharedMemory(name=shortened_id, create=True, size=size)
        return shm

    def _get_shm(self, workflow_instance_id, size: int = 1024 * 1024 * 100):
        # Hash the long workflow_instance_id to a shorter fixed-length string
        if workflow_instance_id:
            shortened_id = hashlib.md5(workflow_instance_id.encode()).hexdigest()[:8]
        else:
            shortened_id = "omagent_lite_ver."
        try:
            shm = shared_memory.SharedMemory(name=shortened_id)
        except FileNotFoundError:
            shm = shared_memory.SharedMemory(create=True, size=size, name=shortened_id)
            self._add_workflow_id(workflow_instance_id)
        return shm

    def __getitem__(self, key: tuple | str) -> Any:
        """
        Retrieve an item or all items from shared memory.

        Args:
            key (tuple | str): Either a tuple containing (workflow_instance_id, key) or just workflow_instance_id

        Returns:
            Any: The value associated with the given key, or a dictionary of all key-value pairs.

        Raises:
            KeyError: If the key is not found.
        """
        if isinstance(key, tuple):
            workflow_instance_id, key = key
            shm = self._get_shm(workflow_instance_id)
            try:
                data = pickle.loads(bytes(shm.buf).strip(b"\x00"))
                if key not in data:
                    raise KeyError(key)
                return data[key]
            except (pickle.UnpicklingError, EOFError):
                raise KeyError(key)
            finally:
                shm.close()
        else:
            workflow_instance_id = key
            shm = self._get_shm(workflow_instance_id)
            try:
                return pickle.loads(bytes(shm.buf).strip(b"\x00"))
            except (pickle.UnpicklingError, EOFError):
                return {}
            finally:
                shm.close()

    def __setitem__(self, key: tuple, value: Any) -> None:
        """
        Set an item in shared memory.

        Args:
            key (tuple): A tuple containing (workflow_instance_id, key)
            value (Any): The value to associate with the key.
        """
        workflow_instance_id, key = key
        self._add_workflow_id(workflow_instance_id)
        shm = self._get_shm(workflow_instance_id)
        try:
            data = pickle.loads(bytes(shm.buf).strip(b"\x00"))
        except (pickle.UnpicklingError, EOFError):
            data = {}

        data[key] = value
        pickled_data = pickle.dumps(data)
        shm.buf[: len(pickled_data)] = pickled_data
        shm.close()

    def __delitem__(self, workflow_instance_id: str, key: str) -> None:
        """
        Delete an item from shared memory.

        Args:
            workflow_instance_id (str): The ID of the workflow instance.
            key (str): The key of the item to delete.

        Raises:
            KeyError: If the key is not found.
        """
        shm = self._get_shm(workflow_instance_id)
        try:
            data = pickle.loads(bytes(shm.buf).strip(b"\x00"))
            if key not in data:
                raise KeyError(key)
            del data[key]
            pickled_data = pickle.dumps(data)
            shm.buf[:] = b"\x00" * len(shm.buf)  # Clear buffer
            shm.buf[: len(pickled_data)] = pickled_data
        except (pickle.UnpicklingError, EOFError):
            raise KeyError(key)
        finally:
            shm.close()

    def __contains__(self, key: tuple) -> bool:
        """
        Check if a key exists in shared memory.

        Args:
            key (tuple): A tuple containing (workflow_instance_id, key)

        Returns:
            bool: True if the key exists, False otherwise.
        """
        workflow_instance_id, key = key
        try:
            self[workflow_instance_id, key]
            return True
        except KeyError:
            return False

    def keys(self, workflow_instance_id: str) -> list:
        """
        Get a list of all keys in shared memory for a workflow instance.

        Args:
            workflow_instance_id (str): The ID of the workflow instance.

        Returns:
            list: A list containing all keys.
        """
        try:
            return list(self[workflow_instance_id].keys())
        except KeyError:
            return []

    def values(self, workflow_instance_id: str) -> list:
        """
        Get a list of all values in shared memory for a workflow instance.

        Args:
            workflow_instance_id (str): The ID of the workflow instance.

        Returns:
            list: A list containing all values.
        """
        try:
            return list(self[workflow_instance_id].values())
        except KeyError:
            return []

    def items(self, workflow_instance_id: str) -> list:
        """
        Get a list of all key-value pairs in shared memory for a workflow instance.

        Args:
            workflow_instance_id (str): The ID of the workflow instance.

        Returns:
            list: A list containing all key-value pairs.
        """
        try:
            return list(self[workflow_instance_id].items())
        except KeyError:
            return []

    def get(self, workflow_instance_id: str, key: str, default: Any = None) -> Any:
        """
        Get an item from shared memory.

        Args:
            workflow_instance_id (str): The ID of the workflow instance.
            key (str): The key of the item to retrieve.
            default (Any, optional): The default value to return if the key is not found.

        Returns:
            Any: The value associated with the given key, or the default value if not found.
        """
        try:
            return self[workflow_instance_id, key]
        except KeyError:
            return default

    def clear(self, workflow_instance_id: str) -> None:
        """
        Remove all items from shared memory for a workflow instance.

        Args:
            workflow_instance_id (str): The ID of the workflow instance.
        """
        try:
            if workflow_instance_id:
                shortened_id = hashlib.md5(workflow_instance_id.encode()).hexdigest()[:8]
            else: 
                shortened_id = "omagent_lite_ver."
            shm = shared_memory.SharedMemory(name=shortened_id)
            shm.buf[:] = b"\x00" * len(shm.buf)
            shm.close()
            shm.unlink()
        except FileNotFoundError:
            pass

    def pop(self, workflow_instance_id: str, key: str, default: Any = None) -> Any:
        """
        Remove and return an item from shared memory.

        Args:
            workflow_instance_id (str): The ID of the workflow instance.
            key (str): The key of the item to remove.
            default (Any, optional): The default value to return if not found.

        Returns:
            Any: The value associated with the given key, or the default value if not found.
        """
        try:
            value = self[workflow_instance_id, key]
            self.__delitem__(workflow_instance_id, key)
            return value
        except KeyError:
            return default

    def update(self, workflow_instance_id: str, other: dict) -> None:
        """
        Update shared memory with key-value pairs from another dictionary.

        Args:
            workflow_instance_id (str): The ID of the workflow instance.
            other (dict): A dictionary containing the key-value pairs to update with.
        """
        for key, value in other.items():
            self[workflow_instance_id, key] = value

    def __len__(self, workflow_instance_id: str) -> int:
        """
        Get the number of items in shared memory for a workflow instance.

        Args:
            workflow_instance_id (str): The ID of the workflow instance.

        Returns:
            int: The number of items in shared memory.
        """
        try:
            return len(self[workflow_instance_id])
        except KeyError:
            return 0


if __name__ == "__main__":
    # Create SharedMemSTM instance
    stm = SharedMemSTM()

    # Test workflow instance ID
    workflow_id = "test_workflow"

    # Get workflow instance proxy
    workflow = stm(workflow_id)

    # # Test basic operations
    # print("Testing basic operations...")

    # # Set items
    # workflow["key1"] = "value1"
    # workflow["key2"] = {"nested": "value2"}

    # # Get items
    # print(f"Get key1: {workflow['key1']}")
    # print(f"Get key2: {workflow['key2']}")

    # # Test contains
    # print(f"Contains key1: {'key1' in workflow}")

    # # Test keys, values, items
    # print(f"Keys: {workflow.keys()}")
    # print(f"Values: {workflow.values()}")
    # print(f"Items: {workflow.items()}")

    # # Test length
    # print(f"Length: {len(workflow)}")

    # # Test pop
    # popped = workflow.pop("key1")
    # print(f"Popped value: {popped}")

    # # Test update
    # workflow.update({"key3": "value3", "key4": "value4"})
    # print(f"After update - keys: {workflow.keys()}")

    # # Test clear
    # workflow.clear()
    # print(f"After clear - length: {len(workflow)}")

    workflow["key1"] = {}
    print(workflow["key1"])
    x = workflow["key1"]
    x["a"] = 1
    workflow["key1"] = x
    print(workflow["key1"])
