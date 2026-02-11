#!/usr/bin/env python3
import json
import codecs

# 读取文件并检测编码
file_path = r"G:\UGit\sui\config\category_mapping.json"

# 尝试用不同编码读取
try:
    with open(file_path, 'rb') as f:
        raw_data = f.read()

    # 检查是否有BOM
    if raw_data.startswith(codecs.BOM_UTF8):
        print("文件有UTF-8 BOM头")
        content = raw_data[3:].decode('utf-8')
    elif raw_data.startswith(codecs.BOM_UTF16):
        print("文件有UTF-16 BOM头")
        content = raw_data.decode('utf-16')
    else:
        # 尝试UTF-8
        try:
            content = raw_data.decode('utf-8')
            print("文件编码为UTF-8")
        except:
            # 尝试GBK
            content = raw_data.decode('gbk')
            print("文件编码为GBK")

    # 保存为标准UTF-8格式
    output_path = r"G:\UGit\sui\config\category_mapping_utf8.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"已保存为标准UTF-8格式文件: {output_path}")

    # 尝试解析
    data = json.loads(content)
    print("JSON解析成功")
    print(f"包含{len(data)}个分类")

except Exception as e:
    print(f"错误: {e}")