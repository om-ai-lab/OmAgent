from .stm_base import STMBase
import pickle
from omagent_core.utils.registry import registry
from omagent_core.services.connectors.redis import RedisConnector


@registry.register_component()
class RedisSTM(STMBase):
    redis_stm_client: RedisConnector
    storage_name: str = 'default'

    
    def _encode_key(self, key):
        """
        Encode a key by prefixing it with the storage name.

        Args:
            key (str): The original key.

        Returns:
            str: The encoded key.
        """
        return self.storage_name + '@@' + key
    
    def _decode_key(self, key):
        """
        Decode a key by removing the storage name prefix.

        Args:
            key (str): The encoded key.

        Returns:
            str: The decoded key.
        """
        return key.replace(self.storage_name+'@@', '', 1)

    def __getitem__(self, key):
        """
        Retrieve an item from the Redis storage.

        Args:
            key (str): The key of the item to retrieve.

        Returns:
            Any: The value associated with the given key.

        Raises:
            KeyError: If the key is not found in the Redis storage.
        """
        key = self._encode_key(key)
        value = self.redis_stm_client.get(key)
        if value is not None:
            return pickle.loads(value)
        raise KeyError(key)

    def __setitem__(self, key, value):
        """
        Set an item in the Redis storage.

        Args:
            key (str): The key of the item to set.
            value (Any): The value to associate with the key.
        """
        key = self._encode_key(key)
        self.redis_stm_client.set(key, pickle.dumps(value))

    def __delitem__(self, key):
        """
        Delete an item from the Redis storage.

        Args:
            key (str): The key of the item to delete.

        Raises:
            KeyError: If the key is not found in the Redis storage.
        """
        key = self._encode_key(key)
        if not self.redis_stm_client.delete(key):
            raise KeyError(key)

    def __contains__(self, key):
        """
        Check if a key exists in the Redis storage.

        Args:
            key (str): The key to check for.

        Returns:
            bool: True if the key exists, False otherwise.
        """
        key = self._encode_key(key)
        return self.redis_stm_client.exists(key)

    def keys(self):
        """
        Get a list of all keys in the Redis storage.

        Returns:
            list: A list containing all keys.
        """
        res = []
        for k in self.redis_stm_client.keys():
            key = k.decode('utf-8')
            if key.startswith(self.storage_name + '@@'):
                res.append(self._decode_key(key))
        return res

    def values(self):
        """
        Get a list of all values in the Redis storage.

        Returns:
            list: A list containing all values.
        """
        return [self[key] for key in self.keys()]

    def items(self):
        """
        Get a list of all key-value pairs in the Redis storage.

        Returns:
            list: A list containing all key-value pairs.
        """
        return [(key, self[key]) for key in self.keys()]

    def get(self, key, default=None):
        """
        Get an item from the Redis storage.

        Args:
            key (str): The key of the item to retrieve.
            default (Any, optional): The default value to return if the key is not found. Defaults to None.

        Returns:
            Any: The value associated with the given key, or the default value if the key is not found.
        """
        try:
            return self[key]
        except KeyError:
            return default

    def clear(self):
        """
        Remove all items from the Redis storage.
        """
        data_keys = self.keys()
        for k in data_keys:
            del self[k]

    def pop(self, key, default=None):
        """
        Remove and return an item from the Redis storage.

        Args:
            key (str): The key of the item to remove.
            default (Any, optional): The default value to return if the key is not found. Defaults to None.

        Returns:
            Any: The value associated with the given key, or the default value if the key is not found.
        """
        try:
            value = self[key]
            del self[key]
            return value
        except KeyError as e:
            print(e)
            return default

    def update(self, other):
        """
        Update the Redis storage with the key-value pairs from another dictionary-like object.

        Args:
            other (dict): A dictionary-like object containing the key-value pairs to update with.
        """
        for key, value in other.items():
            self[key] = value

    def __len__(self):
        """
        Get the number of items in the Redis storage.

        Returns:
            int: The number of items in the Redis storage.
        """
        return len(self.keys())
    
if __name__ == "__main__":
    x = RedisSTM(redis_url='redis://10.8.21.38:7379?db=11',storage_name='test')
    print(len(x), x.keys())
    from PIL import Image
    img = Image.open('/data23/liu_peng/projs/OmAgent-main/20240529170425.jpg')
    x['frame1'] = img 
    x['json1'] = {'a': 1, "b": 2}
    x['str1'] = 'hello'
    print(len(x), x.keys())
    print(x['str1'])
    x['str1'] = 'hello again'
    print(x['str1'])
    print(x.values())
    print(x.items())
    print('-----------------------')
    new_image = x['frame1']
    print(x['json1']) 
    print(len(x), x.keys())
    print('-----------------------')
    im = x.pop('frame1')
    print(len(x), x.keys())
    print('-----------------------')
    print('json1' in x)
    print(x.get('json1'))
    del x['json1']
    print('json1' in x)
    print(x.get('json1'))
    print(len(x), x.items())
    print('-----------------------')
    x.update({'new1': 1, 'new2': dict()})
    print(len(x), x.items())
    print('-----------------------')
    x.clear()
    print(len(x), x.items())


