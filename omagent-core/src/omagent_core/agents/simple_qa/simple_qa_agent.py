from pathlib import Path
from typing import List

from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.utils.registry import registry
from omagent_core.models.llms.schemas import Message, Content
from omagent_core.utils.general import encode_image
from omagent_core.models.llms.prompt.parser import StrParser
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.models.llms.hf_gpt import HuggingFaceLLM

from omagent_core.engine.worker.base import BaseWorker, BaseWorker
from omagent_core.utils.container import container

from pathlib import Path

from omagent_core.utils.registry import registry

from omagent_core.utils.logger import logging
from omagent_core.lite_engine.task import Task
from omagent_core.lite_engine.workflow import Workflow



CURRENT_PATH = Path(__file__).parents[0]


@registry.register_worker()
class SimpleQA(BaseWorker, BaseLLMBackend):
    llm: HuggingFaceLLM

    def _run(self, user_instruction, *args, **kwargs):
        print ("user_instruction",user_instruction)
        # Initialize empty list for chat messages
        chat_message = []
        
        # Add text question as first message
        chat_message.append(Message(role="user", message_type='text', content=user_instruction))
       
       
        # Get response from LLM model
        chat_complete_res = self.llm.generate(records=chat_message)

        # Extract answer text from response
        answer = chat_complete_res
        
        # Send answer via callback and return
        #self.callback.send_answer(self.workflow_instance_id, msg=answer)
        return answer


class QA_Agent:
    def __init__(self, model_name):
        llm = HuggingFaceLLM(model_name=model_name)   
        #llm = OpenaiGPTLLM(api_key="")     
        self.simple_qa = SimpleQA(llm=llm)
        

    def run(self, inputs):        
        simple_qa = Task(name='SimpleQA', func=self.simple_qa, inputs=inputs)        
        workflow = Workflow(name='example_workflow')        
        workflow >> simple_qa
        workflow.execute()        
        return simple_qa.output()
        

