# 执行计划

## 任务总览

| ID | 任务名 | 类型 | 前置依赖 | 涉及文件 |
|----|--------|------|---------|---------|
| T0 | 项目初始化 & 依赖声明 | [CRITICAL_PATH] | 无 | `pyproject.toml`, `requirements.txt`, `.gitignore` |
| T1 | CLI 参数解析 | [CRITICAL_PATH] | T0 | `cli.py` |
| T2 | Excel 读取模块 | [CRITICAL_PATH] | T0 | `reader.py` |
| T3 | 数据聚合逻辑 | [CRITICAL_PATH] | T0 | `aggregator.py` |
| T4 | CSV 输出模块 | [CRITICAL_PATH] | T0 | `writer.py` |
| T5 | 主流程编排（集成） | [CRITICAL_PATH] | T1, T2, T3, T4 | `main.py` |
| T6 | 错误处理与边界测试 | [ENHANCEMENT] | T5 | 各模块 + `tests/` |
| T7 | 类型注解与文档 | [ENHANCEMENT] | T5 | 各模块 |

## 批次规划

### Batch 1: [CRITICAL_PATH] 打通主链

- **T0**: 项目初始化
  - 创建 `pyproject.toml`（项目元数据 + 依赖声明：openpyxl）
  - 创建 `requirements.txt`
  - 创建 `.gitignore`（排除 `__pycache__/`, `*.egg-info/`, `.venv/`）
  - 创建 `tests/` 目录
  - _产出物: 三个配置文件_

- **T1, T2, T3, T4 [parallel]**: 四个独立模块并行开发
  - T1: `cli.py` — argparse 解析 `--input`, `--column`, `--output`
  - T2: `reader.py` — 读取 .xlsx，按列提取数据，返回 DataFrame-like 结构
  - T3: `aggregator.py` — 接收数据列表，按指定列分组聚合（sum）
  - T4: `writer.py` — 接收聚合结果，写入 CSV
  - _这四个模块无相互依赖，只依赖 T0 的项目骨架_

- **T5**: 主流程编排
  - `main.py` — 导入 cli/reader/aggregator/writer，串联完整流程
  - _依赖 T1-T4 全部完成_

### Batch 2: [ENHANCEMENT] 功能完善

- **T6**: 错误处理与边界测试
  - 文件不存在 → 用户友好错误
  - 列名不存在 → 清晰提示
  - 非数值数据 → warning + skip
  - 空文件 → 正确处理

- **T7**: 类型注解与 README
  - 补齐函数签名类型注解
  - 编写 README.md

## 依赖图

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

## 风险与注意事项

- **T2 风险**: openpyxl 的 `load_workbook` 默认只读模式为 `read_only=False`；大文件建议设为 `read_only=True`。V1 用默认模式（小文件优先），标注为已知问题。
- **T1-T4 并行可行性**: 四个模块只依赖统一的接口约定（数据格式），需在并行前约定好中间数据结构——推荐以 `list[dict]` 或 `pandas.DataFrame` 作为模块间传递格式。
- **T5 集成风险**: 如果 T1-T4 的接口约定不一致（如 reader 返回 dict 而 aggregator 期望 list），T5 需要协调修改。建议在 Batch 1 开始时先约定接口契约（`interface_contract.md` 或代码注释）。
