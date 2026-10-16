import os
os.environ['custom_openai_endpoint'] = 'http://10.8.25.27:11434/v1'
os.environ['custom_openai_key'] = 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295'
os.environ['custom_model_id'] = 'qwen2.5:7b'
os.environ['batch_size'] = "1"
os.environ['timeout'] = "300"
os.environ['cot_method'] = "few_shot"
os.environ['dataset_name'] = "math500"
os.environ['dataset_path'] = "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/data/math500_test_converted.jsonl"
os.environ['output_path'] = "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/Output"
os.environ['output_name'] = "math500_results_6"
os.environ['container_yaml'] = "container_6.yaml"
os.environ['config_dir'] = "configs_t1"

import json
import time
import signal
import argparse

from pathlib import Path


from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry
from omagent_core.utils.container import container
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.advanced_components.workflow.sc_cot.workflow import SCCoTWorkflow
from omagent_core.clients.devices.programmatic.client import ProgrammaticClient



def read_jsonl(file_path):
    with open(file_path, 'r') as file:
        data = [json.loads(line.strip()) for line in file if line.strip()]
    return data


def get_missing_questions(original_file, result_file):
    """找出缺失的问题"""
    # 读取原始问题列表
    original_questions = {}
    with open(original_file, 'r') as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                original_questions[data['id']] = data
    
    # 读取已完成的问题
    completed_ids = set()
    if os.path.exists(result_file):
        with open(result_file, 'r') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    completed_ids.add(data['id'])
    
    # 找出未完成的问题
    missing_questions = [q for id, q in original_questions.items() if id not in completed_ids]
    return missing_questions, original_questions


def initialize_workflow():
    logging.init_logger("omagent", "omagent", level="INFO")
    CURRENT_PATH = Path(__file__).parents[0]
    registry.import_module(project_path=CURRENT_PATH.joinpath('agent'))
    container.register_stm("RedisSTM")
    container.from_config(CURRENT_PATH.joinpath(os.environ['container_yaml']))
    return CURRENT_PATH, None


def start_programmatic_client(workflow, CURRENT_PATH):
    config_path = CURRENT_PATH.joinpath(os.environ['config_dir'])
    return ProgrammaticClient(processor=workflow, config_path=config_path, workers=[])


def prepare_data( file_path, cot_examples, cot_method, start=1 ):
    data = read_jsonl( file_path )
    #data = data
    return [
        {
            "id": d['id'],
            "query": d[ 'question' ],
            #"query": "Convert the point $(0,3)$ in rectangular coordinates to polar coordinates.  Enter your answer in the form $(r,\\theta),$ where $r > 0$ and $0 \\le \\theta < 2 \\pi.$",
        } for idx, d in enumerate( data, start=start )
    ]


def setup_environ(model_id):
    os.environ['custom_model_id'] = model_id
    print(f"Model ID: {model_id}")


def arguments():
    class Args:
        def __init__(self):
            self.dataset_name = os.environ['dataset_name']
            self.dataset_path = os.environ['dataset_path']
            self.output_path = os.environ['output_path']
            self.output_name = os.environ['output_name']
    
    args = Args()
    print(f"Environment variables loaded as arguments: {vars(args)}")
    return args


def main():
    args = arguments()
    setup_environ(model_id=os.environ['custom_model_id'])
    # 设置文件路径
    original_file = args.dataset_path
    result_file = os.path.join(args.output_path, f"{args.output_name}.jsonl")
    
    # 直接按批次处理所有缺失的问题
    missing_questions, _ = get_missing_questions(original_file, result_file)
    if not missing_questions:
        print("No missing questions found. All questions have been processed.")
        return

    batch_size = int(os.environ['batch_size'])
    total_batches = (len(missing_questions) + batch_size - 1) // batch_size
    print(f"Total missing questions: {len(missing_questions)}")
    print(f"Processing in {total_batches} batches (batch size {batch_size}).")

    # 初始化工作流
    CURRENT_PATH, _ = initialize_workflow()
    workflow = ConductorWorkflow(name='cot_eval')
    
    # 设置工作流
    cot_workflow = SCCoTWorkflow()
    cot_workflow.set_input(
        id=workflow.input('id'),
        query=workflow.input('query')
    )
    workflow >> cot_workflow
    
    client = start_programmatic_client(workflow, CURRENT_PATH)

    # 定义超时处理函数
    def timeout_handler(signum, frame):
        raise Exception("Batch processing timed out")

    for batch_index in range(total_batches):
        batch = missing_questions[batch_index*batch_size : (batch_index+1)*batch_size]
        print(f"Processing batch {batch_index+1} of {total_batches}, batch size: {len(batch)}")

        workflow_input_list = []
        for q in batch:
            workflow_input_list.append({
                "id": q['id'],
                "query": q['question']
            })

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(os.environ['timeout']))

        try:
            batch_results = client.start_batch_processor(workflow_input_list=workflow_input_list, max_tasks=5)
            signal.alarm(0)

            if batch_results:
                # 将每个结果以一行追加写到 jsonl 文件
                with open(result_file, 'a') as outfile:
                    for result in batch_results:
                        json.dump(result, outfile)
                        outfile.write('\n')
                print(f"Saved results after batch {batch_index+1}")
            else:
                print(f"No results for batch {batch_index+1}")
        except Exception as e:
            signal.alarm(0)
            print(f"Error processing batch {batch_index+1}: {e}")

        time.sleep(15)  # 批次间暂停

    client.stop_processor()
    print("Batch processing completed.")


if __name__ == '__main__':
    main()
