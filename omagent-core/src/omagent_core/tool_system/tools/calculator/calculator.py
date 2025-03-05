import numexpr
import re
import math

from omagent_core.utils.registry import registry
from omagent_core.tool_system.base import ArgSchema, BaseTool

ARGSCHEMA = {
    "formula": {
        "type": "string",
        "description": "Mathematical formula to be executed.",
    }
}


@registry.register_tool()
class Calculator(BaseTool):
    args_schema: ArgSchema = ArgSchema(**ARGSCHEMA)
    description: str = (
        "Calculator tool for executing simple mathematical calculation. Please output a mathematical formula. \
    Addition, subtraction, multiplication, and division are represented by +, -, *, and /, respectively. \
    Exponentiation is denoted by **, and square root is implemented using sqrt(). Other functions are not allowed to be used. \
    Only the constants pi and e are available, representing the mathematical constant pi and Euler's number, respectively."
    )

    def _run(self, formula: str = None) -> dict:
        try:
            # Define local variables, allowing only pi and e
            local_dict = {"pi": math.pi, "e": math.e}

            # Evaluate the expression using numexpr.evaluate
            output = str(
                numexpr.evaluate(
                    formula.strip(),
                    global_dict={},  # Restrict access to global variables
                    local_dict=local_dict,  # Add common mathematical constants
                )
            )
            print("Successfully used calculator for computation")
        except Exception as e:
            raise ValueError(
                f'Failed to evaluate "{formula}". Raised error: {repr(e)}.'
                " Please try again with a valid numerical expression"
            )

        # Remove square brackets from the output
        return re.sub(r"^\[|\]$", "", output)
