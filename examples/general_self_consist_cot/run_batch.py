import os
import json
from pathlib import Path
from dotenv import load_dotenv
from omagent_core.utils.container import container
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.utils.registry import registry
from omagent_core.clients.devices.programmatic.client import ProgrammaticClient
from omagent_core.utils.logger import logging
from omagent_core.advanced_components.workflow.self_consist_cot.workflow import SelfConsistentWorkflow
import yaml

def initialize_workflow():
    load_dotenv()
    logging.init_logger("omagent", "omagent", level="INFO")

    CURRENT_PATH = Path(__file__).parents[0]
    registry.import_module(CURRENT_PATH.joinpath('agent'))
    
    container.register_stm("RedisSTM")
    container.from_config(CURRENT_PATH.joinpath('container.yaml'))
    
    # Load num_path configuration
    config_path = CURRENT_PATH.joinpath('configs')
    with open(config_path.joinpath('path_config.yaml'), 'r') as f:
        path_config = yaml.safe_load(f)
    
    workflow = ConductorWorkflow(name='general_self_consist_cot')
    self_consist_cot_workflow = SelfConsistentWorkflow()
    self_consist_cot_workflow.set_input(user_question=workflow.input('user_question'), num_path=path_config['num_path'])
    
    workflow >> self_consist_cot_workflow
    workflow.register(overwrite=True)
    
    return workflow, CURRENT_PATH

def start_programmatic_client(workflow, CURRENT_PATH):
    config_path = CURRENT_PATH.joinpath('configs')
    return ProgrammaticClient(processor=workflow, config_path=config_path)

def read_input_file(file_path):
    workflow_input_list = []
    with open(file_path, 'r') as file:
        for line in file:
            data = json.loads(line)
            question = data["question"]
            workflow_input_list.append({'user_question': question})
    return workflow_input_list

def save_results(results, output_path):
    formatted_results = {
        "dataset": "aqua",
        "model_id": "Doubao-lite-32k",
        "alg": "SC-COT",
        "model_result": []
    }
    
    for i, result in enumerate(results, 1):


        result_entry = {
            "id": str(i),  # Format ID as 5-digit string with leading zeros
            "question": result["question"],
            "body":result["body"],
            "last_output": result["final_answer"],
            "ground_truth": ""  ,# You may need to adjust this if you have ground truth data,
            "prompt_tokens": result['prompt_tokens'],
            "completion_tokens": result['completion_tokens']
        }
        formatted_results["model_result"].append(result_entry)
    
    with open(output_path, 'w') as outfile:  # Changed from 'a' to 'w' to write complete JSON
        json.dump(formatted_results, outfile, indent=4)

def main():
    workflow, CURRENT_PATH = initialize_workflow()
    client = start_programmatic_client(workflow, CURRENT_PATH)
    
    workflow_input_list = read_input_file('/ceph3/wz/proj/OmAgent/examples/general_self_consist_cot/gsm8k_test.jsonl')
    results = client.start_batch_processor(workflow_input_list=workflow_input_list, max_tasks=1)
    
    output_path = CURRENT_PATH.joinpath('gsm8k_test_doubao.json')
    save_results(results, output_path)
    client.stop_processor()

if __name__ == "__main__":
    main()
