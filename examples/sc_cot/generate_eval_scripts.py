import os
import shutil
from pathlib import Path

# 原始模板文件路径
TEMPLATE_FILE = Path(__file__).parent / "sample_eval_batch.py"
# 输出目录 (直接生成到当前目录)
OUTPUT_DIR = Path(__file__).parent

# 完整配置参数
SCRIPT_CONFIGS = [
    {  # 基础配置
        'script_number': 2,
        'custom_openai_endpoint': 'http://140.207.201.47:11452/v1',
        'custom_openai_key': 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295',
        'custom_model_id': 'qwen2:0.5b',
        'batch_size': "2",
        'timeout': "1000",
        'dataset_name': "math500",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/data/math500_test_converted.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/Output",
        'container_yaml': "container_2.yaml",
        'config_dir': "configs_math500_t0_n5"
    },
    {  # GPT-4配置示例
        'script_number': 3,
        'custom_openai_endpoint': 'http://140.207.201.47:11452/v1',
        'custom_openai_key': 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295',
        'custom_model_id': 'qwen2:1.5b',
        'batch_size': "2",
        'timeout': "1000",
        'dataset_name': "math500",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/data/math500_test_converted.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/Output",
        'container_yaml': "container_3.yaml",
        'config_dir': "configs_math500_t0_n5"
    },
    {  # GPT-4配置示例
        'script_number': 4,
        'custom_openai_endpoint': 'http://140.207.201.47:11452/v1',
        'custom_openai_key': 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295',
        'custom_model_id': 'qwen2.5:7b',
        'batch_size': "2",
        'timeout': "1000",
        'dataset_name': "math500",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/data/math500_test_converted.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/Output",
        'container_yaml': "container_4.yaml",
        'config_dir': "configs_math500_t0_n5"
    },
    {  # GPT-4配置示例
        'script_number': 5,
        'custom_openai_endpoint': "http://121.52.244.250:3000/v1",
        'custom_openai_key': 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295',
        'custom_model_id': 'qwen2.5-72b-instruct',
        'batch_size': "2",
        'timeout': "1000",
        'dataset_name': "math500",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/data/math500_test_converted.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/Output",
        'container_yaml': "container_5.yaml",
        'config_dir': "configs_math500_t0_n5"
    },
    {  # GPT-4配置示例
        'script_number': 6,
        'custom_openai_endpoint': 'http://140.207.201.47:11452/v1',
        'custom_openai_key': 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295',
        'custom_model_id': 'internlm/internlm2.5:7b-chat',
        'batch_size': "2",
        'timeout': "1000",
        'dataset_name': "math500",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/data/math500_test_converted.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/Output",
        'container_yaml': "container_6.yaml",
        'config_dir': "configs_math500_t0_n5"
    },
    {  # GPT-4配置示例
        'script_number': 7,
        'custom_openai_endpoint': 'http://140.207.201.47:11452/v1',
        'custom_openai_key': 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295',
        'custom_model_id': 'llama3.1:8b',
        'batch_size': "2",
        'timeout': "1000",
        'dataset_name': "math500",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/data/math500_test_converted.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/Output",
        'container_yaml': "container_7.yaml",
        'config_dir': "configs_math500_t0_n5"
    },
    {  # GPT-4配置示例
        'script_number': 8,
        'custom_openai_endpoint': "http://121.52.244.250:3000/v1",
        'custom_openai_key': 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295',
        'custom_model_id': 'gpt-3.5-turbo',
        'batch_size': "2",
        'timeout': "1000",
        'dataset_name': "math500",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/data/math500_test_converted.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/Output",
        'container_yaml': "container_8.yaml",
        'config_dir': "configs_math500_t0_n5_use"
    },
    {  # GPT-4配置示例
        'script_number': 9,
        'custom_openai_endpoint': "http://121.52.244.250:3000/v1",
        'custom_openai_key': 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295',
        'custom_model_id': 'gpt-4o',
        'batch_size': "2",
        'timeout': "1000",
        'dataset_name': "math500",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/data/math500_test_converted.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/Output",
        'container_yaml': "container_9.yaml",
        'config_dir': "configs_math500_t0_n5_use"
    },
    {  # GPT-4配置示例
        'script_number': 10,
        'custom_openai_endpoint': "https://ark.cn-beijing.volces.com/api/v3",
        'custom_openai_key': "c549be1a-2cba-40d7-a30b-39622789f190",
        'custom_model_id': 'ep-20250102150313-jp4cc',
        'batch_size': "2",
        'timeout': "1000",
        'dataset_name': "math500",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/data/math500_test_converted.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/Output",
        'container_yaml': "container_10.yaml",
        'config_dir': "configs_math500_t0_n5_use"
    },
    {  # GPT-4配置示例
        'script_number': 11,
        'custom_openai_endpoint': 'http://140.207.201.47:11452/v1',
        'custom_openai_key': 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295',
        'custom_model_id': 'deepseek-r1:1.5b',
        'batch_size': "8",
        'timeout': "1000",
        'dataset_name': "math500",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/data/math500_test_converted.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/Output",
        'container_yaml': "container_11.yaml",
        'config_dir': "configs_math500_t0_n5"
    },
    {  # GPT-4配置示例
        'script_number': 12,
        'custom_openai_endpoint': "http://121.52.244.250:3000/v1",
        'custom_openai_key': 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295',
        'custom_model_id': 'meta-llama/Llama-3.3-70B-Instruct',
        'batch_size': "2",
        'timeout': "1000",
        'dataset_name': "math500",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/data/math500_test_converted.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/Output",
        'container_yaml': "container_12.yaml",
        'config_dir': "configs_math500_t0_n5"
    },
    {  # 基础配置
        'script_number': 13,
        'custom_openai_endpoint': 'http://140.207.201.47:11452/v1',
        'custom_openai_key': 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295',
        'custom_model_id': 'qwen2:0.5b',
        'batch_size': "2",
        'timeout': "1000",
        'dataset_name': "aqua",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/data/aqua_test_formatted.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/Output",
        'container_yaml': "container_13.yaml",
        'config_dir': "configs_aqua_t0_n5"
    },
    {  # GPT-4配置示例
        'script_number': 14,
        'custom_openai_endpoint': 'http://140.207.201.47:11452/v1',
        'custom_openai_key': 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295',
        'custom_model_id': 'qwen2:1.5b',
        'batch_size': "2",
        'timeout': "1000",
        'dataset_name': "aqua",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/data/aqua_test_formatted.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/Output",
        'container_yaml': "container_14.yaml",
        'config_dir': "configs_aqua_t0_n5"
    },
    {  # GPT-4配置示例
        'script_number': 15,
        'custom_openai_endpoint': 'http://140.207.201.47:11452/v1',
        'custom_openai_key': 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295',
        'custom_model_id': 'qwen2.5:7b',
        'batch_size': "2",
        'timeout': "1000",
        'dataset_name': "aqua",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/data/aqua_test_formatted.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/Output",
        'container_yaml': "container_15.yaml",
        'config_dir': "configs_aqua_t0_n5"
    },
    {  # GPT-4配置示例
        'script_number': 16,
        'custom_openai_endpoint': "http://121.52.244.250:3000/v1",
        'custom_openai_key': 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295',
        'custom_model_id': 'qwen2.5-72b-instruct',
        'batch_size': "2",
        'timeout': "1000",
        'dataset_name': "aqua",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/data/aqua_test_formatted.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/Output",
        'container_yaml': "container_16.yaml",
        'config_dir': "configs_aqua_t0_n5"
    },
    {  # GPT-4配置示例
        'script_number': 17,
        'custom_openai_endpoint': 'http://140.207.201.47:11452/v1',
        'custom_openai_key': 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295',
        'custom_model_id': 'internlm/internlm2.5:7b-chat',
        'batch_size': "2",
        'timeout': "1000",
        'dataset_name': "aqua",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/data/aqua_test_formatted.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/Output",
        'container_yaml': "container_17.yaml",
        'config_dir': "configs_aqua_t0_n5"
    },
    {  # GPT-4配置示例
        'script_number': 18,
        'custom_openai_endpoint': 'http://140.207.201.47:11452/v1',
        'custom_openai_key': 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295',
        'custom_model_id': 'llama3.1:8b',
        'batch_size': "2",
        'timeout': "1000",
        'dataset_name': "aqua",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/data/aqua_test_formatted.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/Output",
        'container_yaml': "container_18.yaml",
        'config_dir': "configs_aqua_t0_n5"
    },
    {  # GPT-4配置示例
        'script_number': 19,
        'custom_openai_endpoint': "http://121.52.244.250:3000/v1",
        'custom_openai_key': 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295',
        'custom_model_id': 'gpt-3.5-turbo',
        'batch_size': "2",
        'timeout': "1000",
        'dataset_name': "aqua",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/data/aqua_test_formatted.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/Output",
        'container_yaml': "container_19.yaml",
        'config_dir': "configs_aqua_t0_n5_use"
    },
    {  # GPT-4配置示例
        'script_number': 20,
        'custom_openai_endpoint': "http://121.52.244.250:3000/v1",
        'custom_openai_key': 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295',
        'custom_model_id': 'gpt-4o',
        'batch_size': "2",
        'timeout': "1000",
        'dataset_name': "aqua",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/data/aqua_test_formatted.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/Output",
        'container_yaml': "container_20.yaml",
        'config_dir': "configs_aqua_t0_n5_use"
    },
    {  # GPT-4配置示例
        'script_number': 21,
        'custom_openai_endpoint': "https://ark.cn-beijing.volces.com/api/v3",
        'custom_openai_key': "c549be1a-2cba-40d7-a30b-39622789f190",
        'custom_model_id': 'ep-20250102150313-jp4cc',
        'batch_size': "2",
        'timeout': "1000",
        'dataset_name': "aqua",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/data/aqua_test_formatted.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/Output",
        'container_yaml': "container_21.yaml",
        'config_dir': "configs_aqua_t0_n5_use"
    },
    {  # GPT-4配置示例
        'script_number': 22,
        'custom_openai_endpoint': 'http://140.207.201.47:11452/v1',
        'custom_openai_key': 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295',
        'custom_model_id': 'deepseek-r1:1.5b',
        'batch_size': "2",
        'timeout': "1000",
        'dataset_name': "aqua",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/data/aqua_test_formatted.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/Output",
        'container_yaml': "container_22.yaml",
        'config_dir': "configs_aqua_t0_n5"
    },
    {  # GPT-4配置示例
        'script_number': 23,
        'custom_openai_endpoint': "http://121.52.244.250:3000/v1",
        'custom_openai_key': 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295',
        'custom_model_id': 'meta-llama/Llama-3.3-70B-Instruct',
        'batch_size': "2",
        'timeout': "1000",
        'dataset_name': "aqua",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/data/aqua_test_formatted.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/Output",
        'container_yaml': "container_23.yaml",
        'config_dir': "configs_aqua_t0_n5"
    },
    {  # 基础配置
        'script_number': 24,
        'custom_openai_endpoint': 'http://140.207.201.47:11452/v1',
        'custom_openai_key': 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295',
        'custom_model_id': 'qwen2:0.5b',
        'batch_size': "2",
        'timeout': "1000",
        'dataset_name': "gsm8k",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/data/gsm8k_test.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/Output",
        'container_yaml': "container_24.yaml",
        'config_dir': "configs_gsm8k_t0_n5"
    },
    {  # GPT-4配置示例
        'script_number': 25,
        'custom_openai_endpoint': 'http://140.207.201.47:11452/v1',
        'custom_openai_key': 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295',
        'custom_model_id': 'qwen2:1.5b',
        'batch_size': "2",
        'timeout': "1000",
        'dataset_name': "gsm8k",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/data/gsm8k_test.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/Output",
        'container_yaml': "container_25.yaml",
        'config_dir': "configs_gsm8k_t0_n5"
    },
    {  # GPT-4配置示例
        'script_number': 26,
        'custom_openai_endpoint': 'http://140.207.201.47:11452/v1',
        'custom_openai_key': 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295',
        'custom_model_id': 'qwen2.5:7b',
        'batch_size': "2",
        'timeout': "1000",
        'dataset_name': "gsm8k",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/data/gsm8k_test.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/Output",
        'container_yaml': "container_26.yaml",
        'config_dir': "configs_gsm8k_t0_n5"
    },
    {  # GPT-4配置示例
        'script_number': 27,
        'custom_openai_endpoint': "http://121.52.244.250:3000/v1",
        'custom_openai_key': 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295',
        'custom_model_id': 'qwen2.5-72b-instruct',
        'batch_size': "2",
        'timeout': "1000",
        'dataset_name': "gsm8k",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/data/gsm8k_test.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/Output",
        'container_yaml': "container_27.yaml",
        'config_dir': "configs_gsm8k_t0_n5"
    },
    {  # GPT-4配置示例
        'script_number': 28,
        'custom_openai_endpoint': 'http://140.207.201.47:11452/v1',
        'custom_openai_key': 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295',
        'custom_model_id': 'internlm/internlm2.5:7b-chat',
        'batch_size': "2",
        'timeout': "1000",
        'dataset_name': "gsm8k",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/data/gsm8k_test.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/Output",
        'container_yaml': "container_28.yaml",
        'config_dir': "configs_gsm8k_t0_n5"
    },
    {  # GPT-4配置示例
        'script_number': 29,
        'custom_openai_endpoint': 'http://140.207.201.47:11452/v1',
        'custom_openai_key': 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295',
        'custom_model_id': 'llama3.1:8b',
        'batch_size': "2",
        'timeout': "1000",
        'dataset_name': "gsm8k",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/data/gsm8k_test.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/Output",
        'container_yaml': "container_29.yaml",
        'config_dir': "configs_gsm8k_t0_n5"
    },
    {  # GPT-4配置示例
        'script_number': 30,
        'custom_openai_endpoint': "http://121.52.244.250:3000/v1",
        'custom_openai_key': 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295',
        'custom_model_id': 'gpt-3.5-turbo',
        'batch_size': "2",
        'timeout': "1000",
        'dataset_name': "gsm8k",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/data/gsm8k_test.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/Output",
        'container_yaml': "container_30.yaml",
        'config_dir': "configs_gsm8k_t0_n5_use"
    },
    {  # GPT-4配置示例
        'script_number': 31,
        'custom_openai_endpoint': "http://121.52.244.250:3000/v1",
        'custom_openai_key': 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295',
        'custom_model_id': 'gpt-4o',
        'batch_size': "2",
        'timeout': "1000",
        'dataset_name': "gsm8k",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/data/gsm8k_test.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/Output",
        'container_yaml': "container_31.yaml",
        'config_dir': "configs_gsm8k_t0_n5_use"
    },
    {  # GPT-4配置示例
        'script_number': 32,
        'custom_openai_endpoint': "https://ark.cn-beijing.volces.com/api/v3",
        'custom_openai_key': "c549be1a-2cba-40d7-a30b-39622789f190",
        'custom_model_id': 'ep-20250102150313-jp4cc',
        'batch_size': "2",
        'timeout': "1000",
        'dataset_name': "gsm8k",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/data/gsm8k_test.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/Output",
        'container_yaml': "container_32.yaml",
        'config_dir': "configs_gsm8k_t0_n5_use"
    },
    {  # GPT-4配置示例
        'script_number': 33,
        'custom_openai_endpoint': 'http://140.207.201.47:11452/v1',
        'custom_openai_key': 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295',
        'custom_model_id': 'deepseek-r1:1.5b',
        'batch_size': "2",
        'timeout': "1000",
        'dataset_name': "gsm8k",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/data/gsm8k_test.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/Output",
        'container_yaml': "container_33.yaml",
        'config_dir': "configs_gsm8k_t0_n5"
    },
    {  # GPT-4配置示例
        'script_number': 34,
        'custom_openai_endpoint': "http://121.52.244.250:3000/v1",
        'custom_openai_key': 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295',
        'custom_model_id': 'meta-llama/Llama-3.3-70B-Instruct',
        'batch_size': "2",
        'timeout': "1000",
        'dataset_name': "gsm8k",
        'dataset_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/data/gsm8k_test.jsonl",
        'output_path': "/data23/ljc/project/wang_ze/OmAgent/examples/sc_cot/Output",
        'container_yaml': "container_34.yaml",
        'config_dir': "configs_gsm8k_t0_n5"
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
        "os.environ['custom_openai_endpoint'] = ''": 
            f"os.environ['custom_openai_endpoint'] = '{config['custom_openai_endpoint']}'",
        "os.environ['custom_openai_key'] = ''": 
            f"os.environ['custom_openai_key'] = '{config['custom_openai_key']}'",
        "os.environ['custom_model_id'] = ''": 
            f"os.environ['custom_model_id'] = '{config['custom_model_id']}'",
        "os.environ['batch_size'] = ''": 
            f"os.environ['batch_size'] = \"{config['batch_size']}\"",
        "os.environ['timeout'] = ''": 
            f"os.environ['timeout'] = \"{config['timeout']}\"",
        "os.environ['dataset_name'] = ''": 
            f"os.environ['dataset_name'] = \"{config['dataset_name']}\"",
        "os.environ['dataset_path'] = ''": 
            f"os.environ['dataset_path'] = \"{config['dataset_path']}\"",
        "os.environ['output_path'] = ''": 
            f"os.environ['output_path'] = \"{config['output_path']}\"",
        "os.environ['container_yaml'] = ''": 
            f"os.environ['container_yaml'] = \"{config['container_yaml']}\"",
        "os.environ['config_dir'] = ''": 
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