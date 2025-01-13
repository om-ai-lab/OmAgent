from itertools import combinations_with_replacement
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.registry import registry
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.models.llms.schemas import Message, Content
from omagent_core.utils.logger import logging
from pathlib import Path
from omagent_core.models.llms.prompt.prompt import PromptTemplate
from pydantic import Field
from typing import List

CURRENT_PATH = Path(__file__).parents[0]

@registry.register_worker()
class COTReasoning(BaseLLMBackend, BaseWorker):
    
    """
    
    COTReasoning class is responsible for reasoning using the OpenAI GPT model.
    It manages prompts and invokes the model to generate reasoning paths based on user queries.
    The _run method executes the inference process, collecting reasoning results and token usage.
    
    """


    llm: OpenaiGPTLLM

    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("user_prompt.prompt"), role="user"
            ),
        ]
    )

    def _run(self, user_question: str, num_path: int, examples: str = None, *args, **kwargs):
        
        """
            Executes the reasoning process using the OpenAI GPT model.

        Args:
            user_question (str): The question posed by the user for reasoning.
            num_path (int): The number of reasoning paths to generate.
            examples (str, optional): Examples to guide the reasoning process.

        Returns:
            dict: A dictionary containing the reasoning results.
        """

        reason_path = []
        prompt_token = []
        complete_token = []
        for i in range(num_path):
            reasoning_result = self.simple_infer(question=user_question, examples=examples)
            prompt_token.append(reasoning_result["usage"]["prompt_tokens"])
            complete_token.append(reasoning_result["usage"]["completion_tokens"])
            reasoning_result = reasoning_result["choices"][0]["message"]["content"]
            reason_path.append(reasoning_result)
            if i == 1:
                message = self.prep_prompt([{"question": user_question}])
                body = self.llm._msg2req(message[0])
                self.stm(self.workflow_instance_id)["body"] = body

        self.stm(self.workflow_instance_id)['prompt_token'] = prompt_token
        self.stm(self.workflow_instance_id)['completion_token'] = complete_token
        self.stm(self.workflow_instance_id)['reasoning_result'] = reason_path

        self.callback.send_answer(self.workflow_instance_id, msg=",".join(reason_path))

        return {'reasoning_result': reason_path}


    def _run(self, user_question: str, num_path: int, examples: str = None, *args, **kwargs):
        reason_path = []
        prompt_token = []
        complete_token = []
        for i in range(num_path):
            reasoning_result = self.simple_infer(question=user_question,examples=examples)
            prompt_token.append(reasoning_result["usage"]["prompt_tokens"])
            complete_token.append(reasoning_result["usage"]["completion_tokens"])
            reasoning_result = reasoning_result["choices"][0]["message"]["content"]
            reason_path.append(reasoning_result)
            if i==1:
                message = self.prep_prompt([{"question":user_question}])
                body = self.llm._msg2req(message[0])
                self.stm(self.workflow_instance_id)["body"] = body



        self.stm(self.workflow_instance_id)['prompt_token'] = prompt_token
        self.stm(self.workflow_instance_id)['completion_token'] = complete_token
        self.stm(self.workflow_instance_id)['reasoning_result'] = reason_path

        self.callback.send_answer(self.workflow_instance_id, msg=",".join(reason_path))




        return {'reasoning_result': reason_path}