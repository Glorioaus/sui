# 宁波银行（BOC）

- **格式**：Excel（`.xlsx` / `.xls`）
- **解析器**：`src/parsers/boc_parser.py` → `BOCParser`
- **账户名**：`宁波银行`（accounts.json id=1, type=debit）
- **文件名触发**：`宁波*.xlsx`

## 目录
- [当前实现状态](#当前实现状态)
- [需要补充的信息](#需要补充的信息)

## 当前实现状态

⚠️ **未实现**：

`parse()` 直接 `raise NotImplementedError(...)`，没有任何读取逻辑。这是 9 家机构中**唯一未实现**的——遇到 `宁波*.xlsx` 会显式报错，而不是静默返回 0 条（避免误导用户以为转换成功）。

```python
def parse(self, file_path: str) -> BankStatement:
    raise NotImplementedError(
        "宁波银行 Excel 解析器尚未实现。请提供一份脱敏样例后再补充 BOCParser。"
    )
```

## 需要补充的信息

业务规则**完全缺失**，需要从真实账单样本重新提取。请用户提供宁波银行 Excel 样例后补充以下信息：

- [ ] Excel 表头行位置（是否需要 skiprows）
- [ ] 列名与列索引（日期、金额、描述、余额等）
- [ ] 金额正负规则（储蓄卡约定：正=收入，负=支出）
- [ ] 是否有特殊分类规则（工资、公积金、贷款等）
- [ ] 是否需要跳过银行卡支付/退款对冲逻辑
- [ ] 编码（GBK 还是 UTF-8）

> 补全规则需要一份脱敏的宁波银行 Excel 样例：提供后按上表信息实现 `BOCParser`。
