"""
测试农行PDF解析器
"""
import sys
import os

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'parsers'))

from parsers.abc_parser import ABCParser
from excel_generator import ExcelGenerator

def test_abc_parser():
    # 测试文件路径
    pdf_path = r"G:\UGit\sui\input\农行-6228480318046711970.pdf"
    output_path = r"G:\UGit\sui\output\农行账单_导入_v2.xlsx"

    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 创建解析器
    parser = ABCParser()

    # 解析账单
    statement = parser.parse(pdf_path)

    # 输出结果
    print(f"\n{'='*60}")
    print(f"银行: {statement.bank_name}")
    print(f"账户: {statement.account_name}")
    print(f"账号: {statement.account_number}")
    print(f"周期: {statement.statement_period}")
    print(f"交易数: {statement.get_transaction_count()}")
    print(f"{'='*60}\n")

    # 显示前10条交易
    print("前10条交易:")
    print("-" * 100)
    for i, tx in enumerate(statement.transactions[:10]):
        print(f"{i+1:2}. {tx.date} | {tx.transaction_type} | {tx.amount:>10.2f} | {tx.category}-{tx.subcategory} | {tx.description[:40]}")

    # 统计收入/支出
    income = sum(tx.amount for tx in statement.transactions if tx.transaction_type == "收入")
    expense = sum(tx.amount for tx in statement.transactions if tx.transaction_type == "支出")
    print(f"\n总收入: {income:.2f}")
    print(f"总支出: {expense:.2f}")
    print(f"净额: {income - expense:.2f}")

    # 生成Excel
    print(f"\n生成Excel文件...")
    generator = ExcelGenerator()
    generator.generate(statement, output_path)
    print(f"输出文件: {output_path}")

if __name__ == "__main__":
    test_abc_parser()
