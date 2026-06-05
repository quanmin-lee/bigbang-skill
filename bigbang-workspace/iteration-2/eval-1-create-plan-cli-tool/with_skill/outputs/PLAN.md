# 执行计划：Excel 列汇总 CLI 工具

## 项目概述

开发一个 Python CLI 工具 `excel-summarizer`，读取 Excel 文件（.xlsx），按指定列汇总数值数据，输出汇总结果的 CSV。

### CLI 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--input` | str | 是 | 输入 Excel 文件路径 |
| `--column` | str/int | 是 | 要汇总的列名（字符串）或列号（整数） |
| `--output` | str | 是 | 输出 CSV 文件路径 |

## 架构设计

### 模块划分

```
excel-summarizer/
├── src/
│   ├── __init__.py
│   ├── cli.py              # CLI 入口，argparse 参数解析 + main 串联
│   ├── reader.py            # Excel 文件读取（返回完整 DataFrame）
│   ├── summarizer.py        # 按列 groupby + sum 数值汇总
│   └── writer.py            # DataFrame 写入 CSV（index=False）
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # pytest fixtures（模拟 DataFrame、临时目录）
│   ├── test_cli.py
│   ├── test_reader.py
│   ├── test_summarizer.py
│   ├── test_writer.py
│   └── test_integration.py
├── requirements.txt         # pandas, openpyxl, pytest
└── pyproject.toml
```

### 关键数据流

```
CLI args (--input, --column, --output)
  → cli.py: parse_args()                 → argparse.Namespace
  → reader.py: read_excel(input_path)    → DataFrame（全量）
  → summarizer.py: summarize(df, column) → DataFrame（聚合结果）
  → writer.py: write_csv(df, output)     → CSV 文件（index=False）
```

### 模块接口契约

| 函数 | 签名 | 返回值 | 说明 |
|------|------|--------|------|
| `reader.read_excel` | `(path: str) -> pd.DataFrame` | 完整 DataFrame | 不筛选列，不聚合 |
| `summarizer.summarize` | `(df: pd.DataFrame, column: str\|int) -> pd.DataFrame` | groupby+sum 聚合结果 | column 支持列名或列号 |
| `writer.write_csv` | `(df: pd.DataFrame, path: str) -> None` | 无 | 写入 CSV，index=False |
| `cli.parse_args` | `(argv: list[str]) -> argparse.Namespace` | Namespace | 含 input/column/output 属性 |
| `cli.main` | `() -> int` | 退出码 0/1 | 串联全流程，异常统一处理 |

### 异常处理策略

| 异常场景 | 处理方式 | 退出码 |
|---------|---------|--------|
| 文件不存在 | 捕获 FileNotFoundError，输出友好信息 | 1 |
| 列不存在 | 捕获 KeyError，提示可用列名 | 1 |
| 空 Excel 文件 | 正常返回空 DataFrame，提示无数据 | 0 |
| 非数值列汇总 | 全非数值时报错；混合类型时忽略非数值列 | 1 / 0 |

## 任务分解

| ID | 任务名 | 类型 | 前置依赖 | 涉及文件 |
|----|--------|------|---------|---------|
| T1 | 项目初始化 | [CRITICAL_PATH] | 无 | pyproject.toml, requirements.txt, src/__init__.py, tests/__init__.py |
| T2 | CLI 参数解析 | [CRITICAL_PATH] | T1 | src/cli.py（parse_args） |
| T3 | Excel 读取模块 | [CRITICAL_PATH] | T1 | src/reader.py |
| T4 | 数值汇总模块 | [CRITICAL_PATH] | T3 | src/summarizer.py |
| T5 | CSV 输出模块 | [CRITICAL_PATH] | T1 | src/writer.py |
| T6 | CLI 主流程集成 | [CRITICAL_PATH] | T2, T4, T5 | src/cli.py（main） |
| T7 | 单元测试 | [ENHANCEMENT] | T2, T3, T4, T5 | tests/test_*.py |
| T8 | 集成测试 | [ENHANCEMENT] | T6 | tests/test_integration.py |

