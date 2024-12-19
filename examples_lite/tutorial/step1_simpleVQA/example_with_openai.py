from pathlib import Path
from typing import List

from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.utils.registry import registry
from omagent_core.models.llms.schemas import Message, Content
from omagent_core.utils.general import encode_image
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.models.llms.qwen_vl import Qwen_VL
from omagent_core.models.llms.base import BaseLLM


from omagent_core.engine.worker.base import BaseWorker, BaseWorker
from omagent_core.utils.container import container

from pathlib import Path

from omagent_core.utils.registry import registry
from omagent_core.utils.general import read_image
from omagent_core.utils.logger import logging
from omagent_core.lite_engine.task import Task
from omagent_core.lite_engine.workflow import Workflow
from omagent_core.memories.stms.stm_sharedMem import SharedMemSTM
import os

CURRENT_PATH = Path(__file__).parents[0]


@registry.register_worker()
class InputInterface(BaseWorker):
    """Input interface processor that handles user instructions and image input.
    
    This processor:
    1. Reads user input containing question and image via input interface
    2. Extracts text instruction and image path from the input
    3. Loads and caches the image in workflow storage
    4. Returns the user instruction for next steps
    """
    
    def _run(self, user_input, *args, **kwargs):
        # Read user input through configured input interface
        
        image_path = None
        # Extract text and image content from input message
        content = user_input['messages'][-1]['content']
        for content_item in content:
            if content_item['type'] == 'text':
                user_instruction = content_item['data']
            elif content_item['type'] == 'image_url':
                image_path = content_item['data']
        
        logging.info(f'User_instruction: {user_instruction}\nImage_path: {image_path}')
        
        # Load image from file system
        if image_path:
            img = read_image(input_source=image_path)
            
            # Store image in workflow shared memory with standard key
            image_cache = {'<image_0>' : img}
            print (self.workflow_instance_id)
            self.stm(self.workflow_instance_id)['image_cache'] = image_cache

        #return {'user_instruction': user_instruction}
        return user_instruction


@registry.register_worker()
class SimpleVQA(BaseWorker, BaseLLMBackend):
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
        chat_message = []
        
        # Add text question as first message
        chat_message.append(Message(role="user", message_type='text', content=user_instruction))

        # Retrieve cached image from workflow shared memory
        if self.stm(self.workflow_instance_id).get('image_cache', None):
            img = self.stm(self.workflow_instance_id)['image_cache']['<image_0>']
        
            # Add base64 encoded image as second message
            chat_message.append(Message(role="user", message_type='image', content=[Content(
                                        type="image_url",
                                        image_url={
                                            "url": f"data:image/jpeg;base64,{encode_image(img)}"
                                        },
                                    )]))
        
        # Get response from LLM model
        chat_complete_res = self.llm.generate(records=chat_message)

        # Extract answer text from response
        answer = chat_complete_res["choices"][0]["message"]["content"]
        
        # Send answer via callback and return
        self.callback.send_answer(self.workflow_instance_id, msg=answer)
        return answer


class VQA_Agent:
    def __init__(self,api_key):
        #llm = OpenaiGPTLLM(api_key=api_key)       
        llm = Qwen_VL() 
        self.simple_vqa = SimpleVQA(llm=llm)
        self.inputinterface = InputInterface()
        

    def run(self, inputs):
        inputinterface = Task(name='inputinterface', func=self.inputinterface, inputs=inputs)
        simple_vqa = Task(name='SimpleVQA', func=self.simple_vqa, inputs=inputinterface.output)        
        workflow = Workflow(name='example_workflow')        
        workflow >> inputinterface >> simple_vqa
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
                    "data": "Could you please analyze this image?"
                },
                {
                    "type": "image_url",
                    "data": "demo.jpg"
                }
            ]
        }
    ]
}
    q = VQA_Agent(api_key=os.getenv("OPENAI_API_KEY", "default_api_key"))
    final = q.run(user_input)
    print ("final", final)

