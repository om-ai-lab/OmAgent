from pathlib import Path
from typing import List

from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.utils.registry import registry
from omagent_core.models.llms.qwen_vl import Qwen_VL
from omagent_core.models.llms.base import BaseLLM


from omagent_core.engine.worker.base import BaseWorker, BaseLocalWorker
from omagent_core.utils.container import container

from pathlib import Path

from omagent_core.utils.registry import registry
from omagent_core.utils.logger import logging
from omagent_core.lite_engine.task import Task
from omagent_core.lite_engine.workflow import Workflow
from omagent_core.memories.stms.stm_sharedMem import SharedMemSTM
import os

CURRENT_PATH = Path(__file__).parents[0]


@registry.register_worker()
class SimpleVQA(BaseLocalWorker, BaseLLMBackend):
    """Simple Visual Question Answering processor that handles image-based questions.
    
    This processor:
    1. Takes user instruction and cached image from workflow context
    2. Creates chat messages containing the text question and base64-encoded image
    3. Sends messages to LLM to generate a response
    4. Returns response and sends it via callback
    """
    llm: BaseLLM

    def _run(self, user_instruction, *args, **kwargs):
        # Initialize empty list for chat messages        
        chat_complete_res = self.llm.generate(records=user_instruction)        
        # Extract answer text from response
        answer = chat_complete_res["responses"]        
        # Send answer via callback and return
        #self.callback.send_answer(self.workflow_instance_id, msg=answer)
        return answer


class VQA_Agent:
    def __init__(self,model_name):
        llm = Qwen_VL(model_name=model_name) 
        self.simple_vqa = SimpleVQA(llm=llm)
        
    def run(self, inputs):
        simple_vqa = Task(name='SimpleVQA', func=self.simple_vqa, inputs=inputs)        
        workflow = Workflow(name='example_workflow')        
        workflow  >> simple_vqa
        workflow.execute()        
        return simple_vqa.output()
        


if __name__ == "__main__":
    #def init_agent():
    
    CURRENT_PATH = Path(__file__).parents[0]    
    registry.import_module(project_path=CURRENT_PATH.joinpath('agent'))
    logging.init_logger("omagent", "omagent", level="INFO")
    container.register_stm("SharedMemSTM")    


    user_input = {
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Could you please analyze this image?"
                },
                {
                    "type": "image",
                    "image": "demo.jpg"
                }
            ]
        }
    ]
}
    q = VQA_Agent(model_name="Qwen/Qwen2-VL-2B-Instruct")
    final = q.run(user_input)
    print ("final", final)

