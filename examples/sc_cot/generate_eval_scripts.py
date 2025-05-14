import os
import shutil
from pathlib import Path

# 原始模板文件路径
TEMPLATE_FILE = Path(__file__).parent / "eval_demo_split_batch.py"
# 输出目录 (直接生成到当前目录)
OUTPUT_DIR = Path(__file__).parent

# 完整配置参数
SCRIPT_CONFIGS = [
    {  # 基础配置
        'script_number': 2,
        'custom_openai_endpoint': 'http://140.207.201.47:11434/v1',
        'custom_openai_key': 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295',
        'custom_model_id': 'qwen2.5:7b',
        'batch_size': "5",
        'timeout': "300",
        'cot_method': "few_shot",
        'dataset_name': "math500",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/cot/data/math500_test_converted.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/cot/Output",
        'output_name': "math500_results_1",
        'container_yaml': "container_2.yaml",
        'config_dir': "configs_t1"
    },
    {  # GPT-4配置示例
        'script_number': 3,
        'custom_openai_endpoint': 'http://140.207.201.47:11434/v1',
        'custom_openai_key': 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295',
        'custom_model_id': 'qwen2.5:7b',
        'batch_size': "5",
        'timeout': "1000",
        'cot_method': "few_shot",
        'dataset_name': "math500",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/cot/data/math500_test_converted.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/cot/Output",
        'output_name': "math500_results_3",
        'container_yaml': "container_3.yaml",
        'config_dir': "configs_t1"
    },
    {  # GPT-4配置示例
        'script_number': 4,
        'custom_openai_endpoint': 'http://140.207.201.47:11434/v1',
        'custom_openai_key': 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295',
        'custom_model_id': 'qwen2.5:7b',
        'batch_size': "5",
        'timeout': "1000",
        'cot_method': "few_shot",
        'dataset_name': "math500",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/cot/data/math500_test_converted.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/cot/Output",
        'output_name': "math500_results_4",
        'container_yaml': "container_4.yaml",
        'config_dir': "configs_t1"
    },
    {  # GPT-4配置示例
        'script_number': 5,
        'custom_openai_endpoint': 'http://140.207.201.47:11434/v1',
        'custom_openai_key': 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295',
        'custom_model_id': 'qwen2.5:7b',
        'batch_size': "5",
        'timeout': "1000",
        'cot_method': "few_shot",
        'dataset_name': "math500",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/cot/data/math500_test_converted.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/cot/Output",
        'output_name': "math500_results_5",
        'container_yaml': "container_5.yaml",
        'config_dir': "configs_t1"
    },
    {  # GPT-4配置示例
        'script_number': 6,
        'custom_openai_endpoint': 'http://140.207.201.47:11434/v1',
        'custom_openai_key': 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295',
        'custom_model_id': 'qwen2.5:7b',
        'batch_size': "5",
        'timeout': "1000",
        'cot_method': "few_shot",
        'dataset_name': "math500",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/cot/data/math500_test_converted.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/cot/Output",
        'output_name': "math500_results_6",
        'container_yaml': "container_6.yaml",
        'config_dir': "configs_t1"
    },
    {  # GPT-4配置示例
        'script_number': 7,
        'custom_openai_endpoint': 'http://140.207.201.47:11434/v1',
        'custom_openai_key': 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295',
        'custom_model_id': 'qwen2.5:7b',
        'batch_size': "5",
        'timeout': "1000",
        'cot_method': "few_shot",
        'dataset_name': "math500",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/cot/data/math500_test_converted.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/cot/Output",
        'output_name': "math500_results_7",
        'container_yaml': "container_7.yaml",
        'config_dir': "configs_t0"
    },
    {  # GPT-4配置示例
        'script_number': 8,
        'custom_openai_endpoint': 'http://140.207.201.47:11434/v1',
        'custom_openai_key': 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295',
        'custom_model_id': 'qwen2.5:7b',
        'batch_size': "5",
        'timeout': "1000",
        'cot_method': "few_shot",
        'dataset_name': "math500",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/cot/data/math500_test_converted.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/cot/Output",
        'output_name': "math500_results_8",
        'container_yaml': "container_8.yaml",
        'config_dir': "configs_t0"
    },
    # 可添加更多配置...
]

def generate_eval_script(script_number, config):
    """生成单个评估脚本"""
    # 读取模板内容
    with open(TEMPLATE_FILE, 'r') as f:
        content = f.read()
    
    # 定义所有需要替换的环境变量
    replacements = {
        "os.environ['custom_openai_endpoint'] = 'http://140.207.201.47:11434/v1'": 
            f"os.environ['custom_openai_endpoint'] = '{config['custom_openai_endpoint']}'",
        "os.environ['custom_openai_key'] = 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295'": 
            f"os.environ['custom_openai_key'] = '{config['custom_openai_key']}'",
        "os.environ['custom_model_id'] = 'qwen2:0.5b'": 
            f"os.environ['custom_model_id'] = '{config['custom_model_id']}'",
        "os.environ['batch_size'] = \"10\"": 
            f"os.environ['batch_size'] = \"{config['batch_size']}\"",
        "os.environ['timeout'] = \"300\"": 
            f"os.environ['timeout'] = \"{config['timeout']}\"",
        "os.environ['cot_method'] = \"few_shot\"": 
            f"os.environ['cot_method'] = \"{config['cot_method']}\"",
        "os.environ['dataset_name'] = \"math500\"": 
            f"os.environ['dataset_name'] = \"{config['dataset_name']}\"",
        "os.environ['dataset_path'] = \"/data23/ljc/project/wang_ze/OmAgent/examples/cot/data/math500_test_converted.jsonl\"": 
            f"os.environ['dataset_path'] = \"{config['dataset_path']}\"",
        "os.environ['output_path'] = \"/data23/ljc/project/wang_ze/OmAgent/examples/cot/Output\"": 
            f"os.environ['output_path'] = \"{config['output_path']}\"",
        "os.environ['output_name'] = \"math500_results_1\"": 
            f"os.environ['output_name'] = \"{config['output_name']}\"",
        "os.environ['container_yaml'] = \"container_8.yaml\"": 
            f"os.environ['container_yaml'] = \"{config['container_yaml']}\"",
        "os.environ['config_dir'] = \"configs\"": 
            f"os.environ['config_dir'] = \"{config['config_dir']}\""
    }
    
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    # 写入新文件路径调整
    output_file = OUTPUT_DIR / f"eval_batch_{script_number}.py"
    with open(output_file, 'w') as f:
        f.write(content)
    print(f'Generated {output_file}')

def main():
    # 清理旧文件逻辑调整
    for f in OUTPUT_DIR.glob("eval_batch_*.py"):
        f.unlink()
    
    # 生成所有脚本
    for config in SCRIPT_CONFIGS:
        generate_eval_script(config['script_number'], config)
    
    print(f"Total generated {len(SCRIPT_CONFIGS)} evaluation scripts")

if __name__ == '__main__':
    main() 