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

from omagent_core.utils.env import EnvVar
from omagent_core.utils.registry import registry
from omagent_core.utils.logger import logging
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.models.llms.prompt.prompt import PromptTemplate
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.advanced_components.workflow.general_got.schemas.got_structure import TaskTree, TaskNode
import json_repair
from omagent_core.advanced_components.workflow.general_got.agent.utils import sort_num_errors, sort_parse_refine_answer

CURRENT_PATH = Path(__file__).parents[0]


@registry.register_worker()
class TaskConcluder(BaseLLMBackend, BaseWorker):
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("response_parser_sys_prompt.prompt"), role="system"
            ),
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("response_parser_user_prompt.prompt"), role="user"
            ),
        ]
    )

    def _run(self, *args, **kwargs):
        """
        Execute the task conclusion process using LLM.
        
        This method:
        1. Retrieves the query and task tree from the state management
        2. Identifies the current executable nodes in the last phase
        3. Processes the final output based on special task types
        4. Reports token usage statistics
        
        Returns:
            dict: Contains the final output and token usage information
        """

        # if not split, we will not generate task and response directly. So check if response is None. If not, we will skip the got process and move to the final refine phrase.
        try:
            response = self.stm(self.workflow_instance_id)['response']
            #return {'got_structure': self.stm(self.workflow_instance_id)['task_tree'].model_dump()}
            token_usage = self.stm(self.workflow_instance_id)['token_usage']
            self.callback.info(agent_id=self.workflow_instance_id, progress='The result is:', message=response)
            self.callback.info(agent_id=self.workflow_instance_id, progress='Token usage', message=token_usage)
            return {'Final output': response, 'token_usage': token_usage}
        except:
            query = self.stm(self.workflow_instance_id)['query']
            task_tree = self.stm(self.workflow_instance_id)['task_tree']

        current_nodes = []
        for id in task_tree.leaves:
            node = task_tree.get_node(id)
            can_be_executed = task_tree.is_node_can_be_executed(id)
            if node.phrase == self.stm(self.workflow_instance_id)['phrase'] and can_be_executed:
                current_nodes.append(node)
        
        assert len(current_nodes) == 1, "There should be only one node in the last phrase"

        # Parse the final answer if not special task
        if self.stm(self.workflow_instance_id)['special_task'] is None:
            answer = self.simple_infer(input=query, response=node.current_task_input)
            answer = json_repair.loads(answer['choices'][0]['message']['content'])
            node.current_task_input = answer

        self.callback.info(agent_id=self.workflow_instance_id, progress='Concluder conduct result', message=node.current_task_input)
        print("*"*50)
        self.callback.info(agent_id=self.workflow_instance_id, progress='The task is:', message=query)
        print("*"*50)
        self.callback.info(agent_id=self.workflow_instance_id, progress='The result is:', message=node.current_task_input)

        if self.stm(self.workflow_instance_id)['special_task'] == "sort":
            print(sorted(json_repair.loads(str(node.original_task_input))))
        elif self.stm(self.workflow_instance_id)['special_task'] == "keyword_count":
            print(node.pre_task_input)
        elif self.stm(self.workflow_instance_id)['special_task'] == "set_intersection":
            print(node.pre_task_input)
        token_usage = self.stm(self.workflow_instance_id)['token_usage']
        self.callback.info(agent_id=self.workflow_instance_id, progress='Token usage', message=token_usage)
        return {'Final output': node.current_task_input, 'token_usage': token_usage}
    