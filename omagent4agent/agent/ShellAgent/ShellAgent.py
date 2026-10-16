from pathlib import Path
from typing import List
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.models.llms.base import BaseLLMBackend, BaseLLM
from omagent_core.models.llms.prompt import PromptTemplate
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry
from pydantic import Field
from omagent_core.tool_system.manager import ToolManager

CURRENT_PATH = root_path = Path(__file__).parents[0]


@registry.register_worker()
class ShellAgent(BaseLLMBackend, BaseWorker):
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_file(CURRENT_PATH.joinpath("shell_agent_system.prompt"), role="system"),
            PromptTemplate.from_file(CURRENT_PATH.joinpath("shell_agent_user.prompt"), role="user"),
        ]
    )
    llm: BaseLLM
    tool_manager: ToolManager
    def _run(self, task: str, *args, **kwargs):       
        
        shell_command = self.simple_infer(prompt=task)["choices"][0]["message"].get("content")
        
        self.tool_manager.execute_tool("shell", shell_command)

        self.callback.info(agent_id=self.workflow_instance_id, progress="ShellAgent", message=shell_command)
        

