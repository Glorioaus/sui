# 工作流

## 环境

使用 Python 3.11。仓库通过 `.python-version` 记录推荐版本。

本 skill 自包含：包内 `engine/`、`config/`、`templates/` 是宿主同名目录的快照副本，可脱离宿主仓库独立运行。`run_conversion.py` 优先用包内引擎，找不到才回退宿主 `src/`。

依赖由运行环境提供（本地按 `requirements.txt` 安装，平台由镜像预置）。skill 不在运行时执行包管理命令。

## 校验配置

当修改过 `config/*.json` 时，先运行：

```bash
python -m json.tool config/category_mapping.json > NUL
python -m json.tool config/category_mapping_income.json > NUL
python -m json.tool config/accounts.json > NUL
```

## 转换与合并

推荐使用 skill wrapper：

```bash
python .claude/skills/sui-bill-converter/scripts/run_conversion.py --input input --output output
```

等价的直接命令：

```bash
python src/main.py input/ output/
python src/merge.py output/
```

单文件转换：

```bash
python src/main.py input/农行-xxx.pdf output/
```

只执行合并：

```bash
python src/merge.py output/
```

预期合并结果：

```text
output/merged_账单.xlsx
```

## 引擎同步

修改宿主 `src/`、`config/`、`templates/` 后，必须同步到 skill 包内副本：

```bash
python .claude/skills/sui-bill-converter/scripts/sync_engine.py
```

阻断式 pre-commit hook 会在提交前检测漂移，不一致则拒绝提交。

## 排障清单

- 如果提示文件类型未知，检查文件名是否匹配 `src/main.py` 中的 `FILE_PATTERNS`。
- 如果配置加载失败，校验 JSON 并确认 UTF-8 编码。
- 如果解析结果为 0 条，检查银行是否变更账单版式，或文件名是否路由到错误解析器。
- 如果出现重复记录，检查微信/支付宝银行卡支付跳过规则，以及合并阶段的退款匹配。
- 如果转账缺失，检查生成的转账 Sheet 和 `src/merge.py` 中的转账识别逻辑。
