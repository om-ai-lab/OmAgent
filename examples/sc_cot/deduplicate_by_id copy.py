import json
import os
from collections import OrderedDict

def deduplicate_and_convert(input_file):
    # 获取输入文件的目录和文件名
    dir_path = os.path.dirname(input_file)
    base_name = os.path.basename(input_file)
    jsonl_output = os.path.join(dir_path, f"dedup_{base_name}")
    json_output = jsonl_output.replace('.jsonl', '.json')
    
    # 使用 OrderedDict 保持最后一次出现的记录
    results_dict = OrderedDict()
    total_lines = 0
    
    # 读取输入文件
    print(f"Reading {input_file}...")
    with open(input_file, 'r') as f:
        for line in f:
            if line.strip():
                total_lines += 1
                result = json.loads(line)
                result_id = result.get('id')
                if result_id:
                    results_dict[result_id] = result

    # 写入去重后的 JSONL 结果
    print(f"Writing deduplicated results to {jsonl_output}...")
    with open(jsonl_output, 'w') as f:
        for result in results_dict.values():
            json.dump(result, f)
            f.write('\n')
    
    # 构建完整的 JSON 结构并写入
    print(f"Converting to JSON format: {json_output}...")
    final_data = {
        "dataset": "gsm8k",
        "model_id": base_name.split('_')[2].replace('.jsonl', ''),
        "alg": "SC-COT",
        "model_result": list(results_dict.values())
    }
    
    with open(json_output, 'w') as f:
        json.dump(final_data, f, indent=4)
    
    # 打印统计信息
    unique_count = len(results_dict)
    duplicate_count = total_lines - unique_count
    print(f"\nDeduplication complete:")
    print(f"Total records processed: {total_lines}")
    print(f"Unique records: {unique_count}")
    print(f"Duplicates removed: {duplicate_count}")
    print(f"JSONL output file: {jsonl_output}")
    print(f"JSON output file: {json_output}")
    
    # 打印所有结果的 ID，每行 10 个，按照数字大小排序
    # print("\nFinal result IDs in order:")
    # result_ids = sorted(results_dict.keys())  # 直接对字符串路径排序
    # for i in range(0, len(result_ids), 10):
    #     chunk = result_ids[i:i+10]
    #     # 格式化输出，每个 ID 占用相同宽度
    #     print(" ".join(f"{id:4}" for id in chunk))

if __name__ == "__main__":
    # 处理所有相关的 jsonl 文件
    model_ids = ["math500_results_2",
                 "math500_results_3",
                 "math500_results_4",
                 "math500_results_5",
                 "math500_results_6",
                 "math500_results_7",
                 "math500_results_8"] #"qwen2:0.5b", "qwen2.5:7b", "gpt-4o"
    for model_id in model_ids:
        input_file = f"examples/cot/Output/{model_id}.jsonl"
        if os.path.exists(input_file):
            print(f"\nProcessing {input_file}...")
            deduplicate_and_convert(input_file)
        else:
            print(f"File not found: {input_file}") 