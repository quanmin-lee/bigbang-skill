# 测试验收边界 — Excel 汇总 CLI 工具

## 测试策略

- **测试框架**：pytest（项目已有 pytest 环境）
- **Mock 策略**：
  - 单元测试用 `monkeypatch` 模拟文件操作和 `sys.argv`，避免真实文件依赖
  - 集成测试使用 `tmp_path` 中的真实 `.xlsx` 文件
- **测试文件位置**：`tools/excel-summarizer/tests/`
- **测试文件结构**：
  - `test_cli.py` — 单元测试（mock 文件操作）
  - `test_integration.py` — 集成测试（真实文件）
- **测试数据**：所有 `.xlsx` 文件通过 `openpyxl.Workbook()` 在 `tmp_path` 中动态生成，不提交二进制文件到 git

## 按任务分解

### T1: 搭建项目骨架和依赖 (P0)

- **验收条件**：
  - `tools/excel-summarizer/` 目录存在
  - `tools/excel-summarizer/__init__.py` 存在
  - `requirements.txt` 包含 `openpyxl>=3.1.0`
  - `pyproject.toml` 定义 `excel-sum` 入口点指向 `cli.py:main`
  - `pip install -e .` 可正常安装
- **测试场景**：无测试代码，人工验证

### T2: 核心 CLI 逻辑 (P0)

- **验收条件**：
  - `--input <path>` 参数正确读取 Excel 文件
  - `--column <name>` 参数正确指定汇总列
  - `--output <path>` 参数正确写出 CSV 文件
  - 对指定列的数值单元格求和
  - 非数值单元格被忽略（不报错）
  - 列不存在时提示错误信息并退出（退出码非 0）
  - 输入文件不存在时提示错误信息并退出（退出码非 0）

### T3: 单元测试 (P0)

| 场景 | 测试函数 | 输入 | 预期输出 | 优先级 |
|------|---------|------|---------|--------|
| 正常求和 | `summarize_column()` | 3行数值 (10, 20, 30)，列名 "amount" | 返回 60.0 | P0 |
| 混合类型 | `summarize_column()` | 数值 + 文本 + 空单元格混合 | 只汇总数值部分 | P0 |
| 空列 | `summarize_column()` | 列全为空/非数值 | 返回 0.0 | P0 |
| 参数解析 | `parse_args()` | `--input a.xlsx --column col --output out.csv` | 三个参数正确分离 | P0 |
| CSV 写正确 | `write_csv()` | result=42.0, column="amount" | CSV 内容 `column,sum\namount,42.0` | P0 |
| 单行数据 | `summarize_column()` | 1行数值 99 | 返回 99.0 | P1 |
| 负数值 | `summarize_column()` | -5, 10, -3 | 返回 2.0 | P1 |
| 列不存在 | `summarize_column()` | 列名 "nonexistent" | 抛出 ValueError | P1 |
| 文件不存在 | `read_excel()` | 路径 `no_file.xlsx` | 抛出 FileNotFoundError | P1 |
| 空工作表 | `summarize_column()` | 空列表 `[]` | 返回 0.0 | P1 |

### T4: 端到端集成测试 (P0)

| 场景 | 操作步骤 | 验证内容 | 优先级 |
|------|---------|---------|--------|
| 完整流程 | 创建 .xlsx → 运行 CLI → 读取 CSV | CSV 中总和正确 | P0 |
| 中文列名 | 列名为中文，含中文字段 | 正常读取和汇总，CSV 编码正确 | P1 |
| 大数值 | 列中包含大整数/浮点数 | 精度正确 | P1 |

## 输入/输出契约（T2 函数签名）

| 函数签名 | 输入 | 输出 | 异常 |
|----------|------|------|------|
| `read_excel(path: str) -> list[dict]` | Excel 文件路径 | `[{"col1": val1, "col2": val2}, ...]` | `FileNotFoundError` |
| `summarize_column(data: list[dict], col: str) -> float` | 行数据列表 + 列名 | 数值总和（float） | `ValueError`（列不存在） |
| `write_csv(result: float, col: str, path: str) -> None` | 总和 + 列名 + 路径 | 写入文件，无返回值 | `OSError`（目录不可写） |
| `parse_args(argv: list[str] \| None) -> Namespace` | sys.argv（或测试注入） | `Namespace(input=..., column=..., output=...)` | `SystemExit`（参数缺失） |
| `main()` | 无（读取 sys.argv） | 调用完整管道，`sys.exit(0)` 或 `sys.exit(1)` | — |

## 测试执行顺序

```
T3 (单元测试) ──→ 依赖 T2（基于真实实现编写）
T4 (集成测试) ──→ 依赖 T2+T3（必须在 T2+T3 之后）
```

全部串行执行。

## 注意事项

- 所有测试 `.xlsx` 文件通过 `openpyxl.Workbook()` 在 `tmp_path` 中动态生成，不提交二进制文件到 git
- openpyxl 需要安装后才能跑集成测试 —— `pip install -r tools/excel-summarizer/requirements.txt`
- CSV 写入使用 `encoding='utf-8-sig'`，测试验证时也使用相同编码读取
