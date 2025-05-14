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



CURRENT_PATH = Path(__file__).parents[0]


@registry.register_worker()
class KeepBestN(BaseLLMBackend, BaseWorker):
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("sys_prompt.prompt"), role="system"
            ),
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("user_prompt.prompt"), role="user"
            ),
        ]
    )

    def _run(self, *args, **kwargs):
        """
        Keeps the best N nodes from the task tree based on their scores.
        
        This method:
        1. Identifies nodes that can be executed in the current phrase
        2. Groups nodes by their task type
        3. Selects the top N nodes from each task group based on scores
        4. Creates new nodes for the next phrase using the selected nodes
        
        
        Returns:
            dict: Contains the updated task tree structure
        """
        # if not split, we will not generate task and response directly. So check if response is None. If not, we will skip the got process and move to the final refine phrase.
        try:
            response = self.stm(self.workflow_instance_id)['response']
            self.callback.info(agent_id=self.workflow_instance_id, progress="Select best n nodes is not processed as we did't use got process", message="")
            return {'got_structure': self.stm(self.workflow_instance_id)['task_tree'].model_dump()}
        except:
            query = self.stm(self.workflow_instance_id)['query']
            task_tree = self.stm(self.workflow_instance_id)['task_tree']

        
        current_nodes = []
        task_groups = {}
        for id in task_tree.leaves:
            node = task_tree.get_node(id)
            can_be_executed = task_tree.is_node_can_be_executed(id)
            if node.phrase == self.stm(self.workflow_instance_id)['phrase'] and can_be_executed:
                current_nodes.append(node)
                task_groups[node.task] = task_groups.get(node.task, []) + [node]
        
        assert all(
            node.scored for node in current_nodes
        ), "Not all nodes have been scored"
        
        for key in task_groups.keys():
            task_groups[key].sort(key=lambda x: x.score, reverse=self.higher_is_better)
            predecessors = [node.id for node in task_groups[key]]
            task_groups[key] = task_groups[key][:self.best_n]
            new_node = task_groups[key][0].copy_as_dict(phrase=self.stm(self.workflow_instance_id)['phrase'] + 1)
            if self.best_n == 1:
                new_node['current_task_input'] = task_groups[key][0].current_task_input
            else:
                new_node['current_task_input'] = [node.current_task_input for node in task_groups[key]]
            task_tree.add_node(new_node, predecessors)
            self.callback.info(agent_id=self.workflow_instance_id, progress="Add best {} nodes".format(self.best_n), message=new_node['current_task_input'])

        self.stm(self.workflow_instance_id)['task_tree'] = task_tree
        self.stm(self.workflow_instance_id)['phrase'] = self.stm(self.workflow_instance_id)['phrase'] + 1

        self.callback.info(agent_id=self.workflow_instance_id, progress="Select best n nodes finished", message=new_node)
        return {'got_structure': task_tree.model_dump()}



