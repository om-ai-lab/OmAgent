from pathlib import Path
from omagent_core.utils.registry import registry
from omagent_core.utils.container import container

from pathlib import Path

from omagent_core.utils.registry import registry
from omagent_core.utils.logger import logging
from omagent_core.omagent_simple.agents.simple_qa_agent import QA_Agent


if __name__ == "__main__":
    logging.init_logger("omagent", "omagent", level="INFO")
    container.register_stm("RedisSTM")    

    q = QA_Agent(model_name="Qwen/Qwen2.5-1.5B-Instruct")
    final = q.run("what is 1+1?")
    print ("final", final)