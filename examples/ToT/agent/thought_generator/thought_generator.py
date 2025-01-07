from pathlib import Path
import re
from typing import List

from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.utils.registry import registry
from omagent_core.models.llms.schemas import Message, Content
from omagent_core.utils.general import encode_image
from omagent_core.models.llms.prompt.parser import StrParser
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.container import container
from omagent_core.models.llms.prompt.prompt import PromptTemplate
from pydantic import Field
from typing import List
from omagent_core.advanced_components.workflow.ToT.schemas.ToT_structure import ThoughtTree
# from .prompts import *
# from .utils import *

CURRENT_PATH = Path(__file__).parents[0]

def thought_tree_init(data_input: str):
    thought_tree = ThoughtTree()
    thought_tree.add_node(content=data_input, parent_id=None)
    return thought_tree

def get_board(board):
    board_str = ""
    for row in board:
        board_str += "".join(row) + "\n"
    return board_str

def get_word(key, board):
    if key.startswith('h'):
        row_index = int(key[1:]) - 1
        return "".join(board[row_index])
    else:
        col_index = int(key[1:]) - 1
        return "".join([row[col_index] for row in board])
    
def get_input_data(data_input):
    input_data = ""
    current_board = get_board(data_input['board'])
    unfilled = ""
    filled = ""
    changed = ""
    for key in data_input['unfilled']:
        unfilled += f"{key}. {data_input['clues'][key]}: _____\n"
    for key in data_input['filled']:
        filled += f"{key}. {data_input['clues'][key]}: {get_word(key, data_input['board'])}\n"
    for key in data_input['changed']:
        changed += f"{key}. {data_input['clues'][key]}: {get_word(key, data_input['board'])}\n"
    
    input_data = f"""Current Board:\n{current_board}\nUnfilled:\n{unfilled}\nFilled:\n{filled}\nChanged:\n{changed}\n"""
    return input_data

def get_answers(text):
    # 解析每个块
    confidence_to_value = {'certain': 1, 'high': 0.5, 'medium': 0.2, 'low': 0.1}
    lines = text.split('\n')
    # print(lines)
    head_pattern = r'([hv][1-5])\. '
    answer_pattern = r' ([a-zA-Z]{5,5}) \((certain|high|medium|low)\)'
    answers = []
    for line in lines:
        line = re.sub(r'[*\-\"]', '', line)
        # print(line)
        if re.search(head_pattern, line):
            head = re.search(head_pattern, line).group(0)
            # print(head)
        if re.search(answer_pattern, line):
            # print(line)
            search = re.findall(answer_pattern, line)
            for s in search:
                answers.append((head + s[0], confidence_to_value[s[1]]))
            # break

    return answers

def set_word(text, data_input):
    if text == "":
        return data_input
    split_text = text.split('. ')
    
    key = split_text[0]
    word = split_text[1]
    if key in data_input['unfilled']:
        data_input['unfilled'].remove(key)
        data_input['filled'].append(key)
    elif key in data_input['filled']:
        data_input['filled'].remove(key)
        data_input['changed'].append(key)
    
    changed_key = set()
    if key.startswith('h'):
        row_index = int(key[1:]) - 1
        for i, w in enumerate(word):
            if data_input['board'][row_index][i] != '_':
                changed_key.add(f'v{i+1}')
            data_input['board'][row_index][i] = w
                
    else:
        col_index = int(key[1:]) - 1
        for i, w in enumerate(word):
            if data_input['board'][i][col_index] != '_':
                changed_key.add(f'h{i+1}')
            data_input['board'][i][col_index] = w
    
    for key in changed_key:
        if key in data_input['filled']:
            data_input['filled'].remove(key)
            data_input['changed'].append(key)
            
    return data_input

