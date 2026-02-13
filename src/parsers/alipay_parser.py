"""
支付宝（Alipay）解析器
解析支付宝交易明细CSV格式
"""
import re
import pandas as pd
from typing import List, Optional, Tuple
from base_parser import BaseParser
from models import Transaction, BankStatement


class AlipayParser(BaseParser):
    """
    支付宝解析器
    支持CSV格式的支付宝交易明细
    """

    # 银行卡关键词（用于识别银行卡支付）
    BANK_KEYWORDS = ["银行", "信用卡"]

    # 支付宝钱包支付方式
    WALLET_METHODS = ["余额", "余额宝", "花呗", "借呗"]

    # 需要跳过的交易状态
    SKIP_STATUS = ["交易关闭"]

    # 退款状态
    REFUND_STATUS = ["退款成功"]

    # 等同于交易成功的状态
    SUCCESS_STATUS = ["交易成功", "等待确认收货", "还款成功"]

    def __init__(self, config_path: str = None):
        super().__init__(config_path)
        self.account_name = "支付宝"

    def parse(self, file_path: str) -> BankStatement:
        """
        解析支付宝CSV账单文件
        """
        print(f"开始解析支付宝账单：{file_path}")

        # 读取CSV，跳过头部信息行（前24行）
        df = pd.read_csv(file_path, encoding='gbk', skiprows=24)

        # 清理列名（去除空格和末尾逗号产生的空列）
        df.columns = [col.strip() for col in df.columns if col.strip()]

        # 解析账单周期
        statement_period = self._extract_period(file_path)

        transactions = []
        skipped_closed = 0
        skipped_bank = 0
        refund_as_income = 0
        family_pay_count = 0

        # 收集所有交易用于退款匹配
        all_rows = list(df.iterrows())

        # 第一遍：收集消费记录用于退款匹配
        expense_records = {}  # {(对方, 金额): row_data}
        for _, row in all_rows:
            status = str(row.get('交易状态', '')).strip()
            income_expense = str(row.get('收/支', '')).strip()
            if status in self.SUCCESS_STATUS and income_expense == '支出':
                counterparty = str(row.get('交易对方', '')).strip()
                amount = self._parse_amount(row.get('金额', 0))
                key = (counterparty, amount)
                if key not in expense_records:
                    expense_records[key] = row

        # 第二遍：处理所有交易
        for _, row in all_rows:
            status = str(row.get('交易状态', '')).strip()
            income_expense = str(row.get('收/支', '')).strip()

            # 跳过交易关闭
            if status in self.SKIP_STATUS:
                skipped_closed += 1
                continue

            # 跳过不计收支（银行卡直接交易，避免与银行账单重复）
            if income_expense == '不计收支':
                continue

            # 处理退款
            if status in self.REFUND_STATUS:
                result = self._handle_refund(row, expense_records)
                if result:
                    if result[0]:  # 有匹配的消费，已对冲
                        continue
                    else:  # 无匹配，作为收入
                        transactions.append(result[1])
                        refund_as_income += 1
                continue

            # 等待确认收货等同于交易成功
            if status == '等待确认收货':
                status = '交易成功'

            result = self._parse_row(row)
            if result is None:
                continue

            tx, is_skipped, is_family_pay = result
            if is_skipped:
                skipped_bank += 1
                continue
            if is_family_pay:
                family_pay_count += 1

            transactions.append(tx)

        print(f"解析完成：{len(transactions)} 条记录")
        print(f"  - 跳过交易关闭：{skipped_closed} 条")
        print(f"  - 跳过银行卡支付：{skipped_bank} 条（避免重复）")
        print(f"  - 退款转收入：{refund_as_income} 条")
        print(f"  - 亲友代付标记：{family_pay_count} 条")

        return BankStatement(
            bank_name="支付宝",
            account_name=self.account_name,
            account_number="",
            statement_period=statement_period,
            transactions=transactions
        )

    def _extract_period(self, file_path: str) -> str:
        """从文件名提取账单周期"""
        match = re.search(r'\((\d{8})-(\d{8})\)', file_path)
        if match:
            start = match.group(1)
            end = match.group(2)
            return f"{start[:4]}-{start[4:6]}-{start[6:8]} 至 {end[:4]}-{end[4:6]}-{end[6:8]}"
        return ""

    def _parse_amount(self, amount_val) -> float:
        """解析金额"""
        if pd.isna(amount_val):
            return 0.0
        try:
            return float(str(amount_val).strip())
        except ValueError:
            return 0.0

    def _handle_refund(self, row, expense_records) -> Optional[Tuple[bool, Optional[Transaction]]]:
        """
        处理退款记录
        返回: (是否匹配到消费, Transaction或None)
        """
        counterparty = str(row.get('交易对方', '')).strip()
        amount = self._parse_amount(row.get('金额', 0))
        key = (counterparty, amount)

        # 尝试匹配消费记录
        if key in expense_records:
            # 找到匹配，对冲删除
            del expense_records[key]
            return (True, None)

        # 无匹配，作为收入记录
        trade_time = row.get('交易时间', '')
        if isinstance(trade_time, str):
            date_str = trade_time.split()[0]
        else:
            date_str = str(trade_time)[:10]

        tx = Transaction(
            date=date_str,
            category="其他收入",
            subcategory="退款",
            account=self.account_name,
            amount=amount,
            description=f"退款 {counterparty}",
            transaction_type="收入",
            merchant=counterparty
        )
        return (False, tx)

    def _parse_row(self, row) -> Optional[Tuple[Transaction, bool, bool]]:
        """
        解析单行交易记录
        返回: (Transaction, is_skipped, is_family_pay) 或 None
        """
        # 获取基本字段
        trade_time = row.get('交易时间', '')
        trade_type = str(row.get('交易分类', '')).strip()
        counterparty = str(row.get('交易对方', '')).strip()
        product = str(row.get('商品说明', '')).strip()
        income_expense = str(row.get('收/支', '')).strip()
        amount = self._parse_amount(row.get('金额', 0))
        payment_method = str(row.get('收/付款方式', '')).strip()
        order_no = str(row.get('交易订单号', '')).strip()

        # 跳过无效行
        if not trade_time or pd.isna(trade_time):
            return None

        # 解析日期
        if isinstance(trade_time, str):
            date_str = trade_time.split()[0]
        else:
            date_str = str(trade_time)[:10]

        # 跳过金额为0的记录
        if amount == 0:
            return None

        # 跳过不计收支
        if income_expense == '不计收支':
            return None

        # 检查是否是银行卡支付
        is_bank_payment = self._is_bank_payment(payment_method)

        # 检查是否是"亲友代付"
        is_family_pay = "亲友代付" in trade_type

        # 亲友代付：记录为特殊标记，用于merge匹配银行卡账单
        if is_family_pay and income_expense == '支出':
            bank_name = self._extract_bank_name(payment_method) if is_bank_payment else None
            user_name = counterparty if counterparty else "亲友"
            tx = Transaction(
                date=date_str,
                category="__FAMILY_CARD__",  # 特殊标记
                subcategory=user_name,  # 记录使用者
                account=bank_name or "__ANY_BANK__",  # 银行名或通配
                amount=amount,
                description=f"亲友代付 {user_name} {product}".strip(),
                transaction_type="__MARKER__",  # 特殊标记
                merchant=user_name
            )
            return tx, False, True

        # 如果是银行卡支付的普通支出，跳过（避免重复）
        if is_bank_payment and income_expense == '支出':
            return None, True, False

        # 确定交易类型
        if income_expense == '支出':
            transaction_type = "支出"
            is_income = False
        elif income_expense == '收入':
            transaction_type = "收入"
            is_income = True
        else:
            return None

        # 组合描述
        description = product if product else trade_type
        if counterparty and counterparty != '/':
            description = f"{counterparty} {description}"

        # 应用分类规则
        category, subcategory = self._apply_alipay_rules(
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
            merchant=counterparty if counterparty != '/' else ""
        )
        return tx, False, False

    def _is_bank_payment(self, payment_method: str) -> bool:
        """检查是否是银行卡支付"""
        if not payment_method or payment_method == '/':
            return False
        for keyword in self.BANK_KEYWORDS:
            if keyword in payment_method:
                return True
        return False

    def _extract_bank_name(self, payment_method: str) -> Optional[str]:
        """从支付方式提取银行名称"""
        # 格式: "中信银行信用卡(2359)" -> "中信信用卡"
        if "信用卡" in payment_method:
            match = re.match(r'(.+?)银行信用卡', payment_method)
            if match:
                return f"{match.group(1)}信用卡"
        elif "储蓄卡" in payment_method:
            match = re.match(r'(.+?)银行', payment_method)
            if match:
                return match.group(1)
        return None

    def _apply_alipay_rules(self, trade_type: str, counterparty: str,
                           product: str, is_income: bool) -> Tuple[Optional[str], Optional[str]]:
        """
        应用支付宝特殊分类规则
        """
        text = f"{trade_type} {counterparty} {product}".lower()

        if is_income:
            # === 收入类规则 ===
            if "红包" in text:
                return "其他收入", "抢红包"
            if "退款" in text:
                return "其他收入", "退款"
            if "转账" in text:
                return "其他收入", "支付宝转账收入"
            if "余额宝" in text or "理财" in text:
                return "理财", "理财收益"

        else:
            # === 支出类规则 ===
            if "红包" in text:
                return "人情往来", "送礼请客"
            if "转账" in text:
                return "人情往来", "送礼请客"
            if "外卖" in text or "饿了么" in text or "美团" in text:
                return "食品酒水", "早午晚餐"
            if "淘宝" in text or "天猫" in text:
                return "购物消费", "网购"
            if "话费" in text or "充值" in text:
                return "交流通讯", "手机费"
            if "电费" in text or "水费" in text or "燃气" in text:
                return "居家物业", "水电煤"
            if "还款" in text or "信用卡" in text:
                return "转账", "还款"
            if "投资" in text or "基金" in text:
                return "理财", "基金投资"

        return None, None

    def get_supported_extensions(self) -> List[str]:
        """返回支持的文件扩展名"""
        return [".csv"]
