# 架构评估报告 — Excel 汇总 CLI 工具

## 需求理解

开发一个 Python CLI 工具，功能如下：
1. 读取 `.xlsx` Excel 文件
2. 按用户指定的列名汇总数值数据（求和）
3. 输出汇总结果为 CSV 文件

CLI 参数：
- `--input`：输入 Excel 文件路径
- `--column`：要汇总的列名
- `--output`：输出 CSV 文件路径

这是一个**独立工具**，不依赖本项目现有的飞书/广告投放体系。它应当作为项目根目录下的独立模块，保持最小的外部依赖。

## 项目概览

项目根目录为 `C:\Users\13442\.codex\worktrees\50a5\agent`，是一个飞书 AI Agent 项目，主要技术栈为 Python + LangChain + Lark OAPI。

本项目已有：
- `src/` — 核心代码
- `skills/` — 技能模块
- `configs/` — 配置文件
- `tests/` — 测试目录
- `data/` — 数据目录
- `scripts/` — 脚本

新 CLI 工具作为独立模块 `tools/excel-summarizer/` 放置，不侵入现有业务代码。

## 技术栈选择

| 组件 | 选择 | 理由 |
|------|------|------|
| Python | >=3.10 | 项目已有 Python 环境 |
| Excel 读取 | `openpyxl` | 纯 Python，无系统依赖，处理 `.xlsx` 标准库 |
| CSV 输出 | `csv` (stdlib) | 零依赖 |
| CLI 框架 | `argparse` (stdlib) | 需求简单，无需 Click/typer 等第三方库 |
| 测试框架 | `pytest` | 项目已有 pytest 环境 |

关键设计决策：用 `argparse` + `openpyxl` + `csv`，把外部依赖降到最低（仅 `openpyxl` 一个非 stdlib 依赖）。

## 维度评分

| 维度 | 评分 | 依据 |
|------|------|------|
| 架构健康度 | 4/5 | 新模块独立放置，不耦合现有业务代码；三阶段管道清晰（读 Excel → 汇总 → 写 CSV） |
| 可维护性 | 4/5 | 职责单一：一个函数读 Excel，一个函数做汇总，一个函数写 CSV；便于单测和替换 |
| AI 可读性 | 5/5 | 命名可直接反映功能：`read_excel()`、`summarize_column()`、`write_csv()`；文件结构平铺 |
| 模块化 | 4/5 | 三个函数可独立测试；如需支持 `.xls` 或其他格式，只需替换 `read_excel()` |
| 可测试性 | 5/5 | 输入/输出都是文件，可用临时文件测试；无网络/数据库外部依赖 |

## V1 范围（最小主链）

| 改动点 | 涉及文件 | 风险 | 说明 |
|--------|---------|------|------|
| 项目目录 & 依赖 | `tools/excel-summarizer/` + `requirements.txt` | 低 | 新建目录和依赖文件 |
| 核心逻辑 | `tools/excel-summarizer/cli.py` | 低 | 主入口，含参数解析 + 三个处理函数 |
| 单元测试 | `tools/excel-summarizer/tests/test_cli.py` | 低 | mock 文件操作，测试纯函数 |
| 集成测试 | `tools/excel-summarizer/tests/test_integration.py` | 低 | 真实 `.xlsx` 文件验证 |
| 项目配置 | `pyproject.toml` | 低 | 定义 `excel-sum` CLI 入口点 |

### V1 不做清单（推迟到 V2+）

| 功能 | 说明 |
|------|------|
| 多列汇总 | `--columns col1,col2` 推迟 |
| 分组汇总 | `--group-by category` 推迟 |
| `.xls` 格式支持 | 需 `xlrd` 依赖，推迟 |
| 大文件流式读取 | `read_only=True` 优化，V2 处理 |
| JSON / Markdown 输出 | 仅 CSV，其他格式推迟 |
| pip 包发布 | 注册 PyPI 推迟 |

V1 核心流程：

```
CLI args → openpyxl.load_workbook() → 读取指定列 → sum() → csv.writer 写文件
```

## V2+ 建议

- 支持多列汇总（`--columns col1,col2`）
- 支持按分组汇总（`--group-by category`）
- 支持输出格式选择（JSON / Markdown table）
- 支持 `.xls` 格式（需 `xlrd` 依赖）
- 支持 pip 包发布

## 风险与注意事项

- **openpyxl 大文件性能**：如果 Excel 文件极大（>10MB），`load_workbook(read_only=True)` 可以减少内存占用 — V1 暂不优化，留到 V2
- **空列处理**：如果指定列没有数值数据或列不存在，需给出清晰的错误信息，不崩溃退出
- **CSV 编码**：输出 CSV 默认用 `utf-8-sig`（带 BOM），确保 Windows Excel 打开中文 CSV 不乱码
- **文件路径不存在**：`--input` 路径不存在时给出友好的错误提示并退出码非 0
