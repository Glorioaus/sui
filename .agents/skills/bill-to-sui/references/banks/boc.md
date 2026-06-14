# 宁波银行（BOC）

- **格式**：Excel（`.xlsx` / `.xls`）
- **解析器**：`src/parsers/boc_parser.py` → `BOCParser`
- **账户名**：`宁波银行`（accounts.json id=1, type=debit）
- **文件名触发**：`宁波*.xlsx`

## 目录
- [当前实现状态](#当前实现状态)
- [需要补充的信息](#需要补充的信息)

## 当前实现状态

⚠️ **空实现 / 占位**：

`parse()` 方法直接返回**空交易列表**，没有读取逻辑、没有规则、没有账户名提取。这是 9 家机构中**唯一未实现**的。

```python
def parse(self, file_path: str) -> BankStatement:
    # 当前直接返回空 transactions
    return BankStatement(bank_name="宁波银行", ...)
```

## 需要补充的信息

业务规则**完全缺失**，需要从真实账单样本重新提取。请用户提供宁波银行 Excel 样例后补充以下信息：

- [ ] Excel 表头行位置（是否需要 skiprows）
- [ ] 列名与列索引（日期、金额、描述、余额等）
- [ ] 金额正负规则（储蓄卡约定：正=收入，负=支出）
- [ ] 是否有特殊分类规则（工资、公积金、贷款等）
- [ ] 是否需要跳过银行卡支付/退款对冲逻辑
- [ ] 编码（GBK 还是 UTF-8）

## LLM 泛化解析（临时方案）

在补全规则前，若用户提供了宁波银行账单，可走 [enrichment.md](../enrichment.md) 介入点 2 的 LLM 泛化解析路径：让 LLM 读 Excel 文本，尝试提取交易行，再走 `classify_fallback` 做分类。
