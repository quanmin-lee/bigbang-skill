# 执行计划

## 任务总览
| ID | 任务名 | 类型 | 前置依赖 | 涉及文件 |
|----|--------|------|---------|---------|
| T1 | 创建项目目录结构和依赖文件 | [CRITICAL_PATH] | 无 | 目录结构, requirements.txt, sample.xlsx, `__init__.py` |
| T2 | 实现 Excel 读取和汇总统计逻辑 | [CRITICAL_PATH] | T1 | `excel_summary/core.py` |
| T3 | 实现 CLI 入口 | [CRITICAL_PATH] | T1, T2 | `excel_summary/cli.py` |
| T4 | 编写单元测试 | [CRITICAL_PATH] | T2, T3 | `tests/test_core.py`, `tests/test_cli.py` |
| T5 | 端到端集成验证 | [ENHANCEMENT] | T1, T2, T3, T4 | CLI 运行验证 |

## 批次规划

### Batch 1a: [CRITICAL_PATH] 基础结构搭建
- **T1**: 创建项目目录结构和依赖文件
- *说明*: 无前置依赖，必须先执行。创建 excel-summary/、excel_summary/、tests/ 目录结构，写入 requirements.txt、sample.xlsx、`__init__.py` 文件。

### Batch 1b: [CRITICAL_PATH] 核心逻辑实现
- **T2**: 实现 Excel 读取和汇总统计逻辑
- *说明*: 依赖 T1 的目录结构。实现 `read_column()` 和 `summarize()` 两个核心函数。使用 TDD 方式：先写测试（RED）→ 实现（GREEN）→ 重构（REFACTOR）。

### Batch 1c: [CRITICAL_PATH] CLI 与测试（可并行）
- **T3** [parallel]: 实现 CLI 入口
- **T4** [parallel]: 编写单元测试
- *说明*: T3 依赖 T2 的 `core.py` 导出函数。T4 依赖 T2 的导出接口和 sample.xlsx。T3 和 T4 互不依赖，可并行执行。

### Batch 2: [ENHANCEMENT] 端到端验证
- **T5**: 端到端集成验证
- *说明*: 依赖所有前置任务完成。运行完整 CLI 流程验证输出正确性，测试错误处理路径。

## 依赖图

```
T1 (目录+依赖)
 |
 ├──> T2 (core.py)
 |     |
 |     ├──> T3 (cli.py)
 |     |
 |     └──> T4 (tests) 
 |
 └──> T5 (端到端验证) ←── T3 ──┘
```

```
Batch 1a:     T1
                |
Batch 1b:     T2
              / \
Batch 1c:   T3   T4    (并行)
              \ /
Batch 2:     T5         (串行)
```

## 执行结果

### Batch 1a: T1 -- Done
- 目录结构创建完成
- `requirements.txt`、`__init__.py`、`sample.xlsx` 就绪
- **提交**: `chore: scaffold excel-summary project structure with dependencies and test data`

### Batch 1b: T2 -- Done (TDD: RED → GREEN → REFACTOR)
- RED: 测试文件创建，测试因 ModuleNotFoundError 失败
- GREEN: `core.py` 实现后全部测试通过
- REFACTOR: 提取 `_get_column_index`、`_is_numeric` 辅助函数，`_EMPTY_SUMMARY` 常量
- **提交**: `test: add tests for excel-summary core module` → `feat: implement core.py with read_column and summarize` → `refactor: extract helpers and constants in core.py`

### Batch 1c: T3 -- Done (TDD: RED → GREEN → REFACTOR)
- RED: CLI 测试创建，因 ModuleNotFoundError 失败
- GREEN: `cli.py` 实现后测试通过
- REFACTOR: 合并异常处理到 `EXIT_FAILURE` 常量
- **提交**: `test: add tests for CLI argument parsing and integration` → `feat: implement cli.py with argument parsing and CSV output` → `refactor: consolidate exception handling with EXIT_FAILURE constant in cli.py`

### Batch 1c: T4 -- Done
- `test_core.py`: 10 个测试用例（summarize 6 + read_column 4）
- `test_cli.py`: 5 个测试用例
- 全部 15 个测试通过 ✅
- **注意**: T4 测试已合并到 T2/T3 的 TDD 流程中

### Batch 2: T5 -- Pending（待执行验证）
- **计划**: 运行 CLI 验证统计值正确性 + 错误处理

## 风险与注意事项
1. **openpyxl 依赖**: 必须安装，通过 requirements.txt 管理
2. **T3/T4 并发**: 无数据依赖，可安全并行。T3 写 cli.py，T4 写测试文件，不冲突
3. **非数值处理**: read_column 需要稳健跳过 None/字符串/bool
4. **CSV 输出格式**: 使用 `stat,value` 两列，UTF-8 编码
5. **临时文件清理**: 测试中使用 NamedTemporaryFile 需确保 cleanup
