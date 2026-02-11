import json
import codecs

# 尝试用不同编码读取文件
try:
    # 先尝试UTF-8
    with open("G:\UGit\sui\config\category_mapping.json", "r", encoding="utf-8") as f:
        content = f.read()
    print("UTF-8读取成功，开始解析JSON...")
    data = json.loads(content)
    print("✅ JSON语法正确！")
    print(f"📊 包含 {len(data)} 个分类")
except json.JSONDecodeError as e:
    print(f"❌ JSON语法错误：{e}")
    print(f"错误位置：行 {e.lineno}, 列 {e.colno}")
    print("附近内容：", e.doc[e.pos-50:e.pos+50])
except UnicodeDecodeError as e:
    print(f"❌ UTF-8编码读取失败，尝试GBK编码...")
    try:
        with open("G:\UGit\sui\config\category_mapping.json", "r", encoding="gbk") as f:
            content = f.read()
        print("GBK读取成功，开始解析JSON...")
        data = json.loads(content)
        print("✅ JSON语法正确！")
        print(f"📊 包含 {len(data)} 个分类")
    except Exception as e:
        print(f"❌ GBK编码读取也失败：{e}")
except Exception as e:
    print(f"❌ 发生未知错误：{e}")