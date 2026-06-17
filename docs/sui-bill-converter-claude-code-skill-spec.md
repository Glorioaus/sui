# Spec: Sui Bill Converter Claude Code Skill

## 1. Background

当前项目是 Python 账单转换工具，用于把银行、微信、支付宝账单转换为随手记可导入的 Excel。项目已经有核心转换代码：

- `src/main.py`：按文件名路由解析器，生成单机构 Excel。
- `src/merge.py`：合并结果，做退款对冲、转账识别、亲属卡处理。
- `src/parsers/`：各银行/支付平台解析器。
- `config/`：账户和分类映射。

目标是把现有能力整理成一个标准 Claude Code skill，让 Claude Code 能在本仓库中稳定触发并调用它。

## 2. Goals

将现有 `.claude/skills/sui-bill-converter/` 整理为标准 Claude Code skill。

目标工作流：

```text
用户把账单文件放入本地 input/
-> 用户请求 Claude Code 转换账单
-> Claude Code 触发 sui-bill-converter skill
-> skill 调用仓库内 Python 转换脚本
-> 生成 output/merged_账单.xlsx
```

## 3. Non-Goals

本阶段不做以下事情：

- 不做外部文件平台集成。
- 不处理外部平台适配、密钥管理或服务端运行环境。
- 不把 `src/` 复制到另一套运行包里。
- 不把解析逻辑改写成纯 LLM 提示词。
- 不默认启用复杂 LLM 自动分类闭环。
- 不同时维护 `.claude/skills/` 和 `.agents/skills/` 两套 skill。

## 4. Core Principles

确定性财务逻辑必须留在 Python 代码里：

- 账单解析
- 金额正负处理
- 分类映射
- 退款对冲
- 转账识别
- 亲属卡处理
- Excel 生成

Claude Code skill 负责：

- 识别用户的账单转换意图。
- 引导或调用仓库内脚本。
- 校验配置文件。
- 解释转换失败原因。
- 指导新增解析器。
- 在需要时读取 references 文档，而不是把所有规则塞进主提示。

## 5. Skill Name And Location

保留现有名称：

```text
sui-bill-converter
```

标准位置：

```text
.claude/skills/sui-bill-converter/
```

不使用 `.agents/skills/bill-to-sui/` 作为主入口，因为当前 Claude Code 环境识别的是 `.claude/skills/`。

## 6. Target Skill Structure

推荐最终目录结构：

```text
.claude/skills/sui-bill-converter/
├── SKILL.md
├── scripts/
│   └── run_conversion.py
└── references/
    ├── workflow.md
    ├── parser_extension_guide.md
    ├── output-format.md
    ├── transfer-rules.md
    └── banks/
        ├── abc.md
        ├── alipay.md
        ├── boc.md
        ├── ccb-credit.md
        ├── ccb-debit.md
        ├── citic.md
        ├── cmb.md
        ├── spdb.md
        └── wechat.md
```

`SKILL.md` 保持精简，只描述触发条件、核心原则和工作流。银行细节、分类体系、转账规则放入 `references/`，按需读取。

## 7. Implementation Scope

### Phase 1: Correct Current Documentation

- 移除外部平台、另一套运行包等描述。
- README 中将 skill 描述改回 Claude Code 本地 skill。
- AGENTS.md 中将 skill wrapper 描述改回 `.claude/skills/sui-bill-converter/`。
- SKILL.md frontmatter 只描述 Claude Code 本地 skill。

### Phase 2: Fix Deterministic Bugs

优先修复会影响账单结果的确定性问题：

- `CCBParser` 账户名应与 `config/accounts.json` 和 `merge.py` 对齐。
- `CCBParser` 支出金额应取正数。
- `CCBParser` 收入记录应使用收入分类映射。
- `BOCParser` 已实现宁波银行储蓄卡 PDF 解析；其余未实现路径应显式报错，不能静默返回 0 条。

### Phase 3: Absorb Useful Feat Branch Content

从 `feat/bill-to-sui-skill` 吸收有价值内容，但放到 `.claude/skills/sui-bill-converter/`：

- per-bank reference 文档。
- 更完整的分类、输出格式、转账规则说明。
- 可选地吸收 `run_pipeline.py` 的直接 import 思路，改造现有 `run_conversion.py`。

暂不把 `classify_fallback.py` 和 `match_fuzzy.py` 作为默认主流程；如引入，应标记为 experimental。

## 8. Local Skill Execution Contract

推荐入口：

```bash
python .claude/skills/sui-bill-converter/scripts/run_conversion.py --input input --output output
```

也保留直接脚本方式：

```bash
python src/main.py input/ output/
python src/merge.py output/
```

预期输出：

```text
output/merged_账单.xlsx
```

## 9. LLM Enhancement Strategy

LLM 增强不是默认主流程。

后续可以考虑在以下场景介入：

- 默认分类数量长期较多。
- 转账目标长期落到泛化 `信用卡`。
- 用户明确要求批量重分类。

在这些场景出现之前，优先保持确定性脚本路径简单可靠。

## 10. Acceptance Criteria

最小可用版本必须满足：

- Claude Code 能识别并触发 `.claude/skills/sui-bill-converter/`。
- `SKILL.md` 描述准确，只面向 Claude Code 本地 skill。
- 用户请求“转换账单”“合并账单”“随手记导入”等任务时，skill 能指导或调用正确脚本。
- 生成的 Excel 包含 `支出`、`收入`、`转账` 三个 Sheet。
- 宁波银行 PDF 解析器已实现；其余未实现解析器应显式报错。
- 文档中只有一套主 skill 目录规范：`.claude/skills/sui-bill-converter/`。

## 11. Risks

主要风险：

- 同时维护 `.claude` 和 `.agents` 两套 skill 导致规则漂移。
- reference 文档和 `src/` 行为不一致。
- LLM 增强脚本复制分类枚举，未来与 `config/` 漂移。
- 未实现解析器静默返回空结果，误导用户以为已成功转换。

## 12. Recommended Decision

采用这个方向：

```text
main 为主干，保留 skill 名称 sui-bill-converter，
将 feat 分支的优质 reference 内容迁入 .claude/skills/sui-bill-converter/，
先修确定性解析 bug，再考虑 LLM 增强。
```
