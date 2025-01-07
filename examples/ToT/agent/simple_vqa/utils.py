from .prompts import *


def get_current_numbers(y: str) -> str:
    last_line = y.strip().split('\n')[-1]
    return last_line.split('left: ')[-1].split(')')[0]

def propose_prompt_wrap(x: str, y: str='') -> str:
    current_numbers = get_current_numbers(y if y else x)
    if current_numbers == '24':
        prompt = cot_prompt.format(input=x) + 'Steps:\n' + y
    else:
        prompt = propose_prompt.format(input=current_numbers)
        # print(456, prompt)
    return prompt

def value_prompt_wrap(x: str, y: str) -> str:
    last_line = y.strip().split('\n')[-1]
    if 'left: ' not in last_line:  # last step
        ans = last_line.lower().replace('answer: ', '')
        # print([value_last_step_prompt.format(input=x, answer=ans)])
        return value_last_step_prompt.format(input=x, answer=ans)
    current_numbers = get_current_numbers(y)
    return value_prompt.format(input=current_numbers)

def value_outputs_unwrap(x: str, y: str, value_outputs: list) -> float:
    if len(y.strip().split('\n')) == 4 and 'answer' not in y.lower():
        return 0
    value_names = [_.split('\n')[-1].lower() for _ in value_outputs]
    value_map = {'impossible': 0.001, 'likely': 1, 'sure': 20}  # TODO: ad hoc
    value = sum(value * value_names.count(name) for name, value in value_map.items())
    return value