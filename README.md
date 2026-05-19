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
├── agent-problem-os/       # 核心代码
│   ├── modules/            # 7个模块实现
│   │   ├── preprocess.py   # 问题预处理
│   │   ├── todo.py         # Todo计划
│   │   └── main.py         # 入口
│   ├── soul/               # Agent人格+方法论
│   │   ├── personality.md
│   │   └── methodology.md
│   ├── config/             # 配置文件
│   │   └── config.yaml
│   └── tests/              # 测试
└── README.md
```

## 快速开始

### 安装

```bash
git clone <repo>
cd AgentEvolution/agent-problem-os
```

### 测试

```bash
# 测试预处理模块
python3 tests/test_preprocess.py

# 测试Todo模块
python3 tests/test_todo.py
```

### 运行

```bash
# 预处理一个问题
python3 modules/main.py "如何用Python实现并发编程？以及如何优化性能？"
```

## 七大模块

| 模块 | 状态 | 说明 |
|------|------|------|
| 01-问题预处理 | ✅ 完成 | 拆解问题、判断类型、评估复杂度 |
| 02-问题认知 | 🔜 待做 | 三层知识探测机制 |
| 03-知识库存储 | 🔜 待做 | Markdown格式存储 |
| 04-问题分析 | 🔜 待做 | 深度分析+方法论选择 |
| 05-工具审核 | 🔜 待做 | SlowMist安全审计 |
| 06-工具安装 | 🔜 待做 | 安装通过审核的工具 |
| 07-Todo计划 | ✅ 完成 | 任务状态管理 |

## 文档索引

- [架构设计](docs/01-问题处理OS架构设计.md)
- [完整流程图](docs/06-完整流程图.md)
- [模块输入输出规范](docs/07-模块输入输出规范.md)
- [OpenClaw Soul接入设计](docs/08-OpenClaw-Soul接入设计.md)
