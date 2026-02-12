"""
合并处理脚本
读取所有Excel文件，执行跨文件退款对冲和转账识别
"""
import os
import sys
import re
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
import openpyxl

# 添加src目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import Transaction
from excel_generator import ExcelGenerator


# 转账识别关键词映射
TRANSFER_KEYWORDS = {
    "中信": "中信信用卡",
    "招商": "招商信用卡",
    "浦发": "浦发信用卡",
    "建行信用": "建行信用卡",
    "建行卡": "建行信用卡",
    "花呗": "花呗",
    "京东白条": "京东白条",
    "信用卡还款": None,  # 通用信用卡还款
    "还款": None,
}

# 储蓄卡账户列表（转账来源）
DEBIT_ACCOUNTS = ["农业银行", "宁波银行", "建行储蓄卡", "工商储蓄卡", "招商储蓄卡", "农村信用合作社"]

# 信用卡账户列表（转账目标）
CREDIT_ACCOUNTS = ["中信信用卡", "浦发信用卡", "招商信用卡", "建行信用卡", "花呗", "京东白条"]


def read_excel_transactions(file_path: str) -> List[Transaction]:
    """
    从Excel文件读取交易记录
    """
    transactions = []
    try:
        wb = openpyxl.load_workbook(file_path, read_only=True)
        ws = wb.active

        # 跳过表头，从第2行开始
        for row in ws.iter_rows(min_row=2, values_only=True):
            if row[0] is None:  # 跳过空行
                continue

            # 解析日期
            date_val = row[0]
            if isinstance(date_val, datetime):
                date_str = date_val.strftime("%Y-%m-%d")
            else:
                date_str = str(date_val)

            # 解析金额
            amount = float(row[5]) if row[5] else 0.0

            transaction = Transaction(
                date=date_str,
                category=str(row[1] or ""),
                subcategory=str(row[3] or ""),
                account=str(row[4] or ""),
                amount=amount,
                description=str(row[9] or ""),
                transaction_type=str(row[2] or "支出"),
                merchant=str(row[7] or ""),
            )
            transactions.append(transaction)

        wb.close()
    except Exception as e:
        print(f"读取文件失败 {file_path}: {e}")

    return transactions


