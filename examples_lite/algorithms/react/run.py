from pathlib import Path

from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.utils.container import container

from pathlib import Path
from omagent_core.utils.logger import logging
from omagent_core.memories.stms.stm_redis import RedisSTM

from omagent_core.agents.react_agent.react import ReActAgent
from omagent_core.tool_system.manager import ToolManager
from omagent_core.tool_system.tools.web_search.search import WebSearch
import os


CURRENT_PATH = Path(__file__).parents[0]

if __name__ == "__main__":
    # Initialize logger
    logging.init_logger("omagent", "omagent", level="INFO")
    
    # Register memory storage    
    container.register_stm("RedisSTM")
    
    # Setup LLM
    llm = OpenaiGPTLLM(
        api_key=os.getenv("OPENAI_API_KEY", "default_api_key"),
        model="gpt-4o"
    )
    web_search_tool = WebSearch(bing_api_key=os.getenv("bing_api_key", "bing_api_key"), llm=llm)
    tool_manager = ToolManager(name="WebSearch", tools=[web_search_tool], llm=llm)
    # Create and use agent
    
    agent = ReActAgent(
        llm=llm,
        tool_manager=tool_manager
    )

    # Define input query
    user_input = {
        "messages": [
            {
                "role": "user",
                "content": "What is the weather in Paris?"
            }
        ]
    }
    user_input="What is the weather in Paris?"
    result = agent.run(user_input)
    print("final", result)
