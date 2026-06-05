# 执行计划

## 任务总览
| ID | 任务名 | 类型 | 前置依赖 | 涉及文件 |
|----|--------|------|---------|---------|
| T1 | 创建项目目录结构和依赖文件 | [CRITICAL_PATH] | 无 | `excel-summary/`, `requirements.txt`, `tests/__init__.py` |
| T2 | 实现 Excel 读取和汇总统计逻辑 | [CRITICAL_PATH] | T1 | `excel_summary/core.py` |
| T3 | 实现 CLI 入口 | [CRITICAL_PATH] | T1, T2 | `excel_summary/cli.py` |
| T4 | 创建测试用 sample.xlsx | [CRITICAL_PATH] | T1 | `sample.xlsx` |
| T5 | 编写单元测试 | [CRITICAL_PATH] | T2, T4 | `tests/test_core.py` |
| T6 | 手动端到端验证 | [ENHANCEMENT] | T1, T2, T3, T4, T5 | CLI 运行验证 |

## 批次规划

### Batch 1a: [CRITICAL_PATH] 基础结构搭建
- **T1**: 创建项目目录结构和依赖文件
- *说明*: 无前置依赖，必须先执行，为后续所有任务提供目录基础

### Batch 1b: [CRITICAL_PATH] 核心实现（并行）
- **T2** [parallel]: 实现 Excel 读取和汇总统计逻辑
- **T4** [parallel]: 创建测试用 sample.xlsx
- *说明*: 均依赖 T1 的目录结构，互不依赖，可安全并行

### Batch 1c: [CRITICAL_PATH] 集成与验证（并行）
- **T3** [parallel]: 实现 CLI 入口
- **T5** [parallel]: 编写单元测试
- *说明*: T3 依赖 T2 的 core.py，T5 依赖 T2 的 core.py 和 T4 的 sample.xlsx。T3 和 T5 互不依赖，可并行。注意：T5 的测试编写需依赖 T2 的导出接口和 T4 的测试数据文件，建议 T2 和 T4 稳定后再执行此批次。

### Batch 2: [ENHANCEMENT] 端到端验证
- **T6**: 手动端到端验证
- *说明*: 依赖所有前置任务完成，运行完整的 CLI 流程

## 依赖图

```
T1 (目录+依赖)
 ├──> T2 (core.py) ──┐
 │                    ├──> T3 (cli.py)
 │                    │
 └──> T4 (sample.xlsx)┐
                      ├──> T5 (test_core.py)
                      │
                      └──> T6 (端到端验证) ←── T3 ──┘
```

```
Batch 1a:     T1
                |
Batch 1b:    T2    T4    (并行)
              |     |
Batch 1c:    T3    T5    (并行)
              |     |
Batch 2:       T6         (串行)
```

## 并发执行策略

由于 executor subagent 环境的限制，实际执行中 T2+T4 和 T3+T5 的并行将按顺序模拟（每个任务独立完成，确保 TDD 纪律）。如果支持真正并行，T2/T4 和 T3/T5 可同时由独立的 executor subagent 执行。

## 输入/输出契约
- 所有 Python 文件放入 `excel-summary/excel_summary/` 包目录
- 测试文件放入 `excel-summary/tests/`
- `core.py` 对外暴露两个函数：`read_column(filepath, column_name)` 和 `summarize(values)`
- `cli.py` 是程序入口，通过 `python -m excel_summary.cli` 调用
- 测试通过 `pytest tests/` 运行

## 执行结果

### Batch 1a: T1 -- Done
- 目录结构创建完成
- `requirements.txt`、`tests/__init__.py`、`excel_summary/__init__.py` 创建完成

### Batch 1b: T2 -- Done (TDD: RED → GREEN → REFACTOR)
- RED: 10 个测试全部失败（ModuleNotFoundError）
- GREEN: `core.py` 实现后 10/10 通过
- REFACTOR: 提取 `_get_column_index`、`_is_numeric` 辅助函数，`_EMPTY_SUMMARY` 常量
- 提交: 1 GREEN commit + 1 REFACTOR commit

### Batch 1b: T4 -- Done
- `sample.xlsx` 创建完成，包含 10 行 mix 数值/非数值/空单元格数据

### Batch 1c: T3 -- Done (TDD: RED → GREEN → REFACTOR)
- RED: 5 个 CLI 测试全部失败（ModuleNotFoundError）
- GREEN: `cli.py` 实现后 5/5 通过
- REFACTOR: 合并异常处理为 `except (FileNotFoundError, ValueError)`
- 提交: 1 GREEN commit + 1 REFACTOR commit

### Batch 1c: T5 -- Done (整合在 T2/T3 的 TDD 中)
- core.py 测试 10 个（summarize 6 + read_column 4）
- cli.py 测试 5 个（output、default、file not found、missing args、numeric format）
- 总共 15 个测试全部通过

### Batch 2: T6 -- Done
- 端到端验证通过：amount 列和 score 列结果均正确
- 错误处理验证通过：文件不存在、列不存在、缺少参数
- 最终状态：**SUCCESS**

## 风险与注意事项
1. **openpyxl 安装**: 需要确保 openpyxl 已安装。通过 `requirements.txt` 管理依赖
2. **T3 与 T5 的顺序**: 虽然理论上可并行，但 T5 编写测试时需要知道 core.py 的确切接口签名，建议 T3 和 T5 由同一批次内的不同 executor 按任意顺序执行
3. **非数值单元格处理**: Excel 列可能包含空值/文本/公式结果，read_column 需要稳健地跳过非数值
4. **CLI 入口样式**: 使用 `if __name__ == "__main__": main()` 确保 `python -m` 和直接执行都可用
5. **UTF-8 编码**: CSV 输出使用 UTF-8 with BOM 以确保 Excel 兼容性（可选），至少确保 UTF-8
