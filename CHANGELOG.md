# Changelog

本项目的所有重要变更都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)。

## [Unreleased]

本轮进行中的工作（计划作为下一个大版本）。自 v1.0.1 以来的变更：

### Added
- 建设银行储蓄卡 PDF 解析器 (`CCBDebitParser`)：`extract_tables()` 提取 7 列表格，账户固定 `建行储蓄卡`
- 宁波银行储蓄卡 PDF 解析器 (`BOCParser`)：交易流水行式解析（利息/张颖/礼金等分类）
- `CCBDebitParser` 消费商户分类规则（美团/饿了么→食品酒水、淘宝/京东→日常用品、滴滴/高德→打车租车）
- skill 迁入 per-bank reference 文档（`references/banks/*.md` + classification/output-format/transfer-rules）

### Fixed
- `merge.py` 收紧微信/支付宝转账识别：钱包类目标须同时含转账语义标记（充值/转入/零钱/余额宝/还款/提现），避免「经钱包的商户消费」被误判为转账
- `TRANSFER_KEYWORDS` 补「建设银行信用」→ 建行信用卡（修「还建设银行信用卡」误落通用「信用卡」）
- `CCBParser`：账户名 `建设银行信用卡` → `建行储蓄卡`、支出金额取 `abs()`、收入走收入分类映射
- 硬编码分类对齐 `config/category_mapping.json`：支付宝网购/水电燃气、建行信用卡购物/汽车类分类不再落到不存在的分类或子分类
- 宁波银行「银转证」识别为转账到 `股票账户`，避免计入普通支出

### Changed
- skill 收敛为标准 `.claude/skills/sui-bill-converter`（放弃远程/`.agents` 方案），新增 `docs/sui-bill-converter-claude-code-skill-spec.md`
- 建行储蓄卡 PDF/CSV 分离（PDF 主用，CSV 标遗留）；宁波路由 `宁波*.xlsx` → `宁波*.pdf`，建行 PDF 支持 `建行/建设银行` 双前缀
- 取消跟踪个人配置 `.claude/settings.local.json`

## [1.0.1] - 2026-04-30

### Added
- `sui-bill-converter` skill 封装：`SKILL.md` + `references/`（workflow、parser_extension_guide）+ `scripts/run_conversion.py`
- `AGENTS.md` 仓库协作指引
- README 增加 skill 使用说明

## [1.0.0] - 2026-02-13

首个稳定基线：多银行账单解析 + 跨文件合并处理。

### Added
- 支付宝解析器 (`AlipayParser`)、建设银行信用卡 PDF 解析器 (`CCBCreditParser`)、微信支付解析器 (`WeChatParser`)
- 合并处理器 `merge.py`：跨文件退款对冲（精确 + 模糊两轮）、转账识别（储蓄卡→信用卡/支付宝/微信）、亲属卡/亲友代付处理
- Excel 生成器重写为 3 个 Sheet（支出 / 收入 / 转账）
- 浦发 (`SPDBParser`)、招商 (`CMBParser`)、中信 (`CITICParser`) 信用卡 PDF 解析器（消费/退款对冲、优惠/红包归类为收入）

### Changed
- 大幅更新 `CLAUDE.md`、`README.md`
- `citic_parser`、`abc_parser`、`main.py`、`excel_generator.py` 调整以适配多银行路由与合并流程

### Removed
- `SETUP.md`（并入 README）

## [0.1.0] - 2026-02-12

### Added
- 农业银行 PDF 解析器 (`ABCParser`)
  - 支持"个人活期交易明细清单"格式
  - 自动识别收入/支出交易类型
  - 特殊分类规则：工资、公积金、贷款、微信、支付宝等
- 收入分类配置 `config/category_mapping_income.json`
  - 职业收入：工资、公积金、利息、奖金等
  - 其他收入：退款、报销、礼金等
- Excel 生成器重写
  - 输出 `.xlsx` 格式（非 `.xls`）
  - 10列标准格式：交易日期、分类、类型、子分类、支付账户、金额、成员、商家、项目、备注

### Changed
- 简化 `category_mapping.json` 为两层结构：`{"分类": ["子分类1", "子分类2"]}`
- `base_parser.py` 支持分离的收入/支出分类匹配
- 更新项目文档 (README.md, CLAUDE.md)

### Fixed
- 修复配置文件路径计算错误

---

## 版本说明

- **Added**: 新增功能
- **Changed**: 功能变更
- **Deprecated**: 即将移除的功能
- **Removed**: 已移除的功能
- **Fixed**: Bug 修复
- **Security**: 安全相关修复
