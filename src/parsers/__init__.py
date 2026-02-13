"""
银行解析器模块
"""
from .ccb_parser import CCBParser
from .ccb_credit_parser import CCBCreditParser
from .abc_parser import ABCParser
from .boc_parser import BOCParser
from .citic_parser import CITICParser
from .cmb_parser import CMBParser
from .wechat_parser import WeChatParser
from .alipay_parser import AlipayParser

__all__ = ["CCBParser", "CCBCreditParser", "ABCParser", "BOCParser", "CITICParser", "CMBParser", "WeChatParser", "AlipayParser"]
