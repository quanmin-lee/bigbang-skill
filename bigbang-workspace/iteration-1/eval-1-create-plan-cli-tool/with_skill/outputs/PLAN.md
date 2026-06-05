# PLAN - Excel 列汇总 CLI 工具

## 概述

开发一个 Python CLI 工具，读取 Excel (.xlsx) 文件，按指定列汇总数值数据，输出汇总结果至 CSV 文件。工具接受三个命令行参数：`--input`（输入 Excel 路径）、`--column`（要聚合的列名）和 `--output`（输出 CSV 路径）。

**总体策略**: 最小优先，先打通端到端主链（读取 → 聚合 → 输出），再补错误处理和完善。项目为全新构建（greenfield），无历史代码包袱。

## 架构决策

### 技术栈

| 组件 | 选型 | 理由 |
|------|------|------|
| 语言 | Python 3.10+ | 标准库支持 argparse、csv；类型注解成熟 |
| Excel 读取 | openpyxl | 纯 Python 实现，无需系统依赖；支持 .xlsx 格式 |
| CLI 解析 | argparse | 标准库，零依赖，满足当前三个参数的需求 |
| CSV 输出 | csv（标准库） | 零依赖，功能完备 |
| 测试框架 | pytest + pytest-cov | 社区标准，fixture 和 tmp_path 完美支持文件 IO 测试 |
| 项目打包 | pyproject.toml + setuptools | PEP 621 兼容，声明式配置 |

### 模块架构

```
cli.py              -- argparse 参数解析
reader.py           -- openpyxl 读取 .xlsx，返回 list[dict]
aggregator.py       -- 按列分组聚合（sum），返回 list[dict]
writer.py           -- csv.DictWriter 输出 CSV
main.py             -- 编排 read → aggregate → write 三步流程
```

### 模块间数据契约

各模块间统一以 `list[dict]` 传递，key 为列名（字符串），value 为原始值或聚合值。

```python
# reader 输出示例
[{"品类": "A", "销售额": 100}, {"品类": "B", "销售额": 200}]

# aggregator 输出示例
[{"品类": "A", "销售额": 100}, {"品类": "B", "销售额": 200}]
```

### V1 约定

- 默认聚合方式：sum（后续 V2 通过 `--agg` 参数扩展）
- 只处理第一个 sheet（后续 V2 通过 `--sheet` 参数扩展）
- 列名精确匹配（不区分大小写？V1 约定精确匹配）
- 非数值数据：跳过 + stderr warning
- Python 最低版本 3.10

## 执行计划

### 任务分解

| ID | 任务名 | 类型 | 前置依赖 | 涉及文件 |
|----|--------|------|---------|---------|
| T0 | 项目初始化 & 依赖声明 | [CRITICAL_PATH] | 无 | `pyproject.toml`, `requirements.txt`, `.gitignore`, `conftest.py`, `pytest.ini` |
| T1 | CLI 参数解析 | [CRITICAL_PATH] | T0 | `cli.py` |
| T2 | Excel 读取模块 | [CRITICAL_PATH] | T0 | `reader.py` |
| T3 | 数据聚合逻辑 | [CRITICAL_PATH] | T0 | `aggregator.py` |
| T4 | CSV 输出模块 | [CRITICAL_PATH] | T0 | `writer.py` |
| T5 | 主流程编排（集成） | [CRITICAL_PATH] | T1, T2, T3, T4 | `main.py` |
| T6 | 错误处理与边界测试 | [ENHANCEMENT] | T5 | 各模块 + `tests/` |
| T7 | 类型注解与文档 | [ENHANCEMENT] | T5 | 各模块, `README.md` |

### 批次规划

#### Batch 1: [CRITICAL_PATH] 打通主链

1. **T0**: 项目初始化
   - 创建 `pyproject.toml`（项目名 `excel-summarizer`、Python>=3.10、依赖 openpyxl、pytest）
   - 创建 `requirements.txt`（openpyxl）
   - 创建 `.gitignore`（排除 `__pycache__/`, `*.egg-info/`, `.venv/`）
   - 创建 `tests/` 目录 + `tests/__init__.py`
   - 创建 `conftest.py`（pytest 全局配置，如 test paths）
   - 创建 `pytest.ini`

2. **T1, T2, T3, T4 [parallel]**: 四个独立模块并行开发
   - T1: `cli.py` — argparse 定义 `--input`, `--column`, `--output`，均为 `required=True`
   - T2: `reader.py` — `load_workbook` 读 active sheet → 表头映射 → `list[dict]`
   - T3: `aggregator.py` — 按 column 分组，`sum` 聚合数值列
   - T4: `writer.py` — `csv.DictWriter` 写入指定路径

3. **T5**: 主流程编排
   - `main.py` — `if __name__ == "__main__":` 导入并串联 T1-T4

#### Batch 2: [ENHANCEMENT] 功能完善

4. **T6**: 错误处理与边界场景
   - 文件不存在 / 列名不存在 / 非数值数据 / 空文件
   - 全局 try/except + stderr 友好提示

5. **T7**: 类型注解 + README
   - 补齐所有函数签名注解
   - README.md 包含用法示例

### 依赖图

```
T0 (项目初始化)
  ├── T1 (CLI 解析) ───┐
  ├── T2 (Excel 读取) ──┤
  ├── T3 (聚合逻辑) ────┤
  └── T4 (CSV 输出) ───┤
                        ├── T5 (主流程编排)
                              ├── T6 (错误处理)
                              └── T7 (文档注解)
```

