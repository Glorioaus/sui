# Parser Extension Guide

## Add A Parser

1. Choose the closest existing parser in `src/parsers/`.
2. Create a new snake_case file ending in `_parser.py`.
3. Define a CamelCase class, for example `NewBankParser`.
4. Subclass `BaseParser` and implement:

```python
def parse(self, file_path: str) -> BankStatement:
    ...

def get_supported_extensions(self) -> list[str]:
    ...
```

5. Normalize every row into `Transaction` with:

- `date` as `YYYY-MM-DD`
- `category` and `subcategory` from mappings or explicit rules
- `account` using project account naming
- positive `amount`
- `transaction_type` as `支出`, `收入`, or `转账`
- `merchant` where refund matching needs merchant identity
- `transfer_to_account` only for transfers

## Register The Parser

Update `src/parsers/__init__.py` to export the class. Then update `FILE_PATTERNS` in `src/main.py`. Put specific filename patterns before broad ones such as `.*账单.*\.pdf$`.

Example:

```python
(r'新银行.*\.pdf$', NewBankParser, "新银行信用卡"),
```

## Test Expectations

Test at least:

```bash
python src/main.py input/新银行-样例.pdf output/
python src/main.py input/ output/
python src/merge.py output/
```

Check generated sheets for 支出, 收入, and 转账. Do not commit real statement files or generated output.
