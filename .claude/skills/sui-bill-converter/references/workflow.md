# Workflow

## Environment

Use Python 3.11. The repository pins the expected version in `.python-version`.

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

On Windows, `start.ps1` can prepare the environment interactively.

## Validate Config

Run these commands before conversion when any `config/*.json` file changed:

```bash
python -m json.tool config/category_mapping.json > NUL
python -m json.tool config/category_mapping_income.json > NUL
python -m json.tool config/accounts.json > NUL
```

## Convert And Merge

Preferred skill wrapper:

```bash
python .claude/skills/sui-bill-converter/scripts/run_conversion.py --input input --output output
```

Equivalent direct commands:

```bash
python src/main.py input/ output/
python src/merge.py output/
```

Single file conversion:

```bash
python src/main.py input/农行-xxx.pdf output/
```

Merge only:

```bash
python src/merge.py output/
```

Expected merged result:

```text
output/merged_账单.xlsx
```

## Troubleshooting Checklist

- If the CLI says the file type is unknown, compare the filename with `FILE_PATTERNS` in `src/main.py`.
- If config loading fails, validate JSON and confirm UTF-8 encoding.
- If no transactions are found, check whether the bank changed statement layout or whether the filename routed to the wrong parser.
- If duplicate records appear, review skipped WeChat/Alipay bank-card payments and merge refund matching.
- If transfers are missing, inspect the generated 转账 sheet and transfer detection logic in `src/merge.py`.