## 测试策略

### 总体策略

- **框架**: pytest + pytest-cov
- **Mock 策略**: 不 mock openpyxl，使用 `tmp_path` fixture 动态生成测试 Excel 文件。文件 IO 是工具的核心功能，mock 会降低测试价值
- **测试数据**: 所有测试通过 openpyxl 在 `tmp_path` 中创建 Excel 文件，避免外部 fixture 文件
- **浮点数精度**: 聚合结果使用 `pytest.approx` 而非精确 `==`

### 按任务测试

#### T1: CLI 参数解析 (P0)

| 场景 | 输入 | 预期输出 | 优先级 |
|------|------|---------|--------|
| 正常路径 | `--input data.xlsx --column 销售额 --output result.csv` | 返回三个参数值 | P0 |
| 缺少 --input | `--column 销售额 --output result.csv` | 非零退出 + 提示 | P0 |
| 缺少 --column | `--input data.xlsx --output result.csv` | 非零退出 + 提示 | P0 |
| 缺少 --output | `--input data.xlsx --column 销售额` | 非零退出 + 提示 | P0 |
| --help | `--help` | 打印帮助信息，零退出 | P1 |

**RED 测试**: `test_cli_parses_all_args` — 验证 argparse 解析出三个参数的正确值。

#### T2: Excel 读取模块 (P0)

| 场景 | 输入 | 预期输出 | 优先级 |
|------|------|---------|--------|
| 正常 Excel | 含 3 行数据、2 列的 xlsx | `[{"品类":"A","销售额":100}, ...]` | P0 |
| 空文件 | 只有表头、无数据行的 xlsx | 空列表 `[]` | P1 |
| 列名不存在 | 指定不存在的列名 | 抛出 `ValueError` | P1 |
| 含空值单元格 | 某行指定列为空 | 该行仍返回，空值字段为 `None` | P2 |

**RED 测试**: `test_reader_returns_rows` — 用已知内容的 xlsx 验证返回数据。

#### T3: 数据聚合逻辑 (P0)

| 场景 | 输入 | 预期输出 | 优先级 |
|------|------|---------|--------|
| 正常聚合 | `[{"品类":"A","销售额":100}, {"品类":"A","销售额":200}]` | `[("A", 300)]` | P0 |
| 单一分组 | 所有行同组 | 一条汇总结果 | P0 |
| 空列表 | 空输入 | 空列表 | P1 |
| 非数值数据 | 某行销售额为字符串 | 跳过 + warning；不抛异常 | P1 |

**RED 测试**: `test_aggregator_sums_by_column` — 按列分组求和。

#### T4: CSV 输出模块 (P0)

| 场景 | 输入 | 预期输出 | 优先级 |
|------|------|---------|--------|
| 正常写入 | `[{"品类":"A","销售额":300}]`, path="out.csv" | CSV 内容 `品类,销售额\nA,300` | P0 |
| 空结果 | 空列表 | CSV 仅含表头 | P1 |
| 输出路径不存在 | 路径包含不存在的目录 | 自动创建目录或抛出清晰错误 | P2 |

**RED 测试**: `test_writer_creates_csv` — 写入后读取验证内容。

#### T5: 端到端集成 (P0)

| 场景 | 输入 | 预期输出 | 优先级 |
|------|------|---------|--------|
| 端到端正常 | 构造的 xlsx + 指定列 | CSV 内容与手算一致 | P0 |

#### T6: 错误处理 (P1)

| 场景 | 输入 | 预期输出 | 优先级 |
|------|------|---------|--------|
| 输入文件不存在 | `--input nonexistent.xlsx` | 错误退出 + 友好提示 | P1 |
| 错误列名 | 指定列不存在 | 打印可用列名 | P1 |
| 非 .xlsx 文件 | 传入 .csv 文件 | 错误退出 + 提示只支持 .xlsx | P2 |

### 测试执行顺序

1. T1, T2, T3, T4 各自独立，可并行测试
2. T5 集成测试在所有模块就绪后执行
3. T6 作为 T5 的补充测试，同批次执行

## 附录

### 项目文件结构规划

```
excel-summarizer/
├── pyproject.toml
├── requirements.txt
├── pytest.ini
├── .gitignore
├── README.md
├── src/
│   ├── __init__.py
│   ├── main.py          # 入口：编排 CLI → 读取 → 聚合 → 输出
│   ├── cli.py           # argparse 参数解析
│   ├── reader.py        # openpyxl Excel 读取
│   ├── aggregator.py    # 按列分组聚合
│   └── writer.py        # CSV 输出
└── tests/
    ├── __init__.py
    ├── conftest.py       # pytest 全局 fixture
    ├── test_cli.py
    ├── test_reader.py
    ├── test_aggregator.py
    ├── test_writer.py
    └── test_integration.py
```

### V2+ 后续建议

- `--agg` 参数：sum / mean / count / min / max
- `--sheet` 参数：选择工作表
- `--group-by` 参数：多列分组
- `--format` 参数：CSV / JSON / 终端表格
- `--verbose` 参数：详细日志
- 打包为 `pip install` 可安装包
- `.xls` 旧格式支持（需引入 xlrd）
- 大文件流式读取（pandas chunksize）
- CI 配置（GitHub Actions 自动运行 pytest）

### 参考

- [openpyxl 文档](https://openpyxl.readthedocs.io/)
- [argparse 教程](https://docs.python.org/3/howto/argparse.html)
- [csv 模块文档](https://docs.python.org/3/library/csv.html)
