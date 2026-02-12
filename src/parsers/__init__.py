"""
银行解析器模块
"""
from .ccb_parser import CCBParser
from .abc_parser import ABCParser
from .boc_parser import BOCParser
from .citic_parser import CITICParser
from .cmb_parser import CMBParser

__all__ = ["CCBParser", "ABCParser", "BOCParser", "CITICParser", "CMBParser"]
