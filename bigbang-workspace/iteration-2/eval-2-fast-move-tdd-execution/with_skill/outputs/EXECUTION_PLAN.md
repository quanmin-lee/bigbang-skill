# 执行计划

## 任务总览
| ID | 任务名 | 类型 | 前置依赖 | 涉及文件 |
|----|--------|------|---------|---------|
| T1 | 项目脚手架 | [CRITICAL_PATH] | 无 | `excel-summary/` 目录, `requirements.txt`, `sample.xlsx` |
| T2 | core.py - read_excel | [CRITICAL_PATH] | T1 | `excel-summary/core.py` |
| T3 | core.py - summarize_column | [CRITICAL_PATH] | T1, T2 (同文件，串行) | `excel-summary/core.py` |
| T4 | cli.py - CLI 入口 | [CRITICAL_PATH] | T2, T3 | `excel-summary/cli.py` |
| T5 | 错误处理增强 | [ENHANCEMENT] | T4 | `excel-summary/core.py`, `excel-summary/cli.py` |
| T6 | 扩展测试覆盖 | [ENHANCEMENT] | T2, T3 | `excel-summary/tests/test_core.py` |

## 批次规划

### Batch 1: [CRITICAL_PATH] 打通主链

串行执行（文件依赖链严格）：
1. **T1**: 项目脚手架
2. **T2**: core.py - read_excel 实现
3. **T3**: core.py - summarize_column 实现（追加到同一文件）
4. **T4**: cli.py - CLI 入口

**执行策略**：由于 T2/T3 写入同一文件 (core.py)，必须在同一批次内串行。T1 无依赖，先执行创建基础结构。T2 在 T1 创建好目录后开始。T3 在 T2 的 core.py 基础上追加函数。T4 依赖 T2+T3 的完整 core.py。

### Batch 2: [ENHANCEMENT] 功能完善

串行执行：
1. **T5**: 错误处理增强（修改 core.py + cli.py）
2. **T6**: 扩展测试覆盖

**执行策略**：T5 增强 core.py/cli.py 的错误边界处理。T6 在完整功能实现后追加测试用例。

## 依赖图

```
T1 (scaffold)
 │
 ▼
T2 (core.py - read_excel*) ──┐
 │                           │ (同一文件，串行)
 ▼                           │
T3 (core.py - summarize*) ──┘
 │
 ▼
T4 (cli.py - CLI entry)
 │
 ├──────────────────┐
 ▼                  ▼
T5 (error handling) T6 (extended tests)
```

> `*` T2 和 T3 写入同一文件 `core.py`，必须严格串行。

## 风险与注意事项

1. **文件冲突**: T2 和 T3 都写 `core.py`，必须串行执行，不能并发。每个任务执行前需读取当前文件最新状态，在其基础上追加。
2. **TDD 纪律**: 每个 executor 内部各自执行 RED→GREEN→REFACTOR，确保独立测试覆盖。
3. **sample.xlsx 文件**: T1 创建的 sample.xlsx 数据必须与 T2/T3 的测试期望一致，否则测试会失败。
4. **无并发机会**: 由于文件依赖链严格（单文件逐步构建），本计划所有批次均为串行。
