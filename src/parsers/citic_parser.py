"""
中信银行信用卡（CITIC）解析器
解析中信银行信用卡PDF格式账单
"""
import re
import pdfplumber
from typing import List, Tuple
from base_parser import BaseParser
from models import Transaction, BankStatement


class CITICParser(BaseParser):
    """
    中信银行信用卡解析器
    支持PDF格式的信用卡月账单

    金额规则（与招商相反）：
    - 负金额 = 支出（消费）或优惠/返现（收入）
    - 正金额 = 退款

    特殊处理：
    - 信用卡还款 → 跳过
    - 退款（正金额）→ 与消费对冲
    - 优惠/返现（负金额）→ 收入
    """

    def __init__(self, config_path: str = None):
        super().__init__(config_path)
        self.account_name = "中信信用卡"

    def parse(self, file_path: str) -> BankStatement:
        """
        解析中信信用卡PDF账单文件
        """
        print(f"开始解析中信信用卡账单：{file_path}")

        # 提取PDF文本
        raw_lines = self._extract_pdf_text(file_path)

        # 解析账户信息
        statement_period = self._parse_header(raw_lines)

        # 解析交易记录
        raw_transactions = self._parse_transactions(raw_lines)

        # 处理退款对冲
        transactions = self._process_refunds(raw_transactions)

        print(f"解析完成，共 {len(transactions)} 条交易记录（已对冲退款）")

        return BankStatement(
            bank_name="中信银行",
            account_name=self.account_name,
            account_number="",
            statement_period=statement_period,
            transactions=transactions
        )

    def _extract_pdf_text(self, file_path: str) -> List[str]:
        """
        从PDF提取文本行
        """
        all_lines = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    lines = text.split('\n')
                    all_lines.extend(lines)
        return all_lines

    def _parse_header(self, lines: List[str]) -> str:
        """
        解析头部信息，提取账单周期
        """
        for line in lines[:10]:
            # 匹配 "账单日 2026-01-23" 格式
            if '账单日' in line:
                match = re.search(r'(\d{4})-(\d{2})-(\d{2})', line)
                if match:
                    year = match.group(1)
                    month = match.group(2)
                    return f"{year}-{month}"
        return ""

    def _parse_transactions(self, lines: List[str]) -> List[dict]:
        """
        解析交易记录，返回原始交易列表

        中信银行格式：
        交易日 银行记账日 卡号后四位 交易描述 交易货币/金额 记账货币/金额
        例如：20251214 20260114 2359 美团 CNY -87.50 CNY -87.50

        描述可能跨多行，需要特殊处理
        """
        transactions = []
        pending_description = ""

        for line in lines:
            # 跳过页码行
            if re.match(r'^第\s*\d+\s*页', line):
                continue

            # 匹配交易行格式: YYYYMMDD YYYYMMDD 4位卡号 描述 CNY 金额 CNY 金额
            # 描述可能在当前行，也可能在上一行
            match = re.match(
                r'^(\d{8})\s+(\d{8})\s+(\d{4})\s+(.+?)\s*CNY\s*([-\d.]+)\s+CNY\s*([-\d.]+)$',
                line
            )

            if match:
                trans_date = match.group(1)  # 交易日
                post_date = match.group(2)   # 记账日
                description = match.group(4).strip()
                amount_str = match.group(5)
                amount = float(amount_str)

                # 合并上一行的描述前缀
                if pending_description:
                    description = pending_description + description
                    pending_description = ""

                # 解析日期（使用记账日）
                year = post_date[:4]
                month = post_date[4:6]
                day = post_date[6:8]
                date_str = f"{year}-{month}-{day}"

                transactions.append({
                    'date': date_str,
                    'description': description,
                    'amount': amount,
                    'original_line': line
                })
            else:
                # 检查是否是描述的延续（下一行开头）
                # 如果当前行不是交易行，但看起来像描述的一部分
                if not re.match(r'^\d{8}', line) and not any(x in line for x in ['账单日', 'Statement', '卡号', '第', '页', '【', '】', 'CNY交易', '交易日', 'Trans Date']):
                    # 可能是上一笔交易描述的延续或下一笔的前缀
                    # 由于PDF提取的特点，描述可能在交易行之前
                    clean_line = line.strip()
                    if clean_line and len(clean_line) > 2:
                        # 检查下一行是否会是交易行
                        pending_description = clean_line

        return transactions

    def _process_refunds(self, raw_transactions: List[dict]) -> List[Transaction]:
        """
        处理退款对冲逻辑：
        1. 信用卡还款 → 跳过
        2. 优惠/返现（负金额）→ 收入
        3. 退款（正金额）→ 尝试与同商户消费对冲
        4. 返现取消（正金额）→ 与对应的返现对冲
        """
        # 分类交易
        expenses = []      # 正常消费（负金额）
        refunds = []       # 退款（正金额，待对冲）
        incomes = []       # 优惠/返现（负金额但是收入）
        cashback_cancels = []  # 返现取消（正金额）
        skip_count = 0

        # 优惠/返现关键词
        income_keywords = ['精彩笔笔返', '返现金', '指定银联手机Pay返现', '现金奖励']
        # 返现取消关键词
        cancel_keywords = ['返现取消', '撤销支付券']

        for tx in raw_transactions:
            desc = tx['description']
            amount = tx['amount']

            # 跳过信用卡还款
            if '还款' in desc:
                skip_count += 1
                print(f"  跳过还款: {desc} {amount}")
                continue

            # 负金额处理
            if amount < 0:
                # 检查是否是优惠/返现
                if any(k in desc for k in income_keywords):
                    incomes.append(tx)
                else:
                    # 正常消费
                    expenses.append(tx)
                continue

            # 正金额处理
            if amount > 0:
                # 检查是否是返现取消
                if any(k in desc for k in cancel_keywords):
                    cashback_cancels.append(tx)
                else:
                    # 普通退款
                    refunds.append(tx)

        # 对冲退款
        matched_expense_indices = set()
        matched_refund_indices = set()

        for ri, refund in enumerate(refunds):
            refund_amount = refund['amount']  # 正金额
            refund_merchant = self._extract_merchant(refund['description'])

            # 查找同商户、同金额的消费（消费是负金额）
            for ei, expense in enumerate(expenses):
                if ei in matched_expense_indices:
                    continue

                expense_merchant = self._extract_merchant(expense['description'])
                expense_amount = abs(expense['amount'])  # 转为正数比较

                if (abs(expense_amount - refund_amount) < 0.01 and
                    refund_merchant and expense_merchant and
                    refund_merchant == expense_merchant):
                    # 对冲成功
                    matched_expense_indices.add(ei)
                    matched_refund_indices.add(ri)
                    print(f"  对冲: {expense['description']} {expense['amount']} <-> 退款 {refund['amount']}")
                    break

        # 对冲返现取消（与收入对冲）
        matched_income_indices = set()
        matched_cancel_indices = set()

        for ci, cancel in enumerate(cashback_cancels):
            cancel_amount = cancel['amount']  # 正金额

            # 查找同金额的返现收入（负金额）
            for ii, income in enumerate(incomes):
                if ii in matched_income_indices:
                    continue

                income_amount = abs(income['amount'])

                if abs(income_amount - cancel_amount) < 0.01:
                    # 对冲成功
                    matched_income_indices.add(ii)
                    matched_cancel_indices.add(ci)
                    print(f"  对冲返现: {income['description']} {income['amount']} <-> 取消 {cancel['amount']}")
                    break

        # 生成最终交易列表
        result = []

        # 添加未对冲的消费
        for i, exp in enumerate(expenses):
            if i not in matched_expense_indices:
                category, subcategory = self._categorize(exp['description'], False)
                result.append(Transaction(
                    date=exp['date'],
                    category=category,
                    subcategory=subcategory,
                    account=self.account_name,
                    amount=abs(exp['amount']),
                    description=exp['description'],
                    transaction_type="支出"
                ))

        # 添加未对冲的退款（作为收入）
        for i, ref in enumerate(refunds):
            if i not in matched_refund_indices:
                result.append(Transaction(
                    date=ref['date'],
                    category="其他收入",
                    subcategory="退款",
                    account=self.account_name,
                    amount=ref['amount'],
                    description=ref['description'] + " (未匹配退款)",
                    transaction_type="收入"
                ))

        # 添加未对冲的优惠/返现收入
        for i, inc in enumerate(incomes):
            if i not in matched_income_indices:
                result.append(Transaction(
                    date=inc['date'],
                    category="其他收入",
                    subcategory="抢红包",
                    account=self.account_name,
                    amount=abs(inc['amount']),
                    description=inc['description'],
                    transaction_type="收入"
                ))

        # 添加未对冲的返现取消（作为支出）
        for i, cancel in enumerate(cashback_cancels):
            if i not in matched_cancel_indices:
                result.append(Transaction(
                    date=cancel['date'],
                    category="其他杂项",
                    subcategory="其他支出",
                    account=self.account_name,
                    amount=cancel['amount'],
                    description=cancel['description'] + " (未匹配取消)",
                    transaction_type="支出"
                ))

        print(f"  跳过还款: {skip_count} 笔")
        print(f"  对冲退款: {len(matched_refund_indices)} 笔")
        print(f"  对冲返现取消: {len(matched_cancel_indices)} 笔")
        print(f"  优惠收入: {len(incomes) - len(matched_income_indices)} 笔")

        return result

    def _extract_merchant(self, description: str) -> str:
        """
        从描述中提取商户名称
        例如: "支付宝－上海拉扎斯信息科技有限公司" -> "上海拉扎斯信息科技有限公司"
              "财付通－Babycare" -> "Babycare"
        """
        # 移除支付渠道前缀
        for prefix in ['支付宝－', '支付宝-', '财付通－', '财付通-', '微信支付－', 'Huawei Pay-']:
            if description.startswith(prefix):
                description = description[len(prefix):]
                break

        # 移除 "退款" "退货" 等后缀
        description = re.sub(r'退款|退货|撤销', '', description)

        return description.strip()

    def _categorize(self, description: str, is_income: bool) -> Tuple[str, str]:
        """
        根据描述分类
        """
        desc_lower = description.lower()

        if not is_income:
            # 餐饮（饿了么、美团等）
            if any(k in desc_lower for k in ['拉扎斯', '美团', '饿了么', '肯德基', '麦当劳', 'kfc', '瑞幸', '咖啡', 'coffee']):
                return "食品酒水", "早午晚餐"

            # 购物平台
            if any(k in desc_lower for k in ['拼多多', '淘宝', '天猫', '京东']):
                return "居家物业", "日常用品"

            # 母婴
            if any(k in desc_lower for k in ['母婴', 'babycare', '童心']):
                return "居家物业", "日常用品"

        # 使用通用分类
        return self.match_category(description, is_income)

    def get_supported_extensions(self) -> List[str]:
        """
        返回支持的文件扩展名
        """
        return [".pdf"]
