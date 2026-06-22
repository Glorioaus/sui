---
name: sui-bill-converter
description: 当用户需要在本仓库中转换、合并、校验、排查或扩展随手记账单转换流程时使用本 skill，适用于银行、微信、支付宝账单。它是标准 Claude Code skill，调用仓库内确定性的 Python 引擎，负责引导工作流、诊断失败、扩展解析器、校验配置，并按隐私安全方式处理账单文件。
---

# 随手记账单转换

## 用途

将本 skill 作为本仓库随手记账单转换工具的标准 Claude Code 工作流层。

本 skill 用于帮助 Claude Code 运行转换、校验配置、诊断失败、扩展解析器，同时把所有确定性的财务处理逻辑保留在 `src/` 下的 Python 代码中。

## 核心原则

确定性的财务逻辑必须保留在 Python 代码中：

- 解析与标准化
- 账户和分类映射
- 退款对冲
- 转账识别
- 亲属卡匹配
- Excel 生成

本 skill 是**自包含**的：包内的 `engine/`、`config/`、`templates/` 是宿主仓库同名目录的快照副本，可脱离宿主仓库独立运行。引擎权威源是宿主 `src/`，包内副本通过 `sync_engine.py` 保持一致，不要直接改包内 `engine/`。

## 仓库结构

宿主仓库结构（引擎权威源）：

- `src/main.py`：转换单个账单文件或整个输入目录。
- `src/merge.py`：合并生成的工作簿，并识别退款、转账等跨账单关系。
- `src/parsers/`：银行、微信、支付宝解析器。
- `config/`：分类映射和账户映射。
- `templates/template.xls`：随手记导入模板参考。
- `input/`、`output/`：本地私密账单和生成文件目录，已被 git 忽略。

skill 包内自包含结构（宿主的快照副本）：

- `engine/`：`src/` 的副本，独立平台运行时使用。
- `config/`：宿主 `config/` 的副本。
- `templates/`：宿主 `templates/` 的副本。
- `scripts/sync_engine.py`：把宿主同步到包内，并检测漂移。

## 隐私规则

把输入账单和生成的工作簿都视为私密财务数据。除非用户明确要求，不要在回复中粘贴原始交易行、卡号、余额或完整账单文本。优先汇报文件名、数量、错误信息和少量脱敏示例。

## 标准工作流

1. 确认 Python 虚拟环境已安装依赖。
2. 如果修改过配置，先校验 `config/*.json`。
3. 使用 wrapper 脚本或直接命令运行转换和合并。
4. 检查成功/失败数量，并确认合并输出路径。

`run_conversion.py` 自适应寻根：优先用包内 `engine/`，找不到时回退宿主 `src/`。加 `--prefer-repo` 可强制用宿主引擎。

推荐 wrapper 命令：

```bash
python .claude/skills/sui-bill-converter/scripts/run_conversion.py --input input --output output
```

直接脚本命令仍然可用：

```bash
python src/main.py input/ output/
python src/merge.py output/
```


## 引擎同步

修改宿主 `src/`、`config/`、`templates/` 后，必须同步到 skill 包内副本，否则独立平台运行会用到过期引擎：

```bash
python .claude/skills/sui-bill-converter/scripts/sync_engine.py
```

仓库已配置阻断式 pre-commit hook：提交前自动检测漂移，不一致则拒绝提交并提示先跑同步。检测命令也可单独运行：

```bash
python .claude/skills/sui-bill-converter/scripts/sync_engine.py --check
```

不要直接修改包内 `engine/`、`config/`、`templates/`，它们是宿主的快照。
## 扩展解析器

新增账单格式支持时：

1. 先查看 `src/parsers/` 中最接近的已有解析器。
2. 新增一个以 `_parser.py` 结尾的 snake_case 文件。
3. 新增继承 `BaseParser` 的解析器类。
4. 返回包含标准化 `Transaction` 的 `BankStatement`。
5. 在 `src/parsers/__init__.py` 中注册解析器导入。
6. 在 `src/main.py` 的 `FILE_PATTERNS` 中加入具体文件名匹配规则。
7. 先测试单个匹配文件，再测试完整转换与合并流程。

修改解析器代码前，先阅读 `references/parser_extension_guide.md`。

## 参考文档（按需读取）

- `references/banks/<bank>.md`：处理对应机构账单前阅读，包含金额正负规则、特殊处理和已知状态。
- `references/classification.md`：分类、关键词体系和各机构分类差异。
- `references/output-format.md`：支出、收入、转账三个 Sheet 的 Excel 列契约。
- `references/transfer-rules.md`：`merge.py` 中的退款对冲、转账识别、亲属卡匹配规则。
- `references/workflow.md`：详细运行和排障步骤。
- `references/parser_extension_guide.md`：新增或修改解析器前阅读。

银行文档索引：`abc`（农行）、`ccb-credit`/`ccb-debit`（建行信用/储蓄）、`citic`（中信）、`cmb`（招商）、`spdb`（浦发）、`boc`（宁波储蓄卡 PDF）、`wechat`（微信）、`alipay`（支付宝）。

## LLM 增强策略

先运行确定性转换。只有在确实有价值时再考虑 LLM 增强：

- 大量交易仍落在默认分类
- 转账目标仍是泛化的 `信用卡`
- 文件看起来像账单，但没有解析器能识别

LLM 修改必须可追溯，保留原始描述，不能静默覆盖低置信度的财务判断。默认转换流程不要启用 LLM 兜底，除非已经用代表性样例验证过。

## 失败诊断

根据错误和文件类型定位问题：

- 未知文件类型：检查 `src/main.py` 中的文件名匹配规则顺序。
- JSON 错误：校验 `config/` 下的配置文件。
- PDF 解析问题：检查提取出的文本/表格形态，再调整解析器正则或表格读取逻辑。
- Excel/CSV 问题：检查表头、编码和已跳过的支付来源行。
- 合并结果异常：检查生成的三个 Sheet，再查看 `src/merge.py` 中的退款和转账逻辑。

修复应落在代码或配置中。只有当工作流或指导方式变化时，才修改本 skill。
