import json
import pandas as pd

# 读取JSON文件
with open('data/event_list.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# 假设JSON文件的结构是一个包含字典的列表，每个字典都有'id'字段
# 提取'id'和整个字典转换为需要的格式
ids_and_jsons = [{"id": item["id"], "event": json.dumps(item, ensure_ascii=False)} for item in data]

# 将提取的数据转换为DataFrame
df = pd.DataFrame(ids_and_jsons)

# 存储到CSV文件
df.to_csv('output.csv', index=False, encoding='utf-8')


with open('data/data.json', 'r', encoding='utf-8') as file:
    data = json.load(file)
merge = ""
for i in range(len(data)):
    question = data[i]
    print(question)
    # 执行对话
    input = "# " + question["title"] + "\n"
    for paragraph in question["paragraphs"]:
        input += paragraph
    input += "\n"
    merge += input



with open("data/data_merge.md", 'w', encoding='utf-8') as f:
    f.write(merge)