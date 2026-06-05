# 测试验收边界

## 测试策略
- **框架**: pytest（推荐，标准 Python 测试框架）
- **Mock 策略**: unittest.mock（pytest 内置，无需额外依赖）
- **测试文件命名**: `test_*.py`（pytest 默认发现规则）
- **测试数据**: 在 tests/ 目录下存放 `test_data.xlsx` 作为测试样本
- **类型**: 单元测试为主（mock openpyxl），加少量集成测试（真实 .xlsx 文件）

## 按任务分解

### T1: 项目脚手架 (P0)
- **验收条件**:
  - `pyproject.toml` 存在且包含 openpyxl 依赖
  - `cli_tool/__init__.py` 存在（使 cli_tool 成为可导入包）
  - `tests/__init__.py` 存在
  - `cli_tool/` 和 `tests/` 目录结构正确
- **测试场景**: N/A（纯文件创建，不涉及功能测试）
- **RED 测试**: N/A
- **GREEN 最小实现**: 创建目录结构和文件

### T2: 读取 Excel 核心逻辑 (P0)
- **验收条件**:
  - `read_excel(path)` 接受文件路径，返回 `list[dict]`（每行一个 dict，key=列名，value=单元格值）
  - 能够正确读取 .xlsx 文件的所有行
  - 文件不存在时抛 `FileNotFoundError`
  - 文件格式错误时抛 `ValueError`
- **测试场景**:
  | 场景 | 输入 | 预期输出 | 优先级 |
  |------|------|---------|--------|
  | 正常路径 | 有效的 .xlsx（3行2列，含表头） | `[{col1: val1, col2: val2}, ...]` 列表 | P0 |
  | 文件不存在 | 不存在的路径 | 抛出 `FileNotFoundError` | P0 |
  | 空文件 | 仅有表头无数据行的 .xlsx | 空列表 `[]` | P1 |
  | 空工作簿 | 无 sheet 的 .xlsx | 抛出 `ValueError` | P1 |
- **RED 测试**: `test_read_excel_normal` — 传入 mock openpyxl 返回值，验证返回结构正确
- **GREEN 最小实现**: 用 openpyxl `load_workbook().active` 读取，遍历行构建 dict 列表

### T3: 汇总 + 写 CSV 核心逻辑 (P0)

**语义澄清**: `--column` 指定要汇总的目标列。工具提取该列中所有**数值**数据并求和。输出单行 CSV，格式为 `column,sum\n<列名>,<总和>`。

- **验收条件**:
  - `summarize_column(data, column)`  接受 `list[dict]` 和列名，返回 float（该列所有数值的总和）
  - 非数值数据静默跳过
  - 列不存在时抛 `KeyError`
  - `write_csv(summary, column_name, path)`  写入 CSV（两列 header: column, sum；一行数据）
  - 空数据或无数值行时返回 0.0
- **测试场景**:
  | 场景 | 输入 | 预期输出 | 优先级 |
  |------|------|---------|--------|
  | 正常汇总 | `[{amount: 100}, {amount: 200}, {amount: 300}]`，列=amount | `600.0` | P0 |
  | 单行 | `[{amount: 100}]`，列=amount | `100.0` | P0 |
  | 非数值混合 | `[{v:1},{v:"abc"},{v:2}]`，列=v | `3.0`（"abc" 跳过）| P1 |
  | 全非数值 | `[{v:"x"},{v:"y"}]`，列=v | `0.0` | P1 |
  | 空数据 | `[]`，列=amount | `0.0` | P1 |
  | 列不存在 | `[{a:1}]`，列=b | 抛出 `KeyError` | P0 |
  | 写 CSV 正常 | `600.0`, 列名="amount", 输出路径 | CSV 文件含 `column,sum\namount,600.0` | P0 |
  | 写 CSV 目录不存在 | `1.0`, "a", 无效路径 | 抛出 `FileNotFoundError` | P1 |
- **RED 测试**: `test_summarize_basic` — 传入已知数据，验证汇总结果
- **GREEN 最小实现**: 遍历数据，过滤非数值，用 dict 做 sum 聚合；csv.writer 写文件

### T4: CLI 入口 (P0)
- **验收条件**:
  - `--input` 参数必填
  - `--column` 参数必填
  - `--output` 参数必填
  - 缺少参数时打印 usage 信息并退出（非 0 退出码）
  - 调用 `core.read_excel()` → `core.summarize_column()` → `core.write_csv()` 完整链路
- **测试场景**:
  | 场景 | 输入 | 预期输出 | 优先级 |
  |------|------|---------|--------|
  | 完整参数 | `--input test.xlsx --column amount --output out.csv` | 调用完整链路，exit 0 | P0 |
  | 缺少 --input | `--column a --output o.csv` | 打印错误，exit 非 0 | P0 |
  | 缺少 --column | `--input i.xlsx --output o.csv` | 打印错误，exit 非 0 | P0 |
  | 缺少 --output | `--input i.xlsx --column a` | 打印错误，exit 非 0 | P0 |
  | --help | `--help` | 打印帮助信息，exit 0 | P1 |
- **RED 测试**: `test_cli_missing_input` — mock sys.argv，验证缺少参数时 exit 非 0
- **GREEN 最小实现**: argparse 定义三个必填参数，main() 调用 core 模块的完整流程

### T5: 核心逻辑测试 (P0)
- **验收条件**:
  - 测试文件 `tests/test_core.py` 存在
  - 覆盖 T2、T3 中定义的所有 P0 场景
  - mock openpyxl 避免真实文件依赖
- **测试场景**: 同 T2、T3 中的 P0 测试场景
- **RED 测试**: 先写测试文件，导入未实现的 core 模块 → 测试失败（RED）
- **GREEN 最小实现**: 实现 core.py 中的全部函数，让所有测试通过

### T6: CLI 测试 (P0)
- **验收条件**:
  - 测试文件 `tests/test_cli.py` 存在
  - 测试参数解析全覆盖（正常/缺少参数/--help）
  - 测试 main() 集成的异常处理
- **测试场景**: 同 T4 中的 P0 场景
- **RED 测试**: 先写 CLI 测试，main() 未实现 → 测试失败
- **GREEN 最小实现**: 实现 cli.py，让 CLI 测试全部通过

## 测试执行顺序
```
T5 (core tests)
  └─→ T6 (CLI tests) — 依赖 core 实现通过
        └─→ T7 (集成验证)
```

T5 和 T6 不能并发（T6 依赖 T5 测试通过后 core 的实现完整）。

## 注意事项
- 测试 .xlsx 文件（`tests/test_data.xlsx`）需要预先创建并提交到仓库，用于集成测试
- openpyxl 需要在 `pyproject.toml` 中声明为依赖，测试环境中保证安装
- 所有 mock 使用 `unittest.mock.patch`，避免测试间状态污染
- P1 测试（边界条件）可先写场景描述，在 GREEN 阶段补充实现
