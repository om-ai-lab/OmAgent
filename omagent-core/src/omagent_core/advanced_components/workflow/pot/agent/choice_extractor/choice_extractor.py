from pathlib import Path
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.utils.registry import registry
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.models.llms.prompt.prompt import PromptTemplate
from pydantic import Field
from typing import List
from omagent_core.utils.logger import logging


# Get absolute path to the directory containing this file
CURRENT_PATH = root_path = Path(__file__).parents[0]


@registry.register_worker()
class ChoiceExtractor(BaseWorker, BaseLLMBackend):
    """Choice extractor that processes multiple choice questions using LLM.
    
    This processor analyzes multiple choice questions and extracts the most likely answer:
    1. Takes a multiple choice question and its options as input
    2. Uses LLM to analyze the question and provided answer choices
    3. Returns the selected answer choice with confidence score
    4. Tracks token usage for monitoring purposes
    
    Attributes:
        llm (OpenaiGPTLLM): The OpenAI GPT model used for answer analysis
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

    def _run(self, query: str, prediction: str = None, completion_tokens: int = 0, prompt_tokens: int = 0, examples: str = None, options: str = None, *args, **kwargs):
        """Processes a multiple choice question and extracts the most likely answer.
        
        This method coordinates the answer extraction process:
        1. Validates input parameters
        2. If no options provided, returns existing prediction
        3. Otherwise uses LLM to analyze question and options
        4. Tracks and accumulates token usage
        5. Returns selected answer with usage metrics
        
        Args:
            query (str): The multiple choice question text
            prediction (str, optional): Existing prediction to return if no options
            completion_tokens (int): Running count of completion tokens used
            prompt_tokens (int): Running count of prompt tokens used  
            examples (str, optional): Few-shot examples to guide answer selection
            options (list, optional): List of possible answer choices
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Returns:
            dict: A dictionary containing:
                - 'last_output': The selected answer choice
                - 'completion_tokens': Updated completion token count
                - 'prompt_tokens': Updated prompt token count
                
        Note:
            - Handles both direct return of predictions and LLM-based analysis
            - Accumulates token counts across multiple LLM calls
            - Logs extracted choices and usage metrics for monitoring
        """
        if query == '' or query is None:
            answer =  {'last_output': None, 'completion_tokens': 0, 'prompt_tokens': 0}
        
        if options is None:
            answer = {'last_output': str(prediction), 'completion_tokens': completion_tokens, 'prompt_tokens': prompt_tokens}
        else:
            chat_complete_res = self.simple_infer(question=query, options=options, prediction=prediction)

            # Extract selected answer choice from LLM response
            result = chat_complete_res["choices"][0]["message"]["content"]

            logging.info('extracted choice: {}'.format(result))
            logging.info(chat_complete_res['usage'])

            # Accumulate token usage metrics
            completion_tokens += chat_complete_res['usage']['completion_tokens']
            prompt_tokens += chat_complete_res['usage']['prompt_tokens']

            answer = {'last_output': str(result), 'completion_tokens': completion_tokens, 'prompt_tokens': prompt_tokens}
        logging.info("Answer: {}".format(answer))
        self.callback.send_answer(self.workflow_instance_id, msg=answer, filter_special_symbols=False)
        return answer