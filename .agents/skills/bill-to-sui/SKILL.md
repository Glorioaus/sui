---
name: bill-to-sui
description: 把多家银行/支付平台账单（PDF/Excel/CSV）转换为随手记可导入的 Excel。Use whenever the user wants to convert bank statements, credit card bills, WeChat or Alipay exports into 随手记 import format — even if they just say '导入账单'、'整理账单'、'记账'、'整理这个月的消费'、'把银行流水转成随手记' or drop bill files. 支持 农行/中信/浦发/招商/建行/宁波 银行卡 + 微信 + 支付宝，自动退款对冲、转账识别、亲属卡归类，并可调用 LLM 对默认分类做兜底重判。When the user mentions any of 农行, 农业银行, 中信, 浦发, 招商, 建行, 宁波银行, 微信账单, 支付宝账单, 信用卡账单, 银行流水, 账单转换, 随手记导入, this skill applies.
---

# bill-to-sui —— 银行账单转随手记

将多种银行/支付平台账单（PDF / Excel / CSV）转换为随手记个人理财应用可导入的标准化 Excel（支出 / 收入 / 转账 三个 Sheet）。

本 skill 在保留确定性 Python 脚本核心（金额/日期/对冲/转账匹配）的前提下，叠加一层 LLM 增强，用于商户智能归类、未知格式泛化解析、转账目标与亲属卡的模糊判断。

## 能力概览

- **9 家机构**：农行、中信信用卡、浦发信用卡、招商信用卡、建行信用卡、建行储蓄卡、宁波银行、微信支付、支付宝
- **两阶段流水线**：解析（每家独立输出）→ 合并（跨文件退款对冲 + 转账识别 + 亲属卡处理）
- **LLM 增强**：对落到默认兜底分类的交易做智能重判；对未匹配的转账/亲属卡做模糊归属
- **输出契约**：3 个 Sheet（支出 / 收入 / 转账），列结构见 [output-format.md](references/output-format.md)

## 工作流（4 步）

### 步骤 1：识别文件类型

根据文件扩展名 + 文件名 + 必要时文件头内容判断走哪家机构规则。文件命名规则（main.py 路由依据）：

| 文件名模式 | 机构 | reference |
|-----------|------|-----------|
| `农行*.pdf` | 农业银行储蓄卡 | [banks/abc.md](references/banks/abc.md) |
| `浦发*.pdf` | 浦发信用卡 | [banks/spdb.md](references/banks/spdb.md) |
| `招商*.pdf` | 招商信用卡 | [banks/cmb.md](references/banks/cmb.md) |
| `中信*.pdf` | 中信信用卡 | [banks/citic.md](references/banks/citic.md) |
| `建行信用卡*.pdf` | 建行信用卡 | [banks/ccb-credit.md](references/banks/ccb-credit.md) |
| `*账单*.pdf` | 浦发信用卡（通用账单兜底） | [banks/spdb.md](references/banks/spdb.md) |
| `建行*.csv` | 建设银行储蓄卡 | [banks/ccb-debit.md](references/banks/ccb-debit.md) |
| `宁波*.xlsx` | 宁波银行 | [banks/boc.md](references/banks/boc.md) |
| `微信*.xlsx` | 微信支付 | [banks/wechat.md](references/banks/wechat.md) |
| `支付宝*.csv` | 支付宝 | [banks/alipay.md](references/banks/alipay.md) |

**文件名无法识别但内容明显是账单** → 走 LLM 泛化解析（见 [enrichment.md](references/enrichment.md) 介入点 2）。处理前**读取对应 bank 的 reference 文档**，确认金额正负语义与特殊规则。

### 步骤 2：解析与合并

直接调用封装脚本，内部会执行两阶段流程：

```bash
# 单文件
python scripts/run_pipeline.py <输入文件> <输出目录>

# 整个目录批量
python scripts/run_pipeline.py <输入目录> <输出目录>

# 输出中间 JSON（供 LLM 增强层消费）
python scripts/run_pipeline.py <输入> <输出目录> --emit-json
```

脚本内部流程：`src/main.py`（按文件名路由解析器）→ `src/merge.py`（合并、退款对冲、转账识别、亲属卡处理）→ 生成 `merged_账单.xlsx`。原始解析产生的中间 JSON 会落在输出目录（`--emit-json` 时）。

`run_pipeline.py` 通过 `sys.path` 注入项目根的 `src/`，**不复制 src/ 代码**，保留其作为确定性核心。

### 步骤 3：LLM 增强（可选）

仅在出现以下情况时介入，详见 [enrichment.md](references/enrichment.md)：

1. **默认兜底分类过多**：脚本输出中大量交易落在「其他杂项-其他支出」或「其他收入-意外来钱」→ 运行 `scripts/classify_fallback.py` 批量重判。
2. **转账目标未匹配**：merge.py 把 `transfer_to_account` 写成通用「信用卡」→ 运行 `scripts/match_fuzzy.py` 用 LLM 综合判断。
3. **亲属卡未匹配**：`__FAMILY_CARD__` 标记未能在银行卡账单中找到对应交易 → 运行 `scripts/match_fuzzy.py`。

**降级原则**：LLM 不可用时静默回退到脚本结果，确定性路径永远可用。

### 步骤 4：交付与复核

- 确认输出文件 `output/merged_账单.xlsx` 存在且三个 Sheet 都有数据
- 向用户报告统计：解析条数、退款对冲对数、转账识别条数、亲属卡处理结果
- **列出 LLM 重判过的条目**供用户复核（保留原描述，便于追溯）
- 若转账目标/亲属卡仍无法确定，列出候选方案问用户

## 关键约束

### 金额正负语义（三套，不可混淆）

| 账单类型 | 正金额 | 负金额 |
|---------|--------|--------|
| 储蓄卡（农行/建行储蓄/宁波） | 收入 | 支出 |
| 信用卡（中信/浦发/招商/建行信用） | 消费支出 | 退款/返现/红包 |
| 微信/支付宝 | 恒正，方向由「收/支」列决定 | — |

### 特殊标记（merge.py 的隐式协议，必须保留）

- `category="__REPAYMENT__"`：中信信用卡还款记录，用于跨账单转账匹配后删除
- `category="__FAMILY_CARD__"` + `transaction_type="__MARKER__"`：微信亲属卡/支付宝亲友代付，用于关联银行卡实际扣款

### 不做什么

- 不修改 `src/` 任何代码（保回退路径）
- 不引入新依赖
- 不内置真实账单数据（隐私）

## 何时读哪个 reference

- 处理某家银行前 → 读 `references/banks/<bank>.md`
- 确认分类体系或商户关键词 → 读 [classification.md](references/classification.md)
- 确认输出列结构 → 读 [output-format.md](references/output-format.md)
- 转账/亲属卡规则细节 → 读 [transfer-rules.md](references/transfer-rules.md)
- LLM 增强层使用方法 → 读 [enrichment.md](references/enrichment.md)

## 常见失败模式

1. **PDF 抽取乱码/字段错位**：各银行 PDF 解析器对描述跨行、表头跳过有专门处理，详见对应 bank 文档的「PDF 解析特殊处理」
2. **CSV 编码**：建行/支付宝 CSV 是 GBK 编码（`encoding='gbk'`），微信 Excel 跳过前 16 行头部，支付宝跳过 24 行
3. **重复记账**：微信/支付宝的银行卡支付会自动跳过，避免与银行账单重复
4. **按揭还款误判**：已分类为「金融保险-按揭还款」的记录不会被转账识别逻辑处理
