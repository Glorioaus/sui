# 随手记账单格式转换工具

将各种银行卡账单（PDF、Excel、CSV）转换为随手记可导入的Excel格式。

## 功能特点

- 支持多种银行账单格式（CSV、Excel、PDF）
- 自动识别银行类型
- 批量处理账单文件
- 基于JSON配置文件的分类-子分类映射
- 生成符合随手记导入格式的Excel文件

## 项目结构

```
sui/
├── README.md
├── requirements.txt
├── config/
│   └── category_mapping.json   # 分类-子分类映射配置
├── src/
│   ├── __init__.py
│   ├── models.py              # 数据模型定义
│   ├── base_parser.py         # 基础解析器类
│   ├── parsers/              # 各银行解析器
│   │   ├── __init__.py
│   │   ├── ccb_parser.py       # 建设银行
│   │   ├── abc_parser.py       # 农业银行
│   │   ├── boc_parser.py       # 宁波银行
│   │   └── citic_parser.py     # 中信银行
│   ├── excel_generator.py     # Excel生成器
│   └── main.py              # 主程序入口
├── templates/
│   └── suiji_template.xls   # 随手记导入模板
├── input/                   # 输入账单目录
└── output/                  # 输出Excel目录
```

## 环境搭建

### 首次克隆项目
为了确保项目在不同环境中一致运行，强烈推荐使用虚拟环境。详细的环境搭建指南请参考：[SETUP.md](SETUP.md)

### 快速开始
1. **创建并激活虚拟环境**
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1  # PowerShell
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **验证安装**
```bash
python src/main.py --help
```

## 使用方法

### 首次克隆项目初始化
1. **必须：创建并激活虚拟环境**
```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境（根据终端类型选择）
.venv\Scripts\Activate.ps1  # PowerShell
.venv\Scripts\activate.bat  # CMD
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

### 1. 配置分类映射

编辑 `config/category_mapping.json` 文件，配置分类-子分类映射规则：

```json
{
  "餐饮": {
    "外卖": ["美团", "饿了么", "外卖"],
    "早餐": ["早餐", "包子", "豆浆"],
    "午餐": ["午餐", "盒饭"],
    "晚餐": ["晚餐", "火锅", "烧烤"]
  },
  "交通": {
    "地铁": ["地铁", "城铁"],
    "公交": ["公交", "巴士"],
    "打车": ["滴滴", "出租车"],
    "加油": ["加油", "中石化", "中石油"]
  },
  "购物": {
    "日用品": ["超市", "沃尔玛", "家乐福"],
    "服装": ["服装", "鞋", "衣服"],
    "数码": ["手机", "电脑", "数码", "京东"]
  },
  "其他": {
    "未分类": []
  }
}
```

### 2. 准备账单文件

将账单文件放入 `input/` 目录：
- 建设银行：`.csv` 文件
- 农业银行：`.xlsx` 或 `.xls` 文件
- 宁波银行：`.xlsx` 或 `.xls` 文件
- 中信银行：`.pdf` 文件

### 3. 运行转换

#### 处理单个文件

```bash
python src/main.py input/建行信用卡.csv output/
```

#### 批量处理目录

```bash
python src/main.py input/ output/
```

### 4. 导入随手记

在 `output/` 目录中找到生成的Excel文件，导入到随手记网页端。

## 输出格式

生成的Excel文件包含以下列：

| 列名 | 说明 |
|--------|--------|
| 时间 | 交易日期，格式：YYYY-MM-DD |
| 分类 | 支出/收入分类 |
| 子分类 | 分类下的子分类 |
| 账户 | 资金账户名称 |
| 金额 | 交易金额 |
| 备注 | 交易描述/商户名 |

## 支持的银行

| 银行 | 文件格式 | 解析器 |
|--------|----------|--------|
| 建设银行 | CSV | CCBParser |
| 农业银行 | Excel | ABCParser |
| 宁波银行 | Excel | BOCParser |
| 中信银行 | PDF | CITICParser |

## 注意事项

1. 确保已安装所有依赖包
2. 随手记模板文件需要放在 `templates/` 目录
3. 分类映射配置文件使用UTF-8编码
4. 建设银行CSV文件使用GBK编码
