# Excel 汇总 CLI 工具 — 执行计划

## 项目概述

开发一个 Python CLI 工具 `excel-sum`，读取 `.xlsx` Excel 文件，按指定列汇总数值数据，输出 CSV 汇总结果。

**参数：** `--input <path>`、`--column <name>`、`--output <path>`

**项目位置：** `tools/excel-summarizer/`（独立模块，不侵入现有业务代码）

---

## 架构决策

1. **独立模块**：`tools/excel-summarizer/` 目录，不与现有飞书 Agent 代码耦合
2. **最小依赖**：仅 `openpyxl` 一个外部包（读取 `.xlsx`），CLI 用 stdlib `argparse`，CSV 用 stdlib `csv`
3. **三阶段管道**：`read_excel()` → `summarize_column()` → `write_csv()`，三个纯函数，可独立测试
4. **Python 包命名**：目录名用连字符 `excel-summarizer`，但 Python import 包名用下划线 `excel_summarizer`
5. **CSV 编码**：使用 `utf-8-sig` 以兼容 Excel 直接打开中文 CSV

### V1 范围内（最小主链）

| 功能 | 说明 |
|------|------|
| 读取 `.xlsx` | 使用 openpyxl 读取活动工作表 |
| 按单列汇总 | 对指定列的数值单元格求和 |
| 输出 CSV | 输出两列带表头：`column, sum` |
| CLI 参数 | `--input`、`--column`、`--output` |
| 基本错误处理 | 文件不存在、列不存在时报错退出 |

### V1 不做清单（推迟到 V2+）

| 功能 | 说明 |
|------|------|
| 多列汇总 | `--columns` 参数推迟 |
| 分组汇总 | `--group-by` 参数推迟 |
| `.xls` 格式 | 需要 xlrd 依赖，推迟 |
| 大文件流式读取 | 需要 read_only=True 优化，V2 处理 |
| JSON / Markdown 输出 | 仅 CSV，其他格式推迟 |

---

## 执行计划（任务分解）

### 批次概览

| 批次 | 任务数 | 类型 | 说明 |
|------|--------|------|------|
| Batch 1 | 4 | [CRITICAL_PATH] | 打通最小主链 |
| Batch 2 | 3 | [ENHANCEMENT] | V2+ 增强功能 |

### Batch 1: [CRITICAL_PATH] 打通主链（串行）

**T1: 搭建项目骨架**
- 创建 `tools/excel-summarizer/` 目录及 `__init__.py`
- 创建 `requirements.txt`：`openpyxl>=3.1.0`
- 创建 `pyproject.toml`，定义 `[project.scripts] excel-sum = "excel_summarizer.cli:main"`
- `pip install -e .` 可正常安装

**T2: 实现核心 CLI 逻辑**
- `tools/excel-summarizer/cli.py`
- 函数清单：
  - `parse_args(argv: list[str] | None = None) -> argparse.Namespace` — 参数解析
  - `read_excel(path: str) -> list[dict]` — 读 Excel，返回 `[{col: val}, ...]`
  - `summarize_column(data: list[dict], column: str) -> float` — 对列求和，跳过非数值
  - `write_csv(result: float, column: str, path: str)` — 写 CSV，格式 `column,sum`
  - `main()` — 组合以上四步

**T3: 编写单元测试**
- `tools/excel-summarizer/tests/test_cli.py`
- 覆盖场景：正常求和、混合类型（含非数值）、空列、列不存在、文件不存在、单行数据、负数值
- 使用 `tmp_path` + `monkeypatch` 模拟文件操作和 sys.argv

**T4: 端到端集成测试**
- `tools/excel-summarizer/tests/test_integration.py`
- 用 `openpyxl.Workbook()` 在 tmp_path 生成测试 Excel，调用 CLI 完整链路
- 验证输出 CSV 内容

### 依赖关系

```
T1 (骨架)
  └──→ T2 (核心逻辑)
         └──→ T3 (单元测试)
                └──→ T4 (集成测试)
                       └──→ ✅ V1 完成
```

全部串行。T2 先实现，T3 基于真实实现（而非 stub）编写测试，避免并发冲突。

### Batch 2: [ENHANCEMENT] V2+ 增强（可并发）

| ID | 任务名 | 涉及文件 | 可并发 |
|----|--------|---------|--------|
| T5 | 支持多列汇总（`--columns`） | `cli.py` + 测试 | 是（与 T6/T7 无冲突） |
| T6 | 支持分组汇总（`--group-by`） | `cli.py` + 测试 | 是 |
| T7 | 错误处理优化（友好提示信息） | `cli.py` + 测试 | 是 |

---

## 测试策略

### 测试框架

pytest + `tmp_path` fixture + `monkeypatch`

### P0 测试（主链必须通过）

| 场景 | 输入 | 预期 |
|------|------|------|
| 正常求和 | 3行数值 (10, 20, 30)，列名 "amount" | 返回 60 |
| 混合类型 | 数值 + 文本 + 空单元格混合 | 只汇总数值部分 |
| 空列 | 列全为空 | 返回 0 |
| 参数解析 | `--input a.xlsx --column col --output out.csv` | 三个参数正确分离 |
| CSV 写正确 | result=42, column="amount" | CSV 内容为 `column,sum\namount,42` |

### P1 测试（边界条件）

| 场景 | 输入 | 预期 |
|------|------|------|
| 列不存在 | 列名 "nonexistent" | 抛出 ValueError / SystemExit |
| 文件不存在 | 路径 `no_file.xlsx` | 抛出 FileNotFoundError |
| 单行数据 | 1行数值 99 | 返回 99 |
| 负数值 | -5, 10, -3 | 返回 2 |
| 空工作表 | 无数据行的工作表 | 返回 0 |

---

## 输入/输出契约

| 函数签名 | 输入 | 输出 |
|----------|------|------|
| `read_excel(path: str) -> list[dict]` | Excel 文件路径 | `[{"col1": val1, "col2": val2}, ...]` |
| `summarize_column(data: list[dict], col: str) -> float` | 行数据列表 + 列名 | 数值总和（float） |
| `write_csv(result: float, col: str, path: str)` | 总和 + 列名 + 路径 | 写入文件，无返回值 |
| `parse_args(argv: list[str] \| None) -> Namespace` | sys.argv（或测试注入） | `Namespace(input=..., column=..., output=...)` |
| `main()` | 无（读取 sys.argv） | 调用完整管道，`sys.exit(0)` 或 `sys.exit(1)` |

---

## 关键风险提醒

1. **openpyxl 安装**：环境没有 openpyxl 时，`pip install -r tools/excel-summarizer/requirements.txt` 必须在执行前完成
2. **大文件性能**：V1 不做优化，但需知悉 `load_workbook()` 会一次性全量加载到内存。如果测试中遇到超大文件（>100MB），V1 会 OOM —— 这是预期内的限制，V2 用 `read_only=True` 解决
3. **CSV 格式确认**：输出 CSV 带表头（`column,sum`），只有一行数据（汇总结果），不是原始数据转存。用户在 Excel 中打开时看到的是 `amount, 60` 这样的格式
4. **UTF-8 BOM**：`utf-8-sig` 编码确保 Windows Excel 打开 CSV 时中文不乱码