## 批次规划

### Batch 1: [CRITICAL_PATH] 基础模块

| 步骤 | 任务 | 并行 |
|------|------|------|
| 1a | T1: 项目初始化 | — |
| 1b | T3: Excel 读取模块 | [先于 T4] |
| 1c | T4: 数值汇总模块 | [依赖 T3 接口契约] |
| 1d | **T2: CLI 参数解析** | **[parallel]** |
| 1e | **T5: CSV 输出模块** | **[parallel]** |

执行顺序: 1a → [(1b→1c), 1d, 1e]（T1 完成后，T3→T4 串行，T2 和 T5 与 T3/T4 并行无冲突）

### Batch 2: [CRITICAL_PATH] 主链集成

| 任务 | 说明 |
|------|------|
| T6: CLI 主流程集成 | main() 串联 parse_args → read_excel → summarize → write_csv |

### Batch 3: [ENHANCEMENT] 测试覆盖

| 任务 | 并行 |
|------|------|
| T7: 单元测试 | [parallel] |
| T8: 集成测试 | [parallel] |

## 测试策略

### 测试框架

pytest，无需额外插件。

### Mock 策略

- **Excel 读取**: 使用 `pandas.testing` 生成模拟 DataFrame，测试 reader 时使用 `tmp_path` + `pd.DataFrame.to_excel()` 创建临时 .xlsx fixture 文件
- **CLI 参数**: 使用 pytest `monkeypatch.setattr('sys.argv', [...])` 模拟命令行参数
- **CSV 输出**: 使用 `tmp_path` 创建临时目录写入后断言文件内容

### 测试验收边界（P0 必须覆盖）

| 模块 | 正常运行 | 错误路径 | 边界条件 |
|------|---------|---------|---------|
| **cli.py** | 正常参数返回 Namespace | 缺少参数 → SystemExit | —help 输出包含三个参数名 |
| **reader.py** | 有效 .xlsx 返回 DataFrame | 文件不存在 → FileNotFoundError | 空 Excel → 空 DataFrame |
| **summarizer.py** | groupby + sum 聚合 | 列不存在 → KeyError | 全非数值列 → 报错；混合列 → 忽略非数值 |
| **writer.py** | 写入 CSV | 目录不可写 → 异常 | 空 DataFrame → 空 CSV；**输出不含行号列（index=False）** |

## 依赖图

```
T1 (项目初始化)
 ├── T2 (CLI 参数解析) ──────────┐
 ├── T3 (Excel 读取) ──→ T4 (数值汇总) │
 └── T5 (CSV 输出模块) ───────────┘
                                   │
                                   v
                              T6 (主流程集成)
                                   │
                              ┌────┴────┐
                              T7       T8
                          (单元测试) (集成测试)
```

## V2+ 增强方向

- 支持多列汇总（--columns 多值）
- 支持自定义聚合函数（--agg sum|avg|count|min|max）
- 支持 Excel 多 sheet 选择（--sheet）
- 支持列名模糊匹配（--column 支持正则）
- 添加 --verbose 调试日志模式
- 打包为 pip 可安装包（setup.py 完善）
- 使用 openpyxl 替代 pandas 减小依赖体积

## 关键风险提醒

1. **Contract-first 策略**: T3 和 T4 必须先约定接口（read_excel 返回的 DataFrame 格式），再各自实现。建议在 T1 阶段就将各模块接口签名写入 stub 文件
2. **pandas 依赖**: V1 强依赖 pandas + openpyxl，需确保 requirements.txt 写入正确，CI 环境安装完整
3. **Windows 路径兼容**: 所有文件路径操作使用 `pathlib.Path`，避免硬编码 `/` 或 `\\`
4. **index=False**: CSV 输出时显式指定 `index=False`，否则输出会多一行号列
