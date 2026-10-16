import json
import os
from pathlib import Path

def load_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def replace_answers():
    # 设置文件路径
    current_path = Path(__file__).parent
    dedup_file = current_path / "Output/dedup_math500_results_6.json"
    normalized_file = current_path / "Output/merged_normalized_answers_v2.json"
    output_file = current_path / "Output/replaced_math500_results_merged_v2.json"

    # 加载文件
    print("Loading files...")
    dedup_data = load_json_file(dedup_file)
    normalized_data = load_json_file(normalized_file)

    # 创建normalized_data的id到answer的映射
    normalized_map = {item['id']: item['normalized_answer'] for item in normalized_data}

    # 替换答案
    print("Replacing answers...")
    replaced_count = 0
    
    # 遍历model_result中的每个item
    for item in dedup_data['model_result']:
        if item['id'] in normalized_map:
            item['last_output'] = normalized_map[item['id']]
            replaced_count += 1

    # 保存结果
    print(f"Saving results... (Replaced {replaced_count} answers)")
    save_json_file(dedup_data, output_file)
    print(f"Done! Results saved to {output_file}")

if __name__ == "__main__":
    replace_answers() 