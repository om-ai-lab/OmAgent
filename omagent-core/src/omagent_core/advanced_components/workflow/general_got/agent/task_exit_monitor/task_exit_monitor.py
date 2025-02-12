import json
import re
from pathlib import Path
from typing import List, Tuple, Any

from pydantic import Field
from tenacity import (
    retry,
    retry_if_exception_message,
    stop_after_attempt,
    stop_after_delay,
)

from omagent_core.memories.ltms.ltm import LTM
from omagent_core.utils.env import EnvVar
from omagent_core.utils.registry import registry
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.models.llms.prompt.prompt import PromptTemplate
from omagent_core.tool_system.manager import ToolManager
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.advanced_components.workflow.general_got.schemas.got_structure import TaskTree, TaskNode
import json_repair

CURRENT_PATH = Path(__file__).parents[0]


@registry.register_worker()
class GoTTaskExitMonitor(BaseWorker):

    def _run(self, *args, **kwargs):
        task_tree = self.stm(self.workflow_instance_id)['task_tree']
        if len(task_tree.leaves) == 1 and self.stm(self.workflow_instance_id)['process'] == 'refine':
            return {"exit_flag": True}
        else:
            return {"exit_flag": False}
