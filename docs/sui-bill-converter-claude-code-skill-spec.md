# Spec: Sui Bill Converter Claude Code Skill

## 1. Background

当前项目是 Python 账单转换工具，把银行、微信、支付宝账单转换为随手记可导入的 Excel。核心转换代码位于 `src/`：

- `src/main.py`：按文件名路由解析器，生成单机构 Excel。
- `src/merge.py`：合并结果，做退款对冲、转账识别、亲属卡处理。
- `src/parsers/`：各银行/支付平台解析器。
- `config/`：账户和分类映射。

历史问题：skill 曾是“寄生 skill”，`run_conversion.py` 通过 `sys.path` 找宿主仓库的 `src/`，包内不含引擎。上传到独立平台后引擎缺失，agent 会自行从文档造一套引擎，导致结果错误。本 spec 把 skill 改造为自包含形态，同时保证宿主脚本路径零回归。

## 2. Goals

把 `.claude/skills/sui-bill-converter/` 整理为自包含标准 Claude Code skill：

- skill 包内带完整引擎副本，可脱离宿主仓库独立运行。
- 本地脚本路径（`src/main.py` + `src/merge.py`）保持权威源地位，行为不变。
- 同一份 `run_conversion.py` 兼顾两条路径：包内引擎优先，宿主仓库回退。
- 通过 pre-commit hook 阻断式防止引擎副本与宿主漂移。

目标工作流（两条并行）：

```text
路径 A（宿主仓库内）：
用户把账单放入 input/ -> 触发 skill -> run_conversion.py 回退宿主 src/ -> 生成 output/merged_账单.xlsx

路径 B（独立平台）：
平台部署 skill 包 -> 用户上传账单 -> run_conversion.py 用包内 engine/ -> 生成 merged_账单.xlsx
```

## 3. Non-Goals

- 不做外部文件平台集成（飞书等）。
- 不处理外部平台鉴权、密钥管理。
- 不把宿主 `src/` 废弃或改成引用 skill 包；宿主脚本路径是权威源。
- 不把解析逻辑改写成纯 LLM 提示词。
- 不默认启用 LLM 自动分类闭环。
- 不同时维护 `.claude/skills/` 和 `.agents/skills/` 两套 skill。

## 4. Core Principles

确定性财务逻辑必须留在 Python 代码里：账单解析、金额正负、分类映射、退款对冲、转账识别、亲属卡处理、Excel 生成。

引擎有且只有一份权威实现：宿主 `src/`。skill 包内 `engine/` 是它的快照副本，通过同步脚本保持一致，不接受在包内直接改解析器。

Claude Code skill 负责：识别意图、引导或调用引擎、校验配置、解释失败、指导扩展、按需读 references。

## 5. Skill Name And Location

保留现有名称 `sui-bill-converter`，位置 `.claude/skills/sui-bill-converter/`。不使用 `.agents/skills/`，因为当前 Claude Code 环境识别的是 `.claude/skills/`。

## 6. Target Skill Structure

```text
.claude/skills/sui-bill-converter/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── engine/                      # 宿主 src/ 的快照副本，自包含运行用
│   ├── __init__.py
│   ├── models.py
│   ├── base_parser.py
│   ├── excel_generator.py
│   ├── main.py                  # SuiConverter 部分
│   ├── merge.py
│   └── parsers/
│       └── *_parser.py
├── config/                      # 宿主 config/ 的快照副本
│   ├── accounts.json
│   ├── category_mapping.json
│   └── category_mapping_income.json
├── scripts/
│   ├── run_conversion.py        # 自适应单入口
│   └── sync_engine.py           # 从宿主同步引擎到包内
└── references/
    ├── workflow.md
    ├── parser_extension_guide.md
    ├── output-format.md
    ├── transfer-rules.md
    └── banks/*.md
```

`SKILL.md` 保持精简，只描述触发条件、核心原则和工作流。银行细节、分类体系、转账规则放入 `references/`，按需读取。

## 7. Implementation Scope

### Phase 1: 同步机制先行

- 写 `scripts/sync_engine.py`：从宿主 `src/`、`config/` 复制到包内 `engine/`、`config/`，带 hash 校验。
- 跑一次同步，建立初始副本。
- 写 `scripts/check_drift.py`：比对宿主与包内副本是否一致，供 pre-commit hook 调用。

### Phase 2: 改造入口为自适应

- `run_conversion.py` 寻根顺序：包内 `engine/` 优先，宿主仓库回退。
- 配置路径同理：包内 `config/` 优先，宿主 `config/` 回退。
- 删掉对 `requirements.txt` 是否存在的硬依赖。

### Phase 3: 阻断式漂移防护

- 在仓库根 `.git/hooks/pre-commit` 安装 hook，提交前调用 `check_drift.py`。
- 发现 `src/`/`config/` 与包内副本不一致时，拒绝提交并提示先跑 `sync_engine.py`。

### Phase 4: 文档对齐

- `SKILL.md`、`workflow.md`、`parser_extension_guide.md` 改为描述自包含特性与双路径。
- `AGENTS.md`、`CLAUDE.md`、`README.md` 增加“改解析器/配置后必须跑 `sync_engine.py`”的强制说明。

### Phase 5: 双路径验证

- 宿主脚本路径、skill 宿主路径、skill 自包含路径三路用真实 `input/` 跑，逐单元格对比一致。

## 8. Local Skill Execution Contract

入口（两条路径共用）：

```bash
python .claude/skills/sui-bill-converter/scripts/run_conversion.py --input input --output output
```

宿主直接脚本（权威源，不变）：

```bash
python src/main.py input/ output/
python src/merge.py output/
```

`run_conversion.py` 内部行为：

1. 先找包内 `engine/main.py`，存在则用包内引擎和包内 `config/`。
2. 否则 `find_repo_root` 回退宿主 `src/` 和 `config/`。
3. 两条路径产出同一份 `merged_账单.xlsx`。

## 9. LLM Enhancement Strategy

不变。LLM 增强非默认主流程，待默认分类长期较多或转账目标长期泛化时再考虑。

## 10. Acceptance Criteria

- Claude Code 能识别并触发 skill。
- skill 包单独拷出（脱离宿主仓库）后，`run_conversion.py` 能独立跑通真实账单。
- 宿主脚本路径行为不变，现有用法零回归。
- 三条路径产出逐单元格一致。
- `sync_engine.py` 能同步；`check_drift.py` 能检出包内引擎与宿主的漂移。
- pre-commit hook 在漂移时阻断提交。
- 生成的 Excel 含 `支出`、`收入`、`转账` 三个 Sheet。

## 11. Risks

- 双份引擎漂移（最高风险）：宿主改了解析器但没跑 `sync_engine.py`，平台包过期。缓解：阻断式 pre-commit hook + hash 校验 + 文档强制说明。
- `engine/` 副本与宿主 `src/` 的 import 路径差异导致行为不一致。缓解：同步脚本保持目录结构一致，`run_conversion.py` 统一注入逻辑。
- reference 文档与引擎行为不一致。缓解：文档变更也纳入同步检查范围。
- 未实现解析器静默返回空。缓解：显式报错。

## 12. Recommended Decision

```text
宿主 src/ 为权威源，脚本路径零回归；
skill 包内 engine/ 是宿主的快照副本；
run_conversion.py 自适应：包内优先，宿主回退；
sync_engine.py 负责同步，check_drift.py 负责检测；
阻断式 pre-commit hook 防止漂移；
先建同步机制，再改入口，最后三路验证。
```
