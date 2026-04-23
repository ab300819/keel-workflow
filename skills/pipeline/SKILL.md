---
name: ms-pipeline
description: Top-level orchestrator for DevDocs workflow. Provides 8 entry points (init/feature/bugfix/verify/close/insights/design/realign) that route to appropriate skills automatically. Use when users are unsure which skill to use, want guided workflow, or ask "从哪开始", "where to start", "我该用哪个". Triggers on "pipeline", "devdocs", "开始项目", "新项目", "工作流", "workflow", "我该用哪个", "从哪开始", "where to start", "insights", "洞察", "调研", "借鉴", "竞品", "设计稿", "design ready", "设计到了", "UI稿", "realign", "规范升级", "查漏补缺", "对齐已有产物". NOT for non-DevDocs tasks or direct skill invocation when the user already knows which skill to use.
metadata:
  patterns: [pipeline]
  interaction: multi-turn
  handoff: yaml-summary-v1
allowed-tools: Read, Glob, Grep, AskUserQuestion, Task
user-invocable: true
---

# DevDocs 工作流编排器

顶层编排器，提供 8 个流程入口，降低用户面对 13 个原子 skill 的认知负担。

## 语言规则

- 支持中英文提问
- 统一中文回复

## 定位

```
用户 → /ms-pipeline → 自动路由到合适的 skill 组合
                         ↓
              取代手动选择 13 个原子 skill
```

**核心价值**：用户只需说"我要做什么"，pipeline 负责"用哪些 skill、按什么顺序"。

## 快速开始

**一句话**: 不知道该用哪个 skill？从这里开始，自动路由到正确的工作流。

**最常见用法**: `/ms-pipeline`（自动判断）、`/ms-pipeline init`（新项目）、`/ms-pipeline feature`（加功能）

**不适合?** 已知目标 skill → 直接调用 `/ms-requirements`、`/ms-feature`、`/ms-bugfix` 等

## 运行模式

```bash
/ms-pipeline                → 提问式调度（自动判断）
/ms-pipeline init           → 新项目全流程
/ms-pipeline feature        → 新功能开发（自动检测 Harness 深度）
/ms-pipeline feature --deep → 强制深度模式（透传给 /ms-feature --deep）
/ms-pipeline bugfix         → Bug 修复
/ms-pipeline verify         → 质量检查
/ms-pipeline close          → 周期收尾
/ms-pipeline insights       → 外部洞察吸收
/ms-pipeline design         → 设计稿到达/更新（主动推送）
/ms-pipeline realign        → 规范升级回扫（已完成产物按新规范查漏补缺）
/ms-pipeline realign --dry-run → 只出差距报告，不修改文件
/ms-pipeline realign --no-realign → 显式拒绝本次升级提示，写入 .devdocs-realign-ack（编排调度到 ms-dev-workflow --headless 时必需 --realign/--no-realign 其一，否则透传层 fail-fast）
```

## 提问式调度（智能引导）

无参数调用时，通过阶段感知 + 智能引导收敛到合适的入口：

### 阶段检测

首先扫描 `docs/devdocs/` 已有文件，判断当前阶段：

