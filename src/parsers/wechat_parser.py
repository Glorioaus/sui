"""
微信支付（WeChat）解析器
解析微信支付账单Excel格式
"""
import re
import pandas as pd
from typing import List, Optional, Tuple
from base_parser import BaseParser
from models import Transaction, BankStatement


class WeChatParser(BaseParser):
    """
    微信支付解析器
    支持Excel格式的微信支付账单流水
    """

    # 银行卡关键词（用于识别银行卡支付）
    BANK_KEYWORDS = ["银行", "信用卡"]

    # 微信钱包支付方式（这些交易需要保留）
    WALLET_METHODS = ["零钱", "零钱通"]

    def __init__(self, config_path: str = None):
        super().__init__(config_path)
        self.account_name = "微信"

    def parse(self, file_path: str) -> BankStatement:
        """
        解析微信支付Excel账单文件
        """
        print(f"开始解析微信支付账单：{file_path}")

        # 读取Excel，跳过头部信息行
        df = pd.read_excel(file_path, skiprows=16)

        # 解析账单周期
        statement_period = self._extract_period(file_path)

        transactions = []
        skipped_bank = 0
        transfer_count = 0

        for _, row in df.iterrows():
            result = self._parse_row(row)
            if result is None:
                continue

            tx, is_skipped, is_transfer = result
            if is_skipped:
                skipped_bank += 1
                continue
            if is_transfer:
                transfer_count += 1

            transactions.append(tx)

        print(f"解析完成：{len(transactions)} 条记录")
        print(f"  - 跳过银行卡支付：{skipped_bank} 条（避免重复）")
        print(f"  - 识别为转账：{transfer_count} 条")

        return BankStatement(
            bank_name="微信支付",
            account_name=self.account_name,
            account_number="",
            statement_period=statement_period,
            transactions=transactions
        )

    def _extract_period(self, file_path: str) -> str:
        """从文件名提取账单周期"""
        # 文件名格式: 微信支付账单流水文件(20251112-20260212)_20260212155122.xlsx
        match = re.search(r'\((\d{8})-(\d{8})\)', file_path)
        if match:
            start = match.group(1)
            end = match.group(2)
            return f"{start[:4]}-{start[4:6]}-{start[6:8]} 至 {end[:4]}-{end[4:6]}-{end[6:8]}"
        return ""

    def _parse_row(self, row) -> Optional[Tuple[Transaction, bool, bool]]:
        """
        解析单行交易记录
        返回: (Transaction, is_skipped, is_transfer) 或 None
        """
        # 获取基本字段
        trade_time = row.get('交易时间', '')
        trade_type = str(row.get('交易类型', ''))
        counterparty = str(row.get('交易对方', ''))
        product = str(row.get('商品', ''))
        income_expense = str(row.get('收/支', ''))
        amount_str = str(row.get('金额(元)', ''))
        payment_method = str(row.get('支付方式', ''))
        status = str(row.get('当前状态', ''))
        remark = str(row.get('备注', ''))

        # 跳过无效行
        if not trade_time or pd.isna(trade_time):
            return None

        # 解析日期
        if isinstance(trade_time, str):
            date_str = trade_time.split()[0]
        else:
            date_str = trade_time.strftime("%Y-%m-%d")

        # 解析金额（移除¥符号）
        amount = self._parse_amount(amount_str)
        if amount == 0:
            return None

        # 检查是否是银行卡支付
        is_bank_payment = self._is_bank_payment(payment_method)

        # 检查是否是"转入零钱通"类型的转账
        is_transfer_to_wallet = "转入零钱通" in trade_type or "转入零钱" in trade_type

        # 检查是否是"亲属卡交易"
        is_family_card = "亲属卡" in trade_type

        # 亲属卡交易：记录为特殊标记，用于merge匹配银行卡账单
        # 不管支付方式是什么，都记录标记（因为实际扣款一定在银行卡）
        if is_family_card and income_expense == "支出":
            # 尝试从支付方式提取银行名，如果是零钱通则留空（merge时匹配所有银行卡）
            bank_name = self._extract_bank_name(payment_method) if is_bank_payment else None
            user_name = counterparty if counterparty and counterparty != "/" else "亲属"
            tx = Transaction(
                date=date_str,
                category="__FAMILY_CARD__",  # 特殊标记
                subcategory=user_name,  # 记录使用者（如"张颖"）
                account=bank_name or "__ANY_BANK__",  # 银行名或通配
                amount=amount,
                description=f"亲属卡交易 {user_name}".strip(),
                transaction_type="__MARKER__",  # 特殊标记
                merchant=user_name
            )
            return tx, False, False

        # 如果是银行卡支付的普通支出，跳过（避免重复）
        if is_bank_payment and income_expense == "支出":
            return None, True, False

        # 处理银行卡转入微信钱包（标记为转账）
        if is_transfer_to_wallet and is_bank_payment:
            source_bank = self._extract_bank_name(payment_method)
            tx = Transaction(
                date=date_str,
                category="转账",
                subcategory="转入微信",
                account=source_bank or payment_method,
                amount=amount,
                description=f"{trade_type}".strip(),
                transaction_type="转账",
                transfer_to_account="微信",
                merchant=""
            )
            return tx, False, True

        # 确定交易类型
        if income_expense == "支出":
            transaction_type = "支出"
            is_income = False
        elif income_expense == "收入":
            transaction_type = "收入"
            is_income = True
        else:
            # "/" 通常是内部转账或系统操作，跳过
            return None

        # 组合描述
        description = f"{trade_type}"
        if product and product != "/":
            description += f" {product}"
        if counterparty and counterparty != "/":
            description = f"{counterparty} {description}"

        # 应用分类规则
        category, subcategory = self._apply_wechat_rules(
            trade_type, counterparty, product, is_income
        )

        # 如果特殊规则没有匹配，使用通用匹配
        if category is None:
            category, subcategory = self.match_category(description, is_income)

        tx = Transaction(
            date=date_str,
            category=category,
            subcategory=subcategory,
            account=self.account_name,
            amount=amount,
            description=description,
            transaction_type=transaction_type,
            merchant=counterparty if counterparty != "/" else ""
        )
        return tx, False, False

    def _parse_amount(self, amount_str: str) -> float:
        """解析金额字符串"""
        if not amount_str or amount_str == "/" or pd.isna(amount_str):
            return 0.0
        # 移除¥符号和其他非数字字符
        cleaned = re.sub(r'[^\d.]', '', str(amount_str))
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    def _is_bank_payment(self, payment_method: str) -> bool:
        """检查是否是银行卡支付"""
        if not payment_method or payment_method == "/":
            return False
        for keyword in self.BANK_KEYWORDS:
            if keyword in payment_method:
                return True
        return False

    def _extract_bank_name(self, payment_method: str) -> Optional[str]:
        """从支付方式提取银行名称"""
        # 格式: "农业银行储蓄卡(1970)" -> "农业银行"
        # 或: "中信银行信用卡(2359)" -> "中信信用卡"
        if "储蓄卡" in payment_method:
            match = re.match(r'(.+?)储蓄卡', payment_method)
            if match:
                return match.group(1)
        elif "信用卡" in payment_method:
            match = re.match(r'(.+?)银行信用卡', payment_method)
            if match:
                return f"{match.group(1)}信用卡"
        return None

    def _apply_wechat_rules(self, trade_type: str, counterparty: str,
                           product: str, is_income: bool) -> Tuple[Optional[str], Optional[str]]:
        """
        应用微信特殊分类规则
        """
        text = f"{trade_type} {counterparty} {product}".lower()

        if is_income:
            # === 收入类规则 ===
            if "红包" in text:
                return "其他收入", "抢红包"
            if "退款" in text:
                return "其他收入", "退款"
            if "转账" in text:
                return "其他收入", "微信转账收入"

        else:
            # === 支出类规则 ===
            if "红包" in text:
                return "人情往来", "送礼请客"
            if "转账" in text:
                return "人情往来", "送礼请客"
            if "食堂" in text or "餐" in text:
                return "食品酒水", "早午晚餐"
            if "停车" in text:
                return "行车交通", "停车费"
            if "滴滴" in text or "出行" in text or "打车" in text:
                return "行车交通", "打车租车"
            if "美团" in text or "饿了么" in text or "外卖" in text:
                return "食品酒水", "早午晚餐"

        return None, None

    def get_supported_extensions(self) -> List[str]:
        """返回支持的文件扩展名"""
        return [".xlsx", ".xls"]
