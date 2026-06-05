# 测试验收边界

## 测试策略

- **测试框架**：pytest（项目已有 pytest 环境）
- **Mock 策略**：
  - 单元测试用 `monkeypatch` 或 `unittest.mock` 模拟文件读写，避免真实文件依赖
  - 集成测试使用临时目录中的真实 `.xlsx` 文件
- **测试文件位置**：`tools/excel-summarizer/tests/`
- **测试文件结构**：
  - `test_cli.py` — 单元测试（mock 文件操作）
  - `test_integration.py` — 集成测试（真实文件）
  - `fixtures/` — 测试用 Excel 文件

## 按任务分解

### T1: 搭建项目骨架和依赖 (P0)

- **验收条件**:
  - `tools/excel-summarizer/` 目录存在
  - `tools/excel-summarizer/__init__.py` 存在
  - `requirements.txt` 包含 `openpyxl`
  - `pyproject.toml` 定义 `excel-sum` 入口点指向 `cli.py:main`
  - `pip install -e .` 可正常安装
- **测试场景**: 无测试代码，人工验证

### T2: 核心 CLI 逻辑 (P0)

- **验收条件**:
  - `--input <path>` 参数正确读取 Excel 文件
  - `--column <name>` 参数正确指定汇总列
  - `--output <path>` 参数正确写出 CSV 文件
  - 对指定列的数值单元格求和
  - 非数值单元格被忽略（不报错）
  - 列不存在时提示错误信息并退出
  - 输入文件不存在时提示错误信息并退出
- **测试场景**:

| 场景 | 输入 | 预期输出 | 优先级 |
|------|------|---------|--------|
| 正常路径 | 3行数值的 Excel，指定数值列 | CSV 包含求和结果 | P0 |
| 空列 | 列中有非数值（文本/空单元格） | 只汇总数值部分 | P0 |
| 列不存在 | 指定一个不存在的列名 | 抛出错误，退出码非 0 | P1 |
| 文件不存在 | --input 指向不存在的路径 | 抛出错误，退出码非 0 | P1 |
| 单行数据 | 只有1行数值 | 正确求和 | P1 |

- **RED 测试**: 创建测试文件，调用 `summarize_column()` 传入已知数据，验证返回正确总和
- **GREEN 最小实现**: 用 `openpyxl.load_workbook()` 读取活动工作表，遍历指定列，`isinstance(cell.value, (int, float))` 判断数值类型，`sum()` 累加

### T3: 单元测试 (P0)

- **验收条件**:
  - `test_cli.py` 覆盖 T2 中所有测试场景
  - 使用 `tmp_path` fixture 创建临时文件
  - 测试 `read_excel()`、`summarize_column()`、`write_csv()` 三个纯函数
  - 用 `monkeypatch` 模拟 `sys.argv` 测试 CLI 参数解析
- **测试场景**:

| 场景 | 方法 | 预期 | 优先级 |
|------|------|------|--------|
| 正常求和 | `summarize_column()` | 返回正确总和 | P0 |
| 混合类型列 | `summarize_column()` | 忽略非数值 | P0 |
| 空工作表 | `summarize_column()` | 返回 0 | P1 |
| 参数解析 | `parse_args()` | 正确解析三个参数 | P0 |
| 写 CSV | `write_csv()` | CSV 内容格式正确 | P0 |

### T4: 端到端集成测试 (P0)

- **验收条件**:
  - 创建真实 `.xlsx` 文件，通过 CLI 调用（`subprocess` 或直接调用 `main()`）
  - 验证输出 CSV 内容
- **测试场景**:

| 场景 | 操作 | 验证 | 优先级 |
|------|------|------|--------|
| 完整流程 | 创建 .xlsx → 运行 CLI → 读取 CSV | CSV 中总和正确 | P0 |
| 中文列名 | 列名为中文 | 正常读取和汇总 | P1 |

## 测试执行顺序

```
T3 (单元测试) ──→ 可与 T2 并发（基于约定接口）
T4 (集成测试) ──→ 必须在 T2+T3 之后
```

## 注意事项

- 测试用 `.xlsx` 文件通过 `openpyxl.Workbook()` 在 `tmp_path` 中动态生成，不提交二进制文件到 git
- openpyxl 需要安装后才能跑集成测试 —— 在 CI 或 setup 阶段 `pip install -r requirements.txt`
- UTF-8 编码：写入 CSV 时 `open()` 指定 `encoding='utf-8-sig'` 以兼容 Excel 打开中文 CSV
