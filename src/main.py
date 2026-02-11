"""
主程序入口
处理账单文件并生成随手记Excel
"""
import os
import sys
from typing import List
from parsers import CCBParser, ABCParser, BOCParser, CITICParser
from excel_generator import ExcelGenerator


def check_virtual_environment():
    """
    检查是否在虚拟环境中运行
    提示用户使用虚拟环境进行开发
    """
    # 检查当前Python解释器是否在虚拟环境中
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        return

    # 如果不在虚拟环境中，给出警告提示
    print("="*80)
    print("⚠️  警告：未在虚拟环境中运行")
    print("为了避免依赖版本冲突，推荐使用虚拟环境进行开发！")
    print("\n请按照以下步骤创建并激活虚拟环境：")
    print("1. 创建虚拟环境：python -m venv .venv")
    print("2. 激活虚拟环境：")
    print("   PowerShell： .venv\Scripts\Activate.ps1")
    print("   CMD： .venv\Scripts\activate.bat")
    print("3. 安装依赖：pip install -r requirements.txt")
    print("\n详细说明请参考：SETUP.md")
    print("="*80)
    print()

    # 询问用户是否继续
    try:
        response = input("是否继续在全局环境中运行？(y/N): ")
        if response.lower() not in ['y', 'yes']:
            sys.exit(0)
    except KeyboardInterrupt:
        sys.exit(0)


class SuiConverter:
    """
    随手记转换器主类
    """
    
    def __init__(self):
        """
        初始化转换器
        """
        self.parsers = [
            CCBParser(),
            ABCParser(),
            BOCParser(),
            CITICParser()
        ]
        self.generator = ExcelGenerator()
    
    def get_parser_for_file(self, file_path: str):
        """
        根据文件扩展名获取对应的解析器
        """
        file_ext = os.path.splitext(file_path)[1].lower()
        
        for parser in self.parsers:
            if file_ext in parser.get_supported_extensions():
                return parser
        
        return None
    
    def process_file(self, input_path: str, output_path: str) -> bool:
        """
        处理单个账单文件
        """
        print(f"\n{'='*60}")
        print(f"处理文件：{input_path}")
        print(f"{'='*60}")
        
        parser = self.get_parser_for_file(input_path)
        
        if parser is None:
            print(f"错误：不支持的文件格式")
            return False
        
        try:
            statement = parser.parse(input_path)
            
            if statement.get_transaction_count() == 0:
                print(f"警告：未找到任何交易记录")
                return False
            
            self.generator.generate(statement, output_path)
            return True
            
        except Exception as e:
            print(f"处理失败：{e}")
            return False
    
    def process_directory(self, input_dir: str, output_dir: str):
        """
        批量处理目录中的账单文件
        """
        print(f"\n{'='*60}")
        print(f"批量处理目录：{input_dir}")
        print(f"{'='*60}")
        
        if not os.path.exists(input_dir):
            print(f"错误：输入目录不存在")
            return
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"创建输出目录：{output_dir}")
        
        success_count = 0
        fail_count = 0
        
        for filename in os.listdir(input_dir):
            file_path = os.path.join(input_dir, filename)
            
            if os.path.isfile(file_path):
                base_name = os.path.splitext(filename)[0]
                output_filename = f"{base_name}_随手记.xlsx"
                output_path = os.path.join(output_dir, output_filename)
                
                if self.process_file(file_path, output_path):
                    success_count += 1
                else:
                    fail_count += 1
        
        print(f"\n{'='*60}")
        print(f"处理完成：成功 {success_count} 个，失败 {fail_count} 个")
        print(f"{'='*60}")


def main():
    """
    主函数
    """
    # 检查虚拟环境
    check_virtual_environment()

    converter = SuiConverter()

    if len(sys.argv) < 2:
        print("随手记账单格式转换工具")
        print("=" * 40)
        print("\n使用方法：")
        print("  python src/main.py <输入文件/目录> [输出目录]")
        print("\n示例：")
        print("  python src/main.py input/ output/")
        print("  python src/main.py input/建行信用卡.csv output/")
        print("\n说明：")
        print("  - 输入可以是单个文件或目录")
        print("  - 支持的格式：.csv, .xlsx, .xls, .pdf")
        print("  - 输出目录默认为 output/")
        return
    
    input_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output"
    
    if os.path.isfile(input_path):
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_filename = f"{base_name}_随手记.xlsx"
        output_path = os.path.join(output_dir, output_filename)
        converter = SuiConverter()
        converter.process_file(input_path, output_path)
    elif os.path.isdir(input_path):
        converter = SuiConverter()
        converter.process_directory(input_path, output_dir)
    else:
        print(f"错误：{input_path} 不是有效的文件或目录")


if __name__ == "__main__":
    main()
