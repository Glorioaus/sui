#!/usr/bin/env python3
import json
import sys

# 尝试多种编码方式
def try_decode_file(file_path):
    encodings = ['utf-8', 'gbk', 'utf-16', 'utf-8-sig']

    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                print(f"✅ 使用 {encoding} 编码成功读取文件")

                # 检查是否有BOM
                if content.startswith('\ufeff'):
                    print("⚠️  文件包含UTF-8 BOM头")
                    content = content[1:]

                # 尝试解析JSON
                try:
                    data = json.loads(content)
                    print(f"✅ JSON解析成功！共 {len(data)} 个分类")
                    return True
                except json.JSONDecodeError as e:
                    print(f"❌ JSON解析错误 ({encoding}): {e}")
                    print(f"错误位置: 行 {e.lineno}, 列 {e.colno}")

                    # 显示错误位置附近的内容
                    lines = content.split('\n')
                    if e.lineno <= len(lines):
                        line = lines[e.lineno - 1]
                        print(f"错误行内容: {line.strip()}")
                        if e.colno < len(line):
                            print(f"错误位置标记: {' ' * (e.colno - 1)}^")

        except UnicodeDecodeError:
            print(f"❌ {encoding} 编码读取失败")

    return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python debug_json.py <文件路径>")
        sys.exit(1)

    file_path = sys.argv[1]
    print(f"正在检查文件: {file_path}")
    print("=" * 60)

    success = try_decode_file(file_path)

    print("=" * 60)
    if not success:
        print("❌ 无法解析该JSON文件，请检查文件编码和语法")
        sys.exit(1)