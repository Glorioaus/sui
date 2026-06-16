# 建设银行储蓄卡（CCB Debit）

- **格式**：CSV（**GBK 编码**）
- **解析器**：`src/parsers/ccb_parser.py` → `CCBParser`
- **文件名触发**：`建行*.csv`

## 目录
- [输入格式](#输入格式)
- [金额正负规则](#金额正负规则)
- [当前实现状态](#当前实现状态)

## 输入格式

- CSV，**GBK 编码**，`csv.reader` 读取。
- 至少 6 列；列索引：
  - `row[0]` = 日期
  - `row[5]` = 金额
  - `row[6]` = 描述（≥7 列时）
- 日期用 `parse_date`（8 位或带 `-`），金额用 `parse_amount`（去逗号）。

## 金额正负规则

`amount < 0 → 支出`，`amount ≥ 0 → 收入`。解析后金额统一取 `abs()` 写入（与其它解析器一致），并由 `is_income = amount >= 0` 决定走支出或收入分类映射。

## 当前实现状态

这是最简陋的解析器：

- 没有任何特殊规则、没有关键词映射、没有退款对冲
- 纯靠通用 `match_category(description, is_income=...)` 分类（收入/支出分别走对应映射）
- `account` 写为 `建行储蓄卡`，与 `config/accounts.json`（id=4）和 `merge.py` 的 `DEBIT_ACCOUNTS` 对齐，转账识别可正常工作
