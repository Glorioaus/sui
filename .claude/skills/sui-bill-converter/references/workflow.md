# 工作流

## 环境

使用 Python 3.11。仓库通过 `.python-version` 记录推荐版本。

平台运行时应由镜像或任务环境预置依赖。上传到平台的 skill 不负责安装依赖，也不在运行时执行包管理命令。

本地开发时可按仓库 README 或 `start.ps1` 准备虚拟环境。

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

## 排障清单

- 如果提示文件类型未知，检查文件名是否匹配 `src/main.py` 中的 `FILE_PATTERNS`。
- 如果配置加载失败，校验 JSON 并确认 UTF-8 编码。
- 如果解析结果为 0 条，检查银行是否变更账单版式，或文件名是否路由到错误解析器。
- 如果出现重复记录，检查微信/支付宝银行卡支付跳过规则，以及合并阶段的退款匹配。
- 如果转账缺失，检查生成的转账 Sheet 和 `src/merge.py` 中的转账识别逻辑。
