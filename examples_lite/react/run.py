from pathlib import Path
from omagent_core.utils.registry import registry
from omagent_core.utils.container import container
from omagent_core.utils.logger import logging
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.agents.react_agent import ReActAgent
from omagent_core.tool_system.manager import ToolManager
from omagent_core.tool_system.tools.web_search.search import WebSearch


if __name__ == "__main__":
    # Initialize logger
    logging.init_logger("omagent", "omagent", level="INFO")
    
    # Register memory storage
    container.register_stm("RedisSTM")
    
    # Setup LLM
    llm = OpenaiGPTLLM(
        endpoint="http://36.133.246.107:11002/v1",
        api_key="YOUR_API_KEY",
        model="gpt-4o"
    )
    web_search_tool = WebSearch(bing_api_key="bing_api_key", llm=llm)
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
    
    result = agent.run(user_input)
    print("final", result)
