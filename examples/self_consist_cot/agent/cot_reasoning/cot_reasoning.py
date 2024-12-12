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
    
    llm: OpenaiGPTLLM
    
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("user_prompt.prompt"), role="user"
            ),
        ]
    )

    def _run(self, user_question:str,path_num:str,*args, **kwargs):
       
        reason_path = []
        for i in range(int(path_num)):
            reasoning_result = self.simple_infer(question=user_question)
        
            reasoning_result = reasoning_result["choices"][0]["message"]["content"]
            reason_path.append(reasoning_result)
            
        
        self.stm(self.workflow_instance_id)['reasoning_result'] = reason_path
        
        self.callback.send_answer(self.workflow_instance_id, msg=reason_path)
        
        
        
        
        return {'reasoning_result': reason_path}

   
