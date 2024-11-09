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

from ....memories.ltms.ltm import LTM
from ....utils.env import EnvVar
from ....utils.registry import registry
from ....models.llms.base import BaseLLMBackend
from ....models.llms.prompt.prompt import PromptTemplate
from ....tool_system.manager import ToolManager
from ....engine.worker.base import BaseWorker
from ....engine.workflow.context import BaseWorkflowContext
from ....engine.task.agent_task import TaskTree
import time
from ....utils.general import read_image

CURRENT_PATH = Path(__file__).parents[0]


@registry.register_worker()
class ClientInput(BaseWorker):
    def _run(self, *args, **kwargs):
        user_input = self.input.read_input(workflow_instance_id=self.workflow_instance_id, input_prompt=None)
        tree = TaskTree()
        chat_message = []
        agent_id = user_input['agent_id']
        messages = user_input['messages']
        idx = 0
        message = messages[-1]
        image = None
        text = None
        for each_content in message['content']:
            if each_content['type'] == 'image_url':
                image = read_image(each_content['data'])
            elif each_content['type'] == 'text':
                text = each_content['data']
        if image is not None:
            self.stm(self.workflow_instance_id)['image_cache'] = {f'<image_0>' : image}
        if text is not None:
            tree.add_node({"task": text})
        return {'agent_task': tree.model_dump(), 'last_output': None}
