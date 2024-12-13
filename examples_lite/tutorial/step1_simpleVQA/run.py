from pathlib import Path
from omagent_core.utils.registry import registry
from omagent_core.utils.container import container

from pathlib import Path

from omagent_core.utils.registry import registry
from omagent_core.utils.logger import logging
from omagent_core.agents.simple_vqa.simple_vqa_agent import VQA_Agent


if __name__ == "__main__":
    #CURRENT_PATH = Path(__file__).parents[0]    
    #registry.import_module(project_path=CURRENT_PATH.joinpath('step1_simpleVQA'))
    logging.init_logger("omagent", "omagent", level="INFO")
    container.register_stm("DictSTM")    

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
    q = VQA_Agent(api_key="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")
    final = q.run(user_input)
    print ("final", final)