from pathlib import Path
from omagent_core.utils.registry import registry
from omagent_core.utils.container import container

from pathlib import Path

from omagent_core.utils.registry import registry
from omagent_core.utils.logger import logging
from omagent_core.omagent_simple.agents.simple_vqa_agent import VQA_Agent


if __name__ == "__main__":
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
    q = VQA_Agent(api_key="api_key")
    final = q.run(user_input)
    print ("final", final)