def parse_date(date_str: str) -> Optional[datetime]:
    """解析日期字符串"""
    formats = ["%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def dates_within_range(date1: str, date2: str, days: int = 3) -> bool:
    """检查两个日期是否在指定天数范围内"""
    d1 = parse_date(date1)
    d2 = parse_date(date2)
    if d1 is None or d2 is None:
        return False
    return abs((d1 - d2).days) <= days


def amounts_match(amount1: float, amount2: float, tolerance: float = 0.01) -> bool:
    """检查两个金额是否匹配（允许小误差）"""
    return abs(amount1 - amount2) <= tolerance


def normalize_merchant(merchant: str, description: str) -> str:
    """
    标准化商户名称，用于匹配
    从商户名或描述中提取关键信息
    """
    # 优先使用商户名
    text = merchant if merchant else description
    if not text:
        return ""

    # 移除常见前缀后缀
    text = re.sub(r'^(消费|支付|转账|退款|退货)[:\-\s]*', '', text)
    text = re.sub(r'[\s\-_]+', '', text)

    return text.strip().lower()


def reconcile_refunds(transactions: List[Transaction]) -> List[Transaction]:
    """
    执行退款对冲
    匹配条件：同商户 + 同金额（容差0.01元）
    结果：匹配成功的消费和退款都删除
    """
    print("\n=== 开始退款对冲 ===")

    # 分离支出和收入（退款）
    expenses = []  # (index, transaction)
    refunds = []   # (index, transaction)

    for i, t in enumerate(transactions):
        if t.transaction_type == "支出":
            expenses.append((i, t))
        elif t.transaction_type == "收入":
            # 检查是否是退款类型
            desc_lower = (t.description or "").lower()
            cat_lower = (t.category or "").lower()
            subcat_lower = (t.subcategory or "").lower()
            if "退款" in desc_lower or "退款" in cat_lower or "退款" in subcat_lower:
                refunds.append((i, t))

    # 记录要删除的索引
    to_remove = set()
    matched_count = 0

    for ref_idx, refund in refunds:
        if ref_idx in to_remove:
            continue

        ref_merchant = normalize_merchant(refund.merchant, refund.description)

        for exp_idx, expense in expenses:
            if exp_idx in to_remove:
                continue

            exp_merchant = normalize_merchant(expense.merchant, expense.description)

            # 匹配条件：商户相似 + 金额相同
            if ref_merchant and exp_merchant and ref_merchant == exp_merchant:
                if amounts_match(refund.amount, expense.amount):
                    print(f"  对冲匹配: [{expense.date}] {expense.merchant or expense.description[:20]} "
                          f"¥{expense.amount} <-> [{refund.date}] 退款 ¥{refund.amount}")
                    to_remove.add(ref_idx)
                    to_remove.add(exp_idx)
                    matched_count += 1
                    break

    # 过滤掉已对冲的记录
    result = [t for i, t in enumerate(transactions) if i not in to_remove]

    print(f"退款对冲完成：{matched_count} 对匹配，删除 {len(to_remove)} 条记录")
    return result


def identify_transfer_target(description: str) -> Optional[str]:
    """
    从描述中识别转账目标账户
    """
    if not description:
        return None

    desc_lower = description.lower()

    for keyword, target in TRANSFER_KEYWORDS.items():
        if keyword.lower() in desc_lower:
            return target

    return None


def identify_transfers(transactions: List[Transaction]) -> List[Transaction]:
    """
    执行转账识别
    匹配条件：
    - 账户A有"支出"（如农行转出）
    - 账户B有"收入"或被识别为还款
    - 金额相同，日期接近（±3天）
    结果：删除两条记录，生成一条转账记录
    """
    print("\n=== 开始转账识别 ===")

    # 分离储蓄卡支出（可能是转账）
    debit_expenses = []  # (index, transaction, potential_target)
    credit_incomes = []  # (index, transaction)

    for i, t in enumerate(transactions):
        # 储蓄卡支出
        if t.account in DEBIT_ACCOUNTS and t.transaction_type == "支出":
            target = identify_transfer_target(t.description)
            if target:
                debit_expenses.append((i, t, target))

        # 信用卡收入（还款）
        if t.account in CREDIT_ACCOUNTS and t.transaction_type == "收入":
            credit_incomes.append((i, t))

    # 记录要删除的索引和新增的转账记录
    to_remove = set()
    transfers = []
    matched_count = 0

    for exp_idx, expense, target in debit_expenses:
        if exp_idx in to_remove:
            continue

        matched_income = False

        # 如果有明确目标账户，先尝试匹配信用卡收入
        if target:
            for inc_idx, income in credit_incomes:
                if inc_idx in to_remove:
                    continue

                # 检查是否是目标账户
                if income.account != target:
                    continue

                # 检查金额和日期
                if amounts_match(expense.amount, income.amount) and \
                   dates_within_range(expense.date, income.date):
                    print(f"  转账匹配: [{expense.date}] {expense.account} → {income.account} "
                          f"¥{expense.amount}")

                    # 创建转账记录
                    transfer = Transaction(
                        date=expense.date,
                        category="转账",
                        subcategory="还款",
                        account=expense.account,
                        amount=expense.amount,
                        description=expense.description,
                        transaction_type="转账",
                        transfer_to_account=income.account,
                    )
                    transfers.append(transfer)

                    to_remove.add(exp_idx)
                    to_remove.add(inc_idx)
                    matched_count += 1
                    matched_income = True
                    break

        # 如果没有匹配到信用卡收入，但有明确目标或描述含还款关键词，仍标记为转账
        if not matched_income and exp_idx not in to_remove:
            # 确定转账目标
            transfer_target = target  # 可能是 "中信信用卡" 等
            if not transfer_target:
                desc = expense.description or ""
                if "还款" in desc or "信用卡" in desc:
                    transfer_target = "信用卡"

            if transfer_target:
                print(f"  转账标记: [{expense.date}] {expense.account} → {transfer_target} "
                      f"¥{expense.amount}")

                transfer = Transaction(
                    date=expense.date,
                    category="转账",
                    subcategory="还款",
                    account=expense.account,
                    amount=expense.amount,
                    description=expense.description,
                    transaction_type="转账",
                    transfer_to_account=transfer_target,
                )
                transfers.append(transfer)

                to_remove.add(exp_idx)
                matched_count += 1

    # 过滤并添加转账记录
    result = [t for i, t in enumerate(transactions) if i not in to_remove]
    result.extend(transfers)

    print(f"转账识别完成：{matched_count} 条识别，删除 {len(to_remove)} 条原记录")
    return result


def sort_transactions(transactions: List[Transaction]) -> List[Transaction]:
    """按日期排序交易记录"""
    def sort_key(t):
        d = parse_date(t.date)
        return d if d else datetime.min

    return sorted(transactions, key=sort_key)


def merge_excel_files(input_dir: str, output_path: str = None):
    """
    合并处理主函数
    """
    print(f"=== 开始合并处理 ===")
    print(f"输入目录: {input_dir}")

    # 查找所有Excel文件
    excel_files = []
    for f in os.listdir(input_dir):
        if f.endswith('.xlsx') and not f.startswith('~'):
            excel_files.append(os.path.join(input_dir, f))

    if not excel_files:
        print("未找到Excel文件")
        return

    print(f"找到 {len(excel_files)} 个Excel文件")

    # 读取所有交易记录
    all_transactions = []
    for file_path in excel_files:
        print(f"  读取: {os.path.basename(file_path)}")
        transactions = read_excel_transactions(file_path)
        all_transactions.extend(transactions)
        print(f"    {len(transactions)} 条记录")

    print(f"\n合计 {len(all_transactions)} 条交易记录")

    # 执行退款对冲
    transactions = reconcile_refunds(all_transactions)

    # 执行转账识别
    transactions = identify_transfers(transactions)

    # 按日期排序
    transactions = sort_transactions(transactions)

    # 生成输出文件
    if output_path is None:
        output_path = os.path.join(input_dir, "merged_账单.xlsx")

    print(f"\n=== 生成合并文件 ===")
    generator = ExcelGenerator()
    generator._create_workbook()
    generator.add_transactions(transactions)
    generator.save(output_path)

    print(f"\n处理完成！")
    print(f"  输入文件: {len(excel_files)} 个")
    print(f"  原始记录: {len(all_transactions)} 条")
    print(f"  最终记录: {len(transactions)} 条")
    print(f"  输出文件: {output_path}")


def main():
    if len(sys.argv) < 2:
        print("用法: python merge.py <输出目录> [合并文件名]")
        print("示例: python merge.py output/")
        print("      python merge.py output/ merged.xlsx")
        sys.exit(1)

    input_dir = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    if not os.path.isdir(input_dir):
        print(f"错误: 目录不存在 {input_dir}")
        sys.exit(1)

    merge_excel_files(input_dir, output_path)


if __name__ == "__main__":
    main()
