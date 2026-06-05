# 执行计划 — Excel 汇总 CLI 工具

## 任务总览

| ID | 任务名 | 类型 | 前置依赖 | 涉及文件 |
|----|--------|------|---------|---------|
| T1 | 搭建项目骨架和依赖 | [CRITICAL_PATH] | 无 | `tools/excel-summarizer/`, `requirements.txt`, `pyproject.toml`, `__init__.py` |
| T2 | 实现核心 CLI 逻辑 | [CRITICAL_PATH] | T1 | `tools/excel-summarizer/cli.py` |
| T3 | 编写单元测试 | [CRITICAL_PATH] | T2 | `tools/excel-summarizer/tests/test_cli.py` |
| T4 | 端到端集成测试 | [CRITICAL_PATH] | T2, T3 | `tools/excel-summarizer/tests/test_integration.py` |

## 批次规划

### Batch 1: [CRITICAL_PATH] 打通主链（串行）

**T1: 搭建项目骨架和依赖** [serial]
- 创建 `tools/excel-summarizer/` 目录
- 创建 `tools/excel-summarizer/__init__.py`
- 创建 `requirements.txt`（仅 `openpyxl>=3.1.0`）
- 创建 `pyproject.toml`（`[project.scripts]` 定义 `excel-sum` 入口点）

**T2: 实现核心 CLI 逻辑** [serial, 依赖 T1]
- 文件：`tools/excel-summarizer/cli.py`
- 函数清单：

| 函数 | 职责 |
|------|------|
| `parse_args(argv: list[str] \| None = None) -> argparse.Namespace` | 解析 `--input`, `--column`, `--output` |
| `read_excel(path: str) -> list[dict]` | 读取 `.xlsx`，返回 `[{col: val}, ...]` |
| `summarize_column(data: list[dict], column: str) -> float` | 对指定列求和，跳过非数值单元格 |
| `write_csv(result: float, column: str, path: str)` | 写 CSV，格式 `column,sum` |
| `main()` | 组合以上四步，作为 CLI 入口 |

**T3: 编写单元测试** [serial, 依赖 T2]
- 文件：`tools/excel-summarizer/tests/test_cli.py`
- 使用 `tmp_path` fixture + `monkeypatch` 模拟文件操作和 `sys.argv`
- 覆盖场景：正常求和、混合类型、空列、列不存在、文件不存在、单行数据、负数值

**T4: 端到端集成测试** [serial, 依赖 T2+T3]
- 文件：`tools/excel-summarizer/tests/test_integration.py`
- 用 `openpyxl.Workbook()` 在 `tmp_path` 动态生成测试 Excel 文件
- 调用完整 CLI 流程，验证输出 CSV 内容

### 依赖关系

```
T1 (项目骨架)
 └──→ T2 (核心逻辑)
        └──→ T3 (单元测试)
               └──→ T4 (集成测试)
                      └──→ ✅ V1 完成
```

全部串行。T2 先完成真实实现，T3 基于真实实现编写测试。不建议 T2/T3 并发，因为 T3 需要确认 `summarize_column()` 的真实函数签名和返回值结构。

### Batch 2: [ENHANCEMENT] V2+ 增强（可并发）

| ID | 任务名 | 前置依赖 | 涉及文件 | 可并发 |
|----|--------|---------|---------|--------|
| T5 | 支持多列汇总（`--columns`） | T2 | `cli.py` + 测试 | 是（与 T6/T7 无冲突） |
| T6 | 支持分组汇总（`--group-by`） | T2 | `cli.py` + 测试 | 是 |
| T7 | 错误处理优化（文件不存在、列不存在等） | T2 | `cli.py` + 测试 | 是 |

## 项目结构

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

## 工作估算

| 任务 | 预估时间 |
|------|---------|
| T1 搭建骨架 | 5 min |
| T2 核心逻辑 | 20 min |
| T3 单元测试 | 15 min |
| T4 集成测试 | 10 min |
| **Batch 1 合计** | **~50 min** |

## 风险与注意事项

- **openpyxl 环境依赖**：执行 CLI 或测试前必须 `pip install -r tools/excel-summarizer/requirements.txt`
- **CSV 编码**：`open()` 写 CSV 时指定 `encoding='utf-8-sig'`，确保 Windows Excel 中文不乱码
- **空列健壮性**：`summarize_column()` 需跳过非数值（`isinstance(v, (int, float))`），不抛异常
- **入口点注册**：`pyproject.toml` 中 `[project.scripts]` 配置需确认 Python 版本 >=3.10