```text
扫描 docs/devdocs/ 目录
    │
    ├── 无文件 → 先检测项目状态，再路由
    │     │
    │     ├── PRD 候选检测（两段式）：
    │     │     1. 检查 docs/prd/index.md → 存在则解析 PRD 清单（仅 active 候选，因后续 --from-prd 需回写映射），对每个候选检查 requirements/index.md 是否存在（不存在跳过）；不存在 → legacy：尝试 docs/prd/requirements/index.md
    │     │     2. 仅 1 个可用候选 → 读取其 per-PRD requirements/index.md，从"整体成熟度"字段判断
    │     │        多个可用候选 → AskUserQuestion 让用户选择目标 PRD，再读 maturity
    │     │        0 个可用候选 → 跳过 PRD 检测，继续后续路由
    │     │     └─ per-PRD index 缺失 → "PRD 已登记但未生成可消费总纲"
    │     ├── maturity=ready → "产品需求已就绪，建议运行 /ms-requirements --from-prd <实际检测到的 index.md 路径>"
    │     ├── maturity=idea/draft → "产品需求包未就绪（maturity: <当前值>），建议继续运行 /ms-prd 完善需求"
    │     ├── 项目已有代码（src/、lib/、app/ 等）但无 DevDocs → Q1a：新项目还是已有项目？
    │     │     ├── 已有项目 → "建议先运行 /ms-retrofit 逆向生成文档"
    │     │     └── 新项目（代码是脚手架/模板）→ 继续按输入类型路由
    │     ├── 用户输入明显模糊/极短（<200字，无结构）→ "建议先运行 /ms-prd 探索需求"
    │     └── 用户提供大文档引用（文件/URL/粘贴长文）→ "建议先运行 /ms-prd prd 解析文档"
    │
    └── 有文件 → 分析当前阶段（基于文件存在性，首个命中即路由）
          │
          ├── 有 verify-report（--impl/全部，通过）→ "验证已完成，建议运行 /ms-sync 或 /ms-compound"
          ├── 有代码提交 + 任务进行中 → "开发进行中，建议继续 /ms-dev-workflow"
          ├── 有 01~04 + readiness-report（通过）→ "就绪检查已通过，建议运行 /ms-dev-workflow"
          ├── 有 01~04 + readiness 未通过或缺失 → "建议运行 /ms-verify --readiness"
          ├── 有 01~03 → "测试设计已完成，建议运行 /ms-dev-tasks"
          ├── 有 01 + 02 → "设计已完成，建议运行 /ms-test-cases"
          ├── 仅 01-requirements.md → "需求已完成，建议运行 /ms-system-design"
          └── 有 05-insights.md + 含 ⏳ 待确认条目 → "有未转化洞察，建议运行 /ms-insights 确认后进入 system-design 或 dev-tasks"
          │
          > 报告类文件（readiness-report、verify-report）应比其源文件更新，过期时建议重新验证。
```

### 一次性升级提示（阶段检测后）

阶段检测完成后、返回路由建议之前，执行 schema drift 轻量检查。检测到 drift 且无 `.devdocs-realign-ack` 标记时，打印**一次性**轻量提示（不阻塞原路由），提示用户运行 `/ms-pipeline realign`。用户任一决策后写入标记，之后不再提示。详细规则（检测流程、提示格式、标记失效策略）见 [references/realign.md](references/realign.md) § 一次性升级提示。

**`.devdocs-realign-ack` 读写责任**：读取发生在阶段检测后；**写入仅由 `ms-pipeline realign` / `--no-realign` 执行完成时触发**（整仓决策）—— `ms-feature F-XX realign` / `ms-bugfix BUG-XX realign` 是定向局部对齐，**不写入 ack**（用户未对整仓做决策，下次进入 pipeline 若仍有 drift 仍应提示；若定向 realign 正好清空全部 drift，pipeline 入口自然 drift_count=0 不会提示）。失效条件见 [references/realign.md](references/realign.md)。标记文件入 git，协作者共享决策。

### 自适应 Harness 深度

根据变更影响面自动推荐流程深度，避免轻量任务被重流程拖累，同时确保高风险变更不遗漏验证。

| 档位 | 特征 | 流程深度 | 路由 |
|------|------|----------|------|
| **Lite** | 单文件改动、无新接口、配置变更、UI 微调 | requirements(增量) → dev-tasks → dev-workflow | `/ms-feature --lite` 或 `/ms-pipeline bugfix` |
| **Standard** | 多文件改动、新接口、新模块 | 全流程（requirements → design → tests → tasks → dev） | `/ms-pipeline feature` |
| **Deep** | 跨模块架构变更、安全相关、核心数据模型变更 | 全流程 + 强制 `--review` + 强制 `ms-verify --docs` | `/ms-pipeline feature --deep` |

**自动检测信号**：

| 信号 | 检测方式 | 推荐档位 |
|------|----------|---------|
| 涉及文件 ≤2 且无新增接口 | 用户描述分析 | Lite |
| 新增 API/数据模型/模块 | 用户描述 + 已有 02-system-design 对比 | Standard |
| 跨模块依赖变更 / 安全相关 / 核心表结构变更 | 用户描述 + 架构摘要 | Deep |

