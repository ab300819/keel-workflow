---
name: ms-onboard
description: Generate project context summary for AI tool handover. Supports --read (view only) and --update (rescan) modes. Use when switching AI tools, starting new sessions, or onboarding team members. Triggers on "project context", "handover", "onboard", "项目上下文", "交接", "接手项目", "新会话", "new session", "项目概览". NOT for retrofitting projects (use ms-retrofit) or requirements definition (use ms-requirements).
allowed-tools: Read, Glob, Grep, Write, Bash, AskUserQuestion, Task
metadata:
  patterns: [generator]
  interaction: multi-turn
  handoff: yaml-summary-v1
reads_layout: [layout.v1, layout.v2]
writes_layout: layout.v1
reads_id_scheme: [id.v1, id.v2]
writes_id_scheme: id.v1
reads_traceability: [trace.v0, trace.v1]
writes_traceability: trace.v0
on_incompatible: warn
migration: /ms-pipeline realign --scope=layout
---

# 项目上下文

> ℹ️ 编号双轨：onboard 输出引用项目实际编号（v1 用 `F`/`T`/`INS`，v2 [FUTURE] 用 `FEAT`/`TASK`/`ADR-PATTERN-NOTE`）。详见 [id-scheme-implementation.md](../pipeline/references/layout/id-scheme-implementation.md)。
>
> ℹ️ 输入路径双轨：v1 读 `docs/devdocs/01~05` 单文件；v2 [FUTURE] 读 `docs/devdocs/{requirements,design,tests,tasks,issues,patterns,notes}/index.md` 各类索引聚合。详见 [folder-organization-implementation.md](../pipeline/references/layout/folder-organization-implementation.md)。

生成项目上下文摘要，帮助 AI 工具或团队成员快速了解项目并接手工作。

## 快速开始

**一句话**: 生成项目上下文摘要，用于 AI 工具交接或新会话启动。

**最常见用法**: `/ms-onboard`（自动检测 read/update）

**不适合?** 改造项目→`/ms-retrofit`，需求定义→`/ms-requirements`

## 运行模式

```bash
/ms-onboard              → 智能检测（询问读或写）
/ms-onboard --read       → 只读取现有文档，不修改
/ms-onboard --update     → 强制重新扫描更新
/ms-onboard --realign    → 规范升级回扫：00-context.md 按当前 `context.v1` 查漏补缺（不重扫项目）。复用 [共享契约](../pipeline/references/realign.md)；推荐用户入口 `/ms-pipeline realign`
```

| 模式 | 读取文档 | 扫描项目 | 写入文件 | 适用场景 |
|------|----------|----------|----------|----------|
| 智能检测 | ✅ | 视情况 | 视情况 | 不确定时 |
| `--read` | ✅ | ❌ | ❌ | 新 AI 接手项目 |
| `--update` | - | ✅ | ✅ | 完成阶段性工作后 |

### 智能检测流程

```text
检测 00-context.md 是否存在
        │
        ├── 不存在 → 自动进入更新模式
        │
        └── 存在 → 询问用户
                    ├── "读取现有内容" → 展示文档，不修改
                    └── "重新扫描更新" → 扫描项目，覆盖文件
```

## 语言规则

- 支持中英文提问
- 统一中文回复
- 使用中文生成文档

## 触发条件

- 用户切换 AI 工具，需要传递上下文
- 用户开始新的对话会话
- 团队成员需要了解项目
- 用户要求生成项目简报

## 核心理念

### 上下文传递问题

```text
会话 A (Claude Code)          会话 B (新 AI 工具)
        │                            │
        ├── 了解项目结构              │ ← 需要重新了解
        ├── 读取设计文档              │ ← 需要重新读取
        ├── 理解当前进度              │ ← 需要重新理解
        └── 知道下一步任务            │ ← 需要重新确认
                                     │
                    ┌────────────────┘
                    ▼
             /ms-onboard
                    │
                    ▼
            生成上下文摘要
                    │
                    ▼
             快速接手项目
```

**核心原则**：
- 一份文档包含所有关键上下文
- 新 AI 读取后能立即开始工作
- 避免重复探索和询问

## 工作流程

**`--read` 模式**：仅读取已有 `00-context.md` 展示，不执行任何扫描或写入。文件不存在时提示用户先运行 `--update`。

**`--update` / auto 模式**：

```text
1. 扫描 DevDocs 文档
   │
   ▼
2. 提取关键信息
   ├── 项目概述
   ├── 技术架构
   ├── 当前进度
   └── 待办任务
   │
   ▼
3. 读取代码库盘点 + 采集运行态信息
   │
   ├── 委托 ms-codebase-insight 获取结构化信息（模块、接口、数据对象）
   └── 直接采集运行态信息（git status、git log、目录结构等）
   │
   ▼
4. 生成上下文摘要
   │
   ▼
5. 输出文件（可直接传递给新 AI）
```

