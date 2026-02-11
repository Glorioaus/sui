#!/usr/bin/env python3
import json

# 最简单的JSON检查脚本
file_path = "G:\UGit\sui\config\category_mapping.json"

print(f"检查文件: {file_path}")

# 尝试用UTF-8读取
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        print(f"读取成功，文件长度: {len(content)}字符")

        # 尝试解析
        try:
            data = json.loads(content)
            print("✅ JSON格式正确!")
            print(f"包含 {len(data)} 个分类")
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失败: {e}")
            print(f"行号: {e.lineno}")
            print(f"列号: {e.colno}")
            print(f"错误位置上下文: {e.doc[max(0, e.pos-50):e.pos+50]}")
except UnicodeDecodeError as e:
    print(f"❌ UTF-8编码读取失败: {e}")
    # 尝试用GBK读取
    try:
        with open(file_path, 'r', encoding='gbk') as f:
            content = f.read()
            print(f"GBK读取成功，文件长度: {len(content)}字符")

            try:
                data = json.loads(content)
                print("✅ JSON格式正确!")
                print(f"包含 {len(data)} 个分类")
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析失败: {e}")
    except UnicodeDecodeError as e:
        print(f"❌ GBK编码读取也失败: {e}")
except Exception as e:
    print(f"❌ 其他错误: {e}")
    import traceback
    traceback.print_exc()