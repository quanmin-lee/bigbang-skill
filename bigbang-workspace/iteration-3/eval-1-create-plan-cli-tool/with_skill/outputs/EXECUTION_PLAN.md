# 执行计划

## 任务总览
| ID | 任务名 | 类型 | 前置依赖 | 涉及文件 |
|----|--------|------|---------|---------|
| T1 | 项目脚手架 | [CRITICAL_PATH] | 无 | pyproject.toml, cli_tool/\_\_init\_\_.py, tests/\_\_init\_\_.py |
| T2 | 读取 Excel 核心逻辑 | [CRITICAL_PATH] | T1 | cli_tool/core.py (read_excel) |
| T3 | 汇总 + 写 CSV 核心逻辑 | [CRITICAL_PATH] | T2 | cli_tool/core.py (summarize_column, write_csv) |
| T4 | CLI 入口 | [CRITICAL_PATH] | T3 | cli_tool/cli.py |
| T5 | 核心逻辑测试 | [CRITICAL_PATH] | T2, T3 | tests/test_core.py |
| T6 | CLI 测试 | [CRITICAL_PATH] | T4, T5 | tests/test_cli.py |
| T7 | 端到端集成验证 | [CRITICAL_PATH] | T5, T6 | 测试数据 + 全流程运行 |

## 批次规划

### Batch 1: [CRITICAL_PATH] 最小主链 — 脚手架 + 核心逻辑（串行）
- T1: 项目脚手架（无依赖，首先执行）
  - 创建目录结构、pyproject.toml、空 `__init__.py`
- T2: 读取 Excel 核心逻辑（依赖 T1）
  - `core.py` 中实现 `read_excel(path) → list[dict]`
- T3: 汇总 + 写 CSV 核心逻辑（依赖 T2）
  - `core.py` 中实现 `summarize_column(data, column) → dict` 和 `write_csv(results, path)`
  - 依赖 T2 产出的数据格式

### Batch 2: [CRITICAL_PATH] 最小主链 — CLI + 测试（串行）
- T4: CLI 入口（依赖 T3）
  - `cli.py` 中实现 `parse_args()` 和 `main()`
- T5: 核心逻辑测试（依赖 T2, T3）
  - 验证 `read_excel`、`summarize_column`、`write_csv` 三个函数
- T6: CLI 测试（依赖 T4, T5）
  - 验证参数解析、main 函数集成
  - 依赖 T5 的测试数据可为 T6 复用

### Batch 3: 集成验证
- T7: 端到端集成验证（依赖 T5, T6）
  - 准备测试 .xlsx 文件
  - 运行全流程确认数据流正确

## 依赖图
```
T1 (脚手架)
  └─→ T2 (read_excel)
        └─→ T3 (summarize + write_csv) ─┐
              └─→ T4 (CLI main) ────────┤
                                         ├─→ T7 (集成验证)
              └─→ T5 (core 测试) ────────┘
                    └─→ T6 (CLI 测试) ───┘
```

## 风险与注意事项
- T2 使用 openpyxl 读取 .xlsx：需确保测试环境中安装了 openpyxl（在 pyproject.toml 中声明）
- T5 的测试依赖 openpyxl，属于集成测试；单元测试可用 mock 替代
- T2/T3 共享 core.py 文件，不能并发执行，必须串行
- 测试数据准备（一个简单的 .xlsx 文件）应作为 T5 的一部分提交到仓库
- pyproject.toml 中建议声明 `[project.scripts]` entry point，使 `cli-tool` 命令可直接调用
