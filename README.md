# 随手记账单格式转换工具

将各种银行卡账单（PDF、Excel、CSV）转换为随手记可导入的Excel格式。

## 功能特点

- 支持多种银行账单格式（CSV、Excel、PDF）
- 自动识别银行类型和交易类型（收入/支出）
- 批量处理账单文件
- 分离的收入/支出分类配置
- 生成符合随手记导入格式的Excel文件（xlsx）

## 项目结构

```
sui/
├── README.md
├── CLAUDE.md              # Claude Code 开发指南
├── requirements.txt
├── .python-version        # pyenv 版本配置
├── config/
│   ├── category_mapping.json        # 支出分类映射
│   ├── category_mapping_income.json # 收入分类映射
│   └── accounts.json                # 账户名称映射
├── src/
│   ├── __init__.py
│   ├── models.py              # 数据模型定义
│   ├── base_parser.py         # 基础解析器类
│   ├── parsers/               # 各银行解析器
│   │   ├── __init__.py
│   │   ├── ccb_parser.py      # 建设银行
│   │   ├── abc_parser.py      # 农业银行 (PDF)
│   │   ├── boc_parser.py      # 宁波银行
│   │   └── citic_parser.py    # 中信银行
│   ├── excel_generator.py     # Excel生成器
│   └── main.py                # 主程序入口
├── templates/
│   └── template.xls           # 随手记导入模板（参考）
├── input/                     # 输入账单目录
└── output/                    # 输出Excel目录
```

## 环境搭建

### 推荐：使用 pyenv-win 管理 Python 版本

```powershell
# 安装 Python 3.11
pyenv install 3.11.9
pyenv local 3.11.9

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
.\.venv\Scripts\Activate.ps1  # PowerShell
# 或
.venv\Scripts\activate.bat    # CMD

# 配置国内镜像（可选，解决 SSL 问题）
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
pip config set global.trusted-host mirrors.aliyun.com

# 安装依赖
pip install -r requirements.txt
```

### 验证安装
```bash
python src/main.py --help
```

## 使用方法

### 1. 配置分类映射

**支出分类** `config/category_mapping.json`：
```json
{
  "食品酒水": ["早午晚餐", "饮料", "买菜", "烟酒茶", "水果零食"],
  "居家物业": ["日常用品", "超市", "五险一金", "水电煤气", "房租"],
  "行车交通": ["公共交通", "油费", "停车费", "打车租车"],
  "金融保险": ["银行手续", "按揭还款", "保险"]
}
```

**收入分类** `config/category_mapping_income.json`：
```json
{
  "职业收入": ["工资收入", "公积金转出", "利息收入", "奖金收入"],
  "其他收入": ["退款", "报销", "礼金收入"]
}
```

### 2. 准备账单文件

将账单文件放入 `input/` 目录：
- 建设银行：`.csv` 文件
- 农业银行：`.pdf` 文件（个人活期交易明细）
- 宁波银行：`.xlsx` 或 `.xls` 文件
- 中信银行：`.pdf` 文件

### 3. 运行转换

#### 处理单个文件
```bash
python src/main.py input/农行-xxx.pdf output/
```

#### 批量处理目录
```bash
python src/main.py input/ output/
```

#### 测试农行解析器
```bash
python test_abc.py
```

### 4. 导入随手记

在 `output/` 目录中找到生成的 `.xlsx` 文件，导入到随手记网页端。

## 输出格式

生成的Excel文件包含以下列：

| 列名 | 说明 |
|--------|--------|
| 交易日期 | 格式：YYYY-MM-DD |
| 分类 | 支出/收入分类 |
| 类型 | 收入 或 支出 |
| 子分类 | 分类下的子分类 |
| 支付账户 | 资金账户名称 |
| 金额 | 交易金额（正数）|
| 成员 | 可选 |
| 商家 | 可选 |
| 项目 | 可选 |
| 备注 | 交易描述/商户名 |

## 支持的银行

| 银行 | 文件格式 | 解析器 | 状态 |
|--------|----------|--------|------|
| 建设银行 | CSV | CCBParser | 待实现 |
| 农业银行 | PDF | ABCParser | ✅ 已实现 |
| 宁波银行 | Excel | BOCParser | 待实现 |
| 中信银行 | PDF | CITICParser | 待实现 |

## 注意事项

1. 确保已安装所有依赖包（pdfplumber、openpyxl、pandas等）
2. 分类映射配置文件使用 UTF-8 编码
3. 农行 PDF 需要是"个人活期交易明细清单"格式
4. 生成的文件为 `.xlsx` 格式（非 `.xls`）
