"""
Excel生成器模块
将账单数据生成随手记可导入的Excel文件
"""
import os
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from typing import List
from models import Transaction, BankStatement


class ExcelGenerator:
    """
    Excel生成器类
    生成随手记兼容的Excel格式
    """

    # 随手记导入格式的列定义
    COLUMNS = [
        "交易日期",  # A
        "分类",      # B
        "类型",      # C (收入/支出)
        "子分类",    # D
        "支付账户",  # E
        "金额",      # F
        "成员",      # G
        "商家",      # H
        "项目",      # I
        "备注"       # J
    ]

    def __init__(self, template_path: str = None):
        """
        初始化Excel生成器
        """
        self.template_path = template_path
        self.workbook = None
        self.worksheet = None
        self.start_row = 2

    def _create_workbook(self):
        """
        创建新的工作簿并设置表头
        """
        self.workbook = openpyxl.Workbook()
        self.worksheet = self.workbook.active
        self.worksheet.title = "账单导入"

        # 设置表头样式
        header_font = Font(bold=True)
        header_fill = PatternFill(start_color="DAEEF3", end_color="DAEEF3", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        # 写入表头
        for col, header in enumerate(self.COLUMNS, 1):
            cell = self.worksheet.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = thin_border

        # 设置列宽
        column_widths = [12, 10, 8, 12, 12, 12, 8, 15, 10, 30]
        for col, width in enumerate(column_widths, 1):
            self.worksheet.column_dimensions[openpyxl.utils.get_column_letter(col)].width = width

        print("创建新工作簿完成")

    def add_transaction(self, transaction: Transaction):
        """
        添加交易记录到Excel
        """
        if self.worksheet is None:
            raise Exception("请先创建工作簿")

        row = self.start_row

        # 列映射
        # A: 交易日期
        self.worksheet.cell(row=row, column=1, value=transaction.date)
        # B: 分类
        self.worksheet.cell(row=row, column=2, value=transaction.category)
        # C: 类型
        self.worksheet.cell(row=row, column=3, value=transaction.transaction_type)
        # D: 子分类
        self.worksheet.cell(row=row, column=4, value=transaction.subcategory)
        # E: 支付账户
        self.worksheet.cell(row=row, column=5, value=transaction.account)
        # F: 金额
        self.worksheet.cell(row=row, column=6, value=transaction.amount)
        # G: 成员 (空)
        self.worksheet.cell(row=row, column=7, value="")
        # H: 商家
        merchant = getattr(transaction, 'merchant', None) or ""
        self.worksheet.cell(row=row, column=8, value=merchant)
        # I: 项目 (空)
        self.worksheet.cell(row=row, column=9, value="")
        # J: 备注 - 转账类型时显示目标账户
        if transaction.transaction_type == "转账" and transaction.transfer_to_account:
            remark = f"→ {transaction.transfer_to_account}"
            if transaction.description:
                remark = f"{remark} | {transaction.description}"
        else:
            remark = transaction.description
        self.worksheet.cell(row=row, column=10, value=remark)

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

        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        try:
            self.workbook.save(output_path)
            print(f"成功保存文件：{output_path}")
        except Exception as e:
            raise Exception(f"保存文件失败：{e}")

    def generate(self, statement: BankStatement, output_path: str):
        """
        生成随手记Excel文件
        """
        self._create_workbook()
        self.add_transactions(statement.transactions)
        self.save(output_path)
        print(f"生成完成，共 {len(statement.transactions)} 条记录")
