import asyncio
import os
import subprocess

from ....utils.registry import registry
from ...base import ArgSchema, BaseTool

ARGSCHEMA = {
    "code": {"type": "string", "description": "Code block to be executed"},
    "command": {
        "type": "string",
        "description": "Command to be executed, need to be python filename, e.g. python llm_code.py",
        "required": False,
    },
    "filename": {
        "type": "string",
        "description": "Filename of the code block",
        "required": False,
    },
}


@registry.register_tool()
class CodeInterpreter(BaseTool):
    args_schema: ArgSchema = ArgSchema(**ARGSCHEMA)
    description: str = (
        "Python code must be run via this tool, it can be simple code or complex code like deploying web server. Contains libs like numpy, pandas, matplotlib, sklearn, etc. You must print the result to stdout."
    )

    def _run(
        self, code: str = None, command: str = None, filename: str = "llm_code.py"
    ) -> dict:
        if code:
            with open(filename, "w") as f:
                f.write(code)
        command = command or f"python {filename}"
        try:
            exec_proc = subprocess.Popen(
                command,
                shell=True,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,
                cwd=".",
            )
            stdout, stderr = exec_proc.communicate(timeout=30)

        except Exception as e:
            raise ValueError(e)

        if stderr:
            raise ValueError(f"{code}\nExecute error:\n {stderr.decode()}")
        result = {
            "ReturnCode": exec_proc.returncode,
            "Error": stderr.decode() if stderr else None,
            "Output": stdout.decode() if stdout else None,
            "absolute_filename": os.path.abspath(filename),
        }

        return result

    async def _arun(
        self, code: str = None, command: str = None, filename: str = "llm_code.py"
    ) -> str:
        if code:
            with open(filename, "w") as f:
                f.write(code)

        command = command or f"python {filename}"
        exec_proc = await asyncio.create_subprocess_shell(
            command,
            stderr=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE,
            cwd=".",
        )

        stdout, stderr = await asyncio.wait_for(exec_proc.communicate(), timeout=10)

        result = {
            "ReturnCode": exec_proc.returncode,
            "Error": stderr.decode() if stderr else None,
            "Output": stdout.decode() if stdout else None,
            "absolute_filename": os.path.abspath(filename),
        }

        return result
