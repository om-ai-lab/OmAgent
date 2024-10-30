import importlib
from pathlib import Path
from typing import List, Callable, Any, Dict
from functools import partial

CATEGORIES = ["prompt","llm","node","worker","tool","handler","encoder"]

class Registry:
    """Class for module registration and retrieval."""

    def __init__(self):
        # Initializes a mapping for different categories of modules.
        self.mapping = {key:{} for key in CATEGORIES}

    def __getattr__(self, name: str) -> Callable:
        if name.startswith(('register_', 'get_')):
            prefix, category = name.split('_', 1)
            if category in CATEGORIES:
                if prefix == 'register':
                    return partial(self.register, category)
                elif prefix == 'get':
                    return partial(self.get, category)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def _register(self, category: str, name: str = None):
        """
        Registers a module under a specific category.
        
        :param category: The category to register the module under.
        :param name: The name to register the module as.
        """
        def wrap(module):
            nonlocal name
            name = name or module.__name__
            self.mapping.setdefault(category, {})[name] = module
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

    def import_module(self, project_root: str = None, custom_paths: List[str] = []):
        """
        Imports all modules from default and custom paths, skipping unnecessary files.
        
        :param project_root: The root path of the project.
        :param custom_paths: Custom paths to import modules from.
        """
        default_paths = [
            Path(__file__).parents[1] / "core/prompt",
            Path(__file__).parents[1] / "core/llm",
            Path(__file__).parents[1] / "core/node",
            Path(__file__).parents[1] / "core/encoder",
            Path(__file__).parents[1] / "core/tool_system/tools",
            Path(__file__).parents[1] / "handlers",
        ]

        for path in default_paths:
            self._import_from_path(path, "omagent_core")

        if project_root:
            for custom_path in custom_paths:
                custom_path = Path(custom_path).absolute()
                self._import_from_path(custom_path, str(project_root))

    def _import_from_path(self, path: Path, root: str):
        """
        Helper function to import modules from a specific path, skipping specific files.

        :param path: The directory to search for modules.
        :param root: The root directory to resolve the module name.
        """
        if not path.exists():
            return
        
        for module_file in path.rglob("*.py"):
            if any(skip in module_file.name for skip in ["__init__", "base.py", "entry.py"]):
                continue
            try:
                module_name = (
                    root + str(module_file.relative_to(path.parent)).rsplit(".", 1)[0].replace("/", ".")
                )
                importlib.import_module(module_name)
            except Exception as e:
                print(f"Error importing {module_file}: {e}")

# Instantiate registry
registry = Registry()


if __name__ == "__main__":
    @registry.register_node()
    class TestNode:
        name: "TestNode"
        
    print(registry.get_node('TestNode'))