from omagent_core.utils.container import container
from omagent_core.utils.logger import logging
from omagent_core.agents.simple_vqa.simple_vqa_agent import VQA_Agent
from omagent_core.memories.stms.stm_sharedMem import SharedMemSTM
import os

if __name__ == "__main__":
    #CURRENT_PATH = Path(__file__).parents[0]    
    #registry.import_module(project_path=CURRENT_PATH.joinpath('step1_simpleVQA'))
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