# 最小主链任务清单

## 项目概述
开发一个 Python CLI 工具 `excel-summary`，读取 Excel 文件按列汇总数值数据并输出 CSV。

## 批次概览
| 批次 | 任务数 | 说明 |
|------|--------|------|
| Batch 1 | 5 | 打通主链（[CRITICAL_PATH]）|
| Batch 2 | 1 | 功能完善（[ENHANCEMENT]）|

---

## Batch 1: 打通主链

### T1: 创建项目目录结构和依赖文件 [CRITICAL_PATH]
- **目标**: 创建 `excel-summary/` 目录、`requirements.txt`、`tests/__init__.py`
- **输入**: 无（新建项目）
- **输出**: 
  - `excel-summary/` 目录
  - `excel-summary/requirements.txt`（内容：`openpyxl>=3.1.0`）
  - `excel-summary/tests/__init__.py`（空文件）
- **实现指引**:
  - 使用 `mkdir -p` 创建目录结构
  - 写入 `requirements.txt`，仅包含 `openpyxl>=3.1.0`
  - 创建空的 `tests/__init__.py`
- **验收条件**:
  - 目录 `excel-summary/excel_summary/` 和 `excel-summary/tests/` 存在
  - `requirements.txt` 可读且内容正确
  - `tests/__init__.py` 是合法 Python 文件（可为空）

### T2: 实现 Excel 读取和汇总统计逻辑 [CRITICAL_PATH]
- **目标**: 实现 `excel_summary/core.py`，包含 Excel 读取和数值汇总函数
- **输入**: T1 创建的目录结构
- **输出**: `excel-summary/excel_summary/core.py`
- **实现指引**:
  - 函数 `read_column(filepath: str, column_name: str) -> list[float]`：读取 .xlsx 文件，提取指定列的所有数值（跳过空值和非数值）
  - 函数 `summarize(values: list[float]) -> dict`：计算总和、平均值、最大值、最小值、去重计数
  - 使用 `openpyxl.load_workbook()` 读取，只读活动工作表
  - 异常处理：文件不存在、列不存在、无有效数值
- **验收条件**:
  - `read_column` 返回纯数值列表
  - `summarize` 返回包含 `sum`, `mean`, `max`, `min`, `unique_count` 的字典
  - 能正确处理空列（返回空列表/零值字典）
  - 能跳过非数值单元格

### T3: 实现 CLI 入口 [CRITICAL_PATH]
- **目标**: 实现 `excel_summary/cli.py`，包含 argparse 命令行解析和主入口
- **输入**: T1 目录结构 + T2 的 `core.py`
- **输出**: `excel-summary/excel_summary/cli.py`
- **实现指引**:
  - 参数：`--input <path>`（必填）, `--column <name>`（必填）, `--output <path>`（可选，默认 `output.csv`）
  - 调用 `read_column()` + `summarize()`
  - 输出 CSV：列名为 `stat, value`
  - CSV 格式使用标准库 `csv`，写入 UTF-8 编码
  - 添加 `if __name__ == "__main__": main()` 入口
- **验收条件**:
  - `python -m excel_summary.cli --input test.xlsx --column 金额 --output result.csv` 能正常运行
  - CSV 输出格式正确：`stat,value` 两列
  - 缺少必填参数时显示 usage 信息
  - 文件不存在时给出用户友好的错误信息

### T4: 创建测试用 sample.xlsx [CRITICAL_PATH]
- **目标**: 创建一个包含测试数据的 Excel 文件用于测试
- **输入**: 无（需要安装 openpyxl）
- **输出**: `excel-summary/sample.xlsx`
- **实现指引**:
  - 使用 openpyxl 创建，包含表头和数据列
  - 至少包含一列"金额"或"score"含混合数值
  - 包含一些空单元格和非数值单元格（如文本"无数据"）
  - 至少 10 行数据以产生有意义的统计结果
  - 也可以包含多列（如"姓名"、"金额"、"日期"），但主要用于测试列提取
- **验收条件**:
  - 文件可被 openpyxl 正常打开
  - 指定列包含可提取的数值
  - 非数值单元格不影响提取结果

### T5: 编写单元测试 [CRITICAL_PATH]
- **目标**: 为 `core.py` 编写全面的单元测试
- **输入**: T2 的 `core.py`（导出函数）+ T4 的 sample.xlsx
- **输出**: `excel-summary/tests/test_core.py`
- **实现指引**:
  - 测试 `summarize()` 正常路径：提供一组已知数值，断言 sum/mean/max/min/unique_count
  - 测试 `summarize()` 空列表：返回字段应为 0 或 None
  - 测试 `summarize()` 单元素列表
  - 测试 `read_column()` 通过 sample.xlsx 验证返回值
  - 使用 pytest 作为测试框架
- **验收条件**:
  - `pytest tests/` 全部通过
  - 覆盖率覆盖正常路径和边界情况

---

## Batch 2: 功能完善

### T6: 手动端到端验证 [ENHANCEMENT]
- **目标**: 运行完整 CLI 流程，验证输出正确性
- **输入**: T1-T5 全部产出
- **输出**: 验证日志或记录
- **实现指引**:
  - `python -m excel_summary.cli --input sample.xlsx --column 金额 --output actual_output.csv`
  - 检查 actual_output.csv 内容是否合理
- **验收条件**:
  - CLI 正常退出（exit code 0）
  - CSV 文件包含正确的统计值
  - 可用 `cat actual_output.csv` 验证

---

## 输入/输出契约

| 任务 | 读取 | 写入 | 共享契约 |
|------|------|------|---------|
| T1 | 无 | 目录结构 + requirements.txt | 目录路径：`excel-summary/` |
| T2 | T1 的目录 | `excel_summary/core.py` | `core.py` 导出 `read_column` 和 `summarize` |
| T3 | T1 + T2 | `excel_summary/cli.py` | `cli.py` 导入 `from excel_summary.core import read_column, summarize` |
| T4 | 无 | `sample.xlsx` | 文件格式：标准 .xlsx |
| T5 | T2 + T4 | `tests/test_core.py` | 测试导入 `from excel_summary.core import ...` |
| T6 | T1-T5 | 验证日志 | 无 |