## 输出文件

**主文件**：`docs/devdocs/00-context.md`

此文件设计为可直接复制给新 AI 工具作为初始上下文。

## 文档结构

**文件头必填 frontmatter**（realign 扫描依据）：

```yaml
---
generated_by: ms-onboard
spec_version: context.v1
generated_at: 2026-04-23T10:30:00+08:00
---
```

```markdown
# 项目上下文：<项目名称>

**生成时间**：YYYY-MM-DD HH:mm
**生成工具**：/ms-onboard

---

## 1. 项目概述

### 1.1 项目目标
<从 01-requirements.md 提取；不存在时从 00-baseline.md 的「项目目的与边界」提取，并保留其来源标注>

### 1.2 核心功能
| 编号 | 功能 | 状态 |
|------|------|------|
| F-001 | <功能名称> | ✅ 已完成 / 🔄 进行中 / ⏳ 待开发 |

### 1.3 技术栈
<从 02-system-design.md 提取>

---

## 2. 系统架构

### 2.1 架构概览
<从 02-system-design.md 提取架构图>

### 2.2 核心模块
| 模块 | 职责 | 关键文件 |
|------|------|----------|
| <模块名> | <职责> | `src/xxx/` |

### 2.3 核心接口
<从 02-system-design.md 提取关键接口签名>

---

## 3. 代码结构

### 3.1 目录结构
```
<实际项目目录结构，通过 ls/tree 获取>
```

### 3.2 关键文件说明
| 文件 | 用途 |
|------|------|
| `src/index.ts` | 入口文件 |
| `src/config.ts` | 配置管理 |

---

## 4. 当前进度

### 4.1 总体进度
| 类型 | 总数 | 已完成 | 进行中 | 完成率 |
|------|------|--------|--------|--------|
| 功能点 | X | X | X | XX% |
| 开发任务 | X | X | X | XX% |

### 4.2 最近完成
- T-05: <任务名称> (YYYY-MM-DD)
- T-04: <任务名称> (YYYY-MM-DD)

### 4.3 当前进行中
- T-06: <任务名称>
  - 状态：<进度描述>
  - 涉及文件：`src/xxx.ts`

### 4.4 未提交变更
<如有未提交的代码变更，列出>

---

## 5. 待办任务

### 5.1 下一步任务
| 优先级 | 任务 | 依赖 | 关联需求 |
|--------|------|------|----------|
| P0 | T-07: <任务名称> | T-06 | F-002, AC-005 |

### 5.2 阻塞项
<如有阻塞项，列出>

---

## 6. 重要约定

### 6.1 编码规范
<!-- 阈值摘录自 /code-quality 核心阈值表，变更需同步；按项目实际约定覆写 -->
- 遵循 MTE 原则（可维护、可测试、可扩展），详见 `/code-quality`
- 函数不超过 50 行
- 参数不超过 5 个

### 6.2 测试要求
<!-- 阈值摘录自 /testing-guide 核心阈值表，变更需同步；按项目实际约定覆写 -->
- 单元测试覆盖率 ≥ 80%（详见 `/testing-guide`）
- 禁止弱断言

### 6.3 提交规范
<从 git log 提取项目提交风格>

---

## 7. 快速开始

### 7.1 环境准备
```bash
<安装依赖命令>
```

### 7.2 运行项目
```bash
<运行命令>
```

### 7.3 运行测试
```bash
<测试命令>
```

---

## 8. DevDocs 文档索引

| 文档 | 路径 | 说明 |
|------|------|------|
| 需求文档 | `docs/devdocs/01-requirements.md` | 功能点、用户故事、验收标准 |
| 系统设计 | `docs/devdocs/02-system-design.md` | 架构、接口、数据模型 |
| 测试用例 | `docs/devdocs/03-test-cases.md` | 测试策略、追溯矩阵 |
| 开发任务 | `docs/devdocs/04-dev-tasks.md` | 任务列表、依赖关系 |

---

**接手建议**：
1. 先阅读本文档了解全貌
2. 查看"当前进行中"任务状态
3. 从"下一步任务"继续开发
4. 遇到细节问题查阅对应 DevDocs 文档
```

## 信息提取规则

### 从 DevDocs 提取

| 信息 | 来源文档 | 提取内容 |
|------|----------|----------|
| 项目目标 | `01-requirements.md` | 需求背景、目标用户 |
| 功能列表 | `01-requirements.md` | F-XXX 功能点及状态 |
| 技术栈 | `02-system-design.md` | 技术选型表 |
| 架构图 | `02-system-design.md` | 架构概览图 |
| 核心接口 | `02-system-design.md` | 接口签名表 |
| 当前进度 | `04-dev-tasks.md` | 执行检查清单 |
| 待办任务 | `04-dev-tasks.md` | 未完成的 T-XX |

### 从代码库盘点提取

