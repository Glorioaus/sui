"""
建设银行储蓄卡（CCB Debit）PDF 解析器
解析建设银行「个人活期账户全部交易明细」PDF

PDF 表格列：序号 | 摘要 | 交易日期 | 交易金额 | 账户余额 | 交易地点/附言 | 对方账号与户名
金额带符号：负=支出，正=收入（储蓄卡约定）
"""
import re
import pdfplumber
from typing import List, Optional, Tuple
from base_parser import BaseParser
from models import Transaction, BankStatement


class CCBDebitParser(BaseParser):
    """
    建设银行储蓄卡 PDF 解析器

    用 pdfplumber 的 extract_tables() 提取 7 列表格（折行已合并进单元格），
    每行映射为一条 Transaction：
    - date      ← 交易日期（8 位）
    - amount    ← 交易金额（取 abs）
    - account   ← 建行储蓄卡（与 accounts.json / merge.py DEBIT_ACCOUNTS 对齐）
    - 收入/支出 ← 金额 >= 0 为收入，< 0 为支出，is_income 传给分类映射
    """

    # 支出侧礼金/人情关键词（转出+这些词 → 送礼请客）
    GIFT_KEYWORDS = ["礼金", "生日", "出生", "结婚", "份子", "满月", "升学"]

    def __init__(self, config_path: str = None):
        super().__init__(config_path)
        self.account_name = "建行储蓄卡"

    def parse(self, file_path: str) -> BankStatement:
        """
        解析建设银行储蓄卡 PDF 账单文件
        """
        print(f"开始解析建设银行储蓄卡账单：{file_path}")

        account_number, statement_period = self._parse_header(file_path)
        raw_rows = self._extract_table_rows(file_path)

        transactions: List[Transaction] = []
        for row in raw_rows:
            tx = self._parse_row(row)
            if tx:
                transactions.append(tx)

        print(f"解析完成，共 {len(transactions)} 条交易记录")

        return BankStatement(
            bank_name="建设银行",
            account_name=self.account_name,
            account_number=account_number,
            statement_period=statement_period,
            transactions=transactions,
        )

    def _parse_header(self, file_path: str) -> Tuple[str, str]:
        """
        从首页文本提取账号与起止日期
        格式：卡号/账号:6215... 客户名称:... 起止日期:20260317-20260617
        """
        account_number = ""
        statement_period = ""

        with pdfplumber.open(file_path) as pdf:
            text = pdf.pages[0].extract_text() or ""
            for line in text.split("\n"):
                if not account_number:
                    m = re.search(r"账号[:：]\s*(\d+)", line)
                    if m:
                        account_number = m.group(1)
                if not statement_period:
                    m = re.search(r"起止日期[:：]\s*(\d{8})-(\d{8})", line)
                    if m:
                        s, e = m.group(1), m.group(2)
                        statement_period = (
                            f"{s[:4]}-{s[4:6]}-{s[6:8]} 至 {e[:4]}-{e[4:6]}-{e[6:8]}"
                        )

        return account_number, statement_period

    def _extract_table_rows(self, file_path: str) -> List[list]:
        """
        提取交易表格行（跳过表头与非交易行）
        """
        rows: List[list] = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                for table in (page.extract_tables() or []):
                    for r in table:
                        if not r or r[0] is None:
                            continue
                        first = str(r[0]).strip()
                        # 跳过表头
                        if first == "序号":
                            continue
                        # 交易行：序号为纯数字
                        if not re.match(r"^\d+$", first):
                            continue
                        rows.append(r)
        return rows

    def _parse_row(self, row: list) -> Optional[Transaction]:
        """
        解析单行：[序号, 摘要, 交易日期, 交易金额, 账户余额, 地点/附言, 对方账号户名]
        """
        date_raw = (row[2] or "").strip() if len(row) > 2 else ""
        date_str = self.parse_date(date_raw) if date_raw else ""

        amount = self.parse_amount((row[3] or "0").strip() if len(row) > 3 else "0")
        if amount == 0:
            return None

        summary = (row[1] or "").strip() if len(row) > 1 else ""
        location = (row[5] or "").strip() if len(row) > 5 else ""
        counterparty = (row[6] or "").strip() if len(row) > 6 else ""

        is_income = amount >= 0
        description = self._build_description(summary, location, counterparty)

        category, subcategory = self._apply_rules(summary, location, counterparty, is_income)
        if category is None:
            category, subcategory = self.match_category(description, is_income=is_income)

        return Transaction(
            date=date_str,
            category=category,
            subcategory=subcategory,
            account=self.account_name,
            amount=abs(amount),
            description=description,
            transaction_type="收入" if is_income else "支出",
        )

    def _build_description(self, summary: str, location: str, counterparty: str) -> str:
        """组合描述：摘要 + 附言 + 对方账号户名（跳过空值与占位符）"""
        parts = [p for p in (summary, location, counterparty) if p and p != "/"]
        return " ".join(parts)

    def _apply_rules(self, summary: str, location: str,
                     counterparty: str, is_income: bool) -> Tuple[Optional[str], Optional[str]]:
        """
        建行储蓄卡特殊分类规则（命中返回分类，未命中返回 (None, None) 走 match_category）

        收入：
        - 利息存入 → 职业收入-利息收入
        - 基金赎回/零钱通/余额宝 → 落到 match_category（命中 理财-基金/理财-余额宝）
        - ATM存款/银联入账/其余 → 收入默认（其他收入-意外来钱）

        支出：
        - 跨行转出 + 礼金/人情关键词 → 人情往来-送礼请客
        - 消费（财付通/微信/支付宝等）→ match_category 按商户关键词
        """
        text = f"{summary} {location} {counterparty}".lower()

        if is_income:
            if "利息" in text:
                return "职业收入", "利息收入"
            return None, None  # 其余收入走 match_category（基金/余额宝命中理财，ATM/银联落默认）

        # 支出：高置信度商户关键词（仅"消费"类摘要）
        if summary == "消费":
            merchant_text = f"{location} {counterparty}".lower()
            if any(k in merchant_text for k in (
                "美团", "饿了么", "拉扎斯", "肯德基", "麦当劳", "kfc",
                "瑞幸", "咖啡", "coffee", "叮咚", "盒马", "买菜", "外卖", "食堂",
            )):
                return "食品酒水", "早午晚餐"
            if any(k in merchant_text for k in ("淘宝", "天猫", "京东", "拼多多", "小红书")):
                return "居家物业", "日常用品"
            if any(k in merchant_text for k in ("滴滴", "高德", "打车", "出行", "地铁", "公交")):
                return "行车交通", "打车租车"

        # 转出类 + 礼金人情关键词 → 送礼请客（仅限转账类摘要，避免"生日蛋糕"误判）
        if summary in ("跨行转出", "转出", "转账", "汇出") and any(k in text for k in self.GIFT_KEYWORDS):
            return "人情往来", "送礼请客"
        return None, None  # 其余走 match_category

    def get_supported_extensions(self) -> List[str]:
        return [".pdf"]
