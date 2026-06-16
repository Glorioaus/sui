# 输出格式契约

随手记可导入的 Excel 文件包含 **3 个 Sheet**：支出、收入、转账。列结构由 `src/excel_generator.py` 硬编码生成（`template.xls` 实际未被代码使用，仅作格式参考）。

## 目录
- [三个 Sheet 的列结构](#三个-sheet-的列结构)
- [表头样式](#表头样式)
- [输出文件命名](#输出文件命名)

## 三个 Sheet 的列结构

### 支出 Sheet（10 列）

| 列 | 字段 | 来源 |
|----|------|------|
| A | 交易类型 | 固定 "支出" |
| B | 日期 | `transaction.date`（YYYY-MM-DD） |
| C | 分类 | `transaction.category` |
| D | 子分类 | `transaction.subcategory` |
| E | 支出账户 | `transaction.account` |
| F | 金额 | `transaction.amount` |
| G | 成员 | 空（保留） |
| H | 商家 | `transaction.merchant` |
| I | 项目 | 空（保留） |
| J | 备注 | `transaction.description` |

### 收入 Sheet（10 列）

| 列 | 字段 | 来源 |
|----|------|------|
| A | 交易类型 | 固定 "收入" |
| B | 日期 | `transaction.date` |
| C | 分类 | `transaction.category` |
| D | 子分类 | `transaction.subcategory` |
| E | 收入账户 | `transaction.account` |
| F | 金额 | `transaction.amount` |
| G | 成员 | 空 |
| H | 商家 | `transaction.merchant` |
| I | 项目 | 空 |
| J | 备注 | `transaction.description` |

### 转账 Sheet（9 列，无分类/子分类）

| 列 | 字段 | 来源 |
|----|------|------|
| A | 交易类型 | 固定 "转账" |
| B | 日期 | `transaction.date` |
| C | 转出账户 | `transaction.account` |
| D | 转入账户 | `transaction.transfer_to_account` |
| E | 金额 | `transaction.amount` |
| F | 成员 | 空 |
| G | 商家 | `transaction.merchant` |
| H | 项目 | 空 |
| I | 备注 | `transaction.description` |

## 表头样式

`excel_generator.py` 对表头应用：
- 字体加粗（`Font(bold=True)`）
- 填充色 `DAEEF3`（浅蓝）
- 居中对齐
- 细边框

列宽（支出/收入）：`[10, 20, 12, 12, 12, 10, 8, 15, 10, 30]`
列宽（转账）：`[10, 20, 12, 12, 10, 8, 15, 10, 30]`

## 输出文件命名

### 阶段 1（解析，每家独立）

`{原文件名去扩展名}_随手记.xlsx`，例如 `农行-xxx.pdf` → `农行-xxx_随手记.xlsx`。

### 阶段 2（合并）

默认 `merged_账单.xlsx`，可通过 `merge.py <输出目录> <自定义文件名>` 指定。

## 可选增强（当前主流程未启用）

`run_conversion.py` 当前只输出确定性 Excel（3 个 Sheet）。若未来引入 LLM 兜底分类，会在此基础上扩展中间 JSON 与重判流程；目前主流程未启用，不在本契约范围内。
