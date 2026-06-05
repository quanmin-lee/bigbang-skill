# 最小主链任务清单

## 项目概述
开发一个 Python CLI 工具 `excel-summary`，读取 Excel 文件按列汇总数值数据并输出 CSV。

- **PLAN 来源**: `docs/plans/sample-plan.md`
- **目标**: 实现端到端主链：CLI 参数解析 → Excel 读取 → 数值提取 → 汇总统计 → CSV 输出
- **当前状态**: 项目代码已存在且 15 个测试全部通过

## 批次概览
| 批次 | 任务数 | 说明 |
|------|--------|------|
| Batch 1 | 4 | 打通主链（[CRITICAL_PATH]）-- 验证阶段 |
| Batch 2 | 1 | 功能完善（[ENHANCEMENT]）-- 端到端验证 |

## Batch 1: 打通主链（验证已有实现）

### T1: 创建项目目录结构和依赖文件 [CRITICAL_PATH]
- **目标**: `excel-summary/` 项目骨架，`requirements.txt`，`__init__.py`
- **输入**: 无（新建项目）
- **输出**: 
  - `excel-summary/` 目录结构
  - `excel-summary/requirements.txt`（openpyxl>=3.1.0, pytest>=7.0.0）
  - `excel-summary/excel_summary/__init__.py`（空）
  - `excel-summary/tests/__init__.py`（空）
  - `excel-summary/sample.xlsx`（测试数据文件）
- **验证条件**:
  - 目录结构完整可导入
  - `pip install -r requirements.txt` 可安装依赖
  - `sample.xlsx` 可被 openpyxl 正常打开

### T2: 实现 Excel 读取和汇总统计逻辑 [CRITICAL_PATH]
- **目标**: `excel_summary/core.py` -- `read_column()` + `summarize()`
- **输入**: T1 的目录结构
- **输出**: `excel-summary/excel_summary/core.py`
- **接口契约**:
  - `read_column(filepath: str, column_name: str) -> list[float]`
  - `summarize(values: list[float]) -> dict[str, float | int | None]`
- **验证条件**:
  - 正常列提取返回纯数值列表
  - 非数值和空单元格被跳过
  - 列不存在抛 ValueError
  - 文件不存在抛 FileNotFoundError
  - summarize 返回 sum/mean/max/min/unique_count

### T3: 实现 CLI 入口 [CRITICAL_PATH]
- **目标**: `excel_summary/cli.py` -- argparse + CSV 输出
- **输入**: T1 + T2 产出
- **输出**: `excel-summary/excel_summary/cli.py`
- **接口契约**:
  - `--input <path>`（必填）, `--column <name>`（必填）, `--output <path>`（可选, 默认 output.csv）
  - CSV 格式：两列 `stat, value`
- **验证条件**:
  - CLI 正常处理输入并输出 CSV
  - 缺少参数显示 usage
  - 文件不存在显示友好错误并 exit 1

### T4: 编写单元测试 [CRITICAL_PATH]
- **目标**: 为 core.py 和 cli.py 编写全面测试
- **输入**: T2 + T3 产出 + T1 的 sample.xlsx
- **输出**: 
  - `excel-summary/tests/test_core.py`
  - `excel-summary/tests/test_cli.py`
- **验证条件**:
  - `pytest excel-summary/tests/ -v` 全部通过
  - 覆盖正常路径 + 边界条件 + 错误路径

## Batch 2: 功能完善

### T5: 端到端集成验证 [ENHANCEMENT]
- **目标**: 运行完整 CLI 流程，验证输出正确性
- **输入**: T1-T4 全部产出
- **输出**: 验证记录
- **验证条件**:
  - CLI 正常退出（exit code 0）
  - CSV 输出格式正确，统计值准确
  - 错误处理路径正常工作

## 输入/输出契约

| 任务 | 读取 | 写入 | 共享契约 |
|------|------|------|---------|
| T1 | 无 | 目录 + requirements.txt + sample.xlsx | 项目根: excel-summary/ |
| T2 | T1 目录 | `excel_summary/core.py` | 导出 `read_column`, `summarize` |
| T3 | T1 + T2 | `excel_summary/cli.py` | 导入 `from excel_summary.core import ...` |
| T4 | T2 + T3 | `tests/test_core.py`, `tests/test_cli.py` | 测试框架: pytest |
| T5 | T1-T4 | 验证日志 | CLI 二进制入口 |
