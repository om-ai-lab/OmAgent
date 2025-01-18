from pathlib import Path

from omagent_core.engine.worker.base import BaseWorker
from omagent_core.tool_system.manager import ToolManager
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry

CURRENT_PATH = root_path = Path(__file__).parents[0]


@registry.register_worker()
class WeatherSearcher(BaseWorker):
    """Weather searcher processor that searches for weather information based on user input.

    This processor:
    1. Takes user instruction from workflow context
    2. Constructs a search query to find weather and temperature data
    3. Executes the search using tool manager and logs results
    4. Stores search results in workflow context for downstream use

    Attributes:
        tool_manager: Tool manager instance for executing web searches and retrieving weather data
    """

    tool_manager: ToolManager

    def _run(self, user_instruction: str, *args, **kwargs):
        """Process user instruction to search for weather information.

        Args:
            user_instruction (str): The user's input text containing weather-related query
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments

        Returns:
            None: Results are stored in workflow context

        Raises:
            ValueError: If the web search tool execution fails to retrieve weather data
        """
        # Construct search query with instructions for datetime and location extraction
        search_query = "Please consider the user instruction and generate a search query for the web search tool to search for the weather according to user requirements. You MUST choose the web search tool in the tool_call to excute. When generating the search query, consider to include the datatime and location from provided information. User Instruction: {}".format(
            user_instruction
        )

        # Execute weather search via tool manager and notify user
        execution_status, execution_results = self.tool_manager.execute_task(
            task=search_query
        )
        self.callback.send_block(
            agent_id=self.workflow_instance_id,
            msg="Using web search tool to search for weather information",
        )
        logging.info(execution_results)

        # Store successful results in workflow context or raise error
        if execution_status == "success":
            self.stm(self.workflow_instance_id)["search_info"] = execution_results
        else:
            raise ValueError("Web search tool execution failed.")

        return
