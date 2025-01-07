from pathlib import Path
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
# from .prompts import *
# from .utils import *

CURRENT_PATH = Path(__file__).parents[0]

# def completion_check(workflow_instance_id: str):

def get_word(key, board):
    if key.startswith('h'):
        row_index = int(key[1:]) - 1
        return "".join(board[row_index])
    else:
        col_index = int(key[1:]) - 1
        return "".join([row[col_index] for row in board])

def compare_to_gt(data_input, gt_env, p):
    letter_score = p.get('r_letter', None)
    word_score = p.get('r_word', None)
    game_score = p.get('r_game', None)
    
    letters = 0
    words = 0
    for i in range(len(data_input['board'])):
        for j in range(len(data_input['board'][i])):
            if data_input['board'][i][j] == gt_env['board'][i][j].lower():
                letters += 1
    for key in data_input['filled']+data_input['changed']:
        if get_word(key, data_input['board']) == get_word(key, gt_env['board']).lower():
            words += 1

    if letters/25 >= letter_score:
        letter_score = letters/25
    if words/10 >= word_score:
        word_score = words/10

    if letters == len(data_input['board']) * len(data_input['board'][0]) and words == len(data_input['filled']):
        game_score = True

    return {'r_letter': letter_score, 'r_word': word_score, 'r_game': game_score}

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
class SearchAlgorithm(BaseWorker):
    
    
    
    
    def _run(self, *args, **kwargs):
        thought_tree = self.stm(self.workflow_instance_id).get('thought_tree', None)
        current_depth = self.stm(self.workflow_instance_id).get('current_depth', None)
        max_depth = self.stm(self.workflow_instance_id).get('tot_parameters', None).get('max_depth', None)
        max_step = self.stm(self.workflow_instance_id).get('tot_parameters', None).get('max_step', None)

        task = self.stm(self.workflow_instance_id)['tot_parameters'].get('task', None)
        if task == 'crosswords':
            crosswords_env = self.stm(self.workflow_instance_id).get('crosswords_env', None)
            current_node_id = self.stm(self.workflow_instance_id).get('current_node_id', None)
            dfs_value = thought_tree.nodes[current_node_id].dfs_value
            gt_env = self.stm(self.workflow_instance_id).get('gt_env', None)
            # print(gt_env)
            p = self.stm(self.workflow_instance_id).get('p', None)
            # search_path = self.stm(self.workflow_instance_id).get('search_path', None)
            step = self.stm(self.workflow_instance_id).get('step', None)
            current_path = thought_tree.get_current_path(current_node_id, return_ids=True)
            for node_id in current_path:
                node = thought_tree.nodes[node_id]
                set_word(node.content, crosswords_env)
            
            best_score = compare_to_gt(crosswords_env, gt_env, p)
            if p != best_score:
                self.stm(self.workflow_instance_id)['p'] = best_score
                self.stm(self.workflow_instance_id)['best_path'] = current_path

            print(best_score)

            if dfs_value['impossible'] > 1:
                prune_id = current_node_id
                parent_id = thought_tree.get_parent(current_node_id, return_ids=True)
                thought_tree.prune(prune_id)
                current_depth = current_depth - 1
                # search_path = search_path[:-1]
                self.stm(self.workflow_instance_id)['current_node_id'] = parent_id
                self.stm(self.workflow_instance_id)['current_depth'] = current_depth
                # self.stm(self.workflow_instance_id)['search_path'] = search_path
                self.stm(self.workflow_instance_id)['thought_tree'] = thought_tree

                print('--prune--'*10)
                print(current_path)
                print(current_node_id)
                # print(search_path)
                print('--prune--'*10)

            if step >= max_step or current_depth >= max_depth:
                print('--finish--'*10)
                print(self.stm(self.workflow_instance_id)['best_path'])
                for node_id in self.stm(self.workflow_instance_id)['best_path']:
                    node = thought_tree.nodes[node_id]
                    set_word(node.content, crosswords_env)
                message = {
                    'board': crosswords_env['board'],
                    'score': self.stm(self.workflow_instance_id)['p'],
                    'path': self.stm(self.workflow_instance_id)['best_path']
                }
                self.callback.send_answer(self.workflow_instance_id, msg=message)
                
                return {"finish": True}
            else:
                print('--continue--'*10)
                return {"finish": False}
            
            


        else:
            b = self.stm(self.workflow_instance_id).get('tot_parameters', None).get('n_select_sample', None)
            thought_tree.tot_bfs(depth=current_depth, b=b)
            print(thought_tree.nodes)
            self.stm(self.workflow_instance_id)['thought_tree'] = thought_tree
        
        
            if current_depth >= self.stm(self.workflow_instance_id).get('tot_parameters', None).get('max_depth', None):
                best_node_id = thought_tree.get_highest_score_node_at_depth(depth=current_depth, return_ids=True)
                current_path = thought_tree.get_current_path(node_id=best_node_id)
                # self.stm(self.workflow_instance_id)['optimal_path'] = optimal_path
                self.callback.send_answer(self.workflow_instance_id, msg=current_path)
                return {"finish": True}
            else:
                return {"finish": False}
            
            
        # print(self.search_parameters)
        # print(self.search_parameters.get('n_select_sample', None))
        # print(self.search_parameters.get('n_evaluate_sample', None))
        # pass

    
# @registry.register_worker()
# class StateSelection(BaseWorker, BaseLLMBackend):

#     llm: OpenaiGPTLLM

#     def _run(self, *args, **kwargs):
#         assert self.stm(self.workflow_instance_id).get('all_trajectories', None) is not None and self.stm(self.workflow_instance_id).get('values', None) is not None
#         all_trajectories = self.stm(self.workflow_instance_id)['all_trajectories']
#         values = self.stm(self.workflow_instance_id)['values']
        
#         ids = list(range(len(all_trajectories)))
#         n_select_sample = 2
#         select_ids = sorted(ids, key=lambda x: values[x], reverse=True)[:n_select_sample]
#         selected_trajectories = [all_trajectories[select_id] for select_id in select_ids]
#         sorted_values = [values[select_id] for select_id in select_ids]
        
#         info_str = "\n"
#         for t, v in zip(selected_trajectories, sorted_values):
#             info_str += t
#             info_str += f'Score: {v}'
#             info_str += '\n'
#         # For debug
#         self.callback.send_answer(self.workflow_instance_id, msg=info_str)

#         self.stm(self.workflow_instance_id)['previous_trajectories'] = selected_trajectories

#         if self.stm(self.workflow_instance_id).get('loop_index', None) is None:
#             self.stm(self.workflow_instance_id)['loop_index'] = 0
#         self.stm(self.workflow_instance_id)['loop_index'] = self.stm(self.workflow_instance_id)['loop_index'] + 1
#         # For debug
#         print(111, self.stm(self.workflow_instance_id)['loop_index'])

#         return {"loop_index": self.stm(self.workflow_instance_id)['loop_index']}