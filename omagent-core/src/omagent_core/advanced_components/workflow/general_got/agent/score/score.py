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
from omagent_core.advanced_components.workflow.general_got.agent.utils import sort_num_errors, keyword_count_num_errors, set_intersection_num_errors



CURRENT_PATH = Path(__file__).parents[0]


@registry.register_worker()
class TaskScore(BaseLLMBackend, BaseWorker):
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
    eval_method: str = None

    def _run(self, *args, **kwargs):
        """Score task execution results
        
        Select appropriate scoring function based on special_task type.
        Supported scoring methods:
        - sort_num_errors: Scoring for sorting tasks
        - keyword_count_num_errors: Scoring for keyword counting tasks
        - set_intersection_num_errors: Scoring for set intersection tasks
        """
        
        # if not split, we will not generate task and response directly. So check if response is None. If not, we will skip the got process and move to the final refine phrase.
        try:
            response = self.stm(self.workflow_instance_id)['response']
            self.callback.info(agent_id=self.workflow_instance_id, progress="Score eval is not processed as we did't use got process", message="")
            return {'got_structure': self.stm(self.workflow_instance_id)['task_tree'].model_dump()}
        except:
            query = self.stm(self.workflow_instance_id)['query']
            task_tree = self.stm(self.workflow_instance_id)['task_tree']
            special_task = self.stm(self.workflow_instance_id)['special_task']
    
        self.scoring_function = None
        if special_task in ["sort", "set_intersection", "keyword_count"]:
            self.eval_method = "{}_num_errors".format(special_task)
        else:
            self.eval_method = ""

        # Select scoring function based on eval_method
        if self.eval_method == "sort_num_errors":
            self.scoring_function = sort_num_errors
        elif self.eval_method == "keyword_count_num_errors":
            self.scoring_function = keyword_count_num_errors
        elif self.eval_method == "set_intersection_num_errors":
            self.scoring_function = set_intersection_num_errors
        else:
            self.scoring_function = None
            self.callback.info(agent_id=self.workflow_instance_id, progress='Scoring', message="No scoring function found. LLM will score the nodes.".format(self.eval_method))

        if self.scoring_function is not None:
            self.callback.info(agent_id=self.workflow_instance_id, progress='Scoring', message="Using function {} to score nodes".format(self.eval_method))

        # Get executable leaf nodes
        current_nodes = []
        for id in task_tree.leaves:
            node = task_tree.get_node(id)
            can_be_executed = task_tree.is_node_can_be_executed(id)
            if node.phrase == self.stm(self.workflow_instance_id)['phrase'] and can_be_executed:
                current_nodes.append(node)
        
        # Score each node
        for node in current_nodes:
            if self.eval_method == "keyword_count_num_errors":
                node_score = self.scoring_function(self.stm(self.workflow_instance_id)['all_possible_countries'], node.model_dump())
            elif self.eval_method == "set_intersection_num_errors":
                inputs = json_repair.loads(query)
                set1, _ = inputs['set1'], inputs['set2']
                node_score = self.scoring_function(set1, node.model_dump())
            elif self.eval_method == "sort_num_errors":
                node_score = self.scoring_function(node.model_dump())
            else:
                # use llm to score the node
                self.callback.info(agent_id=self.workflow_instance_id, progress="Scoring", message="Using LLM to score the node")
                node_score = self.simple_infer(query = query, current_task_input = node.current_task_input)['choices'][0]['message']['content']
                try:
                    node_score = json_repair.loads(node_score)
                    self.callback.info(agent_id=self.workflow_instance_id, progress="Scoring", message="Score: {}".format(node_score))
                    node_score = node_score['score']
                except:
                    node_score = 300
                    self.callback.info(agent_id=self.workflow_instance_id, progress="Scoring", message="Invalid score format {}. Score set to 300".format(node_score))
                try:
                    node_score = float(node_score)
                except:
                    node_score = 300
                    self.callback.info(agent_id=self.workflow_instance_id, progress="Scoring", message="Invalid score format {}. Score set to 300".format(node_score))


            self.callback.info(agent_id=self.workflow_instance_id, progress="Original input: {}, Eval score for {}".format(node.original_task_input, node.current_task_input), message=node_score)
            node.score = node_score
            node.executed = True
            node.scored = True
            
        self.stm(self.workflow_instance_id)['task_tree'] = task_tree
        self.callback.info(agent_id=self.workflow_instance_id, progress="Score eval finished", message="")
        return {'got_structure': task_tree.model_dump()}



