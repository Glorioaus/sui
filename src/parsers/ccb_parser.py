"""
建设银行（CCB）解析器
解析建设银行CSV格式账单
"""
import csv
from typing import List
from base_parser import BaseParser
from models import Transaction, BankStatement


class CCBParser(BaseParser):
    """
    建设银行解析器
    """
    
    def parse(self, file_path: str) -> BankStatement:
        """
        解析建设银行CSV账单文件
        """
        print(f"开始解析建设银行账单：{file_path}")
        
        transactions = []
        
        try:
            with open(file_path, "r", encoding="gbk") as f:
                reader = csv.reader(f)
                rows = list(reader)
                
                for row in rows:
                    if len(row) < 6:
                        continue
                    
                    date_str = row[0].strip()
                    amount_str = row[5].strip()
                    description = row[6].strip() if len(row) > 6 else ""
                    
                    if not date_str or not amount_str:
                        continue
                    
                    date = self.parse_date(date_str)
                    amount = self.parse_amount(amount_str)
                    category, subcategory = self.match_category(description)
                    
                    transaction = Transaction(
                        date=date,
                        category=category,
                        subcategory=subcategory,
                        account="建设银行信用卡",
                        amount=amount,
                        description=description,
                        transaction_type="支出" if amount < 0 else "收入"
                    )
                    
                    transactions.append(transaction)
        
        except Exception as e:
            print(f"解析失败：{e}")
        
        return BankStatement(
            bank_name="建设银行",
            account_name="信用卡",
            account_number="",
            statement_period="",
            transactions=transactions
        )
    
    def get_supported_extensions(self) -> List[str]:
        """
        返回支持的文件扩展名
        """
        return [".csv"]
