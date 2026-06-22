"""
招商银行信用卡（CMB）解析器
解析招商银行信用卡PDF格式账单
"""
import re
import pdfplumber
from typing import List, Tuple
from base_parser import BaseParser
from models import Transaction, BankStatement


class CMBParser(BaseParser):
    """
    招商银行信用卡解析器
    支持PDF格式的信用卡月账单

    特殊处理：
    - 信用卡还款 → 跳过
    - 退款（负金额）→ 与消费对冲
    - 优惠/红包 → 收入
    """

    def __init__(self, config_path: str = None):
        super().__init__(config_path)
        self.account_name = "招商信用卡"

    def parse(self, file_path: str) -> BankStatement:
        """
        解析招商信用卡PDF账单文件
        """
        print(f"开始解析招商信用卡账单：{file_path}")

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
            bank_name="招商银行",
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
        for line in lines[:5]:
            # 匹配 "2025年12月" 格式
            match = re.search(r'(\d{4})年(\d{1,2})月', line)
            if match:
                year = match.group(1)
                month = match.group(2).zfill(2)
                return f"{year}-{month}"
        return ""

    def _parse_transactions(self, lines: List[str]) -> List[dict]:
        """
        解析交易记录，返回原始交易列表

        招商银行格式：
        MM/DD MM/DD 描述 金额 卡号后四位 原始金额
        例如：12/06 12/07 财付通-Manner Coffee 25.00 2116 25.00(CN)
        """
        transactions = []
        current_year = None

        # 从头部获取年份
        for line in lines[:10]:
            match = re.search(r'(\d{4})年', line)
            if match:
                current_year = match.group(1)
                break

        if not current_year:
            current_year = "2025"

        for line in lines:
            # 匹配交易行格式: MM/DD MM/DD 描述 金额 卡号后四位 [原始金额]
            # 金额可能是负数（退款）
            match = re.match(
                r'^(\d{1,2}/\d{1,2})\s+(\d{1,2}/\d{1,2})\s+(.+?)\s+([-\d.]+)\s+(\d{4})\s*(.*)?$',
                line
            )
            if match:
                trans_date = match.group(1)  # 交易日
                post_date = match.group(2)   # 记账日
                description = match.group(3).strip()
                amount_str = match.group(4)
                amount = float(amount_str)

                # 解析日期，使用记账日
                month, day = post_date.split('/')
                # 处理跨年情况（12月账单可能包含1月的记账日）
                year = current_year
                if int(month) == 1 and 'year12月' in ''.join(lines[:5]).lower():
                    year = str(int(current_year) + 1)

                date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"

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
        3. 优惠/红包 → 收入
        """
        # 分类交易
        expenses = []  # 正常消费
        refunds = []   # 退款（待对冲）
        incomes = []   # 优惠/红包
        skip_count = 0

        for tx in raw_transactions:
            desc = tx['description']
            amount = tx['amount']

            # 跳过信用卡还款
            if '还款' in desc:
                skip_count += 1
                continue

            # 负金额处理
            if amount < 0:
                # 优惠/红包类 → 收入
                if any(k in desc for k in ['优惠', '红包', '抵扣', '返现', '奖励']):
                    incomes.append(tx)
                else:
                    # 普通退款
                    refunds.append(tx)
                continue

            # 正金额 = 正常消费
            expenses.append(tx)

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
                    amount=abs(ref['amount']),
                    description=ref['description'] + " (未匹配退款)",
                    transaction_type="收入"
                ))

        # 添加优惠/红包收入
        for inc in incomes:
            result.append(Transaction(
                date=inc['date'],
                category="其他收入",
                subcategory="抢红包",
                account=self.account_name,
                amount=abs(inc['amount']),
                description=inc['description'],
                transaction_type="收入"
            ))

        print(f"  跳过还款: {skip_count} 笔")
        print(f"  对冲退款: {len(matched_refund_indices)} 笔")
        print(f"  优惠收入: {len(incomes)} 笔")

        return result

    def _extract_merchant(self, description: str) -> str:
        """
        从描述中提取商户名称
        例如: "财付通-Manner Coffee" -> "Manner Coffee"
              "掌上生活优惠商户-【月度新户专享】肯德基" -> "肯德基"
        """
        # 移除支付渠道前缀
        for prefix in ['财付通-', '支付宝-', '微信支付-', '云闪付-']:
            if prefix in description:
                description = description.replace(prefix, '')
                break

        # 处理掌上生活优惠商户格式
        if '掌上生活优惠商户' in description:
            # 提取最后的商户名（】后面的部分）
            match = re.search(r'】(.+)$', description)
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
            # 餐饮
            if any(k in desc_lower for k in ['肯德基', '麦当劳', 'kfc', 'manner', 'coffee', '咖啡',
                                              '饿了么', '美团', '叮咚', '盒马', '买菜', '餐', '食']):
                return "食品酒水", "早午晚餐"

            # 交通/停车
            if any(k in desc_lower for k in ['停车', '加油', '滴滴', '高德', '打车', '出行', '地铁', '公交']):
                return "行车交通", "停车费" if '停车' in desc_lower else "打车租车"

            # 购物
            if any(k in desc_lower for k in ['淘宝', '天猫', '京东', '拼多多', '小红书']):
                return "居家物业", "日常用品"

            # 会员
            if any(k in desc_lower for k in ['会员', 'vip', '订阅']):
                return "休闲娱乐", "会员"

        # 使用通用分类
        return self.match_category(description, is_income)

    def get_supported_extensions(self) -> List[str]:
        """
        返回支持的文件扩展名
        """
        return [".pdf"]
