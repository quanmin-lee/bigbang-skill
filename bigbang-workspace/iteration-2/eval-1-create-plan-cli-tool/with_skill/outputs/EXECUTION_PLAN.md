# 执行计划

## 任务总览

| ID | 任务名 | 类型 | 前置依赖 | 涉及文件 |
|----|--------|------|---------|---------|
| T1 | 项目初始化 | [CRITICAL_PATH] | 无 | pyproject.toml, requirements.txt, src/__init__.py, tests/__init__.py |
| T2 | CLI 参数解析 | [CRITICAL_PATH] | T1 | src/cli.py |
| T3 | Excel 读取模块 | [CRITICAL_PATH] | T1 | src/reader.py |
| T4 | 数值汇总模块 | [CRITICAL_PATH] | T3 | src/summarizer.py |
| T5 | CSV 输出模块 | [CRITICAL_PATH] | T1 | src/writer.py |
| T6 | CLI 主流程集成 | [CRITICAL_PATH] | T2, T4, T5 | src/cli.py (main 函数) |
| T7 | 单元测试 | [ENHANCEMENT] | T3, T4, T5, T6 | tests/*.py |
| T8 | 集成测试 | [ENHANCEMENT] | T7 | tests/test_integration.py |

## 批次规划

### Batch 1: [CRITICAL_PATH] 打通主链

- **T1: 项目初始化** — 创建项目目录、pyproject.toml、requirements.txt、空模块文件
- **T2: CLI 参数解析** — 使用 argparse 实现 --input、--column、--output 三个参数
- **T3: Excel 读取模块** — 封装 pandas.read_excel()，按列名/列号提取数据
- **T5: CSV 输出模块** — 封装 DataFrame.to_csv()

> 注：T1 必须最先完成。T2、T3、T5 在 T1 完成后可并行。T2 和 T5 间无数据依赖。

### Batch 2: [CRITICAL_PATH] 主链集成

- **T4: 数值汇总模块** — 按指定列 groupby + sum 聚合（依赖 T3 的输出接口）
- **T6: CLI 主流程集成** — main() 串联读取→汇总→输出（依赖 T2、T4、T5）

> 注：T4 需要 T3 的契约（reader 返回的 DataFrame 格式）。T6 需要所有下游模块就绪。

### Batch 3: [ENHANCEMENT] 测试覆盖

- **T7: 单元测试** — reader、summarizer、writer 单元测试
- **T8: 集成测试** — 端到端用真实 Excel 文件测试

> 注：T7 和 T8 可并行。

## 依赖图

```
T1 (项目初始化)
 ├── T2 (CLI 参数解析)
 ├── T3 (Excel 读取) ──→ T4 (数值汇总)
 └── T5 (CSV 输出)
                          └── T6 (主流程集成)
                                    ├── T7 (单元测试)
                                    └── T8 (集成测试)
```

## 风险与注意事项

- T3 依赖 pandas 和 openpyxl，需确保 requirements.txt 写入正确
- T4 的输入契约依赖于 T3 的输出格式，建议 T3 和 T4 先约定接口再各自实现
- T6 是串联关键点，如果 T2/T4/T5 接口不一致会导致阻塞
- T7/T8 需要 mock Excel 文件或使用测试用的 fixtures
- 建议在 T1 阶段就确定好各模块的接口签名（contract-first）
