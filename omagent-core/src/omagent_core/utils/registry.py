import importlib
from pathlib import Path
from typing import List


class Registry:
    """class for module registration"""

    mapping = {
        "prompt": {},
        "llm": {},
        "node": {},
        "tool": {},
        "handler": {},
        "encoder": {},
    }

    def _register(self, category: str, name: str = None):
        def wrap(module, name=name):
            if not name:
                name = module.__name__
            if category not in self.mapping:
                self.mapping[category] = {}
            self.mapping[category][name] = module
            return module

        return wrap

    def _get(self, category: str, name: str):
        if name in self.mapping[category]:
            return self.mapping[category][name]
        else:
            raise Exception(f"Module {name} not found in category {category}")

    def register_prompt(self, name: str = None):
        return self._register("prompt", name=name)

    def get_prompt(self, name):
        return self._get("prompt", name)

    def register_llm(self, name: str = None):
        return self._register("llm", name=name)

    def get_llm(self, name):
        return self._get("llm", name)

    def register_node(self, name: str = None):
        return self._register("node", name=name)

    def get_node(self, name):
        return self._get("node", name)

    def register_tool(self, name: str = None):
        return self._register("tool", name=name)

    def get_tool(self, name):
        return self._get("tool", name)

    def register_handler(self, name: str = None):
        return self._register("handler", name=name)

    def get_handler(self, name):
        return self._get("handler", name)

    def register_encoder(self, name: str = None):
        return self._register("encoder", name=name)

    def get_encoder(self, name):
        return self._get("encoder", name)

    def import_module(self, project_root: str = None, custom: List[str] = []):
        root_path = Path(__file__).parents[1]
        default_path = [
            root_path.joinpath("core/prompt"),
            root_path.joinpath("core/llm"),
            root_path.joinpath("core/node"),
            root_path.joinpath("core/encoder"),
            root_path.joinpath("core/tool_system/tools"),
            root_path.joinpath("handlers"),
        ]
        for path in default_path:
            for module in path.rglob("*.[ps][yo]"):
                module = str(module)
                if "__init__" in module or "base.py" in module or "entry.py" in module:
                    continue
                module = "omagent_core" + module.rsplit("omagent_core", 1)[1].rsplit(
                    ".", 1
                )[0].replace("/", ".")
                importlib.import_module(module)
        if project_root:
            for path in custom:
                path = Path(path).absolute()
                for module in path.rglob("*.[ps][yo]"):
                    module = str(module)
                    if "__init__" in module:
                        continue
                    module = (
                        module.replace(str(project_root) + "/", "")
                        .rsplit(".", 1)[0]
                        .replace("/", ".")
                    )
                    importlib.import_module(module)


registry = Registry()
