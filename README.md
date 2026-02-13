# 随手记账单格式转换工具

将各种银行卡账单（PDF、Excel、CSV）转换为随手记可导入的Excel格式。

## 功能特点

- 支持多种银行账单格式（CSV、Excel、PDF）
- 自动识别银行类型和交易类型（收入/支出/转账）
- 批量处理账单文件
- 两阶段处理：解析 → 合并（跨文件退款对冲、转账识别）
- 生成符合随手记导入格式的Excel文件（3个Sheet：支出、收入、转账）

## 支持的银行

| 银行 | 文件格式 | 解析器 | 文件名模式 |
|------|----------|--------|------------|
| 农业银行 | PDF | ABCParser | `农行*.pdf` |
| 中信信用卡 | PDF | CITICParser | `*中信*账单*.pdf` |
| 浦发信用卡 | PDF | SPDBParser | `浦发*.pdf` 或 `*账单*.pdf` |
| 招商信用卡 | PDF | CMBParser | `招商*.pdf` |
| 建行信用卡 | PDF | CCBCreditParser | `建行信用卡*.pdf` |
| 建设银行储蓄卡 | CSV | CCBParser | `建行*.csv` |
| 宁波银行 | Excel | BOCParser | `宁波*.xlsx` |
| 微信支付 | Excel | WeChatParser | `微信*.xlsx` |
| 支付宝 | CSV | AlipayParser | `支付宝*.csv` |

## 环境搭建

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
.venv\Scripts\Activate.ps1  # Windows PowerShell
# 或
source .venv/bin/activate   # macOS/Linux

# 安装依赖
pip install -r requirements.txt

# 验证安装
python src/main.py --help
```

## 使用方法

### 两阶段处理流程（推荐）

```bash
# 第一阶段：解析各银行账单，生成独立Excel
python src/main.py input/ output/

# 第二阶段：合并处理，执行跨文件退款对冲和转账识别
python src/merge.py output/
# → 生成 output/merged_账单.xlsx
```

### 单独处理

```bash
# 处理单个文件
python src/main.py input/农行-xxx.pdf output/

# 批量处理目录
python src/main.py input/ output/
```

## 项目结构

```
sui/
├── README.md
├── CLAUDE.md              # Claude Code 开发指南（详细规则）
├── requirements.txt
├── config/
│   ├── category_mapping.json        # 支出分类映射
│   ├── category_mapping_income.json # 收入分类映射
│   └── accounts.json                # 账户名称映射
├── src/
│   ├── models.py              # 数据模型定义
│   ├── base_parser.py         # 基础解析器类
│   ├── parsers/               # 各银行解析器
│   │   ├── abc_parser.py      # 农业银行 (PDF)
│   │   ├── citic_parser.py    # 中信信用卡 (PDF)
│   │   ├── spdb_parser.py     # 浦发信用卡 (PDF)
│   │   ├── cmb_parser.py      # 招商信用卡 (PDF)
│   │   ├── ccb_credit_parser.py # 建行信用卡 (PDF)
│   │   ├── ccb_parser.py      # 建设银行储蓄卡 (CSV)
│   │   ├── boc_parser.py      # 宁波银行 (Excel)
│   │   ├── wechat_parser.py   # 微信支付 (Excel)
│   │   └── alipay_parser.py   # 支付宝 (CSV)
│   ├── excel_generator.py     # Excel生成器
│   ├── merge.py               # 合并处理器
│   └── main.py                # 主程序入口
├── templates/
│   └── template.xls           # 随手记导入模板（参考）
├── input/                     # 输入账单目录
└── output/                    # 输出Excel目录
```

## 输出格式

生成的Excel文件包含3个Sheet：

**支出Sheet：**
| 交易类型 | 日期 | 分类 | 子分类 | 支出账户 | 金额 | 成员 | 商家 | 项目 | 备注 |

**收入Sheet：**
| 交易类型 | 日期 | 分类 | 子分类 | 收入账户 | 金额 | 成员 | 商家 | 项目 | 备注 |

**转账Sheet：**
| 交易类型 | 日期 | 转出账户 | 转入账户 | 金额 | 成员 | 商家 | 项目 | 备注 |

## 合并处理功能

`merge.py` 提供以下功能：

1. **退款对冲**：跨文件、跨账户匹配消费和退款记录，自动删除已对冲的记录
2. **转账识别**：识别储蓄卡→信用卡/支付宝/微信的转账记录
3. **亲属卡处理**：识别微信亲属卡和支付宝亲友代付，正确分类

## 配置文件

**支出分类** `config/category_mapping.json`：
```json
{
  "食品酒水": ["早午晚餐", "饮料", "买菜", "水果零食"],
  "居家物业": ["日常用品", "五险一金", "水电煤"],
  "金融保险": ["银行手续", "按揭还款", "保险"]
}
```

**收入分类** `config/category_mapping_income.json`：
```json
{
  "职业收入": ["工资收入", "公积金转出", "利息收入"],
  "其他收入": ["退款", "报销", "抢红包"]
}
```

## 注意事项

1. 微信/支付宝的银行卡支付记录会被跳过（避免与银行账单重复）
2. 信用卡还款记录用于转账匹配，不会出现在最终输出中
3. 详细的解析规则和分类逻辑请参考 `CLAUDE.md`
