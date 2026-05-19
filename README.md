# AgentEvolution

让 Agent 具备**可移植、可进化的问题处理能力**。

## 项目概述

构建一个"问题处理操作系统"，可以加载到任何 Agent 的 Soul 里，使其具备：
- 深度问题分析能力
- 专业领域知识学习能力
- 工具审核与最优解选择能力
- 自主进化能力（Skill编排 + 工具权重）

## 目录结构

```
AgentEvolution/
├── docs/                    # 设计文档
│   ├── 01-问题处理OS架构设计.md
│   ├── 06-完整流程图.md
│   └── ...
├── agent-problem-os/        # 核心代码
│   ├── modules/             # 8个模块实现
│   │   ├── main.py          # 入口（整合全流程）
│   │   ├── preprocess.py    # 01问题预处理
│   │   ├── cognition.py     # 02问题认知（三层探测）
│   │   ├── kb_store.py      # 03知识库存储
│   │   ├── analysis.py      # 04问题分析
│   │   ├── tool_audit.py    # 05工具审核（SlowMist）
│   │   ├── tool_install.py  # 06工具安装
│   │   ├── todo.py          # 07Todo计划
│   │   └── evolution.py     # 08反馈进化
│   ├── soul/                # Agent人格+方法论
│   │   ├── personality.md
│   │   └── methodology.md
│   ├── config/
│   │   └── config.yaml
│   └── tests/
└── README.md
```

## 快速开始

### 安装

```bash
git clone <repo>
cd AgentEvolution/agent-problem-os
```

### 运行完整流程

```bash
python3 modules/main.py "如何用Python实现并发编程？以及如何优化性能？"
```

### 测试所有模块

```bash
python3 modules/main.py "你的问题"
```

## 七大模块

| 模块 | 状态 | 说明 |
|------|------|------|
| 01-问题预处理 | ✅ 完成 | 拆解问题、判断类型、评估复杂度 |
| 02-问题认知 | ✅ 完成 | 三层知识探测机制（置信度自评→知识库验证→主动探测） |
| 03-知识库存储 | ✅ 完成 | Markdown格式存储，支持搜索和归档 |
| 04-问题分析 | ✅ 完成 | 深度分析+方法论选择（按领域） |
| 05-工具审核 | ✅ 完成 | SlowMist安全审计（模拟），评分前2候选 |
| 06-工具安装 | ✅ 完成 | 安装通过审核的工具，支持备选 |
| 07-Todo计划 | ✅ 完成 | 任务状态管理，依赖关系处理 |
| 08-反馈进化 | ✅ 完成 | 根据评分自动调整方法论+工具权重 |

## 完整流程

```
用户问题
    ↓
┌──────────────┐
│ 01预处理      │ → 拆解问题，判断领域和复杂度
└──────┬───────┘
       ↓
┌──────────────┐
│ 02认知（三层）│ → 置信度≥80%？知识库命中？发现盲区？
└──────┬───────┘
       ↓ 触发学习流程时
┌──────────────┐
│ 03知识库存储  │ → 学习并保存领域知识
└──────┬───────┘
       ↓
┌──────────────┐
│ 04问题分析    │ → 深度分析+方法论选择
└──────┬───────┘
       ↓
┌──────────────┐
│ 05工具审核    │ → 评分前2 + SlowMist审计
└──────┬───────┘
       ↓
┌──────────────┐
│ 06工具安装    │ → 安装，失败换备选
└──────┬───────┘
       ↓
┌──────────────┐
│ 07Todo计划    │ → 执行任务计划
└──────┬───────┘
       ↓
┌──────────────┐
│ 08反馈进化    │ → 评分→分析→调整权重（下次更准）
└──────────────┘
```

## 反馈进化机制

问题处理完后可对结果打分（1-5星），系统自动分析哪些**方法论+工具组合**效果好，持续调整权重：

```python
from modules.evolution import FeedbackEvolution

evo = FeedbackEvolution()

# 记录处理结果
evo.record(
    question="如何优化Python性能？",
    domain="技术类",
    methodology="性能剖析法",
    tools_selected=["py-spy", "perf"],
    tool_audit_passed=True
)

# 处理完打分
evo.rate(record_id=1, stars=5, notes="方法论很准")

# 分析并更新权重
evo.apply_weights(evo.adapt())

# 查看进化报告
print(evo.get_report())
```

进化数据持久化在 `~/.hermes/agent-problem-os/evolution_data.json`，不修改代码本身。

## 文档索引

- [架构设计](docs/01-问题处理OS架构设计.md)
- [完整流程图](docs/06-完整流程图.md)
- [模块输入输出规范](docs/07-模块输入输出规范.md)
- [OpenClaw Soul接入设计](docs/08-OpenClaw-Soul接入设计.md)
