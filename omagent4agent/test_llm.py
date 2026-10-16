from typing import List
from pydantic import Field
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.models.llms.prompt import PromptTemplate
from omagent_core.models.llms.prompt.parser import *
from PIL import Image
from omagent_core.utils.container import container
import os 
import json
from omagent_core.memories.stms.stm_sharedMem import SharedMemSTM
from omagent_core.utils.registry import registry
from pathlib import Path
from omagent_core.utils.general import encode_image, read_image
from omagent_core.tool_system.manager import ToolManager
import asyncio
from omagent_core.models.llms.schemas import Message

os.environ["OMAGENT_MODE"] = "lite"
# Set current working directory path
CURRENT_PATH = Path(__file__).parents[0]

# Import registered modules
registry.import_module(project_path=CURRENT_PATH.joinpath("agent"))
container.register_stm("SharedMemSTM")

class LLMTest(BaseLLMBackend):
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_template("You are a helpful assistant.", role="system"),
            PromptTemplate.from_template("detect the objects in the image. the path is '{{image}}'. Return the result in json format. For examples, if the image is a fruit, the result should be like this: {'fruit': ['apple', 'banana', 'orange']}}", role="user"),
        ]
    )
    llm: OpenaiGPTLLM = {
        "name": "OpenaiGPTLLM", 
        "model_id": "ep-20250214102831-7mfjh",  
        "api_key": os.getenv("custom_openai_key"), 
        "endpoint": "https://ark.cn-beijing.volces.com/api/v3",
        "vision": False,
        "response_format": {"type": "text"},
        "use_default_sys_prompt": False,
        "temperature": 0.01,
        "max_tokens": 4096,
    }
    tool_manager: ToolManager = {
        "llm": llm, 
        "tools": []
    }

# Instantiate the test
llm_test = LLMTest(workflow_instance_id="temp")
print("Test initialized with model:", llm_test.llm.model_id)

# Access the tool manager
tool_manager = llm_test.tool_manager

# Print available tools
print("\n--- Available Tools ---")
for name, tool in tool_manager.tools.items():
    
    print(f"Tool: {name} - {tool.description}")
    print (tool.generate_schema())

x = tool_manager.execute_task("browse webpage https://www.milemoa.com/bbs/")
print (x)

