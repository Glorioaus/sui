"""
宁波银行（BOC）解析器
解析宁波银行Excel格式账单
"""
from typing import List
from base_parser import BaseParser
from models import Transaction, BankStatement


class BOCParser(BaseParser):
    """
    宁波银行解析器
    """
    
    def parse(self, file_path: str) -> BankStatement:
        """
        解析宁波银行Excel账单文件
        """
        print(f"开始解析宁波银行账单：{file_path}")
        
        transactions = []
        
        return BankStatement(
            bank_name="宁波银行",
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
