import json

# 嘗試讀取和解析 JSON 文件
json_file_path = 'DSE_vgg16_fuse_0.json'

try:
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        print("JSON 文件已成功解析")
except json.JSONDecodeError as e:
    print(f"JSON 解析錯誤: {e}")