import os
import json
from pathlib import Path
from socketserver import DatagramRequestHandler
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
    logging.init_logger("omagent", "omagent", level="WARNING")

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

def get_missing_questions(original_file, result_file):
    """找出缺失的问题"""
    # 读取原始问题列表
    original_questions = {}
    with open(original_file, 'r') as f:
        for line in f:
            data = json.loads(line)
            original_questions[data['question']] = data['id']
    
    # 读取已有结果
    existing_questions = set()
    if os.path.exists(result_file):
        with open(result_file, 'r') as f:
            result_data = json.load(f)
            for item in result_data.get('model_result', []):
                # 处理可能存在的 "Answer Choices" 后缀
                question = item['question']
                existing_questions.add(question)
    
    # 找出缺失的问题
    missing_questions = []
    for question, qid in original_questions.items():
        if question not in existing_questions:
            missing_questions.append({
                'id': qid,
                'question': question
            })
    
    return missing_questions, original_questions

def read_input_file(missing_questions):
    """只处理缺失的问题"""
    return [{'user_question': q['question']} for q in missing_questions]

def merge_and_sort_results(original_file, result_file, new_results, model_id):
    """合并新旧结果并按原始顺序排序"""
    # 读取原始顺序
    original_order = {}
    with open(original_file, 'r') as f:
        for line in f:
            data = json.loads(line)
            original_order[data['question']] = data['id']
    
    # 读取现有结果
    if os.path.exists(result_file):
        with open(result_file, 'r') as f:
            final_results = json.load(f)
    else:
        final_results = {
            "dataset": "aqua",
            "model_id": model_id,
            "alg": "SC-COT",
            "model_result": []
        }
    
    # 添加新结果
    for result in new_results:
        if result:
            question = result.get("question", "")
            result_entry = {
                "id": str(original_order.get(question, "0")),
                "question": question,
                "body": result.get("body"),
                "last_output": result.get("final_answer"),
                "ground_truth": "",
                "prompt_tokens": result.get('prompt_tokens'),
                "completion_tokens": result.get('completion_tokens')
            }
            final_results["model_result"].append(result_entry)
    
    # 按原始顺序排序
    final_results["model_result"].sort(key=lambda x: int(x["id"]))
    
    return final_results

def main():
    workflow, CURRENT_PATH = initialize_workflow()
    client = start_programmatic_client(workflow, CURRENT_PATH)
    model_id = "internlm2.5_7b-chat"
    
    # 文件路径
    original_file = '/ceph3/wz/proj/OmAgent/examples/general_self_consist_cot/aqua_test_formatted.jsonl'
    result_file = CURRENT_PATH.joinpath(f'aqua_test_{model_id}.json')
    
    # 找出缺失的问题
    missing_questions, original_questions = get_missing_questions(original_file, result_file)
    
    if missing_questions:
        print(f"Found {len(missing_questions)} missing questions to process")
        # 只处理缺失的问题
        workflow_input_list = read_input_file(missing_questions)
        results = client.start_batch_processor(workflow_input_list=workflow_input_list, max_tasks=10)
        
        # 合并结果并排序
        final_results = merge_and_sort_results(original_file, result_file, results, model_id)
        
        # 保存最终结果
        with open(result_file, 'w') as outfile:
            json.dump(final_results, outfile, indent=4)
    else:
        print("No missing questions found")
    
    client.stop_processor()

if __name__ == "__main__":
    main()
