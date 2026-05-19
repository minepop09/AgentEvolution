# OpenClaw Soul 接入设计方案

> 日期：2026-05-19

---

## OpenClaw 现有架构

```
OpenClaw Agent
├── AWP Wallet (~/.openclaw-wallet/)
├── AWP Skill (hermes-agent skill)
├── KYA Identity (链上身份)
├── FluxA Wallet (支付/红包)
└── Cron Jobs (定时任务)
```

---

## Soul 的定义（注入到 Agent）

Soul = **人格记忆 + 问题处理OS + 技能包**

```
┌─────────────────────────────────────────┐
│           OpenClaw Soul                  │
├─────────────────────────────────────────┤
│  人格记忆层                              │
│  ├── Agent 身份设定                      │
│  ├── 问题处理方法论（内置）               │
│  └── 领域专长配置                        │
├─────────────────────────────────────────┤
│  问题处理OS（7个模块 + Todo）            │
│  ├── 问题预处理模块                      │
│  ├── 问题认知模块（三层探测）            │
│  ├── 知识库存储模块                      │
│  ├── 问题分析模块                        │
│  ├── 工具审核模块（SlowMist）            │
│  ├── 工具安装模块                        │
│  └── Todo 计划模块                      │
├─────────────────────────────────────────┤
│  技能包层（按领域加载）                  │
│  ├── 深入分析研究能力                    │
│  ├── 代码工程能力                        │
│  ├── 生图/生视频/写作/PPT                │
│  └── find-skills                         │
└─────────────────────────────────────────┘
```

---

## 接入方式

### 方案：Skill 注入式（推荐）

将问题处理OS做成一个 **Hermes Skill**，在 OpenClaw Agent 初始化时加载：

```bash
# 安装问题处理OS Skill
cd ~/.hermes/skills
git clone <repo> agent-problem-os

# OpenClaw Agent 启动时自动加载
# （通过 agent-hansa 的 skill 系统注入到 system prompt）
```

**注入内容**：
1. **人格设定**：写入 OpenClaw Agent 的 Memory
2. **7个模块**：作为可调用的 function/skill
3. **知识库路径**：指向 `~/.hermes/knowledge-base/`
4. **Todo 计划器**：作为状态管理模块

---

## 目录结构设计

```
~/.hermes/
├── knowledge-base/              # 知识库（跨Agent共享）
│   ├── 技术类/
│   ├── 产品类/
│   ├── 分析类/
│   └── 创意类/
├── agent-problem-os/            # 问题处理OS Skill
│   ├── SKILL.md
│   ├── modules/
│   │   ├── 01-preprocess.py
│   │   ├── 02-cognition.py
│   │   ├── 03-kb-store.py
│   │   ├── 04-analysis.py
│   │   ├── 05-tool-audit.py
│   │   ├── 06-tool-install.py
│   │   └── 07-todo.py
│   ├── soul/
│   │   ├── personality.md      # Agent人格设定
│   │   └── methodology.md      # 问题处理方法论
│   └── config.yaml             # 配置（知识库路径等）
└── skill-packages/             # 能力技能包
    ├── research.yaml
    ├── code-engineering.yaml
    └── ...
```

---

## 接入流程

### Step 1：安装 Agent Soul Skill

```bash
cd ~/.hermes/skills
git clone <repo> agent-soul-openclaw
```

### Step 2：初始化知识库目录

```bash
mkdir -p ~/.hermes/knowledge-base/{技术类,产品类,分析类,创意类}
```

### Step 3：配置人格和专长

编辑 `agent-soul-openclaw/soul/personality.md`：
```markdown
# Agent 人格设定

## 身份
你是一个具备深度问题处理能力的AI助手。

## 核心能力
1. 遇到问题时，先深度分析再行动
2. 善于使用工具解决问题
3. 持续学习并积累领域知识

## 领域专长
[根据Agent类型配置]
- 技术编程类：优先使用代码工程能力
- 产品研究类：优先使用分析研究能力
```

### Step 4：加载到 OpenClaw Agent

在 OpenClaw Agent 的启动配置中引用：
```yaml
# openclaw-agent.yaml
skills:
  - agent-soul-openclaw      # 问题处理OS
  - find-skills              # 找skill能力
  - slowmist-agent-security  # 安全审计

knowledge_base:
  path: ~/.hermes/knowledge-base/
  auto_query: true
```

---

## 进化机制实现

### Skill 编排顺序进化

不同领域的 Agent 会形成不同的 Skill 调用顺序：

```yaml
# 技术类Agent
skill_order:
  - code-engineering
  - find-skills
  - analysis

# 产品类Agent  
skill_order:
  - research
  - analysis
  - find-skills
```

进化方式：根据任务完成率自动调整优先级

### 工具权重进化

```python
# 工具权重表（按成功率动态调整）
tool_weights = {
    "github-code-search": 0.9,   # 成功率90%
    "sourcegraph": 0.85,
    "grep": 0.6,
}
```

---

## 与现有系统的集成

| 现有系统 | 集成点 |
|----------|--------|
| AWP Skill | 问题处理完成后，通过 AWP 提交任务 |
| KYA Identity | 身份验证通过后，加载 Soul |
| FluxA Wallet | 工具安装可能涉及付费 |
| Cron Jobs | 知识库自动更新、定时审计 |
| SlowMist | 工具审核模块调用 |

---

## 下一步行动

1. [ ] 创建 `agent-soul-openclaw` Skill 仓库
2. [ ] 实现7个模块的 Python 代码
3. [ ] 设计知识库 Markdown 格式规范
4. [ ] 写 OpenClaw Agent 的 Soul 加载配置
5. [ ] 设计进化机制的权重更新算法
