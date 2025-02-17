import json
import re
from pathlib import Path
from typing import List, Tuple, Any
import math
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
class TaskSplitter(BaseLLMBackend, BaseWorker):
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

    def _run(self, query: str, task: str, meta: dict, *args, **kwargs):
        """A task splitter that breaks down complex tasks into multiple subtasks.
        
        Args:
            query (str): The input query to be processed.
            task (str): The type of task to be performed (e.g., 'sort', 'set_intersection', 'keyword_count').
            meta (dict): Additional metadata required for task processing.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            dict: A dictionary containing the task tree structure with subtasks.
                  Format: {'got_structure': <task_tree_model_dump>}

        Raises:
            ValueError: If required metadata is missing for specific task types or task cannot be split.
        """

        task_tree = TaskTree()
        if task is not None and task != "":
            self.special_task = task
        else:
            self.special_task = None
        if meta is not None and meta != {}:
            self.meta = meta


        if self.special_task is not None:
            self.prompts = [
                PromptTemplate.from_file(
                    CURRENT_PATH.joinpath("sys_prompt.prompt"), role="system"
                ),
                PromptTemplate.from_file(
                    CURRENT_PATH.joinpath("{}_user_prompt.prompt".format(self.special_task)), role="user"
                ),
            ]
        else:
            self.prompts = [
                PromptTemplate.from_file(
                    CURRENT_PATH.joinpath("check_split_sys_prompt.prompt"), role="system"
                ),
                PromptTemplate.from_file(
                    CURRENT_PATH.joinpath("check_split_user_prompt.prompt"), role="user"
                ),
            ]
            
            check_response = self.simple_infer(input=query)
            print(check_response)
            try:
                check_result = json_repair.loads(check_response['choices'][0]['message']['content'])
                can_split = check_result['can_split']
                self.callback.info(agent_id=self.workflow_instance_id, progress='Task Split Result', message=can_split)
            except Exception as e:
                print(e)
                can_split = False
            if not can_split:
                self.callback.info(agent_id=self.workflow_instance_id, progress='Task Split', message="Task cannot be split, we will not split the task")
                self.stm(self.workflow_instance_id)['query'] = query
                self.prompts = [
                    PromptTemplate.from_file(
                        CURRENT_PATH.joinpath("sys_prompt.prompt"), role="system"
                        ),
                    PromptTemplate.from_file(
                        CURRENT_PATH.joinpath("user_prompt.prompt"), role="user"
                    ),
                ]
                response = self.simple_infer(query=query)['choices'][0]['message']['content']
                task_tree.add_node({"task": "task cannot be split", "original_task_input": self.stm(self.workflow_instance_id)['query'], "phrase": "0"})
                self.stm(self.workflow_instance_id)['task_tree'] = task_tree
                self.stm(self.workflow_instance_id)['response'] = response
                return {'got_structure': None}
            else:
                self.callback.info(agent_id=self.workflow_instance_id, progress='Task Split', message="Task can be split, we will split the task")

                
                self.prompts = [
                    PromptTemplate.from_file(
                        CURRENT_PATH.joinpath("general_split_sys_prompt.prompt"), role="system"
                    ),
                    PromptTemplate.from_file(
                        CURRENT_PATH.joinpath("general_split_user_prompt.prompt"), role="user"
                    ),
                ]
                chat_complete_res = self.simple_infer(input=query)
                print(chat_complete_res)


        self.stm(self.workflow_instance_id)['query'] = query
        self.stm(self.workflow_instance_id)['phrase'] = 0
        self.stm(self.workflow_instance_id)['current_node_id'] = 0
        self.stm(self.workflow_instance_id)['special_task'] = self.special_task
        task_tree.add_node({"task": "split the task into subtasks", "original_task_input": self.stm(self.workflow_instance_id)['query'], "phrase": self.stm(self.workflow_instance_id)['phrase']})
        self.callback.info(agent_id=self.workflow_instance_id, progress='Task Split', message=query)

        if self.special_task == "sort":
            # split the list into sublists by 8 elements
            query_length = len(json_repair.loads(query))
            if self.chunk_size is not None:
                num_chunks = math.ceil(query_length / self.chunk_size)
                self.callback.info(agent_id=self.workflow_instance_id, progress='Task Split', message="Input will be divided into {} sub tasks".format(num_chunks))
            chat_complete_res = self.simple_infer(input=query, query_length=query_length, num_chunks=num_chunks, chunk_size=self.chunk_size)
        elif self.special_task == "set_intersection":
            self.callback.info(agent_id=self.workflow_instance_id, progress='Task Split', message="Chunk size is {}".format(self.chunk_size))
            inputs = json_repair.loads(query)
            set1, set2 = str(inputs['set1']), str(inputs['set2'])
            query_length = len(json_repair.loads(set2))
            if self.chunk_size is not None:
                num_chunks = math.ceil(query_length / self.chunk_size)
                self.callback.info(agent_id=self.workflow_instance_id, progress='Task Split', message="Input will be divided into {} sub tasks".format(num_chunks))
            chat_complete_res = self.simple_infer(input=set2, query_length=query_length, num_chunks=num_chunks, chunk_size=self.chunk_size)
        elif self.special_task == "keyword_count":
            try:
                self.stm(self.workflow_instance_id)['all_possible_countries'] = self.meta['all_possible_countries']
            except Exception:
                raise ValueError("all_possible_countries must be in meta information for keyword_count task. Please check the meta information.")
            chat_complete_res = self.simple_infer(input=query)
        
        # prepare task_tree for each subtasks
        try:
            subtasks = json_repair.loads(chat_complete_res['choices'][0]['message']['content'])
            if self.special_task in ["sort", "set_intersection"] and 'num_chunks' in locals() and len(subtasks.keys()) != num_chunks:
                logging.warning("Expected {} lists in json, but found {}.".format(num_chunks, len(subtasks.keys())))
            
            self.stm(self.workflow_instance_id)['phrase'] = self.stm(self.workflow_instance_id)['phrase'] + 1
            task_tree.nodes[0].current_task_input = subtasks
            for key, value in subtasks.items():
                subtask = {
                    "task": key, 
                    "original_task_input": value, 
                    "current_task_input": value,
                    "phrase": self.stm(self.workflow_instance_id)['phrase'], 
                    }
                task_tree.add_node(subtask, [0])
            
        except Exception as e:
            logging.error(f"Could not parse answer: {chat_complete_res}. Encountered exception: {e}")
            subtasks = chat_complete_res["choices"][0]["message"]["content"]

        self.callback.info(agent_id=self.workflow_instance_id, progress='Task Split', message=subtasks)
        task_tree.get_node(0).executed = True
        self.stm(self.workflow_instance_id)['task_tree'] = task_tree
        return {'got_structure': task_tree.model_dump()}

