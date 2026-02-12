# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 提供在本仓库中工作的指导。

## 常用开发命令

### 安装依赖
```bash
pip install -r requirements.txt
```

### 处理单个文件
```bash
python src/main.py <输入文件> [输出目录]
```
示例：
```bash
python src/main.py input/建行信用卡.csv output/
```

### 批量处理目录
```bash
python src/main.py <输入目录> <输出目录>
```
示例：
```bash
python src/main.py input/ output/
```

### 测试农行解析器
```bash
python src/main.py input/农行-xxx.pdf output/
```

### 批量处理
```bash
python src/main.py input/ output/
```

## 文件命名规则

解析器通过文件名自动识别银行类型：

| 文件名模式 | 解析器 | 说明 |
|-----------|--------|------|
| `农行*.pdf` | ABCParser | 农业银行储蓄卡 |
| `浦发*.pdf` | SPDBParser | 浦发信用卡 |
| `*账单*.pdf` | SPDBParser | 浦发信用卡（账单格式）|
| `中信*.pdf` | CITICParser | 中信银行 |
| `建行*.csv` | CCBParser | 建设银行 |
| `宁波*.xlsx` | BOCParser | 宁波银行 |

## 高层代码架构

### 概述
这是一个银行账单格式转换工具，可将多种银行账单格式（CSV、Excel、PDF）转换为兼容随手记个人理财应用的标准化Excel格式。

### 核心组件

1. **主入口**: `src/main.py`
   - 处理命令行参数
   - 根据文件类型路由到合适的解析器
   - 支持单个文件或批量目录处理

2. **解析器架构**:
   - 抽象基类: `src/base_parser.py`（提供通用工具，如日期解析、金额解析、分类匹配）
   - 银行专用解析器位于 `src/parsers/`:
     - `CCBParser`: 建设银行 (CSV格式)
     - `ABCParser`: 农业银行 (PDF格式) ✅ 已实现
     - `SPDBParser`: 浦发信用卡 (PDF格式) ✅ 已实现
     - `BOCParser`: 宁波银行 (Excel格式)
     - `CITICParser`: 中信银行 (PDF格式)
   - 每个解析器实现 `parse()` 方法，将原始文件转换为 `BankStatement` 对象

3. **数据模型**: `src/models.py`
   - `Transaction`: 表示单个交易记录，包含日期、分类、子分类、账户、金额、描述、交易类型(收入/支出)
   - `BankStatement`: 包含多个交易记录及元数据（如银行名称、账户信息、账单周期）的容器

4. **Excel生成器**: `src/excel_generator.py`
   - 创建随手记兼容格式的xlsx文件
   - 10列：交易日期、分类、类型、子分类、支付账户、金额、成员、商家、项目、备注

5. **配置文件**:
   - `config/category_mapping.json` - 支出分类映射（两层结构：分类 → 子分类列表）
   - `config/category_mapping_income.json` - 收入分类映射
   - `config/accounts.json` - 账户名称映射

### 分类映射结构

```json
{
  "分类名": ["子分类1", "子分类2", ...]
}
```

支出分类示例：食品酒水、居家物业、行车交通、金融保险等
收入分类示例：职业收入、理财、其他收入等

### 数据流
1. 接收输入文件/目录
2. 根据文件扩展名选择合适的解析器
3. 解析器读取原始文件，解析交易记录
4. 根据交易类型（收入/支出）使用对应的分类配置进行自动分类
5. 解析器返回 `BankStatement` 对象
6. Excel生成器创建新工作簿，填充交易数据
7. 最终Excel文件保存到输出目录

### 农行PDF解析器特殊规则

**收入分类规则：**
- 工资/代发/薪 → 职业收入-工资收入
- 公积金/gjj → 职业收入-公积金转出
- 利息/结息 → 职业收入-利息收入
- 退款/退还 → 其他收入-退款
- 张颖 → 张颖转入-其他

**支出分类规则：**
- 贷款/按揭/房贷 → 金融保险-按揭还款
- 公积金/gjj → 居家物业-五险一金
- 微信 → 账单导入-微信账单导入
- 支付宝 → 账单导入-支付宝账单导入
- 短信费 → 交流通讯-手机费

### 浦发信用卡解析器特殊规则

**交易类型处理：**
| 类型 | 识别规则 | 处理方式 |
|------|----------|----------|
| 消费 | 正金额 | 支出 |
| 还款 | 描述含"还款" | 跳过 |
| 红包抵扣 | 负金额 + "分润金/抵扣" | 收入（抢红包）|
| 退款 | 负金额 + 同商户同金额 | 与消费对冲 |
| 未匹配退款 | 负金额 + 无匹配 | 收入（退款）|