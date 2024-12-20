import subprocess

from ....utils.registry import registry
from ...base import ArgSchema, BaseTool

ARGSCHEMA = {
    "command": {
        "type": "string",
        "description": "The shell command to run, you are authorized to modify system's path to fix some problems.",
    }
}


@registry.register_tool()
class ShellTool(BaseTool):
    args_schema: ArgSchema = ArgSchema(**ARGSCHEMA)
    description: str = "Run shell command."

    def _run(self, command) -> dict:
        """Run shell command."""
        result = subprocess.run(command, shell=True, capture_output=True, text=True)

        return_code = result.returncode

        output = result.stdout.strip()

        error = result.stderr.strip()

        if error:
            raise ValueError(error)
        result = {
            "return_code": return_code,
            "output": output,
            "error": error,
            "shell_command": command,
        }
        return result
