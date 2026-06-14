# LLM 增强层使用指南

本 skill 采用**脚本主导、LLM 增强**的混合架构。确定性逻辑（金额/日期/对冲/转账匹配）全部在脚本中，LLM 只在 4 个明确的介入点增强。本文件说明每个介入点的触发条件、调用方式和降级策略。

## 目录
- [核心原则](#核心原则)
- [介入点 1：商户分类兜底](#介入点-1商户分类兜底)
- [介入点 2：未知银行泛化解析](#介入点-2未知银行泛化解析)
- [介入点 3：转账目标模糊匹配](#介入点-3转账目标模糊匹配)
- [介入点 4：交互式纠错（第二阶段）](#介入点-4交互式纠错第二阶段)
- [完整增强工作流](#完整增强工作流)

## 核心原则

1. **降级优先**：任何 LLM 调用失败或不可用时，静默回退到脚本结果，确定性路径永远可用。
2. **可追溯**：LLM 重判过的条目必须保留原描述（description 字段不变），便于复核。
3. **批量优先**：避免逐条调用 LLM，尽量批量处理（classify_fallback 的 extract 一次性产出所有待分类条目）。
4. **置信度分级**：LLM 输出带 confidence（high/medium/low），low 不改写原结果。

## 介入点 1：商户分类兜底

**触发条件**：交易落到默认兜底分类——
- 支出：`其他杂项 / 其他支出`
- 收入：`其他收入 / 意外来钱`

**调用方式**（两阶段桥梁）：

```bash
# 1. 提取待分类清单
python scripts/classify_fallback.py extract output/merged_账单.xlsx output/tasks.json

# 2. （LLM 运行时）读取 tasks.json，对每条 task 给出 category/subcategory/confidence
#    写入 output/results.json，格式：{"results": [{id, sheet, row, category, subcategory, confidence}, ...]}

# 3. 回写到 xlsx
python scripts/classify_fallback.py apply output/merged_账单.xlsx output/results.json
# → 生成 output/merged_账单_enriched.xlsx
```

**LLM 判断要点**：
- 参考 [classification.md](classification.md) 的分类体系，只能用 available_categories 列表中的值
- 综合 description + merchant + amount + account 判断
- 金额大、商户明确 → high；描述模糊（如"消费"无细节）→ low
- 无法判断时 confidence=low，保持原 current_category

**取代的原来什么**：写死在 `_categorize`/`_apply_xxx_rules`/`match_category` 的关键词 if-else（这些仍作为**首选命中规则**，LLM 只兜底未命中的）。

## 介入点 2：未知银行泛化解析

**触发条件**：文件名不匹配任何 FILE_PATTERNS（见 [SKILL.md 步骤 1](../SKILL.md)），但文件内容明显是账单（PDF/Excel/CSV）。

**调用方式**（LLM 直接处理，无脚本桥梁）：

1. LLM 用 pdfplumber/pandas/openpyxl 读取文件文本（或直接读文本内容）
2. 识别交易行的结构特征（日期格式、金额位置、描述字段）
3. 参考 [banks/](banks/) 下相近银行的规则确定金额正负语义
4. 提取交易，调用 classify_fallback 做分类
5. 输出符合 [output-format.md](output-format.md) 的中间 JSON
6. 用 ExcelGenerator 生成 xlsx（或直接复用 run_pipeline 的合并阶段）

**注意**：这个介入点风险最高（LLM 可能误读格式），必须让用户确认提取结果的抽样正确性后再继续。

**取代的原来什么**：`main.py` 直接报错"无法识别文件类型"。

## 介入点 3：转账目标模糊匹配

**触发条件**：
- merge.py 把 `transfer_to_account` 写成通用"信用卡"（identify_transfers 第二轮匹配失败）
- 亲属卡标记未在银行卡找到精确匹配（process_family_card）

**调用方式**：

```bash
# 1. 提取未匹配的转账条目
python scripts/match_fuzzy.py extract output/merged_账单.xlsx output/match_tasks.json

# 2. （LLM 运行时）读取，根据 description 综合判断转入账户
#    输出 results.json: {"results": [{id, sheet, row, to_account, confidence}, ...]}

# 3. 回写
python scripts/match_fuzzy.py apply output/merged_账单.xlsx output/match_results.json
```

**LLM 判断要点**：
- 候选账户见 candidate_accounts（中信/浦发/招商/建行信用卡 + 微信/支付宝等）
- description 含"中信/招商/浦发"等关键词 → 直接匹配对应信用卡
- 仅含"还款/跨行还款"无具体银行 → 看用户历史习惯，无把握则 confidence=low 保持"信用卡"
- 必要时**向用户提问**（列出候选方案）

**取代的原来什么**：merge.py 的 `transfer_to_account="信用卡"` 通用兜底。

## 介入点 4：交互式纠错（第二阶段）

**触发条件**：用户说"这条其实算 XX" / "这个分类不对"。

**当前状态**：⚠️ **第一版未实现**，需要持久化机制。规划如下：

1. LLM 把用户的纠正记录到 `config/user_corrections.json`：
   ```json
   [{"description_pattern": "美团外卖", "category": "食品酒水", "subcategory": "早午晚餐", "learned_at": "..."}]
   ```
2. 下次遇到匹配 description_pattern 的交易，优先应用纠正
3. 累积到阈值（如 5 条）后，提示用户是否沉淀进 `category_mapping.json`

**取代的原来什么**：手动编辑 JSON 配置文件。

## 完整增强工作流

理想的一次性处理流程：

```
1. run_pipeline.py input/ output/ --emit-json
   → output/merged_账单.xlsx + output/transactions.json

2. 检查 transactions.json 的 stats.needs_enrichment：
   - 若 > 0 → 执行介入点 1（classify_fallback extract/apply）
   - 若 0 → 跳过

3. 检查转账 sheet 是否有 to_account="信用卡"：
   - 若有 → 执行介入点 3（match_fuzzy extract/apply）
   - 若无 → 跳过

4. 向用户报告：
   - 总交易数、对冲/转账/亲属卡统计
   - LLM 重判的条目清单（供复核）
   - 仍存疑的条目（confidence=low）
```

**交付物**：`output/merged_账单_enriched.xlsx`（增强版，可直接导入随手记）。
