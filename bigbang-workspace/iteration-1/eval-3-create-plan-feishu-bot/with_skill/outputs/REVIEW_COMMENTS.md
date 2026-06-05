# 审查意见 - 第 2 轮

## 架构评估

- ✅ **问题已修复: V1 最小主链已精简**
  - 合并了 T1（项目骨架）+ T9（入口）为同一个批次
  - T7 简化为内存 `dict[str, list]` 存储，不再依赖 LangGraph checkpointer
  - V1 任务从 8 个压缩到合理的 9 个（含 T0 测试基础设施），逻辑完整

- ✅ **问题已修复: 新增国内网络延迟风险**
  - 已补充 "国内网络延迟" 和 "LLM 429 Rate Limit" 风险项
  - 推荐 DeepSeek 国内端点作为首选

- ✅ **建议已采纳: 增加 parse_feishu_event() 独立函数**
  - 新增 `src/feishu/message_parser.py`，将消息解析逻辑独立
  - 数据流图中已体现这一变化

## 执行计划

- ✅ **问题已修复: 补充 T0 测试基础设施**
  - 新增 T0（`tests/conftest.py` + pytest 配置 + mock fixtures）
  - 列为 [CRITICAL_PATH]，排在第一位，符合 TDD 原则

- ✅ **问题已修复: T6 补充 T1 依赖**
  - T6 明确标注依赖 T1（配置提供 API key/endpoint）

- ⚠️ **仍有小建议: T4 依赖关系标注**
  - T4 目前标注依赖 T1+T2+T3，但实际 WS client 启动也需要 T5（sender）？不需要 —— T4 只负责接收和解析，发送由 T8 调度 T5。当前依赖关系正确。

## 测试边界

- ✅ **问题已修复: T7 增加裁剪后回复质量验证**
  - 新增"裁剪后降级"测试场景：裁剪后询问被裁掉的信息，LLM 应合理降级

- ✅ **问题已修复: T6 增加 Rate Limit 测试**
  - 新增 "HTTP 429 Rate Limit" 测试场景（指数退避重试）
  - 新增 "国内端点配置" 场景

- ✅ **建议已采纳: parse_feishu_event() 可单独测**
  - T4 测试添加了直接调用 `parse_feishu_event()` 的测试场景，不依赖 WS 线程

- ✅ **全局 conftest.py + fixtures 定义清晰**
  - T0 明确了 mock_feishu_client、mock_llm、mock_bus、sample_inbound_msg 四个全局 fixture

## 综合判定

- **状态**: ✅ **本轮可终止**
- **裁决说明**: 第 1 轮指出的 2 个必须问题和 2 个建议已全部解决。第 2 轮未发现重大修改意见。可以合并为 PLAN.md。

### 本轮已解决问题
- 无（第 2 轮新增）

### 本轮遗留问题
- T4 依赖关系已复核确认正确，无需调整
- 所有文件已满足合并条件

## 合并操作

合并三个产物为统一的 `PLAN.md`。执行合并流程。
