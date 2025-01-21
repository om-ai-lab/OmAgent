import json

# 读取jsonl文件获取正确顺序
questions_order = {}
with open('aqua_test.jsonl', 'r') as f:
    for line in f:
        data = json.loads(line)
        questions_order[data['question']] = data['id']

# 读取temp1文件
with open('aqua_test_qwen2.5_7b.json', 'r') as f:
    temp1_data = json.load(f)

# 为每个结果找到对应的正确ID
for item in temp1_data['model_result']:
    question = item['question'].split("Answer Choices")[0]
    if question in questions_order:
        item['id'] = str(questions_order[question])

# 按ID排序
temp1_data['model_result'].sort(key=lambda x: int(x['id']))

# 写入新文件
with open('aqua_test_qwen2.5_7b.json', 'w') as f:
    json.dump(temp1_data, f, indent=4)
