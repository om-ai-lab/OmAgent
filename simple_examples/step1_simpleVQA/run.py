from pathlib import Path
from omagent_core.utils.registry import registry
from omagent_core.utils.container import container

from pathlib import Path

from omagent_core.utils.registry import registry
from omagent_core.utils.logger import logging
from omagent_core.advanced_components.simple_agents.simple_vqa_agent import VQA_Agent


if __name__ == "__main__":
    CURRENT_PATH = Path(__file__).parents[0]    
    registry.import_module(project_path=CURRENT_PATH.joinpath('step1_simpleVQA'))
    logging.init_logger("omagent", "omagent", level="INFO")
    container.register_stm("RedisSTM")    


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
    q = VQA_Agent(api_key="openai_apikey")
    final = q.run(user_input)
    print ("final", final)