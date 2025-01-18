import os

from ....utils.registry import registry
from ...base import ArgSchema, BaseTool

ARGSCHEMA = {"file_path": {"type": "string", "description": "The file path to read."}}


@registry.register_tool()
class ReadFileContent(BaseTool):
    args_schema: ArgSchema = ArgSchema(**ARGSCHEMA)
    description: str = (
        "Reads data from a file. It can be check whether the file exists or not."
    )

    def _run(self, file_path: str = None) -> str:
        if not file_path:
            return "Please specify the file path."
        if not os.path.exists(file_path):
            return "The file path does not exist."
        if not os.path.isfile(file_path):
            return "The file path is not a file."
        with open(file_path, "r") as f:
            return f.read()
