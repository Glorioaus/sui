---
name: sui-bill-converter
description: Use this skill whenever the user asks to convert, merge, validate, troubleshoot, or extend SuiShouJi bill conversion for bank, WeChat, or Alipay statements in this repository. This is a standard Claude Code skill that calls the repository's deterministic Python engine and helps with workflow, diagnosis, parser extension, config validation, and privacy-safe handling of statement files.
---

# Sui Bill Converter

## Purpose

Use this skill as the standard Claude Code workflow layer for this repository's SuiShouJi bill converter.

The skill should help Claude Code run conversions, validate configs, diagnose failures, and extend parsers while keeping all deterministic financial logic in the Python code under `src/`.

## Core Principle

Keep deterministic financial logic in Python:

- parsing and normalization
- account/category mapping
- refund reconciliation
- transfer detection
- family-card matching
- Excel generation

Do not duplicate parser behavior inside the skill. If behavior must change, edit the relevant Python parser or config file.

## Repository Layout

Expect this project shape:

- `src/main.py` - converts one statement or an input directory.
- `src/merge.py` - merges generated workbooks and detects refunds/transfers.
- `src/parsers/` - bank, WeChat, and Alipay parsers.
- `config/` - category and account mappings.
- `templates/template.xls` - reference import template.
- `input/` and `output/` - local private data directories, ignored by git.

## Privacy Rules

Treat input statements and generated workbooks as private financial data. Do not paste raw transaction rows, card numbers, balances, or full statement text into responses unless the user explicitly asks. Prefer filenames, counts, error messages, and short redacted examples.

## Standard Workflow

1. Confirm the repository root contains `src/main.py`, `src/merge.py`, and `requirements.txt`.
2. Ensure Python 3.11 dependencies are installed in a virtual environment.
3. Validate JSON config files before conversion when configs changed.
4. Run conversion with the wrapper script or direct commands.
5. Inspect success/failure counts and confirm the merged output path.

Preferred wrapper command:

```bash
python .claude/skills/sui-bill-converter/scripts/run_conversion.py --input input --output output
```

Direct commands remain valid:

```bash
python src/main.py input/ output/
python src/merge.py output/
```

## Extending Parsers

When adding support for a new statement format:

1. Inspect a similar parser in `src/parsers/`.
2. Add a new `*_parser.py` class that subclasses `BaseParser`.
3. Return `BankStatement` containing normalized `Transaction` objects.
4. Register the parser import in `src/parsers/__init__.py`.
5. Add a specific filename pattern to `FILE_PATTERNS` in `src/main.py`.
6. Test one matching file, then the full convert-and-merge workflow.

Read `references/parser_extension_guide.md` before editing parser code.

## References (read on demand)

- `references/banks/<bank>.md` — read the matching bank doc before handling that institution's statement (amount sign rules, special handling, known status).
- `references/classification.md` — category/keyword system and per-bank classification differences.
- `references/output-format.md` — the 3-Sheet (支出/收入/转账) Excel column contract.
- `references/transfer-rules.md` — refund reconciliation, transfer detection, family-card matching in `merge.py`.
- `references/workflow.md` — detailed run and troubleshooting steps.
- `references/parser_extension_guide.md` — before adding or modifying a parser.

Bank docs: `abc` (农行), `ccb-credit`/`ccb-debit` (建行信用/储蓄), `citic` (中信), `cmb` (招商), `spdb` (浦发), `boc` (宁波储蓄卡 PDF), `wechat` (微信), `alipay` (支付宝).

## LLM Enhancement Policy

Run deterministic conversion first. Consider LLM enhancement only when it adds value:

- many transactions remain in default categories
- transfer target remains generic `信用卡`
- a file looks like a statement but no parser recognizes it

LLM changes should be traceable, preserve original descriptions, and avoid overwriting low-confidence financial decisions silently. Do not make LLM fallback part of the default conversion path until it has been tested with representative samples.

## Failure Diagnosis

Use the traceback and file type to classify failures:

- Unknown file type: check filename pattern order in `src/main.py`.
- JSON error: validate files in `config/`.
- PDF parse issue: inspect extracted text shape, then adjust the parser regex.
- Excel/CSV issue: check headers, encoding, and skipped payment-source rows.
- Merge mismatch: inspect generated sheets, then review refund/transfer logic in `src/merge.py`.

Keep fixes in code or config. Update this skill only when the workflow or guidance changes.
