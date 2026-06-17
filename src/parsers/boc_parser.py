"""
宁波银行（BOC）储蓄卡 PDF 解析器
解析宁波银行「交易流水」PDF（行式格式，无表格框线，extract_tables 返回空）

列：日期 | 摘要 | 币种 | 交易金额 | 余额 | 对方户名 | 对方账号/卡号 | 对方开户行 | 交易备注 | 交易柜员
金额带符号：负=支出，正=收入（储蓄卡约定）
"""
import re
import pdfplumber
from typing import List, Optional, Tuple
from base_parser import BaseParser
from models import Transaction, BankStatement


class BOCParser(BaseParser):
    """
    宁波银行储蓄卡 PDF 解析器（交易流水）

    extract_tables() 对该 PDF 返回空（无框线），改用行式解析：
    以 YYYY-MM-DD 开头且含「摘要 币种 金额 余额」的行作为交易行；
    续行（如对方户名折行的「司」「账」）合并到上一条。
    """

    # 交易行：日期 摘要 币种 金额 余额 [对方户名 账号 开户行 备注 柜员]
    TX_RE = re.compile(
        r"^(\d{4}-\d{2}-\d{2})\s+(\S+)\s+\S+\s+(-?[\d,]+\.\d{2})\s+[\d,]+\.\d{2}\s*(.*)$"
    )

    # 分隔符行（全是破折号/连字符/空格）
    SEPARATOR_RE = re.compile(r"^[—–\-\s]+$")

    # 非交易前缀（标题/表头/统计/账户信息）
    SKIP_PREFIXES = (
        "宁波银行", "户 名", "户名", "币 种", "币种", "打印日期",
        "合并统计", "日期 摘要", "人民币 ", "第", "温馨提示",
        "本交易流水", "生成时间",
    )

    # 支出侧礼金/人情关键词
    GIFT_KEYWORDS = ["礼金", "满月", "生日", "出生", "结婚", "份子", "送节", "过节"]

    def __init__(self, config_path: str = None):
        super().__init__(config_path)
        self.account_name = "宁波银行"

    def parse(self, file_path: str) -> BankStatement:
        """
        解析宁波银行储蓄卡 PDF 账单文件
        """
        print(f"开始解析宁波银行账单：{file_path}")

        account_number, statement_period = self._parse_header(file_path)
        lines = self._extract_lines(file_path)
        merged = self._merge_continuation(lines)

        transactions: List[Transaction] = []
        for line in merged:
            tx = self._parse_line(line)
            if tx:
                transactions.append(tx)

        print(f"解析完成，共 {len(transactions)} 条交易记录")

        return BankStatement(
            bank_name="宁波银行",
            account_name=self.account_name,
            account_number=account_number,
            statement_period=statement_period,
            transactions=transactions,
        )

    def _parse_header(self, file_path: str) -> Tuple[str, str]:
        """
        从首页文本提取卡号与账单周期
        格式：户 名: 马燥 卡 号: 621418... / 2026-03-18 — 2026-06-16
        """
        account_number = ""
        statement_period = ""

        with pdfplumber.open(file_path) as pdf:
            text = pdf.pages[0].extract_text() or ""
            for line in text.split("\n"):
                if not account_number:
                    m = re.search(r"卡\s*号[:：]\s*(\d+)", line)
                    if m:
                        account_number = m.group(1)
                if not statement_period:
                    m = re.search(r"(\d{4}-\d{2}-\d{2})\s*[—–\-]+\s*(\d{4}-\d{2}-\d{2})", line)
                    if m:
                        statement_period = f"{m.group(1)} 至 {m.group(2)}"

        return account_number, statement_period

    def _extract_lines(self, file_path: str) -> List[str]:
        """提取所有页的非空文本行"""
        all_lines: List[str] = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                all_lines.extend((page.extract_text() or "").split("\n"))
        return [line.strip() for line in all_lines if line.strip()]

    def _merge_continuation(self, lines: List[str]) -> List[str]:
        """
        合并续行：不以日期开头的行作为上一条交易的延续（处理对方户名/摘要折行）。
        跳过分隔符、标题、表头、统计、页脚等非交易行。
        """
        merged: List[str] = []
        for line in lines:
            if self.SEPARATOR_RE.match(line):
                continue
            if self.TX_RE.match(line):
                merged.append(line)
                continue
            # 非交易行：跳过标题/表头/统计/账户信息
            if any(line.startswith(p) for p in self.SKIP_PREFIXES):
                continue
            # 否则视为上一条交易的续行：仅合并短折行（对方户名/摘要尾部，通常 1-3 字）；
            # 长行（页脚/免责声明）直接丢弃，避免污染描述
            if merged and len(line) <= 10:
                merged[-1] = merged[-1].rstrip() + line
        return merged

    def _parse_line(self, line: str) -> Optional[Transaction]:
        """解析单条交易行"""
        m = self.TX_RE.match(line)
        if not m:
            return None

        date_str = m.group(1)
        summary = m.group(2)
        amount = self.parse_amount(m.group(3))
        if amount == 0:
            return None

        rest_tokens = self._clean_rest((m.group(4) or "").strip())
        description = self._build_description(summary, rest_tokens)

        is_income = amount >= 0
        category, subcategory = self._apply_rules(summary, rest_tokens, is_income)
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

    def _clean_rest(self, rest: str) -> List[str]:
        """清理金额后的剩余字段：去掉占位 '--'/'—' 和纯数字账号/卡号"""
        tokens = []
        for tok in rest.split():
            if tok in ("--", "—", "-"):
                continue
            if re.fullmatch(r"\d{6,}", tok):  # 账号/卡号
                continue
            tokens.append(tok)
        return tokens

    def _build_description(self, summary: str, rest_tokens: List[str]) -> str:
        return " ".join([summary, *rest_tokens]).strip()

    def _apply_rules(self, summary: str, rest_tokens: List[str],
                     is_income: bool) -> Tuple[Optional[str], Optional[str]]:
        """
        宁波银行特殊分类规则（命中返回分类，未命中返回 (None, None) 走 match_category）

        收入：
        - 利息 → 职业收入-利息收入
        - 对方户名含 张颖/小张 → 张颖转入-其他
        - 备注/对方含 礼金/满月/生日/结婚 → 其他收入-礼金收入
        - 其余（现金存入/银联转入/网银转账）→ 收入默认

        支出：
        - 银转证（银行转证券）/ 云闪付转账 等投资转出 → match_category（暂落默认支出）
        - 备注/对方含 礼金/人情关键词 → 人情往来-送礼请客
        - 其余 → match_category
        """
        text = f"{summary} {' '.join(rest_tokens)}".lower()

        if is_income:
            if "利息" in text:
                return "职业收入", "利息收入"
            if any(k in text for k in ("张颖", "小张")):
                return "张颖转入", "其他"
            if any(k in text for k in ("礼金", "满月", "生日", "结婚", "送节", "过节", "端午")):
                return "其他收入", "礼金收入"
            return None, None

        # 支出
        if any(k in text for k in self.GIFT_KEYWORDS):
            return "人情往来", "送礼请客"
        return None, None

    def get_supported_extensions(self) -> List[str]:
        return [".pdf"]
