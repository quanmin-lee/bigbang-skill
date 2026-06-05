# 执行计划

## 任务总览

| ID | 任务名 | 类型 | 前置依赖 | 涉及文件 |
|----|--------|------|---------|---------|
| T1 | 搭建项目骨架和依赖 | [CRITICAL_PATH] | 无 | `tools/excel-summarizer/`, `requirements.txt`, `pyproject.toml` |
| T2 | 实现核心 CLI 逻辑 | [CRITICAL_PATH] | T1 | `tools/excel-summarizer/cli.py` |
| T3 | 编写单元测试 | [CRITICAL_PATH] | T1 | `tools/excel-summarizer/tests/test_cli.py` |
| T4 | 端到端集成测试验证 | [CRITICAL_PATH] | T2, T3 | `tools/excel-summarizer/tests/test_integration.py` |

## 批次规划

### Batch 1: [CRITICAL_PATH] 打通主链

- **T1: 搭建项目骨架和依赖** [serial]
  - 创建 `tools/excel-summarizer/` 目录
  - 创建 `requirements.txt`（仅 `openpyxl`）
  - 创建 `pyproject.toml`（`[project.scripts]` 定义 `excel-sum` 入口点）
  - 创建 `tools/excel-summarizer/__init__.py`

- **T2 & T3: 核心逻辑 + 测试** [parallel]
  - T2 和 T3 可**并发执行**，因为它们都只依赖 T1，互不依赖
  - T2 实现 `cli.py`：`parse_args()` + `read_excel()` + `summarize_column()` + `write_csv()` + `main()`
  - T3 编写 `tests/test_cli.py`：单元测试，mock 文件操作

- **T4: 端到端集成测试** [serial, 依赖 T2+T3]
  - 使用真实 `.xlsx` 测试文件
  - 验证完整 CLI 调用链
  - 验证输出 CSV 内容正确

### Batch 2: [ENHANCEMENT] 功能完善（V2+）

| ID | 任务名 | 前置依赖 | 涉及文件 |
|----|--------|---------|---------|
| T5 | 支持多列汇总 | T2 | `cli.py` + 测试 |
| T6 | 支持分组汇总 | T2 | `cli.py` + 测试 |
| T7 | 错误处理优化（文件不存在、列不存在等） | T2 | `cli.py` + 测试 |

## 依赖图

```
T1 (项目骨架)
 ├──→ T2 (核心逻辑) ──→ T4 (集成测试) ──→ V1 完成
 └──→ T3 (单元测试) ──→ T4 (集成测试)
```

V2+ 增强任务全部依赖 T2，可以自由并发。

## 风险与注意事项

- **T2 和 T3 并发**：虽然是 [parallel]，但 T3 测试需要 mock T2 的函数签名。建议 T2 先定义好函数签名（stub），T3 基于 stub 写测试，T2 再填充实现。如果严格并发可能有版本不一致风险。
- **openpyxl 安装**：如果当前环境没有 openpyxl，T2 开始前需要先 `pip install -r requirements.txt`
- **pyproject.toml 配置**：确认 Python 版本设置与项目一致（>=3.10）
