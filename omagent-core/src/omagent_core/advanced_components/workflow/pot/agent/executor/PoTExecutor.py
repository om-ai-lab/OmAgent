from pathlib import Path
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.utils.registry import registry
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.models.llms.prompt.prompt import PromptTemplate
from pydantic import Field
from typing import List
from omagent_core.utils.logger import logging
import func_timeout
import numpy as np
import math
import statistics
from sympy import symbols, solve, And, sqrt, Symbol
import itertools

# Get absolute path to the directory containing this file
CURRENT_PATH = root_path = Path(__file__).parents[0]


@registry.register_worker()
class PoTExecutor(BaseWorker, BaseLLMBackend):
    """Program-of-Thought (PoT) executor that solves math word problems step by step.
    
    This executor takes a natural language math problem as input, uses a large language model (LLM)
    to generate Python code that solves the problem, safely executes the generated code in an
    isolated environment, and returns the numerical answer.
    
    The workflow consists of:
    1. Receiving a math word problem text input
    2. Using an LLM (OpenAI GPT) to generate Python code that solves the problem
    3. Safely executing the generated code with timeouts and error handling
    4. Processing and returning the numerical answer
    
    Attributes:
        llm (OpenaiGPTLLM): The OpenAI GPT model used for code generation
        prompts (List[PromptTemplate]): List of prompt templates used for LLM interaction.
            Defaults to using the basic user prompt template.
    """
    llm: OpenaiGPTLLM
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("user_prompt.prompt"), role="user"
            ),
        ]
    )

    def floatify_ans(self, ans):
        """Attempts to convert an answer to float format when possible.
        
        This method handles various input types and tries to convert them to a float
        representation while preserving the semantic meaning of the answer.
        
        Args:
            ans: Answer in any format (dict, bool, list, tuple, etc.)
            
        Returns:
            float or str: The converted answer as a float when possible, otherwise as a string.
                Returns None if input is None or an empty list/tuple.
                
        Examples:
            >>> floatify_ans({'result': 42})
            42.0
            >>> floatify_ans(True)
            True
            >>> floatify_ans([3.14])
            3.14
        """
        try:
            if ans != 0 and ans is None:
                return None
            elif type(ans) == dict:
                # For dictionaries, extract the first value
                ans = list(ans.values())[0]
            elif type(ans) == bool:
                # Preserve boolean values without conversion
                ans = ans
            elif type(ans) in [list, tuple]:
                if not ans:
                    return None
                else:
                    # For sequences, try to convert first element to float
                    try:
                        ans = float(ans[0])
                    except Exception:
                        ans = str(ans[0])
            else:
                # For all other types, attempt float conversion
                try:
                    ans = float(ans)
                except Exception:
                    ans = str(ans)
        except Exception as e:
            logging.info(f"Error in floatify_ans: {e}")
            return None
        return ans

    def extract_code_blocks(self, text, is_fewshot=False):
        code_blocks = []
        lines = text.split('\n')
        if '```python' not in text:
            if is_fewshot:
                return text
            
            if 'def solver():' in text:
                return text
            
            for line in lines:
                if not line.strip():  # Skip empty lines or lines with only whitespace
                    continue
                if not line.startswith('    '):
                    code_blocks.append('    ' + line)
                else:
                    code_blocks.append(line)
            return '\n'.join(code_blocks)
        
        in_code_block = False
        current_block = []
        
        for line in lines:
            if line.strip().startswith('```'):
                if in_code_block:
                    # End of code block
                    in_code_block = False
                    if current_block:  # Only add non-empty blocks
                        if current_block[0].startswith('    '):
                            code_blocks.append('\n'.join(current_block))
                            
                        # Detect if code needs to be indented as a function
                        elif 'def solver():' not in '\n'.join(current_block):
                            # Add proper indentation for function body
                            indented_block = []
                            for code_line in current_block:
                                if code_line.strip():  # Skip empty lines
                                    if is_fewshot:
                                        indented_block.append(code_line)
                                    else:
                                        indented_block.append('    ' + code_line)
                                else:
                                    indented_block.append(code_line)
                            code_blocks.append('\n'.join(indented_block))
                        else:
                            code_blocks.append('\n'.join(current_block))
                    current_block = []
                else:
                    # Start of code block
                    in_code_block = True
            elif in_code_block and not line.startswith('```'):
                current_block.append(line)
    
        return '\n'.join(code_blocks)

    def safe_execute(self, code_string: str, keys=None):
        """Safely executes generated Python code with timeout protection.
        
        Provides a sandboxed environment for executing potentially unsafe code
        with a timeout mechanism to prevent infinite loops or long-running code.
        
        Args:
            code_string (str): Python code to execute
            keys (List[str], optional): List of variable names to extract from locals()
            
        Returns:
            Any: The execution result or None if execution fails/times out. 
                If keys are provided, returns a list of values for those keys from locals().
                
        Note:
            - Code execution is limited to 5 seconds
            - Automatically handles markdown code block formatting
            - Catches and logs all execution exceptions
        """
        def execute(x):
            try:
                exec(x)
                locals_ = locals()
                if keys is None:
                    return locals_.get('ans', None)
                else:
                    return [locals_.get(k, None) for k in keys]
            except Exception as e:
                logging.info("\n--------------\nExecution error: error message {}, code_string:\n{}\n--------------".format(e, code_string))
                return None
        try:
            # Execute with 5 second timeout
            ans = func_timeout.func_timeout(5, execute, args=(code_string,))
        except func_timeout.FunctionTimedOut:
            ans = None

        return ans
    
    def simplify_ans(self, ans, convert_to_str: bool = True):
        """Simplifies and normalizes answer formats to consistent representations.
        
        Handles various numeric types including numpy arrays, sympy expressions,
        and other mathematical objects, converting them to simple float or string format.
        
        Args:
            ans: Answer in any format (numpy array, sympy expression, etc.)
            convert_to_str (bool): Whether to convert the final result to string
            
        Returns:
            Union[float, str, None]: Simplified answer in float or string format.
                Returns None if input is falsy.
                
        Note:
            - Rounds floating point numbers to 2 decimal places
            - Handles special cases for numpy arrays and sympy expressions
            - Preserves relational expressions as strings
        """
        if ans is None:
            return None
        if isinstance(ans, (int, float)) and math.isinf(ans):
            return None
        if 'relational' in str(type(ans)):
            # Preserve relational expressions as strings
            return str(ans)
        elif 'numpy' in str(type(ans)):
            if ans.shape == ():
                # Handle scalar numpy value
                ans = round(float(ans), 2)
            else:
                # Handle array numpy value - check array length
                if len(ans) == 1:
                    ans = round(float(ans[0]), 2)
                else:
                    # If array has multiple values, convert all elements
                    ans = [round(float(x), 2) for x in ans]
            if convert_to_str:
                return str(ans)
            else:
                return ans
        elif ans == 0:
            return ans
        elif not ans:
            return None
        else:
            if type(ans) in [list, tuple]:
                # Handle sympy expressions in lists/tuples
                if 'sympy' in str(type(ans[0])):
                    try:
                        ans = [round(float(x), 2) for x in ans]
                    except Exception:
                        ans = [str(x) for x in ans]
                if len(ans) == 1:
                    ans = ans[0]
            else:
                # Handle single sympy expression
                if 'sympy' in str(type(ans)):
                    try:
                        ans = round(float(ans), 2)
                    except Exception:
                        ans = str(ans)
            if convert_to_str:
                return str(ans)
            else:
                return ans

    def _run(self, query: str, examples: str = None, options: str = None, *args, **kwargs):
        """Processes a math word problem and returns the numerical answer.
        
        This is the main execution method that coordinates the entire solution process:
        1. Validates input and selects appropriate prompt template
        2. Generates Python code using LLM
        3. Safely executes the code
        4. Processes and returns the result
        
        Args:
            query (str): The math word problem text to solve
            examples (str, optional): Few-shot examples to guide code generation
            options (list, optional): Additional processing options
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Returns:
            dict: A dictionary containing:
                - 'last_output': The numerical answer
                - 'completion_tokens': Number of tokens in the completion
                - 'prompt_tokens': Number of tokens in the prompt
                - 'body': Response body
            
        Note:
            - Handles both zero-shot and few-shot scenarios
            - Automatically adds necessary imports for zero-shot cases
            - Logs all major steps for debugging
        """
        logging.info("input query: {}".format(query))
        if query == '' or query is None:
            return {'last_output': None, 'completion_tokens': 0, 'prompt_tokens': 0}

        # Select appropriate prompt template based on whether examples are provided
        if examples is None:
            # Use standard prompt for zero-shot
            self.prompts = [
                PromptTemplate.from_file(
                    CURRENT_PATH.joinpath("user_prompt.prompt"), role="user"
                ),
            ]
            chat_complete_res = self.simple_infer(question=query)
        else:
            # Use few-shot prompt with examples
            self.prompts = [
                PromptTemplate.from_file(
                    CURRENT_PATH.joinpath("user_prompt_fewshot.prompt"), role="user"
                ),
            ]
            chat_complete_res = self.simple_infer(question=query, examples=examples)

        # Extract generated code from LLM response
        result = chat_complete_res["choices"][0]["message"]["content"]
        print('---------------------\n')
        print(result)
    
        result = self.extract_code_blocks(result, is_fewshot = examples != None)
        
        # For zero-shot cases, add imports and answer extraction
        if examples is None:
            if 'def solver():' in result:
                result = result + '\nans = solver()'
            else:
                result = 'import math\nimport numpy as np\nimport statistics\ndef solver():\n' + result + '\nans = solver()'

        logging.info('generated execution code:\n{}'.format(result))
        
        # Execute code safely and process result
        ans = self.safe_execute(result)
        logging.info("Result of execution: {}".format(ans))
        logging.info(chat_complete_res['usage'])

        if options is None:
            prediction = self.floatify_ans(self.simplify_ans(ans, False))
        else:
            prediction = self.floatify_ans(self.simplify_ans(ans, True))
        logging.info("Refined result: {}".format(prediction))
        completion_tokens = chat_complete_res['usage']['completion_tokens']
        prompt_tokens = chat_complete_res['usage']['prompt_tokens']
        
        return {'last_output': str(prediction), 'completion_tokens': completion_tokens, 'prompt_tokens': prompt_tokens}
