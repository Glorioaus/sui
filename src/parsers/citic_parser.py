"""
中信银行（CITIC）解析器
解析中信银行PDF格式账单
"""
from typing import List
from base_parser import BaseParser
from models import Transaction, BankStatement


class CITICParser(BaseParser):
    """
    中信银行解析器
    """

    def parse(self, file_path: str) -> BankStatement:
        """
        解析中信银行PDF账单文件
        """
        print(f"开始解析中信银行账单：{file_path}")

        transactions = []

        return BankStatement(
            bank_name="中信银行",
            account_name="信用卡",
            account_number="",
            statement_period="",
            transactions=transactions
        )

    def get_supported_extensions(self) -> List[str]:
        """
        返回支持的文件扩展名
        """
        return [".pdf"]
