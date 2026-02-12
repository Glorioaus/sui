# Changelog

本项目的所有重要变更都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)。

## [Unreleased]

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
