# PLAN.md — Excel 列汇总 CLI 工具

## 项目概述
开发一个 Python CLI 工具，读取 Excel 文件（.xlsx），提取指定列的所有数值做求和汇总，输出 CSV 结果。

**参数说明**:
| 参数 | 必填 | 说明 |
|------|------|------|
| `--input` | 是 | 输入 .xlsx 文件路径 |
| `--column` | 是 | 要汇总的目标列名（提取该列所有数值并求和） |
| `--output` | 是 | 输出 .csv 文件路径 |

**输出格式**: CSV 文件，两行两列：
```
column,sum
<列名>,<总和>
```

## 架构设计

### 模块结构
```
cli_tool/
  __init__.py          ← 包标识
  cli.py               ← argparse 参数解析 + main() 入口
  core.py              ← read_excel() / summarize_column() / write_csv()
tests/
  __init__.py          ← 包标识
  test_core.py         ← core 模块单元测试
  test_cli.py          ← CLI 集成测试
  test_data.xlsx       ← 测试样本文件
pyproject.toml         ← 项目元数据、依赖、entry point
```

### 技术栈
| 组件 | 选择 | 理由 |
|------|------|------|
| Excel 读取 | openpyxl | 纯 Python，无系统依赖，只读 .xlsx |
| CSV 输出 | csv（标准库） | 零额外依赖 |
| CLI 解析 | argparse（标准库） | Python 内置 |
| 测试 | pytest + unittest.mock | 标准 Python 测试生态 |

### 核心函数契约

```python
def read_excel(path: str) -> list[dict]:
    """读取 .xlsx，第一行为表头（作为 dict key），后续每行转为 dict。"""

def summarize_column(data: list[dict], column: str) -> float:
    """提取指定列所有数值并求和。非数值静默跳过，空数据返回 0.0。列不存在抛 KeyError。"""

def write_csv(summary: float, column_name: str, path: str) -> None:
    """写 CSV：column,sum 两列，一行数据。目录不存在抛 FileNotFoundError。"""

def main() -> int:
    """CLI 入口：解析参数 → read_excel → summarize_column → write_csv。返回 exit code。"""
```

### 维度评分
| 维度 | 评分 | 说明 |
|------|------|------|
| 架构健康度 | 4/5 | 两模块清晰分离，数据流单向传递 |
| 可维护性 | 4/5 | 单一职责函数，修改范围局限在单模块 |
| AI 可读性 | 5/5 | 函数名自描述，结构简单 |
| 模块化 | 4/5 | 核心与 CLI 解耦；openpyxl 可替换但未做抽象接口 |
| 可测试性 | 4/5 | 纯函数设计可 mock；文件 IO 需额外测试样板代码 |

## 执行计划

### 任务分解
| ID | 任务名 | 类型 | 前置依赖 | 涉及文件 |
|----|--------|------|---------|---------|
| T1 | 项目脚手架 | [CRITICAL_PATH] | 无 | pyproject.toml, cli_tool/\_\_init\_\_.py, tests/\_\_init\_\_.py |
| T2 | read_excel 实现 | [CRITICAL_PATH] | T1 | cli_tool/core.py |
| T3 | summarize + write_csv 实现 | [CRITICAL_PATH] | T2 | cli_tool/core.py |
| T4 | CLI 入口实现 | [CRITICAL_PATH] | T3 | cli_tool/cli.py |
| T5 | core 单元测试 | [CRITICAL_PATH] | T2, T3 | tests/test_core.py |
| T6 | CLI 集成测试 | [CRITICAL_PATH] | T4 | tests/test_cli.py |
| T7 | 端到端集成验证 | [CRITICAL_PATH] | T5, T6 | test_data.xlsx + 全流程 |

### 批次规划

#### Batch 1: [CRITICAL_PATH] 脚手架 + 核心逻辑（串行）
```
T1 → T2 → T3
```
- **T1**: 创建目录结构、pyproject.toml、空 `__init__.py` 文件
  - pyproject.toml 声明: 项目名 `excel-summary-cli`，依赖 `openpyxl`，entry point `excel-summary`
- **T2**: `core.py` 实现 `read_excel(path)` — 用 openpyxl 读取 .xlsx，返回 `list[dict]`
- **T3**: `core.py` 追加 `summarize_column(data, column)` 和 `write_csv(summary, column_name, path)`

#### Batch 2: [CRITICAL_PATH] CLI + 测试（串行）
```
T4 → T5 → T6
```
- **T4**: `cli.py` 实现 `parse_args()` 和 `main()` — argparse 定义 `--input`/`--column`/`--output`
  - 三个参数均为必填，缺失时 argparse 自动报错并 exit(2)
- **T5**: `tests/test_core.py` — mock openpyxl，覆盖所有 P0/P1 测试场景
- **T6**: `tests/test_cli.py` — mock sys.argv，测试参数解析和 main() 集成

