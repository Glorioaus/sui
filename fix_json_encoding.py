#!/usr/bin/env python3
import json
import os

# 检测文件编码
def detect_encoding(file_path):
    import codecs
    encodings = ['utf-8', 'gbk', 'utf-16', 'utf-32', 'cp1252']

    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                f.read()
            return encoding
        except UnicodeDecodeError:
            continue
    return None

# 修复JSON文件
def fix_json_file(input_path, output_path):
    # 检测编码
    encoding = detect_encoding(input_path)
    if not encoding:
        print("❌ 无法检测文件编码")
        return False

    print(f"✅ 检测到文件编码: {encoding}")

    # 读取文件内容
    try:
        with open(input_path, 'r', encoding=encoding) as f:
            content = f.read()
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return False

    # 移除可能的BOM头
    content = content.lstrip('\ufeff')

    # 尝试解析JSON
    try:
        data = json.loads(content)
        print("✅ JSON解析成功")
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析错误: {e}")
        print(f"错误位置: 行 {e.lineno}, 列 {e.colno}")

        # 尝试修复常见问题
        import re

        # 移除行尾多余的逗号
        lines = content.split('\n')
        for i, line in enumerate(lines):
            # 匹配行尾逗号（后面没有引号或括号）
            if re.search(r',\s*$', line) and not re.search(r',\s*[}"]', line):
                lines[i] = re.sub(r',\s*$', '', line)
                print(f"修复行 {i+1}: 移除行尾多余逗号")

        # 重新尝试解析
        fixed_content = '\n'.join(lines)
        try:
            data = json.loads(fixed_content)
            print("✅ 修复后JSON解析成功")
            content = fixed_content
        except json.JSONDecodeError as e:
            print(f"❌ 修复失败，仍然有JSON错误: {e}")
            return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return False

    # 保存修复后的文件
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ 修复后的文件已保存: {output_path}")
        return True
    except Exception as e:
        print(f"❌ 保存文件失败: {e}")
        return False

if __name__ == '__main__':
    input_file = r"G:\UGit\sui\config\category_mapping.json"
    output_file = r"G:\UGit\sui\config\category_mapping_fixed.json"

    if not os.path.exists(input_file):
        print(f"❌ 文件不存在: {input_file}")
        exit(1)

    fix_json_file(input_file, output_file)