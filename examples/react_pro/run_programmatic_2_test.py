import os
import math

# 设置代理环境变量
os.environ['HTTP_PROXY'] = 'http://10.8.21.200:47890'
os.environ['HTTPS_PROXY'] = 'http://10.8.21.200:47890'

from omagent_core.utils.container import container
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from pathlib import Path
from omagent_core.utils.registry import registry
from omagent_core.clients.devices.programmatic.client import ProgrammaticClient
from omagent_core.utils.logger import logging
from omagent_core.advanced_components.workflow.react_pro.workflow import ReactProWorkflow
import json

def read_input_texts(file_path):
    """从 jsonl 文件读取问题"""
    input_texts = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():  # 跳过空行
                data = json.loads(line)
                input_texts.append((data['question'], str(data['id'])))
    return input_texts

def split_input_data(input_texts, num_splits):
    """将输入数据切分成n份"""
    total_items = len(input_texts)
    items_per_split = math.ceil(total_items / num_splits)
    
    splits = []
    for i in range(num_splits):
        start_idx = i * items_per_split
        end_idx = min((i + 1) * items_per_split, total_items)
        splits.append(input_texts[start_idx:end_idx])
    
    return splits

def process_results(results, dataset_name="aqua"):
    """将结果转换为标准格式"""
    formatted_output = {
        "dataset": dataset_name,
        "model_id": "gpt-3.5-turbo",
        "alg": "ReAct",
        "model_result": []
    }
    
    for result in results:
        output_data = result.get('output', {})
        
        model_result = {
            "id": output_data.get('id'),
            "question": output_data.get('query'),
            "body": output_data.get('body', {}),
            "last_output": output_data.get('output', ''),
            "ground_truth": "",
            "step_number": output_data.get('step_number', 0),
            "prompt_tokens": output_data.get('token_usage', {}).get('prompt_tokens', 0),
            "completion_tokens": output_data.get('token_usage', {}).get('completion_tokens', 0)
        }
        
        formatted_output["model_result"].append(model_result)
    
    return formatted_output

logging.init_logger("omagent", "omagent", level="INFO")

# 设置当前工作目录路径
CURRENT_PATH = Path(__file__).parents[0]

# 导入注册的模块
registry.import_module(CURRENT_PATH.joinpath('agent'))

# 加载 container 配置从 YAML 文件
container.register_stm("RedisSTM")
container.from_config(CURRENT_PATH.joinpath('container.yaml'))

# 初始化工作流
workflow = ConductorWorkflow(name='react_pro_example')

# 配置 React 工作流
react_workflow = ReactProWorkflow()
react_workflow.set_input(
    query=workflow.input('query'),
    id=workflow.input('id')
)

# 配置工作流执行流程
workflow >> react_workflow 

# 注册工作流
workflow.register(overwrite=True)

# 设置参数
input_file = "/home/li_jingcheng/项目/OmAgent/data/hotpot_dev_select_500_data_test_0107.jsonl"
num_splits = 5  # 设置要切分的份数

# 读取并切分输入数据
input_texts = read_input_texts(input_file)
data_splits = split_input_data(input_texts, num_splits)

# 初始化 programmatic client
config_path = CURRENT_PATH.joinpath('configs')
# programmatic_client = ProgrammaticClient(
#     processor=workflow,
#     config_path=config_path,
#     workers=[]  # React workflow 不需要额外的 workers
# )

# 按顺序处理每一份数据
for i, split_data in enumerate(data_splits, 1):
    print(f"\nProcessing split {i}/{num_splits}...")
    if i in [1,2,3,4]:
        continue

    programmatic_client = ProgrammaticClient(
    processor=workflow,
    config_path=config_path,
    workers=[]  # React workflow 不需要额外的 workers
)
    
    # 准备输入数据
    workflow_input_list = [
        {"query": text[0], "id": text[1]} for text in split_data
    ]

    workflow_input_list = [
  {
    "query": "毛泽东的出生日期",
    "id": "5a7cfb2755429907fabef084"
  }
]
    
    print(f"Processing {len(workflow_input_list)} queries in this split...")
    
    # 处理数据
    res = programmatic_client.start_batch_processor(
        workflow_input_list=workflow_input_list
    )
    
    # 处理结果
    formatted_results = process_results(res, dataset_name="aqua")
    
    # 保存结果到文件
    #output_file = f"/home/li_jingcheng/项目/OmAgent/data/hotpot_dev_select_500_data_test_0109_gpt4omini_part{i}.json"
    output_file = f"/home/li_jingcheng/项目/OmAgent/data/debug.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(formatted_results, f, ensure_ascii=False, indent=2)
    
    print(f"Results for split {i} saved to {output_file}")

    programmatic_client.stop_processor()



print("\nAll splits processed successfully!")