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
from omagent_core.advanced_components.workflow.general_got.agent.utils import sort_parse_refine_answer, keyword_count_parse_refine_answer, set_intersection_parse_refine_answer

CURRENT_PATH = Path(__file__).parents[0]


@registry.register_worker()
class TaskGenerater(BaseLLMBackend, BaseWorker):
    """
    A task generator class that handles task generation, aggregation and refinement using LLM.
    """
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

    def next_process(self, process: str, *args, **kwargs):
        """
        Determines the next process in the workflow sequence.
        
        Args:
            process: Current process name
            
        Returns:
            str: Next process name according to the process map
        """
        process_map = {
            'conduct': "aggregate",
            'aggregate': "refine",
            'refine': "aggregate"
        }
        return process_map[process]
    
    def infer_n_times(self,n, **kwargs):
        self.llm.n = n
        responses = self.simple_infer(**kwargs)
        responses = [r['message']['content'] for r in responses['choices']]
        self.llm.n = 1
        assert len(responses) == n, "The number of responses {} is not equal to the number of branches response {}".format(len(responses), n)
        return responses

    def _run(self, *args, **kwargs):
        """
        Main execution method for task generation.
        Handles the task generation, aggregation and refinement processes using LLM.
        
        Returns:
            dict: Contains the updated task tree structure
        """
        # if not split, we will not generate task and response directly. So check if response is None. If not, we will skip the got process and move to the final refine phrase.
        try:
            response = self.stm(self.workflow_instance_id)['response']
            process = "refine"
            task_tree = self.stm(self.workflow_instance_id)['task_tree']
            self.stm(self.workflow_instance_id)['process'] = "refine"
            return {'got_structure': self.stm(self.workflow_instance_id)['task_tree'].model_dump()}
        except:
            query = self.stm(self.workflow_instance_id)['query']
            task_tree = self.stm(self.workflow_instance_id)['task_tree']

        
        try:
            process = self.stm(self.workflow_instance_id)['process']
            process = self.next_process(process)
        except:
            process = "conduct"

        # Get current executable nodes at the current phrase
        current_nodes = []
        for id in task_tree.leaves:
            node = task_tree.get_node(id)
            can_be_executed = task_tree.is_node_can_be_executed(id)
            if node.phrase == self.stm(self.workflow_instance_id)['phrase'] and can_be_executed:
                current_nodes.append(node)
        
        special_task = self.stm(self.workflow_instance_id)['special_task']
        if special_task is not None:
            # Define prompts based on special task and process
            sys_prompt = "sys_prompt.prompt"
            user_prompt = "{}_{}_user_prompt.prompt".format(special_task, process)
            self.prompts = [
                PromptTemplate.from_file(
                    CURRENT_PATH.joinpath("{}".format(sys_prompt)), role="system"
                ),
                PromptTemplate.from_file(
                    CURRENT_PATH.joinpath("{}".format(user_prompt)), role="user"
                ),
            ]
        else:
            sys_prompt = "{}_sys_prompt.prompt".format(process)
            user_prompt = "{}_user_prompt.prompt".format(process)
            self.prompts = [
                PromptTemplate.from_file(
                    CURRENT_PATH.joinpath("{}".format(sys_prompt)), role="system"
                ),
                PromptTemplate.from_file(
                    CURRENT_PATH.joinpath("{}".format(user_prompt)), role="user"
                ),
            ]





        
        if process == 'conduct':
            # Handle the conduct process 
            self.callback.info(agent_id=self.workflow_instance_id, progress='Num Branches Response', message=self.num_branches_response)
            for node in current_nodes:

                if special_task == "set_intersection":
                    inputs = json_repair.loads(query)
                    set1, set2 = inputs['set1'], inputs['set2']
                    input = """Input Set 1: {}
Input Set 2: {}""".format(set1, str(node.current_task_input))
                else:
                    input = str(node.current_task_input)
                
                responses = self.infer_n_times(n = self.num_branches_response, input=input)
                self.callback.info(agent_id=self.workflow_instance_id, progress='Generater conduct result', message=responses)
                
                dist_res = list(set(responses)) # remove duplicate responses
                for r in dist_res:
                    current_res = json_repair.loads(r)
                    new_node = node.copy_as_dict(pre_task_input = node.current_task_input, current_task_input=current_res, phrase=self.stm(self.workflow_instance_id)['phrase'] + 1)
                    task_tree.add_node(new_node, [node.id])
                    self.callback.info(agent_id=self.workflow_instance_id, progress='Add conducted new node', message=current_res)
                node.executed = True

        elif process == 'aggregate':
            # Handle the aggregate process - combine results from multiple nodes
            self.callback.info(agent_id=self.workflow_instance_id, progress='Num Branches Response for Aggregater', message=self.num_branches_response_for_aggregater)
            
            # Process nodes in pairs
            for i in range(0, len(current_nodes), 2):
                if i + 1 >= len(current_nodes):
                    # Handle odd number of nodes
                    node1 = current_nodes[i]
                    new_node = node1.copy_as_dict(phrase=self.stm(self.workflow_instance_id)['phrase'] + 1)
                    task_tree.add_node(new_node, [node.id for node in [node1]])
                    self.callback.info(agent_id=self.workflow_instance_id, progress='Add aggregated same node', message="")
                    node1.executed = True
                else:
                    # Aggregate pair of nodes
                    node1 = current_nodes[i]
                    node2 = current_nodes[i+1]


                    if special_task == "sort":
                        chat_complete_res = self.infer_n_times(n = self.num_branches_response_for_aggregater, length1=str(len(json_repair.loads(str(node1.current_task_input)))), length2=str(len(json_repair.loads(str(node2.current_task_input)))), total_length=str(len(json_repair.loads(str(node1.current_task_input)) + json_repair.loads(str(node2.current_task_input)))), input1=str(node1.current_task_input), input2=str(node2.current_task_input))
                    else:
                        chat_complete_res = self.infer_n_times(n = self.num_branches_response_for_aggregater, input1=str(node1.current_task_input), input2=str(node2.current_task_input))

                    self.callback.info(agent_id=self.workflow_instance_id, progress='Aggregrate conduct result', message=chat_complete_res)
                    dist_res = list(set(chat_complete_res))
                    for r in dist_res:
                        current_res = json_repair.loads(r)
                        new_node = node1.copy_as_dict(original_task_input=node1.original_task_input + node2.original_task_input, pre_task_input = {"task1":node1.current_task_input, "task2": node2.current_task_input}, current_task_input=current_res, phrase=self.stm(self.workflow_instance_id)['phrase'] + 1)
                        task_tree.add_node(new_node, [node.id for node in [node1, node2]])
                        self.callback.info(agent_id=self.workflow_instance_id, progress='Add aggregated new node', message=current_res)
                    
                    for node in [node1, node2]:
                        node.executed = True

        elif process == 'refine':
            # Handle the refine process - improve existing results
            self.callback.info(agent_id=self.workflow_instance_id, progress='Num Branches Response for Refiner', message=self.num_branches_response_for_refiner)

            # Select appropriate parsing method based on special task
            if special_task in ["sort", "set_intersection", "keyword_count"]:
                self.parse_method = "{}_parse_refine_answer".format(special_task)
            else:
                self.parse_method = ""

            # Get the corresponding parsing function
            self.parsing_function = None
            if self.parse_method == "sort_parse_refine_answer":
                self.parsing_function = sort_parse_refine_answer
            elif self.parse_method == "keyword_count_parse_refine_answer":
                self.parsing_function = keyword_count_parse_refine_answer
            elif self.parse_method == "set_intersection_parse_refine_answer":
                self.parsing_function = set_intersection_parse_refine_answer
            else:
                self.callback.info(agent_id=self.workflow_instance_id, progress='Refine', message="No parsing function found, we will not parse the result".format(special_task))
            
            # Process each node for refinement
            for node in current_nodes:
                if special_task == "keyword_count":
                    if "task1" in node.pre_task_input and "task2" in node.pre_task_input:
                        combined_input = """Dictionary 1:
{input1}
Dictionary 2:
{input2}
""".format(input1=str(node.pre_task_input["task1"]), input2=str(node.pre_task_input["task2"]))
                        chat_complete_res = self.infer_n_times(n = self.num_branches_response_for_refiner, input=combined_input, incorrectly_input=json_repair.loads(str(node.current_task_input)))
                    else:
                        chat_complete_res =  [str(node.current_task_input)]
                elif special_task == "set_intersection":
                    # Dummy process for set_intersection
                    chat_complete_res = [str(node.current_task_input)]
                elif special_task == "sort":
                    chat_complete_res = self.infer_n_times(n = self.num_branches_response_for_refiner, input=str(json_repair.loads(str(node.original_task_input))), incorrectly_input=json_repair.loads(str(node.current_task_input)))
                else:
                    chat_complete_res = self.infer_n_times(n = self.num_branches_response_for_refiner, query=query, current_task_input=json_repair.loads(str(node.current_task_input)))
                   
                
                self.callback.info(agent_id=self.workflow_instance_id, progress='Generater conduct result', message=chat_complete_res)
                dist_res = list(set(chat_complete_res))
                for r in dist_res:
                    if self.parsing_function is not None:
                        current_res = self.parsing_function(r)
                    else:
                        current_res = r
                        
                    new_node = node.copy_as_dict(pre_task_input = node.current_task_input, current_task_input=current_res, phrase=self.stm(self.workflow_instance_id)['phrase'] + 1)
                    task_tree.add_node(new_node, [node.id])
                    self.callback.info(agent_id=self.workflow_instance_id, progress='Add refined new node', message=current_res)
                node.executed = True


        else:
            raise ValueError("Invalid process task: {}".format(self.process))
        
        # Update workflow state
        self.stm(self.workflow_instance_id)['phrase'] = self.stm(self.workflow_instance_id)['phrase'] + 1
        self.stm(self.workflow_instance_id)['task_tree'] = task_tree
        self.stm(self.workflow_instance_id)['process'] = process
        return {'got_structure': task_tree.model_dump()}

