#!/usr/bin/env python3
import json
import sys

# 直接解析JSON文件
try:
    with open('G:\UGit\sui\config\category_mapping.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    print("✅ JSON文件格式正确!")
    print(f"包含 {len(data)} 个主分类")
    for category, subcategories in data.items():
        print(f"  - {category}: {len(subcategories)} 个子分类")
except json.JSONDecodeError as e:
    print(f"❌ JSON语法错误:")
    print(f"  位置: 行 {e.lineno}, 列 {e.colno}")
    print(f"  错误信息: {e.msg}")
    # 显示错误行内容
    with open('G:\UGit\sui\config\category_mapping.json', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        if e.lineno <= len(lines):
            print(f"  错误行内容: {lines[e.lineno-1].strip()}")
            print(f"  错误标记: {' '*(e.colno-1)}^")
except Exception as e:
    print(f"❌ 其他错误: {e}")
    sys.exit(1)