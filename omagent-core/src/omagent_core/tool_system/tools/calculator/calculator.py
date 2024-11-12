import os
import subprocess

from ....utils.registry import registry
from ...base import ArgSchema, BaseTool

ARGSCHEMA = {
    "code": {
        "type": "string",
        "description": "Python code block to be executed of mathematical calculation derivation.",
    }
}


@registry.register_tool()
class Calculator(BaseTool):
    args_schema: ArgSchema = ArgSchema(**ARGSCHEMA)
    description: str = (
        "Calculator tool for executing all mathematical calculation. Final result must be wrapped by print function and output to stdout."
    )

    def _run(self, code: str = None, filename: str = "calculator_code.py") -> dict:
        if code:
            with open(filename, "w") as f:
                f.write(code)
        command = f"python {filename}"
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
