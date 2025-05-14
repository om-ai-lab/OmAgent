import os
os.environ["OMAGENT_MODE"] = "lite"
from typing import List
from pydantic import Field
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.models.llms.prompt import PromptTemplate
from omagent_core.models.llms.prompt.parser import *
from PIL import Image
from omagent_core.utils.container import container
from omagent_core.memories.stms.stm_sharedMem import SharedMemSTM
from omagent_core.utils.registry import registry
from pathlib import Path
from omagent_core.utils.general import encode_image, read_image
from omagent_core.tool_system.manager import ToolManager
import asyncio

# Set current working directory path
CURRENT_PATH = Path(__file__).parents[0]

# Import registered modules
registry.import_module(project_path=CURRENT_PATH.joinpath("agent"))
container.register_stm("SharedMemSTM")

class LLMTest(BaseLLMBackend):
    llm: OpenaiGPTLLM ={
        "name": "OpenaiGPTLLM", 
        "model_id": "gpt-4o-mini", 
        "api_key": os.getenv("custom_openai_key"), 
        "endpoint": "https://api.openai.com/v1",   
        "vision": False,
        "response_format": "text",
        "use_default_sys_prompt": False,
        }
    tool_manager: ToolManager ={
        "llm": llm, 
        "tools": []
    }

llm_test = LLMTest(workflow_instance_id="temp")

tool_manager = llm_test.tool_manager
x = tool_manager.execute_task("command ls -l for the current directory") 
print(x)

