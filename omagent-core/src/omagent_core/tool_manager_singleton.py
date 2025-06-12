from omagent_core.tool_system.manager import ToolManager
from pathlib import Path
import os
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM


llm= OpenaiGPTLLM = {
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
    
# Create a single global instance
global_tool_manager = ToolManager(llm=llm, tools=[])

# Initialize it once with your configuration
def initialize(config_path=None):
    if config_path:        
        global_tool_manager.initialize_mcp(Path(config_path))
    else:
        global_tool_manager.initialize_mcp()
    return global_tool_manager

# Access the singleton instance
def get_tool_manager():
    return global_tool_manager