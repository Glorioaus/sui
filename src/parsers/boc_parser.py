"""
宁波银行（BOC）解析器
解析宁波银行Excel格式账单
"""
from typing import List
from base_parser import BaseParser
from models import BankStatement


class BOCParser(BaseParser):
    """
    宁波银行解析器

    当前尚未实现具体 Excel 格式解析。保留路由入口是为了后续接入样例后实现，
    但不能静默返回空交易，否则会误导用户以为转换成功。
    """
    
    def parse(self, file_path: str) -> BankStatement:
        """
        解析宁波银行Excel账单文件
        """
        print(f"开始解析宁波银行账单：{file_path}")

        raise NotImplementedError(
            "宁波银行 Excel 解析器尚未实现。请提供一份脱敏样例后再补充 BOCParser。"
        )
    
    def get_supported_extensions(self) -> List[str]:
        """
        返回支持的文件扩展名
        """
        return [".xlsx", ".xls"]
