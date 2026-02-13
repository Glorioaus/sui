"""
建设银行信用卡（CCB Credit）解析器
解析建设银行信用卡PDF格式账单
"""
import re
import pdfplumber
from typing import List, Tuple
from base_parser import BaseParser
from models import Transaction, BankStatement


class CCBCreditParser(BaseParser):
    """
    建设银行信用卡解析器
    支持PDF格式的信用卡月账单

    特殊处理：
    - 信用卡还款（负金额，含"还款"）→ 跳过
    - 退款（负金额）→ 与消费对冲
    """

    def __init__(self, config_path: str = None):
        super().__init__(config_path)
        self.account_name = "建行信用卡"

    def parse(self, file_path: str) -> BankStatement:
        """
        解析建行信用卡PDF账单文件
        """
        print(f"开始解析建行信用卡账单：{file_path}")

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
            bank_name="建设银行",
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
        格式: 账单周期 Statement Cycle 2025/10/24-2025/11/23
        """
        for line in lines:
            # 匹配账单周期
            match = re.search(r'Statement Cycle\s+(\d{4})/(\d{2})/(\d{2})-(\d{4})/(\d{2})/(\d{2})', line)
            if match:
                return f"{match.group(1)}-{match.group(2)}"
            # 备用匹配
            match = re.search(r'(\d{4})/(\d{2})/\d{2}-\d{4}/(\d{2})/\d{2}', line)
            if match:
                return f"{match.group(1)}-{match.group(3)}"
        return ""

    def _parse_transactions(self, lines: List[str]) -> List[dict]:
        """
        解析交易记录，返回原始交易列表
        格式: 2025-11-05 2025-11-05 5427 描述 CNY 金额 CNY 金额
        """
        transactions = []
        in_transaction_section = False

        for line in lines:
            # 检测交易明细开始
            if '[人民币账户]' in line or 'RMB Account' in line:
                in_transaction_section = True
                continue

            # 检测交易明细结束
            if '结束' in line and 'End' in line:
                break

            if not in_transaction_section:
                continue

            # 匹配交易行格式: YYYY-MM-DD YYYY-MM-DD 卡号后四位 描述 CNY 金额 CNY 金额
            match = re.match(
                r'^(\d{4}-\d{2}-\d{2})\s+\d{4}-\d{2}-\d{2}\s+\d{4}\s+(.+?)\s+CNY\s+([-\d.]+)\s+CNY\s+([-\d.]+)$',
                line.strip()
            )
            if match:
                date_str = match.group(1)
                description = match.group(2).strip()
                amount_str = match.group(3)
                amount = float(amount_str)

                transactions.append({
                    'date': date_str,
                    'description': description,
                    'amount': amount,
                    'original_line': line
                })

        return transactions

    def _process_refunds(self, raw_transactions: List[dict]) -> List[Transaction]:
        """
        处理退款对冲逻辑：
        1. 信用卡还款 → 跳过
        2. 退款 → 尝试与同商户消费对冲
        """
        # 分类交易
        expenses = []  # 正常消费
        refunds = []   # 退款（待对冲）
        skip_count = 0

        for tx in raw_transactions:
            desc = tx['description']
            amount = tx['amount']

            # 跳过信用卡还款（负金额 + 含"还款"）
            if amount < 0 and '还款' in desc:
                skip_count += 1
                continue

            # 正常消费（正金额）
            if amount > 0:
                expenses.append(tx)
            else:
                # 负金额（退款）
                refunds.append(tx)

        # 对冲退款
        matched_expense_indices = set()
        matched_refund_indices = set()

        for ri, refund in enumerate(refunds):
            refund_amount = abs(refund['amount'])
            refund_merchant = self._extract_merchant(refund['description'])

            # 查找同商户、同金额的消费
            for ei, expense in enumerate(expenses):
                if ei in matched_expense_indices:
                    continue

                expense_merchant = self._extract_merchant(expense['description'])
                if (abs(expense['amount'] - refund_amount) < 0.01 and
                    refund_merchant and expense_merchant and
                    refund_merchant == expense_merchant):
                    # 对冲成功
                    matched_expense_indices.add(ei)
                    matched_refund_indices.add(ri)
                    print(f"  对冲: {expense['description']} {expense['amount']} <-> 退款 {refund['amount']}")
                    break

        # 生成最终交易列表
        result = []

        # 添加未对冲的消费
        for i, exp in enumerate(expenses):
            if i not in matched_expense_indices:
                category, subcategory = self._categorize(exp['description'], False)
                merchant = self._extract_merchant(exp['description'])
                result.append(Transaction(
                    date=exp['date'],
                    category=category,
                    subcategory=subcategory,
                    account=self.account_name,
                    amount=abs(exp['amount']),
                    description=exp['description'],
                    transaction_type="支出",
                    merchant=merchant
                ))

        # 添加未对冲的退款（作为收入）
        for i, ref in enumerate(refunds):
            if i not in matched_refund_indices:
                merchant = self._extract_merchant(ref['description'])
                result.append(Transaction(
                    date=ref['date'],
                    category="其他收入",
                    subcategory="退款",
                    account=self.account_name,
                    amount=abs(ref['amount']),
                    description=ref['description'] + " (未匹配退款)",
                    transaction_type="收入",
                    merchant=merchant
                ))

        print(f"  跳过还款: {skip_count} 笔")
        print(f"  对冲退款: {len(matched_refund_indices)} 笔")

        return result

    def _extract_merchant(self, description: str) -> str:
        """
        从描述中提取商户名称
        例如: "支付宝-叮咚买菜" -> "叮咚买菜"
              "北京 跨行消费 京东商城平台商户" -> "京东商城平台商户"
        """
        # 移除支付渠道前缀
        for prefix in ['支付宝-支付宝-消费-', '支付宝-', '微信支付-', '财付通-', '云闪付-']:
            if prefix in description:
                description = description.split(prefix)[-1]
                break

        # 移除地点和交易类型前缀（如 "北京 跨行消费"）
        match = re.search(r'(?:跨行消费|消费)\s+(.+)$', description)
        if match:
            description = match.group(1)

        # 移除 "退款" "退货" 等后缀
        description = re.sub(r'退款|退货|撤销', '', description)

        return description.strip()

    def _categorize(self, description: str, is_income: bool) -> Tuple[str, str]:
        """
        根据描述分类
        """
        desc_lower = description.lower()

        if not is_income:
            # 餐饮/外卖
            if any(k in desc_lower for k in ['饿了么', '拉扎斯', '美团', '三快', '叮咚', '盒马', '买菜', '餐', '食品']):
                return "食品酒水", "早午晚餐"

            # 交通
            if any(k in desc_lower for k in ['滴滴', '高德', '打车', '出行', '地铁', '公交']):
                return "行车交通", "打车租车"

            # 购物
            if any(k in desc_lower for k in ['淘宝', '天猫', '京东', '拼多多', '小红书']):
                return "购物消费", "网购"

            # 医疗
            if any(k in desc_lower for k in ['药房', '药店', '医院', '诊所']):
                return "医疗保健", "药品费"

            # 汽车
            if any(k in desc_lower for k in ['汽车', '车用', '加油']):
                return "行车交通", "汽车用品"

        # 使用通用分类
        return self.match_category(description, is_income)

    def get_supported_extensions(self) -> List[str]:
        """
        返回支持的文件扩展名
        """
        return [".pdf"]