> 原则：**最小可行 Harness**（[参考](https://www.anthropic.com/engineering/harness-design-long-running-apps)）——每个流程环节都是对模型局限性的假设编码，随模型能力提升应定期评估是否仍有必要。

### 兜底问答

阶段检测无法判断时，通过 2-3 个问题收敛：

```text
Q1: "项目已有 DevDocs 文档吗？"
    │
    ├── 没有 → Q1a: "已有代码还是全新项目？"
    │           ├── 全新项目 → init
    │           └── 已有代码 → /ms-retrofit（非 pipeline 管辖）
    │
    └── 有 → Q2: "你要做什么？"
              ├── 新功能  → feature
              ├── 修 Bug  → bugfix
              ├── 检查质量 → verify
              ├── 吸收外部参考 → insights
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
/ms-requirements
    │
    ▼
/ms-system-design
    │
    ▼
/ms-test-cases
    │
    ▼
/ms-dev-tasks
    │
    ▼
/ms-verify --readiness   ← 就绪关卡（P1 阻塞则修复后重试）
    │
    ▼
/ms-dev-workflow（批量模式）
    │  ← 批量模式内部已含逐任务 sync + compound
    ▼
/ms-verify --docs --impl  ← 全量验证（显式指定维度，覆盖文档对齐 + 实现正确性）
    │
    ▼
/ms-sync          ← 全量补充同步（幂等，捕获跨任务遗漏）
```

> **就绪关卡**：dev-tasks 完成后自动调用 `verify --readiness`。检查项包括：AC↔测试用例对齐、任务文件路径具体性、依赖无环、设计↔任务一致性。P1 问题阻塞进入 dev-workflow，显示问题清单并建议修复后重试。
>
> **粒度说明**：dev-workflow 批量模式内部已执行逐任务 sync 和 compound。pipeline 此处的 verify → sync 是**全量验证+补充同步**，覆盖跨任务的整体一致性。sync 是幂等的，多次执行不会产生错误结果。不再额外执行 compound——dev-workflow 批量模式已默认执行。

**上下文传递**：pipeline 启动时优先检查 `docs/devdocs/00-context.md`，如存在则读取作为参考上下文。但 pipeline 始终以 `docs/devdocs/` 目录下的实际文件进行阶段检测（而非依赖 00-context.md 中的进度数据），确保路由基于最新文档状态。

### feature — 新功能开发

适用于已有项目追加新功能。根据自适应 Harness 深度选择流程档位。

```text
/ms-feature（含 requirements/design/tests/tasks + readiness 关卡 + 自动衔接 dev-workflow）
    │  ← feature 内置 Step 4.5 verify --readiness，P1 阻塞则修复后重试
    │  ← dev-workflow 内部已含逐任务 sync
    ▼
/ms-verify --docs --impl  ← 全量验证（显式指定维度，与 init 流程一致）
    │
    ▼
/ms-sync          ← 全量补充同步（幂等，捕获跨任务遗漏）
```

**--deep 模式**（跨模块/架构/安全变更时自动推荐或手动指定）：
- dev-workflow 所有任务强制 `--review`（对抗式验证）
- feature 完成后额外执行 `ms-verify --docs`（确保文档层间对齐）
- pipeline 展示 Deep 档位建议时附带影响面摘要

> `/ms-feature` 已内置 Step 4.5 readiness 关卡和 Step 6 自动衔接 dev-workflow，pipeline 只需在 feature 完成后补充 verify 和 sync。verify 是全量验证，覆盖 dev-workflow 逐任务验证可能遗漏的跨任务一致性；sync 是幂等的全量补充同步，不是重复执行。

### bugfix — Bug 修复

适用于已有项目修复 Bug。

```text
评估复杂度
    │
    ├── 简单 Bug → /ms-bugfix（直接修复）
    │                  │
    │                  ▼
    │              /ms-verify --impl
    │                  │
    │                  ▼
    │              /ms-sync
    │
    └── 复杂 Bug → /ms-dev-tasks（拆分任务）
                       │
                       ▼
                   /ms-dev-workflow
                       │
                       ▼
                   /ms-verify --impl
                       │
                       ▼
                   /ms-sync
```

### verify — 质量检查

适用于任意阶段的质量检查。

```text
自动判断维度
    │
    ├── 有代码变更 → /ms-verify --impl
    ├── 有文档变更 → /ms-verify --docs
    ├── 有 UI 设计稿 → /ms-verify --ui
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
/ms-sync（trace + audit）
    │
    ▼
/ms-compound（知识沉淀）
    │
    ▼
/ms-onboard --update（更新上下文摘要）
```

### realign — 规范升级回扫

当 DevDocs 规范（模板/校验规则/证据标准）升级后，已完成的产物会按"已完成"被跳过；realign 入口让用户按新规范重新对齐，**不破坏原完成证据**，仅追加差距补齐。

```text
扫描 docs/devdocs/ 所有产物 → 比对各 skill 当前 spec_version
    │
    ├── --dry-run → 只出差距报告（分 additive / restructuring 两级）
    │
    └── 执行 → 按 DevDocs 主链路顺序依次调度（传递 context）：
         # Phase 1：B 类上游（PRD 流程产物，如果相关文件存在）
         Task: /ms-prd-parser --realign       （若 docs/prd/<prd_id>/chunks/ 存在）
             │
             ▼
         Task: /ms-prd-brainstorm --realign   （若 docs/prd/<prd_id>/requirements/ 存在）
             │
             ▼
         # Phase 2：A 类 DevDocs 主链路
         Task: /ms-requirements --realign
             │
             ▼
         Task: /ms-system-design --realign
             │
             ▼
         Task: /ms-test-cases --realign
             │
             ▼
         Task: /ms-dev-tasks --realign
             │
             ▼
         Task: /ms-dev-workflow --all --realign
             │
             ▼
         # Phase 3：B 类旁路（洞察/onboard）
         Task: /ms-insights --realign         （若 docs/devdocs/05-insights.md 存在）
             │
             ▼
         Task: /ms-onboard --realign          （若 docs/devdocs/00-context.md 存在）
             │
             ▼
         汇总 yaml-summary-v1 → 用户报告（N 产物 / M 任务 / K 差距补齐）
```

**关键约束**：
- realign **不是**续做信号（不混入 ms-dev-workflow 12 种续做机制）
- restructuring 差距必须 `⚠️ 必须确认`，additive 差距可直接补齐
- 二次运行幂等（无新差距即 no-op）
- `--headless` 下必须显式 `--realign` 或 `--no-realign`（不隐式触发）

详细规则见 [references/realign.md](references/realign.md)（共享契约）与各 skill 的 `references/realign.md`（实例化差异矩阵）。

### design — 设计稿到达/更新

用户主动推送设计资产的入口。Pipeline 仅做阶段检测和收集，写入/回填委托原子 skill。

> 详细流程见 [prd/references/design-context.md](../prd/references/design-context.md) § 主动推送协议。

```text
1. 阶段检测（复用现有阶段扫描逻辑，首个命中即路由）
   │
   ├── no-prd → 收集信息，提示先 /ms-prd 或 /ms-requirements
   ├── prd-ready → 收集 → Task: /ms-requirements --update-design --target prd-index
   ├── post-requirements / post-design → 收集 → Task: /ms-requirements --update-design
   ├── in-dev（有 04 + 有代码提交/任务进行中）→ 收集 → Task: /ms-requirements --update-design → 提示 /ms-verify --ui
   └── post-tasks（有 04 + 无代码提交）→ 收集 → Task: /ms-requirements --update-design → Task: /ms-dev-tasks --backfill-design
```

**约束**：
- Pipeline 不写文档，仅路由和委托
- no-prd 阶段不阻塞：收集 design_context 信息并暂存在委托参数中，提示用户先建立文档基础
- 不中断当前进行中的 dev-workflow 任务

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
    ├── Task: /ms-requirements → YAML 摘要
    ├── Task: /ms-system-design → YAML 摘要
    ├── Task: /ms-test-cases → YAML 摘要
    ├── Task: /ms-dev-tasks → YAML 摘要
    ├── Task: /ms-verify --readiness → YAML 摘要
    ├── Task: /ms-dev-workflow → YAML 摘要
    ├── Task: /ms-verify → YAML 摘要
    └── Task: /ms-sync → YAML 摘要
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

### 阶段边界约束（全局规则）

DevDocs 工作流严格区分**文档阶段**和**编码阶段**：

| 阶段 | 技能 | 产出类型 | 允许编码 |
|------|------|----------|----------|
| 需求 | ms-requirements | 文档 | ❌ |
| 设计 | ms-system-design | 文档 | ❌ |
| 测试设计 | ms-test-cases | 文档 | ❌ |
| 任务拆分 | ms-dev-tasks | 文档 | ❌ |
| 项目改造 | ms-retrofit | 文档 | ❌ |
| **开发执行** | **ms-dev-workflow** | **代码** | **✅** |
| **Bug 修复** | **ms-bugfix** | **代码** | **✅** |

- [ ] **⛔ 禁止继续：文档阶段不得产出实现代码，仅写入 `docs/devdocs/` 下的 Markdown 文档**（恢复方式：将代码产出移至 dev-workflow/bugfix 阶段）
- [ ] **编码仅在 ms-dev-workflow 和 ms-bugfix 阶段发生**
- [ ] 编排器不得在文档阶段启动编码操作

### 编排约束

- [ ] **pipeline 仅负责路由和衔接，不复制任何原子 skill 的逻辑**
- [ ] **每个阶段必须委托给对应的原子 skill 执行**
- [ ] **阶段间传递的信息仅限：新增编号列表、状态摘要、文件路径**
- [ ] 用户可在任意阶段退出 pipeline

### 提问式调度约束

- [ ] **优先使用阶段检测自动判断，无法判断时才提问**
- [ ] **兜底问答最多 3 个问题收敛到入口**
- [ ] **问题必须有明确的选项（不开放式提问）**
- [ ] 识别到 retrofit 场景时，路由到 `/ms-retrofit` 并退出 pipeline
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
| feature | feature(含 readiness + dev-workflow) → verify → sync（--deep 时 dev-workflow 强制 --review + verify 含 --docs） |
| bugfix | bugfix / (dev-tasks → dev-workflow) → verify → sync |
| verify | verify --docs/--impl/--ui |
| insights | 见下方 insights 流程图 |
| close | sync → compound → onboard --update |
| design | 阶段检测 → 委托 ms-requirements --update-design [→ ms-dev-tasks --backfill-design] |
| realign | Phase 1 B 类上游：prd-parser/prd-brainstorm --realign（若存在）→ Phase 2 A 类主链路：requirements → system-design → test-cases → dev-tasks → dev-workflow --all → Phase 3 B 类旁路：insights/onboard（若存在）（详见 [references/realign.md](references/realign.md)） |

> **补充说明**：dev-workflow 批量模式内部会调用 `/ms-test-run --trace` 执行全量测试 + 追溯验证，详见 `skills/dev-workflow/SKILL.md`。

### insights 入口流程

```text
/ms-insights（收集 + 用户确认 + 追加 01-requirements.md）
    │
    ▼
评估是否涉及架构变更
    │
    ├── 有架构变更（新 API / 数据模型 / 新模块）
    │   └── /ms-system-design → /ms-test-cases → /ms-dev-tasks
    │       → **verify --readiness** → /ms-dev-workflow → /ms-verify → /ms-sync
    │
    └── 简单改进（纯配置 / 样式调整）
        └── /ms-dev-tasks → /ms-dev-workflow → /ms-verify → /ms-sync
```

## 子 Agent 摘要格式

当本 Skill 作为子 Agent 运行时，返回以下结构化摘要：

```yaml
skill: ms-pipeline
status: success | failed | interrupted | partial
summary:
  headline: "init 流程完成 2/5 阶段"
  details:
    entry: init | feature | bugfix | verify | close | insights | design
    stages_completed:
      - { skill: ms-requirements, status: success }
      - { skill: ms-system-design, status: success }
    stages_remaining:
      - ms-test-cases
    interrupt_reason: "用户选择退出"  # 仅中断时
blockers: []
output_files:
  - docs/devdocs/01-requirements.md
  - docs/devdocs/02-system-design.md
new_ids:
  features: [F-001, F-002]
  acceptance: [AC-001~AC-012]
next_recommended:
  skill: ms-test-cases
```

## 下一步

pipeline 完成后，所有产出文档均已生成/更新。用户可：

- 继续下一轮 feature/bugfix
- 运行 `/ms-onboard --read` 传递上下文给新 AI

> ⚠️ 新增功能开发时，不得跳过 test-cases、dev-tasks、verify --readiness 直接进入 dev-workflow。Bug 修复按 `/ms-pipeline bugfix` 路径处理。
