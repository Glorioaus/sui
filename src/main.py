"""
主程序入口
处理账单文件并生成随手记Excel
"""
import os
import sys
import re
from typing import Optional
from parsers import CCBParser, ABCParser, BOCParser, CITICParser, CMBParser
from parsers.spdb_parser import SPDBParser
from excel_generator import ExcelGenerator
from models import BankStatement


def check_virtual_environment():
    """
    检查是否在虚拟环境中运行
    """
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        return

    print("=" * 60)
    print("警告：未在虚拟环境中运行")
    print("推荐使用虚拟环境：python -m venv .venv")
    print("=" * 60)
    print()

    try:
        response = input("是否继续？(y/N): ")
        if response.lower() not in ['y', 'yes']:
            sys.exit(0)
    except KeyboardInterrupt:
        sys.exit(0)


# 文件名匹配规则
# 格式: (正则模式, 解析器类, 描述)
# 注意：顺序很重要，特定银行模式应在通用模式之前
FILE_PATTERNS = [
    (r'农行.*\.pdf$', ABCParser, "农业银行储蓄卡"),
    (r'浦发.*\.pdf$', SPDBParser, "浦发信用卡"),
    (r'招商.*\.pdf$', CMBParser, "招商信用卡"),
    (r'中信.*\.pdf$', CITICParser, "中信银行"),
    (r'.*账单.*\.pdf$', SPDBParser, "浦发信用卡(账单)"),  # 通用账单格式放最后
    (r'建行.*\.csv$', CCBParser, "建设银行"),
    (r'宁波.*\.xlsx?$', BOCParser, "宁波银行"),
]


class SuiConverter:
    """
    随手记转换器主类
    """

    def __init__(self):
        self.generator = ExcelGenerator()

    def get_parser_for_file(self, file_path: str):
        """
        根据文件名匹配规则获取解析器
        """
        filename = os.path.basename(file_path).lower()

        # 按文件名规则匹配
        for pattern, parser_class, desc in FILE_PATTERNS:
            if re.search(pattern, filename, re.IGNORECASE):
                print(f"识别为: {desc}")
                return parser_class()

        # 未匹配，提示用户
        print(f"无法识别文件类型: {filename}")
        print("支持的命名格式:")
        print("  - 农行*.pdf     → 农业银行储蓄卡")
        print("  - 浦发*.pdf     → 浦发信用卡")
        print("  - *账单*.pdf    → 浦发信用卡")
        print("  - 招商*.pdf     → 招商信用卡")
        print("  - 中信*.pdf     → 中信银行")
        print("  - 建行*.csv     → 建设银行")
        print("  - 宁波*.xlsx    → 宁波银行")
        return None

    def process_file(self, input_path: str, output_path: str) -> bool:
        """
        处理单个账单文件
        """
        print(f"\n{'=' * 60}")
        print(f"处理文件: {os.path.basename(input_path)}")
        print(f"{'=' * 60}")

        parser = self.get_parser_for_file(input_path)

        if parser is None:
            return False

        try:
            statement = parser.parse(input_path)

            if statement.get_transaction_count() == 0:
                print("警告: 未找到任何交易记录")
                return False

            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            self.generator.generate(statement, output_path)
            return True

        except Exception as e:
            print(f"处理失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def process_directory(self, input_dir: str, output_dir: str):
        """
        批量处理目录中的账单文件
        """
        print(f"\n{'=' * 60}")
        print(f"批量处理目录: {input_dir}")
        print(f"{'=' * 60}")

        if not os.path.exists(input_dir):
            print("错误: 输入目录不存在")
            return

        os.makedirs(output_dir, exist_ok=True)

        success_count = 0
        fail_count = 0
        skip_count = 0

        for filename in os.listdir(input_dir):
            file_path = os.path.join(input_dir, filename)

            if not os.path.isfile(file_path):
                continue

            # 跳过隐藏文件和临时文件
            if filename.startswith('.') or filename.startswith('~'):
                continue

            base_name = os.path.splitext(filename)[0]
            output_filename = f"{base_name}_随手记.xlsx"
            output_path = os.path.join(output_dir, output_filename)

            result = self.process_file(file_path, output_path)
            if result:
                success_count += 1
            elif result is False:
                fail_count += 1
            else:
                skip_count += 1

        print(f"\n{'=' * 60}")
        print(f"处理完成: 成功 {success_count}, 失败 {fail_count}, 跳过 {skip_count}")
        print(f"{'=' * 60}")


def main():
    """
    主函数
    """
    check_virtual_environment()

    if len(sys.argv) < 2:
        print("随手记账单格式转换工具")
        print("=" * 40)
        print("\n使用方法:")
        print("  python src/main.py <输入文件/目录> [输出目录]")
        print("\n示例:")
        print("  python src/main.py input/农行-xxx.pdf output/")
        print("  python src/main.py input/ output/")
        print("\n文件命名规则:")
        print("  农行*.pdf     → 农业银行储蓄卡")
        print("  浦发*.pdf     → 浦发信用卡")
        print("  *账单*.pdf    → 浦发信用卡")
        print("  招商*.pdf     → 招商信用卡")
        print("  中信*.pdf     → 中信银行")
        print("  建行*.csv     → 建设银行")
        print("  宁波*.xlsx    → 宁波银行")
        return

    input_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output"

    converter = SuiConverter()

    if os.path.isfile(input_path):
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_filename = f"{base_name}_随手记.xlsx"
        output_path = os.path.join(output_dir, output_filename)
        converter.process_file(input_path, output_path)
    elif os.path.isdir(input_path):
        converter.process_directory(input_path, output_dir)
    else:
        print(f"错误: {input_path} 不是有效的文件或目录")


if __name__ == "__main__":
    main()