#### Batch 3: [CRITICAL_PATH] 集成验证
```
T7
```
- **T7**: 准备 `tests/test_data.xlsx`（3-5 行数据），运行 `python -m cli_tool.cli` 全流程
  - 验证 `--input` → `--column` → `--output` 链路正确
  - 验证 CSV 输出内容正确
  - 验证缺少参数时非 0 退出

### 依赖图
```
T1 (脚手架)
  └─→ T2 (read_excel)
        └─→ T3 (summarize + write_csv)
              ├─→ T4 (CLI main)
              │     └─→ T6 (CLI 测试)
              └─→ T5 (core 测试) ──────→ T7 (集成验证)
```

## 测试策略

### 框架与约定
- 框架: pytest（自动发现 `tests/test_*.py`）
- Mock: `unittest.mock.patch`（mock openpyxl，避免真实文件依赖）
- 测试数据: `tests/test_data.xlsx`（提交到仓库，用于 T7 集成验证）

### P0 测试场景（必须通过）
| 测试 | 覆盖函数 | 场景 |
|------|---------|------|
| `test_read_excel_normal` | `read_excel` | 有效 .xlsx，3 行 2 列，含表头 → 正确返回 `list[dict]` |
| `test_read_excel_not_found` | `read_excel` | 文件不存在 → `FileNotFoundError` |
| `test_summarize_normal` | `summarize_column` | 3 行数值 → 正确求和 |
| `test_summarize_column_not_found` | `summarize_column` | 列不存在 → `KeyError` |
| `test_write_csv_normal` | `write_csv` | 正常参数 → 正确写 CSV |
| `test_cli_missing_input` | `main` | 缺少 `--input` → exit 非 0 |
| `test_cli_missing_column` | `main` | 缺少 `--column` → exit 非 0 |
| `test_cli_missing_output` | `main` | 缺少 `--output` → exit 非 0 |
| `test_cli_full` | `main` | 完整参数 → exit 0，核心函数被调用 |

### P1 测试场景（应通过）
| 测试 | 覆盖函数 | 场景 |
|------|---------|------|
| `test_read_excel_empty` | `read_excel` | 仅有表头无数据 → 空列表 |
| `test_summarize_non_numeric_mixed` | `summarize_column` | 非数值混合 → 跳过非数值，正确求和 |
| `test_summarize_all_non_numeric` | `summarize_column` | 全非数值 → 返回 0.0 |
| `test_summarize_empty_data` | `summarize_column` | 空输入 → 返回 0.0 |
| `test_write_csv_bad_dir` | `write_csv` | 输出目录不存在 → `FileNotFoundError` |
| `test_cli_help` | `main` | `--help` → exit 0，打印帮助 |

## V2+ 建议（不在此次实现）
- 支持 pandas 后端（大文件性能优化）
- 支持多列汇总（`--columns` 复数参数）
- 支持分组汇总（`--group-by` 参数）
- 支持输出格式选择（CSV / JSON / Excel）
- 非数值行警告（`--verbose` 参数）
- 更多聚合函数（平均/计数/最大/最小）

## 关键风险提醒
1. **openpyxl 首行识别**: 第一行默认视为表头，`read_excel` 需跳过首行作为 key，从第二行开始读取数据
2. **非数值静默跳过**: V1 默认静默跳过非数值行，不做警告
3. **大文件 OOM**: openpyxl 全量加载到内存，超大 .xlsx 有 OOM 风险（V2 使用 pandas 分片）
4. **安装 openpyxl**: pyproject.toml 中声明依赖，CI 和开发者需执行 `pip install -e .` 安装

---

## 执行摘要

### 生成过程
- **流程**: create-plan（Lead Agent 降级模式，因 Agent 工具不可用）
- **迭代轮次**: 2 轮
  - 第 1 轮: 架构师 + 策划师 + 测试工程师并行 → 审查员（判定需第 2 轮）
  - 第 2 轮: 架构师（修复评分）+ 测试工程师（澄清语义）→ 审查员（判定可终止）
- **产出文件**:
  - `ARCH.md` — 架构评估与设计
  - `EXECUTION_PLAN.md` — 执行计划
  - `TEST_BOUNDARIES.md` — 测试验收边界
  - `REVIEW_COMMENTS.md` — 审查意见（含两轮）

### 关键设计决策
1. **汇总语义**: `--column` 指定**求和目标列**（单值求和，非分组聚合）
2. **非数值处理**: 静默跳过（V1），`--verbose` 延至 V2
3. **测试框架**: pytest + unittest.mock，mock openpyxl 避免真实文件依赖

### 下一步
运行 `/bigbang fast-move --plan PLAN.md` 进入 TDD 执行阶段。
