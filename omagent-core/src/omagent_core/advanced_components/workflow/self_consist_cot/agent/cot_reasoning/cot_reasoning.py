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

from pydantic_core.core_schema import NoInfoWrapValidatorFunctionSchema

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
        if self.llm.model_id in ["gpt4o","gpt4o-mini","gpt3.5-turbo"]:
            reasoning_result = self.infer(input_list=[{"question": user_question, "examples": examples}], n=num_path)[0]
            reason_path = [choice["message"]["content"] for choice in reasoning_result["choices"]]
            message = self.prep_prompt([{"question": user_question, "examples": examples}])
            body = self.llm._msg2req(message[0])
            self.stm(self.workflow_instance_id)["body"] = body
        else:
            reason_path = []
            for i in range(num_path):
                reasoning_result = self.simple_infer(question=user_question,examples=examples)
                reasoning_result = reasoning_result["choices"][0]["message"]["content"]
                reason_path.append(reasoning_result)
                if i==1:
                    message = self.prep_prompt([{"question":user_question, "examples": examples}])
                    body = self.llm._msg2req(message[0])
                    self.stm(self.workflow_instance_id)["body"] = body
        self.stm(self.workflow_instance_id)['reasoning_result'] = reason_path
        self.callback.send_answer(self.workflow_instance_id, msg=",".join(reason_path))
        return {'reasoning_result': reason_path}
