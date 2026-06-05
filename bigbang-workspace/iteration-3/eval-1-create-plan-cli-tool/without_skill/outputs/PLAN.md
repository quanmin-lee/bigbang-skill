# Excel 汇总 CLI 工具 — 完整规划

> 合并自：ARCH.md + EXECUTION_PLAN.md + TEST_BOUNDARIES.md + REVIEW_COMMENTS.md

---

## 项目概述

开发一个 Python CLI 工具 `excel-sum`，读取 `.xlsx` Excel 文件，按指定列汇总数值数据，输出 CSV 汇总结果。

**参数：** `--input <path>`、`--column <name>`、`--output <path>`

**项目位置：** `tools/excel-summarizer/`（独立模块，不侵入现有业务代码）

---

## 一、架构决策

### 1. 独立模块

新工具放在 `tools/excel-summarizer/`，不侵入现有飞书 Agent 业务代码。

### 2. 最小依赖

| 组件 | 选择 | 理由 |
|------|------|------|
| Python | >=3.10 | 项目已有 Python 环境 |
| Excel 读取 | `openpyxl` | 纯 Python，无系统依赖 |
| CSV 输出 | `csv` (stdlib) | 零依赖 |
| CLI 框架 | `argparse` (stdlib) | 零依赖 |
| 测试框架 | `pytest` | 项目已有 |

外部依赖仅 `openpyxl` 一个。

### 3. 三阶段管道

```
read_excel(path) → list[dict]
summarize_column(data, column) → float
write_csv(result, column, path) → None
```

三个阶段对应三个纯函数，可独立测试。

### 4. UTF-8 BOM

CSV 使用 `utf-8-sig` 编码（带 BOM），确保 Windows Excel 直接打开中文 CSV 不乱码。

### 5. V1 范围（最小主链）

| 功能 | 说明 |
|------|------|
| 读取 `.xlsx` | 使用 openpyxl 读取活动工作表 |
| 按单列汇总 | 对指定列的数值单元格求和，跳过非数值 |
| 输出 CSV | 输出两列带表头：`column, sum` |
| CLI 参数 | `--input`、`--column`、`--output` |
| 基本错误处理 | 文件不存在、列不存在时报错退出（退出码非 0） |

### 6. V1 不做清单（推迟到 V2+）

| 功能 | 说明 |
|------|------|
| 多列汇总 | `--columns col1,col2` 推迟 |
| 分组汇总 | `--group-by category` 推迟 |
| `.xls` 格式支持 | 需 `xlrd` 依赖，推迟 |
| 大文件流式读取 | `read_only=True` 优化，V2 处理 |
| JSON / Markdown 输出 | 仅 CSV，其他格式推迟 |
| pip 包发布 | 注册 PyPI 推迟 |

---

## 二、执行计划

### 项目结构

```
tools/excel-summarizer/
  ├── __init__.py
  ├── cli.py               # 主程序入口
  ├── requirements.txt      # 依赖清单
  ├── pyproject.toml        # 项目配置与 CLI 入口定义
  └── tests/
      ├── __init__.py
      ├── test_cli.py       # 单元测试
      └── test_integration.py  # 集成测试
```

### Batch 1: [CRITICAL_PATH] 打通主链（串行）

```
T1 (骨架) ──→ T2 (核心逻辑) ──→ T3 (单元测试) ──→ T4 (集成测试) ──→ ✅ V1 完成
```

| ID | 任务 | 类型 | 前置 | 预估时间 |
|----|------|------|------|---------|
| T1 | 搭建项目骨架（目录、`pyproject.toml`、`requirements.txt`、`__init__.py`） | [CRITICAL_PATH] | 无 | 5 min |
| T2 | 实现核心 CLI 逻辑（`cli.py`） | [CRITICAL_PATH] | T1 | 20 min |
| T3 | 编写单元测试（`tests/test_cli.py`） | [CRITICAL_PATH] | T2 | 15 min |
| T4 | 端到端集成测试（`tests/test_integration.py`） | [CRITICAL_PATH] | T2+T3 | 10 min |

#### T1: 搭建项目骨架

- 创建 `tools/excel-summarizer/` 目录
- 创建 `tools/excel-summarizer/__init__.py`
- 创建 `requirements.txt`：`openpyxl>=3.1.0`
- 创建 `pyproject.toml`，定义 `[project.scripts] excel-sum = "excel_summarizer.cli:main"`

#### T2: 实现核心 CLI 逻辑

文件 `tools/excel-summarizer/cli.py`，包含以下函数：

