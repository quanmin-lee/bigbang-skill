# 架构评估报告

## 需求理解
开发一个 Python CLI 工具，从 Excel 文件（.xlsx）中读取数据，按指定列汇总数值数据，输出汇总结果到 CSV 文件。支持三个 CLI 参数：`--input`（输入文件路径）、`--column`（要汇总的列名）、`--output`（输出 CSV 路径）。

## 项目概览
- **性质**: 全新项目，尚无代码
- **技术栈**: Python 3，依赖 openpyxl 或 pandas（读取 .xlsx），csv 标准库（输出 CSV）
- **核心数据流**: 输入 .xlsx → 读取指定列 → 数值汇总 → 输出 .csv
- **CLI 前端**: argparse 标准库解析参数

## 维度评分（前瞻评估）
| 维度 | 评分 | 依据 |
|------|------|------|
| 架构健康度 | 4/5 | 两模块设计（cli.py / core.py），关注点分离清晰，数据流单向传递 |
| 可维护性 | 4/5 | 每个函数单一职责，修改范围局限在单个模块内；缺少异常统一处理层（-1） |
| AI 可读性 | 5/5 | 函数名自描述（read_excel / summarize_column / write_csv），结构简单 |
| 模块化 | 4/5 | 核心逻辑与 CLI 解耦，可独立测试；openpyxl 依赖可替换（-1 因未做抽象接口） |
| 可测试性 | 4/5 | 纯函数设计天然可 mock；但 openpyxl 文件 IO 需要 mock，增加测试样板代码（-1） |

## 架构设计方案（从零设计）

### 推荐方案：两模块结构

```
cli_tool/
  __init__.py
  cli.py          ← CLI 入口，参数解析 + 调用核心逻辑
  core.py         ← 核心逻辑：读取 Excel → 汇总 → 写 CSV
tests/
  __init__.py
  test_cli.py     ← CLI 参数解析测试
  test_core.py    ← 核心逻辑测试
pyproject.toml    ← 项目元数据 + 依赖声明
```

### 模块职责

| 模块 | 职责 | AI 可读性要点 |
|------|------|--------------|
| `cli.py` | argparse 参数定义，调用 `core.py` 函数，异常处理 | 函数名 `parse_args()`、`main()` 自描述 |
| `core.py` | `read_excel()`、`summarize_column()`、`write_csv()` 三个纯函数 | 每个函数单一职责，输入输出类型明确 |

### 关键数据流
```
--input .xlsx → read_excel() → DataFrame/iter_rows
  → summarize_column(column_name) → {value: sum} dict
  → write_csv() → --output .csv
```

### 依赖选择

| 依赖 | 用途 | 替代方案 |
|------|------|---------|
| `openpyxl` | 读取 .xlsx（轻量，无 pandas 依赖） | pandas（更重但功能更强）|
| Python `csv` | 输出 CSV（标准库，无需额外依赖） | pandas DataFrame.to_csv() |
| Python `argparse` | CLI 参数解析（标准库） | click, typer |

**推荐使用 openpyxl + csv 标准库**，保持最小依赖。如果用户需要处理大文件或复杂数据转换，可升级到 pandas（标注为 V2+）。

## 最小主链（V1）

| 改动点 | 涉及文件 | 风险 | 说明 |
|--------|---------|------|------|
| 项目脚手架 | pyproject.toml, cli_tool/__init__.py, tests/__init__.py | 低 | 标准 Python 项目结构 |
| CLI 入口 | cli_tool/cli.py | 低 | argparse 三个参数，调用 core.main() |
| 读取 Excel | cli_tool/core.py (read_excel) | 中 | openpyxl 读取 .xlsx，处理空值/非数值行 |
| 汇总逻辑 | cli_tool/core.py (summarize_column) | 低 | 对指定列做 sum 聚合 |
| 写 CSV | cli_tool/core.py (write_csv) | 低 | csv.writer 写汇总结果 |
| CLI 测试 | tests/test_cli.py | 低 | 测试参数解析和 main 函数 |
| 核心逻辑测试 | tests/test_core.py | 中 | 测试 Excel 读取、汇总、CSV 写入 |

## V2+ 建议
- 支持 pandas 作为可选后端（大文件性能）
- 支持多列汇总（--columns 复数参数）
- 支持分组汇总（--group-by 参数）
- 支持输出格式选择（CSV / JSON / Excel）
- 添加 type hints 和 docstrings

## 风险与注意事项
- **Excel 文件不存在或格式错误**: 需要友好的错误提示，非崩溃退出
- **指定列不存在**: 需给出清晰的错误信息，列出可用列名
- **非数值数据**: 列中包含非数值数据时应跳过或报错，策略需明确
- **大文件**: openpyxl 加载整个工作簿到内存，超大文件可能 OOM（V2 考虑 pandas 分片）
