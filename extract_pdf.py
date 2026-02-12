import pdfplumber
import json
import re

pdf_path = r"G:\UGit\sui\input\农行-6228480318046711970.pdf"

with pdfplumber.open(pdf_path) as pdf:
    print(f"总页数: {len(pdf.pages)}")

    for i, page in enumerate(pdf.pages):
        print(f"\n===== 第{i+1}页 =====")
        text = page.extract_text()
        if text:
            lines = text.split('\n')
            for idx, line in enumerate(lines):
                # 检查是否是交易行 (以日期开头 YYYYMMDD)
                if re.match(r'^\d{8}', line):
                    print(f"[交易] {line}")
                elif idx < 10:  # 头部信息
                    print(f"[头部] {line}")