@registry.register_worker()
class ThoughtGenerator(BaseWorker, BaseLLMBackend):
# class ThoughtGenerator(BaseWorker):
    
    llm: OpenaiGPTLLM
    
    prompts: List[PromptTemplate] = Field(
        default=[
            # PromptTemplate.from_file(
            #     CURRENT_PATH.joinpath("sys_prompt.prompt"), role="system"
            # ),
            # PromptTemplate.from_file(
            #     CURRENT_PATH.joinpath("user_prompt.prompt"), role="user"
            # ),
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("crossword.prompt"), role="user"
            ),
            
        ]
    )

    
    # def _run(self, fun_path: str = None, *args, **kwargs):
    def _run(self, *args, **kwargs):
        
        # if fun_path:
        #     exec(f"from {fun_path} import *")
            
        data_input = self.stm(self.workflow_instance_id)['data_input']
        crosswords_env = self.stm(self.workflow_instance_id)['crosswords_env']
        if self.stm(self.workflow_instance_id).get('thought_tree', None) is None:
            thought_tree = thought_tree_init(data_input)
            self.stm(self.workflow_instance_id)['thought_tree'] = thought_tree
            self.stm(self.workflow_instance_id)['current_depth'] = 0
            self.stm(self.workflow_instance_id)['best_path'] = []
            self.stm(self.workflow_instance_id)['current_node_id'] = 0
        else:
            thought_tree = self.stm(self.workflow_instance_id)['thought_tree']

        current_depth = self.stm(self.workflow_instance_id)['current_depth']
        
        current_nodes = thought_tree.get_nodes_at_depth(current_depth)
        
        n_generate_sample = self.stm(self.workflow_instance_id)['tot_parameters'].get('n_generate_sample', None)
        
        method_generate = self.stm(self.workflow_instance_id)['tot_parameters'].get('method_generate', None)
        
        task = self.stm(self.workflow_instance_id)['tot_parameters'].get('task', None)
        if task == "crosswords":
            current_node_id = self.stm(self.workflow_instance_id)['current_node_id']
            # search_path = self.stm(self.workflow_instance_id)['search_path']
            step = self.stm(self.workflow_instance_id)['step']
            # current_path = thought_tree.get_current_path(current_node_id, return_ids=True)
            explored = self.stm(self.workflow_instance_id)['explored']
            # search_path.append(current_node_id)
            # best_path = self.stm(self.workflow_instance_id)['best_path']
            # best_path.append(current_node_id)
            while current_node_id in explored and thought_tree.nodes[current_node_id].children == []:
                parent_id = thought_tree.get_parent(current_node_id, return_ids=True)
                thought_tree.prune(current_node_id)
                current_node_id = parent_id
                current_depth -= 1
            print('-wrong--'*10)
            print(current_node_id)
            print(thought_tree.nodes[current_node_id].children)
            print(thought_tree.nodes)
            print('-wrong--'*10)
            if thought_tree.nodes[current_node_id].children != []:
                best_node_id = thought_tree.get_highest_bfs_score_node_in_childerens(current_node_id, return_ids=True)
                # print(best_node_id)
                self.stm(self.workflow_instance_id)['current_node_id'] = best_node_id
                # search_path.append(best_node_id)
                # self.stm(self.workflow_instance_id)['search_path'] = search_path
                self.stm(self.workflow_instance_id)['current_depth'] = current_depth + 1
                self.stm(self.workflow_instance_id)['step'] = step + 1
                        

            else:
                current_path = thought_tree.get_current_path(current_node_id, return_ids=True)
                for node_id in current_path:
                    set_word(thought_tree.nodes[node_id].content, crosswords_env)
                input_data = get_input_data(crosswords_env)
                candidates_to_scores = {}
                for i in range(n_generate_sample):
                    response = self.simple_infer(input=input_data)["choices"][0]["message"]["content"]
                    parsed_response = get_answers(response)

                    if parsed_response:
                        for candidate, score in parsed_response:
                            candidates_to_scores[candidate] = candidates_to_scores.get(candidate, 0) + score

                for key, value in candidates_to_scores.items():
                    # new_content = set_word(key, node.content.copy())
                    thought_tree.add_node(content=key, parent_id=current_node_id, bfs_value=value)
                
                best_node_id = thought_tree.get_highest_bfs_score_node_in_childerens(current_node_id, return_ids=True)
                # print(best_node_id)
                self.stm(self.workflow_instance_id)['current_node_id'] = best_node_id
                # search_path.append(best_node_id)
                # self.stm(self.workflow_instance_id)['search_path'] = search_path
                self.stm(self.workflow_instance_id)['current_depth'] = current_depth + 1
                self.stm(self.workflow_instance_id)['step'] = step + 1
                self.stm(self.workflow_instance_id)['explored'].append(current_node_id)
            
            
            # print('-'*100)
            # print(self.stm(self.workflow_instance_id)['search_path'])
            print('-'*100)
            print(self.stm(self.workflow_instance_id)['current_depth'])
            print('-'*100)
            print(self.stm(self.workflow_instance_id)['current_node_id'])
            print('-'*100)
            # print(self.stm(self.workflow_instance_id)['best_path'])
            # print('-'*100)
            # print(thought_tree.thought_tree_to_dict())
            # print(thought_tree.thought_tree_to_dict())
        
        else:
            if method_generate == "sample":
                for node in current_nodes:
                    for i in range(n_generate_sample):
                        response = self.simple_infer(input=node.content)["choices"][0]["message"]["content"]
                        thought_tree.add_node(content=response, parent_id=node.id)
                # print(response)
                
            elif method_generate == "propose":
                for node in current_nodes:
                    response = self.simple_infer(input=node.content)["choices"][0]["message"]["content"]
                    next_content = response.split('\n')
                    for next_content in next_content:
                        thought_tree.add_node(content=next_content, parent_id=node.id)
        
        self.stm(self.workflow_instance_id)['thought_tree'] = thought_tree
        self.stm(self.workflow_instance_id)['current_depth'] = current_depth + 1
        
        print(thought_tree.thought_tree_to_dict())
        # data_input = '7 8 3 1'
        # steps = "7 - 3 = 4 (left: 4 1 8) \n(4 - 1 = 3) (left: 8, 3) \n8 * 3 = 24 (left: 24)"
        # print('-'*100)
        # print(self.prompts[0].format(input=data_input,steps=steps))
        # print('-'*100)
        # print(self.simple_infer(input=self.prompts[0].format(input=data_input,steps=steps))["choices"][0]["message"]["content"])

            # full_trajectories = [pt + next_state + '\n' for next_state in next_states]
            # all_trajectories.extend(full_trajectories)
        # print(thought_tree)
        
        # previous_trajectories = self.stm(self.workflow_instance_id)['previous_trajectories']
        # task = self.stm(self.workflow_instance_id)['task']
        
        
        # thought_tree = ThoughtTree()
        # thought_tree.add_node(content="2 8 8 14", parent_id=None)
        # self.stm(self.workflow_instance_id)['thought_tree'] = thought_tree
        # self.stm(self.workflow_instance_id)['depth'] = 0
        # depth = self.stm(self.workflow_instance_id)['depth']
        # # depth = 0
        # thought_tree2 = self.stm(self.workflow_instance_id)['thought_tree']
        # print(thought_tree2)
        # nodes_at_depth = thought_tree2.get_nodes_at_depth(depth)
        # for node in nodes_at_depth:
        #     print(node.content)
        
        
        
        
        # return "Hello World"




