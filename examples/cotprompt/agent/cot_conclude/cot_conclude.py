from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.registry import registry
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.models.llms.schemas import Message, Content
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.utils.logger import logging
from pathlib import Path
from omagent_core.models.llms.prompt.prompt import PromptTemplate
from pydantic import Field
from pathlib import Path
from typing import List


CURRENT_PATH = Path(__file__).parents[0]

@registry.register_worker()
class COTConclusion(BaseLLMBackend, BaseWorker):
    
    
    llm: OpenaiGPTLLM
    
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("user_prompt.prompt"), role="user"
            ),
        ]
    )

    def _run(self, user_question:str, reasoning_result:str, *args, **kwargs):
        
        final_answer = self.simple_infer(question=user_question, reasoning_result=reasoning_result)
        
        final_answer = final_answer["choices"][0]["message"]["content"]
        
        
        self.stm(self.workflow_instance_id)['final_answer'] = final_answer
        
        self.callback.send_answer(self.workflow_instance_id, msg=final_answer)
        
        return {'final_answer': final_answer}

    