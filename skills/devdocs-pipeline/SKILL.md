---
name: devdocs-pipeline
description: Top-level orchestrator for DevDocs workflow. Provides 5 entry points (init/feature/bugfix/verify/close) that route to appropriate skills automatically. Use when users are unsure which skill to use, want guided workflow, or ask "从哪开始", "where to start", "我该用哪个". Triggers on "pipeline", "devdocs", "开始项目", "新项目", "工作流", "workflow", "我该用哪个", "从哪开始", "where to start". NOT for non-DevDocs tasks or direct skill invocation when the user already knows which skill to use.
allowed-tools: Read, Glob, Grep, AskUserQuestion, Task
user-invocable: true
---

# DevDocs 工作流编排器

顶层编排器，提供 5 个流程入口，降低用户面对 13 个原子 skill 的认知负担。

## 语言规则

- 支持中英文提问
- 统一中文回复

## 定位

```
用户 → /devdocs-pipeline → 自动路由到合适的 skill 组合
                         ↓
              取代手动选择 13 个原子 skill
```

**核心价值**：用户只需说"我要做什么"，pipeline 负责"用哪些 skill、按什么顺序"。

## 运行模式

```bash
/devdocs-pipeline                → 提问式调度（自动判断）
/devdocs-pipeline init           → 新项目全流程
/devdocs-pipeline feature        → 新功能开发
/devdocs-pipeline bugfix         → Bug 修复
/devdocs-pipeline verify         → 质量检查
/devdocs-pipeline close          → 周期收尾
```

## 提问式调度（智能引导）

无参数调用时，通过阶段感知 + 智能引导收敛到合适的入口：

### 阶段检测

首先扫描 `docs/devdocs/` 已有文件，判断当前阶段：

```text
扫描 docs/devdocs/ 目录
    │
    ├── 无文件 → 新项目判断（见下方 Q1）
    │
    └── 有文件 → 分析当前阶段
          │
          ├── 仅 01-requirements.md → "需求已完成，建议运行 /devdocs-system-design"
          ├── 有 01 + 02 → "设计已完成，建议运行 /devdocs-test-cases"
          ├── 有 01~03 → "测试设计已完成，建议运行 /devdocs-dev-tasks"
          ├── 有 01~04 + 有 readiness-report → "就绪检查已通过，建议运行 /devdocs-dev-workflow"
          ├── 有 01~04 + 无 readiness-report → "任务已拆分，建议运行 /devdocs-verify --readiness"
          ├── 有代码提交 + 任务进行中 → "开发进行中，建议继续 /devdocs-dev-workflow"
          └── 有 verify-report → "验证已完成，建议运行 /devdocs-sync 或 /devdocs-compound"
```

### 轻量分轨提示

根据用户描述的变更规模，给出路径建议：

| 变更规模 | 特征 | 建议路径 |
|----------|------|----------|
| 小改动 | bugfix、单文件修复、配置变更 | `/devdocs-pipeline bugfix` |
| 标准功能 | 新功能、需求变更、多文件改动 | `/devdocs-pipeline feature` |
| 大功能 | 跨模块、新架构、全新项目 | `/devdocs-pipeline init` 完整路径 |

### 兜底问答

阶段检测无法判断时，通过 2-3 个问题收敛：

```text
Q1: "项目已有 DevDocs 文档吗？"
    │
    ├── 没有 → Q1a: "已有代码还是全新项目？"
    │           ├── 全新项目 → init
    │           └── 已有代码 → /devdocs-retrofit（非 pipeline 管辖）
    │
    └── 有 → Q2: "你要做什么？"
              ├── 新功能  → feature
              ├── 修 Bug  → bugfix
              ├── 检查质量 → verify
              └── 收尾/沉淀 → close

Q3（feature/bugfix 追加，可选）:
    "这次改动涉及 UI 吗？"
    ├── 是 → verify 阶段包含 --ui 维度
    └── 否 → verify 阶段仅 --docs/--impl
```

## 入口详解

### init — 新项目全流程

适用于全新项目，从需求到开发的完整流程。

