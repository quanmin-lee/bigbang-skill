# 架构评估报告

## 需求理解

开发一个 Python CLI 工具，功能为：
1. 读取 Excel 文件（.xlsx）
2. 按指定列汇总数值数据（求和）
3. 输出汇总结果的 CSV 文件

CLI 参数：
- `--input`：输入 Excel 文件路径
- `--column`：要汇总的列名/列号
- `--output`：输出 CSV 文件路径

这是一个全新的独立工具，不依赖现有项目代码。

## 项目概览

本工具是一个全新的命令行项目，从零搭建。不需要与现有代码库集成。

- **项目类型**: 独立的 Python CLI 工具
- **技术栈**: Python 3.8+，依赖 `openpyxl` 或 `pandas` 处理 Excel，标准库 `csv` 输出
- **关键数据流**: 输入参数解析 → Excel 文件读取 → 列数据提取汇总 → CSV 写入
- **部署形态**: pip-installable package 或 standalone script

## 维度评分

| 维度 | 评分 | 依据 |
|------|------|------|
| 架构健康度 | 不适用 | 新项目，从零搭建，无需评估现有架构 |
| 可维护性 | 不适用 | 新项目，需在设计中考虑 |
| AI 可读性 | 不适用 | 新项目，需在设计中考虑 |
| 模块化 | 不适用 | 新项目，需在设计中考虑 |
| 可测试性 | 不适用 | 新项目，需在设计中考虑 |

## 建议架构设计（新项目）

### 模块划分

```
excel-summarizer/
├── src/
│   ├── cli.py              # CLI 入口，argparse 参数解析
│   ├── reader.py            # Excel 文件读取与列提取
│   ├── summarizer.py        # 数值汇总逻辑
│   └── writer.py            # CSV 输出
├── tests/
│   ├── test_reader.py
│   ├── test_summarizer.py
│   └── test_writer.py
├── requirements.txt
└── setup.py / pyproject.toml
```

### 关键数据流

```
CLI args (--input, --column, --output)
  → cli.py parse
  → reader.py: load_excel(path) → DataFrame
  → summarizer.py: summarize(df, column) → aggregated data
  → writer.py: write_csv(data, output_path) → CSV file
```

### 依赖选型建议

| 方案 | 依赖 | 优点 | 缺点 |
|------|------|------|------|
| openpyxl | openpyxl | 轻量，纯 Excel 处理 | 需手动处理数值检测 |
| pandas | pandas + openpyxl | 开发快，API 丰富 | 依赖较重 |

建议 V1 用 pandas（开发效率高），V2 考虑 openpyxl 瘦身。

## 最小主链（V1）

| 改动点 | 涉及文件 | 风险 | 说明 |
|--------|---------|------|------|
| 项目骨架 | pyproject.toml, requirements.txt, src/cli.py | 低 | 标准 Python 项目初始化 |
| Excel 读取 | src/reader.py | 低 | pandas.read_excel() 封装 |
| 列汇总 | src/summarizer.py | 低 | groupby + sum 聚合 |
| CSV 输出 | src/writer.py | 低 | to_csv() 封装 |
| CLI 入口 | src/cli.py | 低 | argparse 三个参数 |
| 单元测试 | tests/* | 中 | 需要 mock 文件读写 |

## V2+ 建议

- 支持多列汇总（--columns 多值）
- 支持自定义聚合函数（sum/avg/count/min/max）
- 支持 Excel 多 sheet 选择（--sheet）
- 支持列名模糊匹配（--column 支持正则）
- 添加 --verbose 调试模式
- 打包为 pip 可安装包
- 使用 openpyxl 替代 pandas 减小依赖体积

## 风险与注意事项

- Excel 文件编码问题（xlsx 为二进制，风险低）
- 非数值列的处理（需提供清晰的错误信息）
- 大文件性能（V1 对 10MB+ 文件需注意内存）
- 列不存在时的错误提示（argparse 级别校验或读取后报错）
- Windows 路径处理（使用 pathlib 跨平台兼容）
