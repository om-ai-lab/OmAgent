from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.registry import registry
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.models.llms.schemas import Message, Content
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.utils.logger import logging
from pathlib import Path
from omagent_core.models.llms.prompt.prompt import PromptTemplate
from pydantic import Field
from typing import List

CURRENT_PATH = Path(__file__).parents[0]

@registry.register_worker()
class COTConclusion(BaseLLMBackend, BaseWorker):
    
    """
    COTConclusion is a worker class that leverages OpenAI's GPT model to conclude the reasoning process
    based on previous interactions. It manages the inference workflow, collects token usage metrics,
    and sends final answers back to the workflow instance. The class is registered in the worker registry
    for use within the agent's operational framework.
    """


    llm: OpenaiGPTLLM

    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("user_prompt.prompt"), role="user"
            ),
        ]
    )
   
    def _run(self,  final_answer:List[str],question:str, *args, **kwargs):
        
        """
        Executes the reasoning conclusion process based on the final answers provided.

        Args:
            final_answer (List[str]): A list of final answers to conclude from.
            question (str): The question that was posed to the reasoning process.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            dict: A dictionary containing the final answer, question, prompt tokens,
                  completion tokens, and the body of the request.
        """
        reasoning_result = self.simple_infer(final_answer=str(final_answer))
        reasoning_result = reasoning_result["choices"][0]["message"]["content"]
        self.stm(self.workflow_instance_id)['final_answer'] = reasoning_result
        body = self.stm(self.workflow_instance_id)["body"] 
        return {'final_answer': reasoning_result,'question': question,'prompt_tokens': self.token_usage['prompt_tokens'], 'completion_tokens': self.token_usage['completion_tokens'],"body":body}