```text
/devdocs-requirements
    │
    ▼
/devdocs-system-design
    │
    ▼
/devdocs-test-cases
    │
    ▼
/devdocs-dev-tasks
    │
    ▼
/devdocs-verify --readiness   ← 就绪关卡（P1 阻塞则修复后重试）
    │
    ▼
/devdocs-dev-workflow（批量模式）
    │  ← 批量模式内部已含逐任务 sync + compound
    ▼
/devdocs-verify        ← 全量验证（覆盖 dev-workflow 逐任务验证可能遗漏的跨任务一致性）
    │
    ▼
/devdocs-sync          ← 全量补充同步（幂等，捕获跨任务遗漏）
```

> **就绪关卡**：dev-tasks 完成后自动调用 `verify --readiness`。检查项包括：AC↔测试用例对齐、任务文件路径具体性、依赖无环、设计↔任务一致性。P1 问题阻塞进入 dev-workflow，显示问题清单并建议修复后重试。
>
> **粒度说明**：dev-workflow 批量模式内部已执行逐任务 sync 和 compound。pipeline 此处的 verify → sync 是**全量验证+补充同步**，覆盖跨任务的整体一致性。sync 是幂等的，多次执行不会产生错误结果。不再额外执行 compound——dev-workflow 批量模式已默认执行。

**上下文传递**：pipeline 启动时优先检查 `docs/devdocs/00-context.md`，如存在且未过期（< 24h），读取作为快速上下文，避免重复扫描。

### feature — 新功能开发

适用于已有项目追加新功能。

```text
/devdocs-feature（含 requirements/design/tests/tasks + readiness 关卡 + 自动衔接 dev-workflow）
    │  ← feature 内置 Step 4.5 verify --readiness，P1 阻塞则修复后重试
    │  ← dev-workflow 内部已含逐任务 sync
    ▼
/devdocs-verify        ← 全量验证（覆盖所有新增任务的整体一致性）
    │
    ▼
/devdocs-sync          ← 全量补充同步（幂等，捕获跨任务遗漏）
```

> `/devdocs-feature` 已内置 Step 4.5 readiness 关卡和 Step 6 自动衔接 dev-workflow，pipeline 只需在 feature 完成后补充 verify 和 sync。verify 是全量验证，覆盖 dev-workflow 逐任务验证可能遗漏的跨任务一致性；sync 是幂等的全量补充同步，不是重复执行。

### bugfix — Bug 修复

适用于已有项目修复 Bug。

```text
评估复杂度
    │
    ├── 简单 Bug → /devdocs-bugfix（直接修复）
    │                  │
    │                  ▼
    │              /devdocs-verify --impl
    │                  │
    │                  ▼
    │              /devdocs-sync
    │
    └── 复杂 Bug → /devdocs-dev-tasks（拆分任务）
                       │
                       ▼
                   /devdocs-dev-workflow
                       │
                       ▼
                   /devdocs-verify --impl
                       │
                       ▼
                   /devdocs-sync
```

### verify — 质量检查

适用于任意阶段的质量检查。

```text
自动判断维度
    │
    ├── 有代码变更 → /devdocs-verify --impl
    ├── 有文档变更 → /devdocs-verify --docs
    ├── 有 UI 设计稿 → /devdocs-verify --ui
    └── 不确定 → 询问用户
    │
    ▼
生成修复建议
    │
    ▼
路由到对应 skill 执行修复
```

### close — 周期收尾

适用于开发周期结束后的收尾工作。

```text
/devdocs-sync（trace + audit）
    │
    ▼
/devdocs-compound（知识沉淀）
    │
    ▼
/devdocs-onboard --update（更新上下文摘要）
```

## 阶段间衔接

pipeline 在每个阶段完成后：

1. **状态检查**：确认阶段产出文件存在
2. **简要摘要**：向用户展示本阶段结果概要
3. **衔接提示**：询问用户是否继续下一阶段（默认是）

```
✅ 需求文档已完成（F-001~F-003, AC-001~AC-012）
是否继续进入系统设计阶段？[是(默认)/否]
```

