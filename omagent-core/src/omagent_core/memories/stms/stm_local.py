from .stm_base import STMBase
import os
import pickle
from omagent_core.utils.registry import registry
from pydantic import Field
from typing import Any


@registry.register_component()
class LocalSTM(STMBase):
    base_directory: str = Field(default='./stm_storage')
    storage_name: str = Field(default='default')
    
    def model_post_init(self, __context: Any) -> None:
        self.directory = os.path.join(self.base_directory, self.storage_name)
        os.makedirs(self.directory, exist_ok=True)

    def _get_filepath(self, key):
        return os.path.join(self.directory, f"{key}.pkl")

    def __getitem__(self, key):
        filepath = self._get_filepath(key)
        if not os.path.exists(filepath):
            raise KeyError(f"{key} not found")
        with open(filepath, 'rb') as f:
            return pickle.load(f)

    def __setitem__(self, key, value):
        filepath = self._get_filepath(key)
        with open(filepath, 'wb') as f:
            pickle.dump(value, f)

    def __delitem__(self, key):
        filepath = self._get_filepath(key)
        if os.path.exists(filepath):
            os.remove(filepath)
        else:
            raise KeyError(f"{key} not found")

    def __contains__(self, key):
        return os.path.exists(self._get_filepath(key))

    def keys(self):
        return [f[:-4] for f in os.listdir(self.directory) if f.endswith('.pkl')]

    def values(self):
        return [self[key] for key in self.keys()]

    def items(self):
        return [(key, self[key]) for key in self.keys()]

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def clear(self):
        for key in self.keys():
            del self[key]

    def pop(self, key, default=None):
        try:
            value = self[key]
            del self[key]
            return value
        except KeyError:
            if default is not None:
                return default
            raise

    def update(self, other):
        for key, value in other.items():
            self[key] = value

    def __len__(self):
        return len(self.keys())
    
if __name__ == "__main__":
    x = LocalSTM(storage_name='test')
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