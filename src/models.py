"""
数据模型定义模块
定义统一的账单数据结构
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Transaction:
    """
    交易记录数据模型
    """
    date: str
    category: str
    subcategory: str
    account: str
    amount: float
    description: str
    transaction_type: str = "支出"
    
    def to_dict(self) -> dict:
        """
        转换为字典格式
        """
        return {
            "date": self.date,
            "category": self.category,
            "subcategory": self.subcategory,
            "account": self.account,
            "amount": self.amount,
            "description": self.description,
            "transaction_type": self.transaction_type
        }


@dataclass
class BankStatement:
    """
    银行账单数据模型
    """
    bank_name: str
    account_name: str
    account_number: str
    statement_period: str
    transactions: list[Transaction]
    
    def add_transaction(self, transaction: Transaction):
        """
        添加交易记录
        """
        self.transactions.append(transaction)
    
    def get_transaction_count(self) -> int:
        """
        获取交易记录数量
        """
        return len(self.transactions)
