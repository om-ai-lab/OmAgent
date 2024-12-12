from pathlib import Path
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.registry import registry
from omagent_core.tool_system.manager import ToolManager
from omagent_core.utils.logger import logging

CURRENT_PATH = root_path = Path(__file__).parents[0]


@registry.register_worker()
class MemeSearcher(BaseWorker):

    tool_manager : ToolManager

    def _run(self, user_instruction:str, *args, **kwargs):
        # Construct search query with instructions for datetime and location extraction
        # search_query = "Please consider the user instruction and generate a search query for the internet memo search tool to search for the explaination according to user requirements. You MUST choose the web search tool in the tool_call to excute. When generating the search query, please include how this memo comes from how to use this memo. User Instruction: {}".format(user_instruction)

        # search_query = "Please consider the user instruction and generate a search query for the internet memo search. You MUST choose the web search tool in the tool_call to excute. User Instruction: 搜索{}, 并提供相关的3个例子，需要获得三个query results".format(user_instruction)

        search_query = "Please consider the user instruction and generate a search query for the internet meme search. You MUST choose the web search tool in the tool_call to excute. User Instruction: search {} meme, and provide three examples of {} usage in context，need to gie out three query results".format(user_instruction, user_instruction)
        
        logging.info(search_query)
        # Execute memo search via tool manager and notify user
        execution_status, execution_results = self.tool_manager.execute_task(
                task=search_query
            )
        self.callback.send_block(agent_id=self.workflow_instance_id, msg='Using web search tool to search for meme information')
        logging.info(execution_results)

        # Store successful results in workflow context or raise error 
        if execution_status == "success":
            self.stm(self.workflow_instance_id)["search_info"] = execution_results
        else:
            raise ValueError("Web search tool execution failed.")
        
        return
