"""
农业银行（ABC）解析器
解析农业银行PDF格式账单
"""
import re
import pdfplumber
from typing import List, Optional, Tuple
from base_parser import BaseParser
from models import Transaction, BankStatement


class ABCParser(BaseParser):
    """
    农业银行解析器
    支持PDF格式的个人活期交易明细清单
    """

    def __init__(self, config_path: str = None):
        super().__init__(config_path)
        self.account_name = "农行储蓄卡"

    def parse(self, file_path: str) -> BankStatement:
        """
        解析农业银行PDF账单文件
        """
        print(f"开始解析农业银行账单：{file_path}")

        # 提取PDF文本
        raw_lines = self._extract_pdf_text(file_path)

        # 解析账户信息
        account_number, statement_period = self._parse_header(raw_lines)

        # 合并多行交易记录
        merged_lines = self._merge_transaction_lines(raw_lines)

        # 解析每条交易
        transactions = []
        for line in merged_lines:
            tx = self._parse_transaction_line(line)
            if tx:
                transactions.append(tx)

        print(f"解析完成，共 {len(transactions)} 条交易记录")

        return BankStatement(
            bank_name="农业银行",
            account_name=self.account_name,
            account_number=account_number,
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

    def _parse_header(self, lines: List[str]) -> Tuple[str, str]:
        """
        解析头部信息，提取账号和日期范围
        """
        account_number = ""
        statement_period = ""

        for line in lines[:10]:  # 只检查前10行
            # 匹配账号: 账户：6228480318046711970 或 账户:6228...
            account_match = re.search(r'账户[：:]\s*(\d+)', line)
            if account_match:
                account_number = account_match.group(1)

            # 匹配日期范围: 起止日期：20251110-20260212
            period_match = re.search(r'(\d{8})-(\d{8})', line)
            if period_match:
                start = period_match.group(1)
                end = period_match.group(2)
                statement_period = f"{start[:4]}-{start[4:6]}-{start[6:8]} 至 {end[:4]}-{end[4:6]}-{end[6:8]}"

        return account_number, statement_period

    def _merge_transaction_lines(self, lines: List[str]) -> List[str]:
        """
        合并多行交易记录
        以8位日期开头的行为新交易，其他行追加到上一条
        """
        merged = []
        current_line = ""

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 检查是否是交易行开头（8位日期）
            if re.match(r'^\d{8}\s', line):
                if current_line:
                    merged.append(current_line)
                current_line = line
            elif current_line:
                # 追加到当前行
                current_line += " " + line

        # 添加最后一条
        if current_line:
            merged.append(current_line)

        return merged

    def _parse_transaction_line(self, line: str) -> Optional[Transaction]:
        """
        解析单条交易记录

        格式示例:
        20251110 191619 转支 -15.00 21978.18 0051325048423775 1598069932 自动扣费还款-招行
        20251120 代发工资 -2754.36 21513.44 39602057400003997 1202072435

        字段: 日期 [时间] 摘要 金额 余额 对方信息...
        """
        # 匹配日期
        date_match = re.match(r'^(\d{8})', line)
        if not date_match:
            return None

        date_str = date_match.group(1)
        date_formatted = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"

        # 剩余部分
        rest = line[8:].strip()

        # 尝试匹配时间（6位数字）
        time_match = re.match(r'^(\d{6})\s+', rest)
        if time_match:
            rest = rest[7:].strip()

        # 匹配金额（带+/-符号的数字）
        amount_match = re.search(r'([+-]?\d+\.\d{2})', rest)
        if not amount_match:
            return None

        amount_str = amount_match.group(1)
        amount = float(amount_str)

        # 确定交易类型
        is_income = amount > 0
        if is_income:
            transaction_type = "收入"
        else:
            transaction_type = "支出"
            amount = abs(amount)

        # 提取摘要（金额之前的部分）
        amount_pos = rest.find(amount_str)
        summary = rest[:amount_pos].strip() if amount_pos > 0 else ""

        # 提取备注（金额之后的部分）
        after_amount = rest[amount_pos + len(amount_str):].strip()
        # 跳过余额（下一个数字）
        balance_match = re.match(r'^[\s]*[\d,]+\.\d{2}\s*', after_amount)
        if balance_match:
            after_amount = after_amount[balance_match.end():].strip()

        # 组合描述
        description = f"{summary} {after_amount}".strip()

        # 应用特殊分类规则
        category, subcategory = self._apply_special_rules(summary, description, is_income)

        # 如果特殊规则没有匹配，使用通用匹配
        if category is None:
            category, subcategory = self.match_category(description, is_income)

        return Transaction(
            date=date_formatted,
            category=category,
            subcategory=subcategory,
            account=self.account_name,
            amount=amount,
            description=description,
            transaction_type=transaction_type
        )

    def _apply_special_rules(self, summary: str, description: str, is_income: bool) -> Tuple[Optional[str], Optional[str]]:
        """
        应用特殊分类规则
        返回 (None, None) 表示没有匹配的特殊规则
        """
        text = (summary + " " + description).lower()

        if is_income:
            # === 收入类规则 ===
            # 工资/代发
            if "工资" in text or "代发" in text or "薪" in text:
                return "职业收入", "工资收入"

            # 公积金
            if "公积金" in text or "gjj" in text:
                return "职业收入", "公积金转出"

            # 利息
            if "利息" in text or "结息" in text:
                return "职业收入", "利息收入"

            # 退款
            if "退款" in text or "退还" in text:
                return "其他收入", "退款"

            # 报销
            if "报销" in text:
                return "其他收入", "报销"

            # 转账收入（来自特定人）
            if "张颖" in text or "小张" in text:
                return "张颖转入", "其他"

        else:
            # === 支出类规则 ===
            # 贷款还款
            if "贷款" in text or "按揭" in text or "房贷" in text:
                return "金融保险", "按揭还款"

            # 公积金代扣
            if "公积金" in text or "gjj" in text:
                return "居家物业", "五险一金"

            # 微信相关
            if "微信" in text:
                return "账单导入", "微信账单导入"

            # 支付宝相关
            if "支付宝" in text:
                return "账单导入", "支付宝账单导入"

            # 短信费
            if "短信费" in text:
                return "交流通讯", "手机费"

            # 银行手续费
            if "手续费" in text:
                return "金融保险", "银行手续"

        return None, None

    def get_supported_extensions(self) -> List[str]:
        """
        返回支持的文件扩展名
        """
        return [".pdf"]
