import importlib
from functools import partial
from pathlib import Path
from typing import Any, Callable, Dict, List

CATEGORIES = [
    "prompt",
    "llm",
    "node",
    "worker",
    "tool",
    "encoder",
    "connector",
    "component",
]


class Registry:
    """Class for module registration and retrieval."""

    def __init__(self):
        # Initializes a mapping for different categories of modules.
        self.mapping = {key: {} for key in CATEGORIES}

    def __getattr__(self, name: str) -> Callable:
        if name.startswith(("register_", "get_", "unregister_")):
            prefix, category = name.split("_", 1)
            if category in CATEGORIES:
                if prefix == "register":
                    return partial(self.register, category)
                elif prefix == "get":
                    return partial(self.get, category)
                elif prefix == "unregister":
                    return partial(self.unregister, category)
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )

    def _register(self, category: str, name: str = None):
        """
        Registers a module under a specific category.

        :param category: The category to register the module under.
        :param name: The name to register the module as.
        """

        def wrap(module):
            nonlocal name
            name = name or module.__name__
            if name in self.mapping[category]:
                #raise ValueError(
                #    f"Module {name} [{self.mapping[category].get(name)}] already registered in category {category}. Please use a different class name."
               # )
                del self.mapping[category][name]
                #print (f"Module {name} [{self.mapping[category].get(name)}] already registered in category {category}. Please use a different class name.")
            
            self.mapping.setdefault(category, {})[name] = module
            #print (f"Module {name} registered in category {category}.")
            return module

        return wrap

    def _get(self, category: str, name: str):
        """
        Retrieves a module from a specified category.

        :param category: The category to search in.
        :param name: The name of the module to retrieve.
        :raises KeyError: If the module is not found.
        """
        try:
            return self.mapping[category][name]
        except KeyError:
            raise KeyError(f"Module {name} not found in category {category}")

    def register(self, category: str, name: str = None):
        """
        Registers a module under a general category.

        :param category: The category to register the module under.
        :param name: Optional name to register the module as.
        """
        return self._register(category, name)

    def get(self, category: str, name: str):
        """
        Retrieves a module from a general category.

        :param category: The category to search in.
        :param name: The name of the module to retrieve.
        """
        return self._get(category, name)

    def unregister(self, category: str, name: str):
        """
        Unregisters a module from a specified category.

        :param category: The category to remove the module from.
        :param name: The name of the module to remove.
        :raises KeyError: If the module is not found.
        """

        try:
            if name in self.mapping[category]:
                del self.mapping[category][name]
                #print(f"Module {name} unregistered from category {category}.")            
        except KeyError:
            raise KeyError(f"Module {name} not found in category {category}")

    def import_module(self, project_path: List[str] | str = None):
        """Import modules from default paths and optional project paths.

        Args:
            project_path: Optional path or list of paths to import modules from
        """
        # Handle default paths
        root_path = Path(__file__).parents[1]
        default_path = [
            root_path.joinpath("models"),
            root_path.joinpath("tool_system"),
            root_path.joinpath("services"),
            root_path.joinpath("memories"),
            root_path.joinpath("advanced_components"),
            root_path.joinpath("clients"),
        ]

        for path in default_path:
            for module in path.rglob("*.[ps][yo]"):
                if module.name == "workflow.py":
                    continue
                module = str(module)
                if "__init__" in module or "base.py" in module or "entry.py" in module:
                    continue
                module = "omagent_core" + module.rsplit("omagent_core", 1)[1].rsplit(
                    ".", 1
                )[0].replace("/", ".")
                importlib.import_module(module)
        # Handle project paths        
        if project_path:
            if isinstance(project_path, (str, Path)):
                project_path = [project_path]

            for path in project_path:
                path = Path(path).absolute()
                project_root = path.parent
                for module in path.rglob("*.[ps][yo]"):
                    module = str(module)
                    if "__init__" in module:
                        continue
                    module = (
                        module.replace(str(project_root) + "/", "")
                        .rsplit(".", 1)[0]
                        .replace("/", ".")
                    )
                    #print (module)
                    #module =path.split("/")[-2]+"/"+module
                    importlib.import_module(module)


# Instantiate registry
registry = Registry()


if __name__ == "__main__":

    @registry.register_node()
    class TestNode:
        name: "TestNode"

    print(registry.get_node("TestNode"))