## 编排规范（子 Agent 调度）

### 调度原则

pipeline 调用其他技能时，**必须通过 Task tool 启动子 Agent**：

```text
pipeline（编排层）
    │
    ├── Task: /devdocs-requirements → YAML 摘要
    ├── Task: /devdocs-system-design → YAML 摘要
    ├── Task: /devdocs-test-cases → YAML 摘要
    ├── Task: /devdocs-dev-tasks → YAML 摘要
    ├── Task: /devdocs-verify --readiness → YAML 摘要
    ├── Task: /devdocs-dev-workflow → YAML 摘要
    ├── Task: /devdocs-verify → YAML 摘要
    └── Task: /devdocs-sync → YAML 摘要
```

### 摘要传递

阶段间只传递 YAML 摘要 + 文件路径。编排 Agent **不读取**子技能的完整输出文档。

### 异常回退

子 Agent 返回 `status: failed` + `blockers` 时：
1. 展示阻塞项给用户
2. 询问用户处理方式（修复/跳过/终止）
3. **不自行读取文档排障**

### 上下文隔离

每个子 Agent 自行读取所需的前置文档（从 `docs/devdocs/` 文件系统），不依赖编排 Agent 传递全文。

## 约束

### 编排约束

- [ ] **pipeline 仅负责路由和衔接，不复制任何原子 skill 的逻辑**
- [ ] **每个阶段必须委托给对应的原子 skill 执行**
- [ ] **阶段间传递的信息仅限：新增编号列表、状态摘要、文件路径**
- [ ] 用户可在任意阶段退出 pipeline

### 提问式调度约束

- [ ] **优先使用阶段检测自动判断，无法判断时才提问**
- [ ] **兜底问答最多 3 个问题收敛到入口**
- [ ] **问题必须有明确的选项（不开放式提问）**
- [ ] 识别到 retrofit 场景时，路由到 `/devdocs-retrofit` 并退出 pipeline
- [ ] **分轨提示基于变更规模，不引入额外术语**

### 上下文约束

- [ ] **优先读取 00-context.md 作为快速上下文（如存在且 < 24h）**
- [ ] pipeline 编排层不读取大量源代码（委托给子 skill）
- [ ] 每个阶段完成后展示简要摘要（< 10 行）

### 编排约束（子 Agent）

- [ ] **调用其他技能时必须通过 Task tool 启动子 Agent**
- [ ] **阶段间只传递 YAML 摘要 + 文件路径**
- [ ] **子 Agent 失败时展示阻塞项询问用户，不自行排障**
- [ ] **每个子 Agent 自行读取前置文档，编排层不传递全文**

## Skill 协作

| 入口 | 编排的 Skill 链 |
|------|----------------|
| init | requirements → system-design → test-cases → dev-tasks → **verify --readiness** → dev-workflow → verify → sync |
| feature | feature(含 readiness + dev-workflow) → verify → sync |
| bugfix | bugfix / (dev-tasks → dev-workflow) → verify → sync |
| verify | verify --docs/--impl/--ui |
| close | sync → compound → onboard --update |

## 子 Agent 摘要格式

当本 Skill 作为子 Agent 运行时，返回以下结构化摘要：

```yaml
skill: devdocs-pipeline
entry: init | feature | bugfix | verify | close
stages_completed:
  - { skill: devdocs-requirements, status: success }
  - { skill: devdocs-system-design, status: success }
stages_remaining:
  - devdocs-test-cases
summary:
  new_ids: [F-001, F-002, AC-001~AC-012]
  status: completed | interrupted | failed
  interrupt_reason: "用户选择退出"  # 仅中断时
output_files:
  - docs/devdocs/01-requirements.md
  - docs/devdocs/02-system-design.md
```

## 下一步

pipeline 完成后，所有产出文档均已生成/更新。用户可：

- 继续下一轮 feature/bugfix
- 运行 `/devdocs-onboard --read` 传递上下文给新 AI
- 直接进入编码（已有 dev-tasks 和 dev-workflow 的产出）
