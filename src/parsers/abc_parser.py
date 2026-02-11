"""
农业银行（ABC）解析器
解析农业银行Excel格式账单
"""
from typing import List
from base_parser import BaseParser
from models import Transaction, BankStatement


class ABCParser(BaseParser):
    """
    农业银行解析器
    """
    
    def parse(self, file_path: str) -> BankStatement:
        """
        解析农业银行Excel账单文件
        """
        print(f"开始解析农业银行账单：{file_path}")
        
        transactions = []
        
        return BankStatement(
            bank_name="农业银行",
            account_name="",
            account_number="",
            statement_period="",
            transactions=transactions
        )
    
    def get_supported_extensions(self) -> List[str]:
        """
        返回支持的文件扩展名
        """
        return [".xlsx", ".xls"]
