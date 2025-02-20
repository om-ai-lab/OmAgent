import json
from pathlib import Path

def load_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def compare_answers():
    # 设置文件路径
    current_path = Path(__file__).parent
    file1 = current_path / "Output/normalized_answers_2_v1.json"
    file2 = current_path / "Output/normalized_answers_2_v2.json"

    # 加载文件
    print("Loading files...")
    data1 = load_json_file(file1)
    data2 = load_json_file(file2)

    # 创建id到answer的映射
    answers1 = {item['id']: item['normalized_answer'] for item in data1}
    answers2 = {item['id']: item['normalized_answer'] for item in data2}

    # 获取所有唯一的id
    all_ids = set(answers1.keys()) | set(answers2.keys())
    
    # 比较差异
    print("\nComparing answers...")
    print(f"Total questions in v1: {len(answers1)}")
    print(f"Total questions in v2: {len(answers2)}")
    
    # 检查是否有id不同
    only_in_v1 = set(answers1.keys()) - set(answers2.keys())
    only_in_v2 = set(answers2.keys()) - set(answers1.keys())
    
    if only_in_v1:
        print(f"\nQuestions only in v1: {len(only_in_v1)}")
        for id in only_in_v1:
            print(f"ID: {id}")
    
    if only_in_v2:
        print(f"\nQuestions only in v2: {len(only_in_v2)}")
        for id in only_in_v2:
            print(f"ID: {id}")

    # 检查答案不同的问题
    different_answers = []
    for id in all_ids:
        if id in answers1 and id in answers2:
            if answers1[id] != answers2[id]:
                different_answers.append({
                    'id': id,
                    'v1_answer': answers1[id],
                    'v2_answer': answers2[id]
                })

    if different_answers:
        print(f"\nFound {len(different_answers)} questions with different answers:")
        for diff in different_answers:
            print(f"\nID: {diff['id']}")
            print(f"V1 answer: {diff['v1_answer']}")
            print(f"V2 answer: {diff['v2_answer']}")
    else:
        print("\nNo differences found in answers for common questions.")

if __name__ == "__main__":
    compare_answers() 