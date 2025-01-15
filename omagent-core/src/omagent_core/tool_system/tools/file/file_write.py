from ....utils.registry import registry
from ...base import ArgSchema, BaseTool

ARGSCHEMA = {
    "file_path": {"type": "string", "description": "The file path to write."},
    "content": {"type": "string", "description": "The content to write."},
    "file_mode": {
        "type": "string",
        "description": "The file mode to write.",
        "required": False,
    },
}


@registry.register_tool()
class WriteFileContent(BaseTool):
    args_schema: ArgSchema = ArgSchema(**ARGSCHEMA)
    description: str = "Write data to a file, replacing the file if it already exists."

    def _run(self, file_path: str, content: str, file_mode: str = "w") -> str:
        if not file_path:
            return "Please specify the file path."
        with open(file_path, file_mode) as f:
            f.write(content)
        return f"Write file successfully in {file_path}."
