from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.registry import registry
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.models.llms.schemas import Message, Content
from omagent_core.utils.logger import logging
from omagent_core.models.llms.prompt.prompt import PromptTemplate
from omagent_core.advanced_components.workflow.cot.schemas.cot_create_examples import CoTExample
from pydantic import Field
from pathlib import Path
from typing import List

CURRENT_PATH = Path( __file__ ).parents[ 0 ]


@registry.register_worker()
class CoTReasoning( BaseLLMBackend, BaseWorker ):

    prompts: List[ PromptTemplate ] = Field( default=[] )

    def _run( self, id: int, query: str, cot_method: str, cot_examples: List[ dict ] = [], *args, **kwargs ):
        """
        Executes a reasoning task based on the specified Chain-of-Thought (CoT) method.
        Args:
            id (int): The identifier for the reasoning task.
            query (str): The query string to be processed.
            cot_method (str): The CoT method to use, either 'few_shot' or 'zero_shot'.
            cot_examples (List[dict], optional): A list of examples for few-shot CoT. Defaults to an empty list.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        Returns:
            dict: A dictionary containing the task id, question, model output, prompt tokens, and completion tokens.
        Raises:
            ValueError: If an invalid CoT method is provided.
        """

        if cot_method == 'few_shot':
            self.prompts = [
                PromptTemplate.from_file( CURRENT_PATH.joinpath( "few_shot_cot.prompt" ), role="user" ),
            ]

            assert cot_examples, "Few-shot COT requires examples."

            demo = CoTExample().create_examples( cot_examples )

            res = self.simple_infer( query=query, demo=demo )

            body = self.llm._msg2req( [ p for prompts in self.prep_prompt( [ { "query": query, "demo": demo} ] ) for p in prompts ] )
        elif cot_method == 'zero_shot':
            self.prompts = [
                PromptTemplate.from_file( CURRENT_PATH.joinpath( "zero_shot_cot.prompt" ), role="user" ),
            ]

            res = self.simple_infer( query=query )

            body = self.llm._msg2req( [ p for prompts in self.prep_prompt( [ { "query": query} ] ) for p in prompts ] )
        else:
            raise ValueError( f"Invalid cot_method: {cot_method}" )

        # Extract the reasoning result from the response.
        prompt_tokens = res[ 'usage' ][ 'prompt_tokens' ]
        completion_tokens = res[ 'usage' ][ 'completion_tokens' ]
        last_output = res[ "choices" ][ 0 ][ "message" ][ "content" ]
        question = body.get( 'messages' )[ 0 ][ 'content' ][ 0 ][ 'text' ]

        self.callback.send_answer(self.workflow_instance_id, msg=last_output)
        return { 'id': id, 'question': question, 'last_output': last_output, 'prompt_tokens': prompt_tokens, "completion_tokens": completion_tokens}
