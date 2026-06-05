# 测试验收边界

## 测试策略

- **测试框架**: pytest
- **Mock 策略**:
  - 文件读取：使用 `pandas.testing` 生成模拟 DataFrame，避免真实 Excel 依赖（T3）
  - 文件写入：使用 `tempfile` 临时目录或 `io.StringIO`（T5）
  - CLI 参数：使用 `pytest` 的 `monkeypatch` 模拟 `sys.argv`（T2）
- **fixture 管理**: 合并在 `tests/conftest.py` 中
- **测试粒度**: 以模块为单位的单元测试 + 端到端集成测试

## 按任务分解

### T2: CLI 参数解析 (P0)

- **验收条件**:
  - argparse 正确注册 `--input`、`--column`、`--output` 三个参数
  - 缺少必选参数时打印 usage 并退出
  - 参数值正确传递给处理逻辑
- **测试场景**:

| 场景 | 输入 | 预期输出 | 优先级 |
|------|------|---------|--------|
| 正常路径 | `--input test.xlsx --column 金额 --output result.csv` | Namespace(input='test.xlsx', column='金额', output='result.csv') | P0 |
| 缺少参数 | 只传 `--input test.xlsx` | SystemExit (argparse 报错) | P0 |
| 空字符串路径 | `--input "" --column 金额 --output r.csv` | 合理报错或拒绝 | P1 |
| 帮助标志 | `--help` | 打印帮助信息后 SystemExit(0) | P1 |

- **RED 测试**: 调用 parse_args(['--input', 'test.xlsx']) 并断言缺少 --column 和 --output 时抛出 SystemExit
- **GREEN 最小实现**: argparse.ArgumentParser 定义三个参数，调用 parse_args()

### T3: Excel 读取模块 (P0)

- **验收条件**:
  - 能读取有效的 .xlsx 文件并返回 pandas DataFrame
  - 文件不存在或格式错误时抛出有意义的异常
  - 列名匹配支持字符串列名
- **测试场景**:

| 场景 | 输入 | 预期输出 | 优先级 |
|------|------|---------|--------|
| 正常路径 | 含数值列的 DataFrame | 返回完整的 DataFrame | P0 |
| 文件不存在 | 不存在的路径 | FileNotFoundError | P0 |
| 空 Excel | 无数据的 .xlsx | 空 DataFrame | P1 |
| 非 .xlsx 格式 | .csv 或 .txt 文件 | 格式错误异常 | P1 |

- **RED 测试**: read_excel('nonexistent.xlsx') 断言抛出 FileNotFoundError
- **GREEN 最小实现**: pandas.read_excel 封装，基础异常转换

### T4: 数值汇总模块 (P0)

- **验收条件**:
  - 对指定数值列执行 sum 聚合
  - 非数值列参与计算时报错或忽略
  - 空 DataFrame 返回空结果
- **测试场景**:

| 场景 | 输入 | 预期输出 | 优先级 |
|------|------|---------|--------|
| 正常汇总 | 含分类列 + 数值列的 DataFrame | groupby + sum 后的 DataFrame | P0 |
| 空数据 | 空 DataFrame | 空 DataFrame | P1 |
| 列不存在 | 列名不包含在 DataFrame 中 | KeyError | P0 |
| 非数值列 | 列全为字符串 | 报错或返回空系列 | P1 |

- **RED 测试**: summarize(df, 'nonexistent_column') 断言抛出 KeyError
- **GREEN 最小实现**: df.groupby(by=group_cols).agg({value_col: 'sum'}).reset_index()

### T5: CSV 输出模块 (P0)

- **验收条件**:
  - 将 DataFrame 写入指定路径的 CSV 文件
  - 输出目录不存在时自动创建
  - 写入后文件可读
- **测试场景**:

| 场景 | 输入 | 预期输出 | 优先级 |
|------|------|---------|--------|
| 正常写入 | DataFrame + 合法路径 | 文件存在且内容正确 | P0 |
| 只读目录 | 不可写的路径 | PermissionError | P1 |
| 空 DataFrame | 空 DataFrame | 写入空 CSV | P1 |

- **RED 测试**: write_csv(df, '/nonexistent_dir/out.csv') 断言抛出异常
- **GREEN 最小实现**: df.to_csv(output_path, index=False)

### T6: CLI 主流程集成 (P0)

- **验收条件**:
  - 完整链路：参数解析 → 读取 → 汇总 → 输出
  - 各模块异常被统一捕获并以用户友好方式输出
  - 退出码 0 表示成功，非 0 表示失败
- **测试场景**:

| 场景 | 输入 | 预期输出 | 优先级 |
|------|------|---------|--------|
| 完整流水线 | 真实 Excel 文件 + 参数 | 输出 CSV 文件 | P0 |
| 文件不存在 | 不存在的输入 | stderr 报错 + sys.exit(1) | P0 |

- **RED 测试**: 用 monkeypatch 模拟 sys.argv，调用 main() 并检查文件是否生成
- **GREEN 最小实现**: cli.py 中 main() 串联 parse_args() → read_excel() → summarize() → write_csv()

## 测试执行顺序

```
并发: T2 / T3 / T5 的单元测试
  └── T4 依赖 T3 接口测试就绪
       └── T6 集成测试依赖所有模块就绪
            └── T8 端到端测试 (最后)
```

## 注意事项

- T3 测试需要 pandas 和 openpyxl 都安装在测试环境中
- T2 测试需要 mock sys.argv，注意测试间隔离（使用 pytest monkeypatch）
- T4 的测试需要约定 T3 返回的 DataFrame 格式（列名、索引等）
- 测试用的 .xlsx fixture 文件可使用 openpyxl 在 conftest.py 中动态生成，避免提交二进制文件到版本控制
