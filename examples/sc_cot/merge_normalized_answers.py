import json
from pathlib import Path
from collections import Counter
import random
from math_verify import parse, verify

def load_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def are_answers_equivalent(ans1, ans2):
    """使用math_verify来判断两个答案是否等价"""
    try:
        parsed_ans1 = parse(ans1)
        parsed_ans2 = parse(ans2)
        return verify(parsed_ans1, parsed_ans2)
    except Exception as e:
        print(f"Warning: Error comparing answers: {ans1} and {ans2}")
        print(f"Error: {e}")
        # 如果解析失败，回退到字符串比较
        return ans1 == ans2

def count_equivalent_answers(answers):
    """统计等价答案的数量"""
    counts = {}  # {answer: count}
    
    for new_ans in answers:
        # 检查是否有等价的答案已经存在
        found_equivalent = False
        for existing_ans in counts:
            if are_answers_equivalent(new_ans, existing_ans):
                counts[existing_ans] += 1
                found_equivalent = True
                break
        
        # 如果没有找到等价答案，添加新的
        if not found_equivalent:
            counts[new_ans] = 1
    
    return counts

def merge_answers():
    # 设置文件路径
    current_path = Path(__file__).parent
    input_files = [
        current_path / f"Output/normalized_answers_{i}.json" 
        for i in range(2, 7)  # 2到6
    ]
    output_file = current_path / "Output/merged_normalized_answers_v2.json"

    # 存储所有ID的所有答案
    all_answers = {}  # {id: [answers from different files]}
    
    # 加载所有文件
    print("Loading files...")
    for file_path in input_files:
        try:
            data = load_json_file(file_path)
            print(f"Loaded {len(data)} items from {file_path.name}")
            
            # 收集每个ID的答案
            for item in data:
                id = item['id']
                if id not in all_answers:
                    all_answers[id] = []
                all_answers[id].append(item['normalized_answer'])
        except Exception as e:
            print(f"Error loading {file_path}: {e}")

    # 处理每个ID的答案
    print("\nProcessing answers...")
    result = []
    for id, answers in all_answers.items():
        # 使用数学等价性来计算答案出现次数
        answer_counts = count_equivalent_answers(answers)
        
        # 找出出现次数最多的答案
        max_count = max(answer_counts.values())
        # 获取所有出现次数最多的答案
        most_common_answers = [ans for ans, count in answer_counts.items() if count == max_count]
        # 如果有多个答案出现次数相同，随机选择一个
        selected_answer = random.choice(most_common_answers)
        
        result.append({
            'id': id,
            'normalized_answer': selected_answer,
            'answer_counts': dict(answer_counts),  # 保存所有答案的出现次数，用于分析
            'files_count': len(answers),  # 有多少文件包含这个ID
            'equivalent_groups': len(answer_counts)  # 不同等价类的数量
        })

    # 输出统计信息
    print(f"\nTotal unique IDs processed: {len(result)}")
    
    # 统计每个ID在多少个文件中出现
    appearance_counts = Counter(item['files_count'] for item in result)
    print("\nID appearance statistics:")
    for count in sorted(appearance_counts.keys()):
        print(f"IDs appearing in {count} files: {appearance_counts[count]}")

    # 统计等价类的分布
    equiv_group_counts = Counter(item['equivalent_groups'] for item in result)
    print("\nEquivalent groups statistics:")
    for count in sorted(equiv_group_counts.keys()):
        print(f"IDs with {count} different equivalent answer groups: {equiv_group_counts[count]}")

    # 保存结果
    print(f"\nSaving results to {output_file}")
    save_json_file(result, output_file)
    print("Done!")

if __name__ == "__main__":
    merge_answers() 