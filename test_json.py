import json
import os

# 读取文件并检查JSON语法
file_path = r"G:\UGit\sui\config\category_mapping.json"

try:
    # 以二进制模式读取，检查原始内容
    with open(file_path, 'rb') as f:
        raw_content = f.read()

    print("文件前20个字节:", raw_content[:20])
    print("文件后20个字节:", raw_content[-20:])

    # 检查是否有UTF-8 BOM
    if raw_content.startswith(b'\xef\xbb\xbf'):
        print("文件包含UTF-8 BOM头")
        content = raw_content[3:].decode('utf-8')
    else:
        # 尝试不同编码
        try:
            content = raw_content.decode('utf-8')
            print("使用UTF-8编码读取成功")
        except UnicodeDecodeError:
            content = raw_content.decode('gbk')
            print("使用GBK编码读取成功")

    # 检查是否有特殊字符
    for i, c in enumerate(content[:100]):
        if ord(c) > 127 and not c.strip():
            print(f"发现特殊字符在位置{i}: {ord(c)} = {repr(c)}")

    # 尝试解析JSON
    data = json.loads(content)
    print(f"JSON解析成功，共{len(data)}个顶级键")

except Exception as e:
    print(f"错误: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()