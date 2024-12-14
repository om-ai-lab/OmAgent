from omagent_core.utils.container import container
from omagent_core.utils.logger import logging
from omagent_core.memories.stms.stm_sharedMem import SharedMemSTM

from omagent_core.agents.simple_qa.simple_qa_agent import QA_Agent


if __name__ == "__main__":
    logging.init_logger("omagent", "omagent", level="INFO")
    container.register_stm("SharedMemSTM")    

    q = QA_Agent(model_name="Qwen/Qwen2.5-1.5B-Instruct")
    final = q.run("what is 1+1?")
    print ("final", final)