# @registry.register_worker()
# class NextStatePrediction(BaseWorker, BaseLLMBackend):

#     llm: OpenaiGPTLLM

#     def _run(self, *args, **kwargs):
#         assert self.stm(self.workflow_instance_id).get('data_input', None) is not None and self.stm(self.workflow_instance_id).get('previous_trajectories', None) is not None
        
#         data_input = self.stm(self.workflow_instance_id)['data_input']
#         previous_trajectories = self.stm(self.workflow_instance_id)['previous_trajectories']
#         task = self.stm(self.workflow_instance_id)['task']

#         all_trajectories = []
#         # Set prompts for next state prediction 
#         self.prompts = self.set_prompts([CURRENT_PATH.joinpath(f'prompts/{task}/propose_prompt.prompt')])
#         for pt in previous_trajectories:
            
#             input_next_state_prediction = propose_prompt_wrap(x=data_input, y=pt)
#             next_states_response = self.simple_infer(input=input_next_state_prediction)["choices"][0]["message"]["content"]

#             next_states = next_states_response.split('\n')

#             full_trajectories = [pt + next_state + '\n' for next_state in next_states]
#             all_trajectories.extend(full_trajectories)
        
#         self.stm(self.workflow_instance_id)['all_trajectories'] = all_trajectories
        
#         info_str = "\n"
#         info_str += '\n'.join(all_trajectories)
#         # For debug
#         self.callback.send_answer(self.workflow_instance_id, msg=info_str)

#         return next_states_response
    
if __name__ == "__main__":
    
    prompt = PromptTemplate.from_file(
                CURRENT_PATH.joinpath("user_prompt.prompt"), role="user"
            )
    print(prompt)
    print(prompt.input_variables)
    format_list = prompt.input_variables
    # infer_prompt = 
    print(type(prompt))
    print(prompt.format(input="2 8 8 14"))
    
    # thought_tree = ThoughtTree()
    # thought_tree.add_node(content="2 8 8 14", parent_id=None)
    # thought_tree.add_node(content="2 + 8 = 10 (left: 8 10 14)", parent_id=0)
    # thought_tree.add_node(content="8 / 2 = 4 (left: 4 8 14)", parent_id=0)
    # thought_tree.add_node(content="14 + 2 = 16 (left: 8 8 16)", parent_id=0)
    # thought_tree.add_node(content="2 * 8 = 16 (left: 8 14 16)", parent_id=0)
    # thought_tree.add_node(content="8 - 2 = 6 (left: 6 8 14)", parent_id=0)
    # thought_tree.add_node(content="14 - 8 = 6 (left: 2 6 8)", parent_id=0)
    # thought_tree.add_node(content="14 / 2 = 7 (left: 7 8 8)", parent_id=0)
    # thought_tree.add_node(content="14 - 2 = 12 (left: 8 8 12)", parent_id=0)
    
    # print(thought_tree.get_nodes_at_depth(0))
    
    # # import os
    # # os.environ["OPENAI_API_KEY"] = "sk-iytCHBhtNvAhtxeBC8E5A71e473c45C1B9847b6bB2F6461b"
    # # os.environ["OPENAI_API_BASE"] = "http://192.168.0.114:6006/v1"
    
    # # llm = OpenaiGPTLLM()
    
    # thought_generator = ThoughtGenerator()
    # thought_generator.workflow_instance_id = 1
    
    # thought_generator.stm(workflow_instance_id=1)['thought_tree'] = thought_tree
    # thought_generator._run()
