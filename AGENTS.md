# Repository Guidelines

## Project Structure & Module Organization

本仓库是 Python 3.11 编写的账单转换工具，用于把银行、微信、支付宝账单转换为随手记可导入的 Excel。核心代码在 `src/`：`main.py` 是命令行入口，`merge.py` 负责合并处理，`models.py` 定义 `Transaction` 和 `BankStatement`，`excel_generator.py` 生成最终 XLSX。银行专用解析器位于 `src/parsers/`，应继承 `src/base_parser.py` 中的 `BaseParser`。配置文件在 `config/`，包括分类映射和账户映射。`templates/template.xls` 是导入模板参考。`input/` 和 `output/` 被忽略，用于本地私密账单和生成文件。

## Build, Test, and Development Commands

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1      # Windows PowerShell
pip install -r requirements.txt
python src/main.py input/ output/
python src/merge.py output/
```

Windows 可运行 `start.ps1` 辅助创建虚拟环境并安装依赖。`python src/main.py <file> output/` 处理单个账单；`python src/main.py input/ output/` 批量处理目录；`python src/merge.py output/` 合并结果并生成 `output/merged_账单.xlsx`。

## Coding Style & Naming Conventions

使用 4 空格缩进和 UTF-8 编码，命名保持清晰。解析器文件使用 snake_case，并以 `_parser.py` 结尾；解析器类使用银行相关的 CamelCase 名称，例如 `ABCParser`、`CCBCreditParser`。`src/main.py` 中的文件名匹配规则要从具体到宽泛排列。不要随意修改中文分类、子分类和账户名称，它们会直接影响 Excel 导入结果。

## Testing Guidelines

当前没有正式测试套件。修改后请用本地 `input/` 中的代表性私密样例验证，并检查生成 XLSX 的 支出、收入、转账 三个 Sheet。修改配置前先校验 JSON：

```bash
python -m json.tool config/category_mapping.json > NUL
python -m json.tool config/category_mapping_income.json > NUL
python -m json.tool config/accounts.json > NUL
```

新增解析器时，至少测试一个匹配文件的单独处理，以及 `main.py` 加 `merge.py` 的完整两阶段流程。

## Skill Wrapper

`.claude/skills/sui-bill-converter/` 提供面向 LLM 的工作流封装，用于引导转换、诊断失败和扩展解析器。它不复制解析逻辑，底层仍调用 `src/main.py` 和 `src/merge.py`。常用入口是 `python .claude/skills/sui-bill-converter/scripts/run_conversion.py --input input --output output`；直接脚本调用方式仍然有效。

## Commit & Pull Request Guidelines

近期提交使用简短的 Conventional Commit 风格，常见格式如 `feat(parsers): 新增浦发、招商、中信银行信用卡PDF解析器`、`feat(config): 新增账户配置并简化分类映射`。建议遵循 `type(scope): summary`。PR 应说明支持的输入格式、解析器或配置变更、已运行命令和样例输出检查。不要提交真实账单，也不要提交 `input/`、`output/` 中的生成或私密文件。