> 结构化信息（模块、接口、数据对象）从 `docs/codebase-insight.md` 读取，不存在时委托 `ms-codebase-insight` 生成。
> 运行态信息（目录树、git 状态）仍由 onboard 直接采集。

| 信息 | 来源 |
|------|------|
| 系统边界 | codebase-insight.md → 系统边界章节 |
| 核心模块 | codebase-insight.md → 核心模块章节 |
| 公开接口 | codebase-insight.md → 公开接口章节 |
| 技术栈 | codebase-insight.md → 技术栈与约束章节 |
| 目录结构 | `ls -la` 或 `tree`（onboard 直接执行） |
| 关键文件 | 分析 package.json、入口文件（onboard 直接执行） |
| 未提交变更 | `git status`（onboard 直接执行） |
| 提交风格 | `git log --oneline -5`（onboard 直接执行） |
| 运行命令 | 从 package.json scripts 或 Makefile 提取（onboard 直接执行） |

## 使用场景

### 场景一：完成工作，准备交接（--update）

```text
用户: /ms-onboard --update

Agent: 正在扫描项目并生成上下文...
✅ 已更新 docs/devdocs/00-context.md

您可以将此文件内容复制给新的 AI 工具，它将快速了解项目并接手工作。
```

### 场景二：新 AI 接手项目（--read）

```text
用户: /ms-onboard --read

Agent: 正在读取项目上下文...

[展示 00-context.md 内容]

当前进度：8/12 任务已完成 (67%)
下一步：T-09 用户认证模块

建议从"待办任务"部分继续开发。
```

### 场景三：不确定时（智能检测）

```text
用户: /ms-onboard

Agent: 检测到 docs/devdocs/00-context.md 已存在（更新于 2 小时前）

请选择：
1. 读取现有内容（不修改）
2. 重新扫描更新

用户: 1

Agent: [展示现有文档内容]
```

## 约束

### 生成约束

- [ ] **--update 模式：扫描所有 DevDocs 文档 + 读取/生成 codebase-insight + 采集 git 状态**
- [ ] **--read 模式：仅读取已有 00-context.md 展示，不扫描、不写入、不委托生成任何文件**
- [ ] 输出文件必须自包含（不依赖外部链接理解）
- [ ] 关键信息必须直接展示（不只是引用文档路径）

### 内容约束

- [ ] **项目概述不超过 200 字**
- [ ] **架构图必须包含（ASCII 或 Mermaid）**
- [ ] **必须列出下一步可执行的任务**
- [ ] 敏感信息（密钥、密码）不得包含
- [ ] 文件路径必须准确可访问

### 更新约束

- [ ] 每次生成覆盖旧文件
- [ ] 生成时间必须记录
- [ ] 如 DevDocs 不存在，提示用户先运行相关 skill

## Skill 协作

| 场景 | 协作 Skill | 说明 |
|------|-----------|------|
| DevDocs 不存在 | `/ms-retrofit` | 先建立项目基线（`00-baseline.md`） |
| 进度信息过时 | `/ms-sync` | 先同步文档状态 |
| 需要详细任务 | `/ms-dev-tasks` | 查看完整任务列表 |
| 记忆文件同步 | `/agent-memory` | 更新 AGENTS.md;DevDocs 项目同步时包含工作流路由节 |

## 命令选项

```bash
# 智能检测：根据文档存在状态询问用户
/ms-onboard

# 只读模式：读取并展示现有文档，不做任何修改
/ms-onboard --read

# 更新模式：强制重新扫描项目并更新文档
/ms-onboard --update
```

## 子 Agent 摘要格式

当本 Skill 作为子 Agent 运行时，返回以下结构化摘要：

> envelope 字段定义（status 枚举 / blockers / output_files / new_ids 等保留字段）见 [_shared/constraints.md §yaml-summary-v1](../_shared/constraints.md)；下例重点为 `summary.details` 私有字段。

```yaml
skill: ms-onboard
status: success | partial
summary:
  headline: "项目上下文已更新，进度 67%"
  details:
    mode: read | update | auto
    project_name: "<项目名>"
    progress: "X/Y tasks completed (XX%)"
    next_task: T-XX
    context_age: "<N hours/days since last update>"
blockers: []
output_files:                   # --update 模式
  - docs/devdocs/00-context.md
  # --read 模式：output_files: []（不写入文件）
new_ids: {}
next_recommended:
  skill: ""
  args: ""
```

**output_files 规则**：
- `--update` / `auto`（写入模式）：`[docs/devdocs/00-context.md]`
- `--read`：`[]`（只读，不产出文件）

## 下一步

### 交接方（工具 A）
1. 完成阶段性工作后，运行 `/ms-onboard --update`
2. 将 `00-context.md` 内容传递给新 AI 工具

### 接手方（工具 B）
1. 运行 `/ms-onboard --read` 了解项目
2. 从"待办任务"部分继续开发
3. 完成工作后运行 `/ms-onboard --update` 更新上下文