| 函数 | 职责 |
|------|------|
| `parse_args(argv: list[str] \| None = None) -> argparse.Namespace` | 解析 `--input`, `--column`, `--output` |
| `read_excel(path: str) -> list[dict]` | 读取 `.xlsx`，返回行数据列表 |
| `summarize_column(data: list[dict], column: str) -> float` | 对指定列求和，跳过非数值 |
| `write_csv(result: float, column: str, path: str)` | 写 CSV，格式 `column,sum` |
| `main()` | 组合以上四步，CLI 入口 |

#### T3: 编写单元测试

文件 `tools/excel-summarizer/tests/test_cli.py`。

测试框架：pytest + `tmp_path` + `monkeypatch`。

#### T4: 端到端集成测试

文件 `tools/excel-summarizer/tests/test_integration.py`。

使用 `openpyxl.Workbook()` 在 `tmp_path` 动态生成测试 Excel 文件，验证完整 CLI 链路。

### Batch 2: [ENHANCEMENT] V2+ 增强（可并发）

| ID | 任务名 | 前置依赖 | 可并发 |
|----|--------|---------|--------|
| T5 | 支持多列汇总（`--columns`） | T2 | 是（与 T6/T7 无冲突） |
| T6 | 支持分组汇总（`--group-by`） | T2 | 是 |
| T7 | 错误处理优化 | T2 | 是 |

---

## 三、测试策略

### 测试框架

pytest + `tmp_path` fixture + `monkeypatch`

### P0 测试（主链必须通过）

| 场景 | 测试函数 | 输入 | 预期 |
|------|---------|------|------|
| 正常求和 | `summarize_column()` | 3行数值 (10, 20, 30)，列名 "amount" | 返回 60.0 |
| 混合类型 | `summarize_column()` | 数值 + 文本 + 空单元格混合 | 只汇总数值部分 |
| 空列 | `summarize_column()` | 列全为空/非数值 | 返回 0.0 |
| 参数解析 | `parse_args()` | `--input a.xlsx --column col --output out.csv` | 三个参数正确分离 |
| CSV 写正确 | `write_csv()` | result=42.0, column="amount" | CSV 内容 `column,sum\namount,42.0` |
| 完整集成 | `main()` | 真实 .xlsx + 完整 CLI 调用 | 输出 CSV 中总和正确 |

### P1 测试（边界条件）

| 场景 | 输入 | 预期 |
|------|------|------|
| 列不存在 | 列名 "nonexistent" | 抛出 ValueError / SystemExit |
| 文件不存在 | 路径 `no_file.xlsx` | 抛出 FileNotFoundError |
| 单行数据 | 1行数值 99 | 返回 99.0 |
| 负数值 | -5, 10, -3 | 返回 2.0 |
| 空工作表 | 空列表 `[]` | 返回 0.0 |

---

## 四、输入/输出契约

| 函数签名 | 输入 | 输出 | 异常 |
|----------|------|------|------|
| `read_excel(path: str) -> list[dict]` | Excel 文件路径 | `[{col: val}, ...]` | `FileNotFoundError` |
| `summarize_column(data: list[dict], col: str) -> float` | 行数据 + 列名 | 数值总和（float） | `ValueError`（列不存在） |
| `write_csv(result: float, col: str, path: str) -> None` | 总和 + 列名 + 路径 | 写入文件 | `OSError`（不可写） |
| `parse_args(argv \| None) -> Namespace` | sys.argv | input/column/output | `SystemExit` |
| `main()` | 无（读取 sys.argv） | 调用管道，exit(0/1) | — |

---

## 五、关键风险提醒

1. **openpyxl 环境依赖**：执行 CLI 或测试前必须 `pip install -r requirements.txt`，否则全部失败
2. **CSV 编码**：`utf-8-sig` 确保 Excel 打开中文不乱码；测试读取时使用相同编码
3. **pyproject.toml 包名映射**：目录 `excel-summarizer`（连字符）与 Python 包 `excel_summarizer`（下划线）的映射必须正确配置
4. **0 值 vs 空列语义**：`summarize_column()` 在"全 0 列"和"空列"下均返回 0.0，当前无法区分。如果下游需要区分，V2 考虑返回 `Optional[float]`
5. **大文件性能**：`openpyxl.load_workbook()` 全量加载到内存，>10MB 文件有 OOM 风险。V1 不做优化，V2 用 `read_only=True` 解决

---

## 六、工作估算

| 任务 | 预估时间 |
|------|---------|
| T1 搭建骨架 | 5 min |
| T2 核心逻辑 | 20 min |
| T3 单元测试 | 15 min |
| T4 集成测试 | 10 min |
| **合计** | **~50 min** |
