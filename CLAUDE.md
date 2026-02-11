# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 提供在本仓库中工作的指导。

## 常用开发命令

### 安装依赖
```bash
pip install -r requirements.txt
```

### 处理单个文件
```bash
python src/main.py <输入文件> [输出目录]
```
示例：
```bash
python src/main.py input/建行信用卡.csv output/
```

### 批量处理目录
```bash
python src/main.py <输入目录> <输出目录>
```
示例：
```bash
python src/main.py input/ output/
```

## 高层代码架构

### 概述
这是一个银行账单格式转换工具，可将多种银行账单格式（CSV、Excel、PDF）转换为兼容随手记个人理财应用的标准化Excel格式。

### 核心组件

1. **主入口**: `src/main.py`
   - 处理命令行参数
   - 根据文件类型路由到合适的解析器
   - 支持单个文件或批量目录处理

2. **解析器架构**:
   - 抽象基类: `src/base_parser.py`（提供通用工具，如日期解析、金额解析、分类匹配）
   - 银行专用解析器位于 `src/parsers/`:
     - `CCBParser`: 建设银行 (CSV格式)
     - `ABCParser`: 农业银行 (Excel格式)
     - `BOCParser`: 宁波银行 (Excel格式)
     - `CITICParser`: 中信银行 (PDF格式)
   - 每个解析器实现 `parse()` 方法，将原始文件转换为 `BankStatement` 对象

3. **数据模型**: `src/models.py`
   - `Transaction`: 表示单个交易记录，包含日期、分类、子分类、账户、金额和描述
   - `BankStatement`: 包含多个交易记录及元数据（如银行名称、账户信息、账单周期）的容器

4. **Excel生成器**: `src/excel_generator.py`
   - 从 `templates/suiji_template.xls` 加载模板
   - 使用交易数据填充模板
   - 生成兼容随手记导入格式的Excel文件

5. **配置文件**: `config/category_mapping.json`
   - 定义交易描述到分类/子分类的映射
   - 解析器使用此配置自动对交易进行分类

### 数据流
1. 接收输入文件/目录
2. 根据文件扩展名选择合适的解析器
3. 解析器读取原始文件，解析交易记录，并使用配置文件进行分类
4. 解析器返回 `BankStatement` 对象
5. Excel生成器加载模板，使用 `BankStatement` 中的交易数据填充模板
6. 最终Excel文件保存到输出目录