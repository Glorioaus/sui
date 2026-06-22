"""
基础解析器模块
定义抽象解析器基类和分类映射逻辑
"""
import json
import os
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from models import Transaction, BankStatement


class BaseParser(ABC):
    """
    基础解析器抽象类
    """

    def __init__(self, config_path: str = None):
        """
        初始化解析器
        """
        self.expense_mapping = self._load_category_mapping("category_mapping.json")
        self.income_mapping = self._load_category_mapping("category_mapping_income.json")

    def _load_category_mapping(self, filename: str) -> dict:
        """
        加载分类映射配置文件
        """
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config",
            filename
        )

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"警告：配置文件 {config_path} 未找到，使用默认分类")
            return {}
        except json.JSONDecodeError as e:
            print(f"警告：配置文件解析失败 {e}，使用默认分类")
            return {}

    def match_category(self, description: str, is_income: bool = False) -> Tuple[str, str]:
        """
        根据交易描述匹配分类和子分类
        返回：(分类, 子分类)

        Args:
            description: 交易描述
            is_income: 是否为收入类型
        """
        if not description:
            if is_income:
                return "其他收入", "意外来钱"
            return "其他杂项", "其他支出"

        description_lower = description.lower()
        mapping = self.income_mapping if is_income else self.expense_mapping

        for category, subcategories in mapping.items():
            for subcategory in subcategories:
                if subcategory.lower() in description_lower:
                    return category, subcategory

        # 默认分类
        if is_income:
            return "其他收入", "意外来钱"
        return "其他杂项", "其他支出"
    
    def parse_date(self, date_str: str) -> str:
        """
        解析日期格式，返回 YYYY-MM-DD 格式
        """
        date_str = date_str.strip()
        
        if len(date_str) == 8:
            return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        elif "-" in date_str:
            parts = date_str.split("-")
            if len(parts) == 3:
                year = parts[0]
                month = parts[1].zfill(2)
                day = parts[2].zfill(2)
                return f"{year}-{month}-{day}"
        
        return date_str
    
    def parse_amount(self, amount_str: str) -> float:
        """
        解析金额字符串，返回浮点数
        """
        try:
            amount_str = amount_str.strip().replace(",", "")
            return float(amount_str)
        except ValueError:
            return 0.0
    
    @abstractmethod
    def parse(self, file_path: str) -> BankStatement:
        """
        解析账单文件，返回银行账单对象
        """
        pass
    
    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """
        返回支持的文件扩展名列表
        """
        pass
