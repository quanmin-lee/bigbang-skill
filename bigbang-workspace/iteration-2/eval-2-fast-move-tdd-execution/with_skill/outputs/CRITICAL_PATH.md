# 最小主链任务清单

## 项目概述
开发一个 Python CLI 工具，读取 Excel 文件按列汇总数值数据并输出 CSV。

## 批次概览
| 批次 | 任务数 | 说明 |
|------|--------|------|
| Batch 1 | 4 | 打通主链（[CRITICAL_PATH]）|
| Batch 2 | 2 | 功能完善（[ENHANCEMENT]）|

## 输入/输出契约

| 共享数据 | 格式 | 说明 |
|---------|------|------|
| `excel-summary/core.py` | Python 模块 | `read_excel(path, column)` + `summarize_column(values)` |
| `excel-summary/cli.py` | Python CLI | 入口点，使用 argparse |
| `excel-summary/tests/test_core.py` | pytest | 测试套件 |
| `excel-summary/sample.xlsx` | xlsx | 测试用 Excel 文件 |
| stdout/CSV | 文本 | CLI 最终输出 |

---

## Batch 1: 打通主链 [CRITICAL_PATH]

### T1: 项目脚手架 [CRITICAL_PATH]
- **目标**: 创建 `excel-summary/` 目录结构、依赖文件和测试用 sample.xlsx
- **输入**: 无（从零开始）
- **输出**:
  - `excel-summary/` 目录
  - `excel-summary/requirements.txt`（依赖 openpyxl）
  - `excel-summary/sample.xlsx`（含数值和文本列的测试 Excel）
  - `excel-summary/tests/__init__.py`
  - `excel-summary/__init__.py`
- **验收条件**:
  - 目录结构符合 PLAN.md 规格
  - `pip install -r requirements.txt` 可安装依赖
  - `sample.xlsx` 可被 openpyxl 正常打开，包含列: `name`, `score`, `grade`, `amount`
- **实现指引**:
  - 使用 openpyxl 创建工作簿；`name` 列含文本，`score` 和 `amount` 列含数值，`grade` 列含混合数据
  - `score` 列: 10 行数据 (50, 60, 70, 80, 90, 100, 110, 120, 130, 140)
  - `amount` 列: 8 行数据 (100, 200, 300, 400, 500, 600, 700, 800) + 2 个空单元格
  - 新开一列 `grade`，包含文本（"A", "B", "C"）

### T2: 核心逻辑 -- Excel 读取与数值提取 [CRITICAL_PATH]
- **目标**: 实现 `core.py`，包含 `read_excel(path, column)` 函数
- **输入**: `excel-summary/core.py`（新建）
- **输出**: `excel-summary/core.py`（含 read_excel 函数）
- **实现指引**:
  - 函数签名: `def read_excel(path: str, column: str) -> list[float]`
  - 使用 openpyxl 加载工作簿，遍历第一个 sheet 的所有行
  - 查找表头行定位指定列名的索引
  - 提取该列所有数值（跳过非数值、空单元格和表头本身）
  - 返回 `list[float]`
  - 异常处理: 文件不存在、列不存在、空数值列
- **验收条件**:
  - 提供 `sample.xlsx` 的 `score` 列应返回 `[50, 60, 70, 80, 90, 100, 110, 120, 130, 140]`
  - 提供 `sample.xlsx` 的 `amount` 列应返回 `[100.0, 200.0, 300.0, 400.0, 500.0, 600.0, 700.0, 800.0]`
  - 提供 `sample.xlsx` 的 `grade` 列应返回 `[]`（无数值）
  - 不存在的列应抛出 `ValueError`
  - 路径不存在应抛出 `FileNotFoundError`

### T3: 核心逻辑 -- 汇总统计 [CRITICAL_PATH]
- **目标**: 在 `core.py` 中追加 `summarize_column(values)` 函数
- **输入**: `excel-summary/core.py`（T2 产出）
- **输出**: `excel-summary/core.py`（追加 summarize_column 函数）
- **实现指引**:
  - 函数签名: `def summarize_column(values: list[float]) -> dict[str, float | int]`
  - 计算: `sum`, `avg` (mean), `max`, `min`, `count` (去重后数值个数)
  - 返回字典，key 为统计名，value 为对应值
  - 空列表的处理: sum=0, avg=0, max=0, min=0, count=0
  - 使用 `statistics.mean()` 计算平均值
- **验收条件**:
  - `summarize_column([50, 60, 70, 80, 90])` 返回 `{sum: 350, avg: 70, max: 90, min: 50, count: 5}`
  - `summarize_column([100, 100, 200, 200])` 返回 `{sum: 600, avg: 150, max: 200, min: 100, count: 2}`（去重后 2 个值）
  - `summarize_column([])` 正确返回零值
  - 单元素列表正确返回

### T4: CLI 入口 [CRITICAL_PATH]
- **目标**: 实现 `cli.py`，对接 `core.py` 的函数，通过 argparse 解析参数并输出 CSV
- **输入**: `excel-summary/core.py`（T3 产出）
- **输出**: `excel-summary/cli.py`
- **实现指引**:
  - 使用 argparse 解析 `--input`（必填）、`--column`（必填）、`--output`（可选，默认 `output.csv`）
  - 调用 `core.read_excel()` 和 `core.summarize_column()`
  - 使用 csv 标准库将结果写入输出文件
  - CSV 格式: 列名 `stat,value`，每行一个统计量
  - 示例输出:
    ```
    stat,value
    sum,350
    avg,70
    max,90
    min,50
    count,5
    ```
- **验收条件**:
  - `python cli.py --input sample.xlsx --column score --output result.csv`
  - `result.csv` 包含正确的 5 行统计结果
  - 缺少必填参数时显示 usage 信息
  - 使用 `if __name__ == "__main__"` 模式

---

## Batch 2: 功能完善 [ENHANCEMENT]

### T5: 错误处理与健壮性 [ENHANCEMENT]
- **目标**: 增强错误处理和边界情况覆盖
- **输入**: `excel-summary/core.py`, `excel-summary/cli.py`
- **输出**: 增强后的 `core.py` 和 `cli.py`
- **实现指引**:
  - `cli.py`: 捕获 `FileNotFoundError` 显示友好错误消息
  - `cli.py`: 捕获 `ValueError`（列不存在）显示友好错误消息
  - `core.py`: 空文件（仅表头）优雅处理
  - `core.py`: 所有单元格均非数值时返回空列表
- **验收条件**:
  - 不存在的文件输出: `Error: File not found: ...`
  - 不存在的列输出: `Error: Column 'xxx' not found in spreadsheet`
  - 全空列返回全零统计

### T6: 测试扩展 [ENHANCEMENT]
- **目标**: 扩展现有测试覆盖更多边界场景
- **输入**: `excel-summary/tests/test_core.py`
- **输出**: 增强后的 `excel-summary/tests/test_core.py`
- **实现指引**:
  - 测试空单元格处理
  - 测试混合类型列
  - 测试非常大的数值
  - 测试浮点精度
- **验收条件**:
  - 测试覆盖率达到 90%+
  - 所有测试通过
