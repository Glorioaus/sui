"""
Excel生成器模块
将账单数据生成随手记可导入的Excel文件
"""
import os
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from typing import List
from models import Transaction, BankStatement


class ExcelGenerator:
    """
    Excel生成器类
    """
    
    def __init__(self, template_path: str = None):
        """
        初始化Excel生成器
        """
        self.template_path = template_path or self._get_default_template_path()
        self.workbook = None
        self.worksheet = None
        self.start_row = 2
    
    def _get_default_template_path(self) -> str:
        """
        获取默认模板路径
        """
        return os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "..",
            "templates",
            "suiji_template.xls"
        )
    
    def load_template(self):
        """
        加载随手记模板文件
        """
        try:
            self.workbook = openpyxl.load_workbook(self.template_path)
            self.worksheet = self.workbook.active
            print(f"成功加载模板文件：{self.template_path}")
            print(f"工作表名称：{self.worksheet.title}")
            print(f"表头行：{[cell.value for cell in self.worksheet[1]]}")
        except FileNotFoundError:
            raise FileNotFoundError(f"模板文件未找到：{self.template_path}")
        except Exception as e:
            raise Exception(f"加载模板文件失败：{e}")
    
    def add_transaction(self, transaction: Transaction):
        """
        添加交易记录到Excel
        """
        if self.worksheet is None:
            raise Exception("请先加载模板文件")
        
        row = self.start_row
        
        self.worksheet.cell(row=row, column=1, value=transaction.date)
        self.worksheet.cell(row=row, column=2, value=transaction.category)
        self.worksheet.cell(row=row, column=3, value=transaction.subcategory)
        self.worksheet.cell(row=row, column=4, value=transaction.account)
        self.worksheet.cell(row=row, column=5, value=transaction.amount)
        self.worksheet.cell(row=row, column=6, value=transaction.description)
        
        self.start_row += 1
    
    def add_transactions(self, transactions: List[Transaction]):
        """
        批量添加交易记录
        """
        for transaction in transactions:
            self.add_transaction(transaction)
    
    def save(self, output_path: str):
        """
        保存Excel文件
        """
        if self.workbook is None:
            raise Exception("没有工作簿可保存")
        
        try:
            self.workbook.save(output_path)
            print(f"成功保存文件：{output_path}")
        except Exception as e:
            raise Exception(f"保存文件失败：{e}")
    
    def generate(self, statement: BankStatement, output_path: str):
        """
        生成随手记Excel文件
        """
        self.load_template()
        self.add_transactions(statement.transactions)
        self.save(output_path)
        print(f"生成完成，共 {len(statement.transactions)} 条记录")
