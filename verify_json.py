#!/usr/bin/env python3
import json
import os

# 直接读取文件内容并验证
file_path = r"G:\UGit\sui\config\category_mapping.json"

try:
    # 先尝试用UTF-8读取
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        print("读取文件成功，长度:", len(content))

        # 尝试解析
        data = json.loads(content)
        print("✅ JSON解析成功!")
        print(f"分类数量: {len(data)}")
        for key in data:
            print(f"  - {key}: {len(data[key])}个子分类")

        # 尝试重新写入一个新文件
        new_file_path = r"G:\UGit\sui\config\category_mapping_fixed.json"
        with open(new_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 已生成修复后的文件: {new_file_path}")

except json.JSONDecodeError as e:
    print(f"❌ JSON解析错误: {e}")
    print(f"行: {e.lineno}, 列: {e.colno}")

except UnicodeDecodeError as e:
    print(f"❌ 编码错误: {e}")
    print("尝试用GBK编码读取...")
    with open(file_path, 'r', encoding='gbk') as f:
        content = f.read()
        print("GBK读取成功，长度:", len(content))
        data = json.loads(content)
        print("✅ JSON解析成功!")

except Exception as e:
    print(f"❌ 其他错误: {e}")
    import traceback
    traceback.print_exc()