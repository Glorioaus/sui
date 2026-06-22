# 解析器扩展指南

## 新增解析器

1. 先选择 `src/parsers/` 中最接近的已有解析器作为参考。
2. 新建一个以 `_parser.py` 结尾的 snake_case 文件。
3. 定义银行相关的 CamelCase 类名，例如 `NewBankParser`。
4. 继承 `BaseParser` 并实现：

```python
def parse(self, file_path: str) -> BankStatement:
    ...

def get_supported_extensions(self) -> list[str]:
    ...
```

5. 将每一行账单标准化为 `Transaction`，字段要求：

- `date` 使用 `YYYY-MM-DD`
- `category` 和 `subcategory` 来自配置映射或显式规则
- `account` 使用项目中的账户命名
- `amount` 始终为正数
- `transaction_type` 为 `支出`、`收入` 或 `转账`
- `merchant` 在退款匹配需要商户身份时填写
- `transfer_to_account` 仅在转账记录中填写

## 注册解析器

在 `src/parsers/__init__.py` 中导出新类，然后更新 `src/main.py` 的 `FILE_PATTERNS`。具体文件名规则要放在宽泛规则之前，例如放在 `.*账单.*\.pdf$` 之前。

示例：

```python
(r'新银行.*\.pdf$', NewBankParser, "新银行信用卡"),
```

## 同步到 skill 包

解析器或配置改完后，必须把宿主改动同步到 skill 包内副本，否则独立平台运行会用过期引擎：

```bash
python .claude/skills/sui-bill-converter/scripts/sync_engine.py
```

阻断式 pre-commit hook 会检测漂移；也可单独检测：

```bash
python .claude/skills/sui-bill-converter/scripts/sync_engine.py --check
```

不要直接改包内 `engine/`，它是宿主的快照。

## 测试要求

至少测试：

```bash
python src/main.py input/新银行样例.pdf output/
python src/main.py input/ output/
python src/merge.py output/
```

检查生成文件中的支出、收入、转账三个 Sheet。不要提交真实账单文件，也不要提交生成的 output 文件。
