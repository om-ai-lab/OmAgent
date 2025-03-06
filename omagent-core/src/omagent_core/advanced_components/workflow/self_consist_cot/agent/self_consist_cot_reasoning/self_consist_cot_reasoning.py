from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.registry import registry
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.utils.logger import logging
from omagent_core.models.llms.prompt.prompt import PromptTemplate
from pydantic import Field
from pathlib import Path
from typing import List
import re
from collections import Counter
import random

CURRENT_PATH = Path( __file__ ).parents[ 0 ]

@registry.register_worker()
class SCCoTReasoning( BaseLLMBackend, BaseWorker ):

    prompts: List[ PromptTemplate ] = Field( default=[] )
    example: str = Field(default="")
    num : int = Field(default=5)  # Default number of runs: 5
    use_n : bool = Field(default=False)

    def extract_final_answer(self, text):
        """Extract the final answer from the output text"""
        def find_matching_brace(s, start):
            """Find matching braces"""
            count = 1
            i = start
            while i < len(s) and count > 0:
                if s[i] == '{':
                    count += 1
                elif s[i] == '}':
                    count -= 1
                i += 1
            return i if count == 0 else -1

        # Find all positions of \boxed{
        boxed_positions = [(m.start(), m.end()) for m in re.finditer(r'\\boxed{', text)]
        if not boxed_positions:
            return text

        # Find position of "Final Answer"
        final_answer_pos = text.find("Final Answer")
        
        if final_answer_pos != -1:
            # If "Final Answer" is found, select the closest \boxed
            closest_boxed = None
            min_distance = float('inf')
            
            for start, end in boxed_positions:
                distance = abs(start - final_answer_pos)
                if distance < min_distance:
                    min_distance = distance
                    closest_boxed = (start, end)
            
            # Extract content from the closest \boxed
            content_start = closest_boxed[1]  # end of '\boxed{'
            content_end = find_matching_brace(text, content_start)
            
            if content_end == -1:
                return text
                
            return text[content_start:content_end-1].strip()
        else:
            # If "Final Answer" is not found, use the first \boxed
            content_start = boxed_positions[0][1]  # end of '\boxed{'
            content_end = find_matching_brace(text, content_start)
            
            if content_end == -1:
                return text
                
            return text[content_start:content_end-1].strip()

    def get_most_common_answer(self, answers):
        """Get the most frequent answer"""
        # Filter out None values
        valid_answers = [ans for ans in answers if ans is not None]
        if not valid_answers:
            return None
        
        # Count answer frequencies
        answer_counts = Counter(valid_answers)
        # Find answers with maximum occurrences
        max_count = max(answer_counts.values())
        most_common = [ans for ans, count in answer_counts.items() if count == max_count]
        
        # If multiple answers have the same frequency, randomly select one
        return random.choice(most_common)

    def _run( self, id: int, query: str, *args, **kwargs ):
        """
        Executes a reasoning task based on the specified Chain-of-Thought (CoT) method.
        Args:
            id (int): The identifier for the reasoning task.
            query (str): The query string to be processed.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        Returns:
            dict: A dictionary containing the task id, question, all outputs from multiple runs.
        """

        self.prompts = [
                PromptTemplate.from_file( CURRENT_PATH.joinpath( "self_consist_cot.prompt" ), role="user" ),
            ]

        formatted_query = self.example.replace("{{query}}", query)

        if self.use_n:
            res = self.infer(input_list=[{"query": formatted_query}], n=self.num)[0]
            all_results = [self.extract_final_answer(choice["message"]["content"]) for choice in res["choices"]]
            
        else:
            all_results = []  # Store all run results
            for run_idx in range(self.num):
                print(f"Running iteration {run_idx + 1}/{self.num}")
                
                # Run single inference
                res = self.simple_infer(query=formatted_query) 

                # Get complete output
                full_output = res["choices"][0]["message"]["content"]
                
                # Extract final answer
                final_answer = self.extract_final_answer(full_output)

                # Extract results
                result = {
                    'run_index': run_idx + 1,
                    'prompt_tokens': res['usage']['prompt_tokens'],
                    'completion_tokens': res['usage']['completion_tokens'],
                    'last_output': full_output,
                    'final_answer': final_answer
                }
                all_results.append(result['final_answer'])
                
        # Send current results to callback
        self.callback.send_answer(self.workflow_instance_id, 
                                        msg=f"{all_results}")

        # Get the most common answer
        most_common_answer = self.get_most_common_answer(all_results)
        body = self.llm._msg2req(self.prep_prompt([{"query": formatted_query}])[0])
        
        
        return {
            'id': id,
            'question': query,
            'body': body,
            'last_output': most_common_answer,
            'prompt_tokens': self.token_usage['prompt_tokens'],
            'completion_tokens': self.token_usage['completion_tokens']
        }

