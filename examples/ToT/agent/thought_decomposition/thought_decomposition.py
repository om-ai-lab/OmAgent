from pathlib import Path
from typing import List
import json

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

gt_data = json.load(open(CURRENT_PATH.parents[1] / "data" / "mini0505.json", "r"))

@registry.register_worker()
class ThoughtDecomposition(BaseWorker):
    
    tot_parameters: dict = Field(
        default={
            "task": "crosswords",
            "method_generate": "sample",
            "method_evaluate": "vote",
            "method_select": "greedy",
            "max_depth": 10,
            "max_step": 10,
            "n_generate_sample": 3,
            "n_evaluate_sample": 2,
            "n_select_sample": 1
        }
    )
    
    def _run(self, *args, **kwargs):
        self.stm(self.workflow_instance_id)['tot_parameters'] = self.tot_parameters
        print(self.tot_parameters)

        gt_0 = gt_data[0]
        # print(gt_0)
        clues = gt_0[0]
        letters = gt_0[1]
        
        gt_board = [["_" for _ in range(5)] for _ in range(5)]

        for i in range(5):
            for j in range(5):
                gt_board[i][j] = letters[i*5+j]
        
        # print(gt_board)

        clues_dict = {
            "h1": clues[0],
            "h2": clues[1],
            "h3": clues[2],
            "h4": clues[3],
            "h5": clues[4],
            "v1": clues[5],
            "v2": clues[6],
            "v3": clues[7],
            "v4": clues[8],
            "v5": clues[9]
        }

        gt_env = {
            "board": gt_board,
            "clues": clues_dict,
        }

        print(gt_env)
         
        
        crosswords_env = {
            "board": [
                ["_", "_", "_", "_", "_"],
                ["_", "_", "_", "_", "_"],
                ["_", "_", "_", "_", "_"],
                ["_", "_", "_", "_", "_"],
                ["_", "_", "_", "_", "_"]
            ],
            "clues": {
                "h1": "An agendum; something to be done", 
                "h2": "An engine",
                "h3": "Pretentious; flowery",
                "h4": "A salon; a hall",
                "h5": "To mock; to sneer",
                "v1": "To heap",
                "v2": "An Indian antelope",
                "v3": "To intend; to plan; to devise; a nettle; to guess",
                "v4": "A nozzle",
                "v5": "Desiccator; more dry"
                },
            "filled": [],
            "unfilled": ["h1","h2", "h3", "h4", "h5", "v1", "v2", "v3", "v4", "v5"],
            "changed": []
        }
        self.stm(self.workflow_instance_id)['crosswords_env'] = crosswords_env
        data_input = ""
        self.stm(self.workflow_instance_id)['data_input'] = data_input
        self.stm(self.workflow_instance_id)['current_depth'] = 0
        self.stm(self.workflow_instance_id)['best_path'] = []
        # self.stm(self.workflow_instance_id)['search_path'] = []
        self.stm(self.workflow_instance_id)['current_node_id'] = None
        self.stm(self.workflow_instance_id)['gt_env'] = gt_env
        self.stm(self.workflow_instance_id)['p'] = {'r_letter': 0.0, 'r_word': 0.0, 'r_game': False}
        self.stm(self.workflow_instance_id)['step'] = 0
        self.stm(self.workflow_instance_id)['explored'] = []
if __name__ == "__main__":
    data_input = {
    "board": [
        ["_", "_", "_", "_", "_"],
        ["_", "_", "_", "_", "_"],
        ["_", "_", "_", "_", "_"],
        ["_", "_", "_", "_", "_"],
        ["_", "_", "_", "_", "_"]
    ],
    "clues": {
        "h1": "An agendum; something to be done", 
        "h2": "An engine",
        "h3": "Pretentious; flowery",
        "h4": "A salon; a hall",
        "h5": "To mock; to sneer",
        "v1": "To heap",
        "v2": "An Indian antelope",
        "v3": "To intend; to plan; to devise; a nettle; to guess",
        "v4": "A nozzle",
        "v5": "Desiccator; more dry"
        },
    "filled": ["h1"],
    "unfilled": ["h2", "h3", "h4", "h5", "v1", "v2", "v3", "v4", "v5"],
    "changed": []
    
    }
    print(data_input)
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
        print(input_data)  
    
    get_input_data(data_input)
    
    def set_word(text, board):
        split_text = text.split('. ')
        key = split_text[0]
        word = split_text[1]
        if key.startswith('h'):
            row_index = int(key[1:]) - 1
            board[row_index] = list(word)
        else:
            col_index = int(key[1:]) - 1
            for row, w in zip(board, word):
                row[col_index] = w
    
    text = "h5. DRIER"
    
    set_word(text, data_input['board'])
    print(data_input['board'])
