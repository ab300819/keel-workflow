---
name: pipeline
description: 选择并编排 DevDocs 的初始化、功能、修复、验证、收尾、洞察、设计与规范升级流程。仅用于 DevDocs 工作；已指定原子 skill 时直接使用它。
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
用户 → /pipeline → 自动路由到合适的 skill 组合
                         ↓
              取代手动选择 13 个原子 skill
```

**核心价值**：用户只需说"我要做什么"，pipeline 负责"用哪些 skill、按什么顺序"。

## 快速开始

**一句话**: 不知道该用哪个 skill？从这里开始，自动路由到正确的工作流。

**最常见用法**: `/pipeline`（自动判断）、`/pipeline init`（新项目）、`/pipeline feature`（加功能）

**不适合?** 已知目标 skill → 直接调用 `/requirements`、`/feature`、`/bugfix` 等

## 路由播报（强制）

选定入口后、**委托第一个 skill 之前**，先播报三行：

```
路由：<入口名>            ← 依据：<阶段检测命中的那一条>
链路：skillA → skillB → skillC
排除：<最接近的另一个入口> —— <一句话为什么不是它>
```

播报之后才开始委托。⛔ 不得边跑边说。

**为什么强制**：路由选错的代价在链路跑完后才显现，而那时已产生文档与提交。
播报把纠错点提前到零成本的位置——用户看一眼就知道走没走岔。
它同时把"静默跳步"变成可观察的缺席：链路已声明，少跑一步是看得见的。

## 详细文档

- 共享约束 SSOT：[../shared/constraints.md](../shared/constraints.md)
- pipeline 治理 SSOT：[references/realign.md](references/realign.md)

> 本 skill 遵循共享约束 SSOT：门控标记、yaml-summary-v1、Task 委托、用户确认、Recovery 格式、只读 / dry-run、FUTURE 三态、realign / spec_version 见 [skills/shared/constraints.md](../shared/constraints.md)。本文件只描述 pipeline 编排私有规则。

## 运行模式 / 入口语法

```bash
/pipeline                → 提问式调度（自动判断）
/pipeline init           → 新项目全流程
/pipeline feature        → 新功能开发（自动检测 Harness 深度）
/pipeline bugfix         → Bug 修复
/pipeline verify         → 质量检查
/pipeline close          → 周期收尾
/pipeline insights       → 外部洞察吸收
/pipeline design         → 设计稿到达/更新（主动推送）
/pipeline realign        → 规范升级入口（统一 realign 维度）
```

档位与详略由自然语言决定，编排层归一化后下传（[`task/intent-normalization`](../shared/constraints.md)），用户不需要记参数。

### realign 参数语法

```bash
/pipeline realign [--scope=<spec|layout|prd-mapping|health>] [--target=<path>] [--dry-run|--apply] [--fix=<rule_id>]
/pipeline realign --no-realign
```

| 参数 | 说明 |
|------|------|
| `--scope=spec` | 默认值；处理 spec_version 维度 |
| `--scope=prd-mapping` | 处理 PRD 映射维度 |
| `--scope=health` | 文档健康度主动审查（3 维度 / health-lint rule，清单见 [references/health-lint-implementation.md](references/health-lint-implementation.md)），执行接口见 [references/realign-scope-health.md](references/realign-scope-health.md) |
| `--target=<path>` | 限定回扫目标路径 |
| `--dry-run` | 只出差距报告，**业务产物零写入**；scope=health 允许写 `.health-report.md` 作报告载体 |
| `--apply` | 执行已确认的迁移 / 补齐动作 |
| `--fix=<rule_id>` | 仅 scope=health；仅修复指定 rule 的违规（须配 `--dry-run` 或 `--apply`，未配视为 `--dry-run`）|
| `--no-realign` | 拒绝升级提示，写入 `.devdocs-realign-ack`（`--headless` 时必需） |

## 提问式调度（智能引导）

无参数调用时，通过阶段感知 + 智能引导收敛到合适的入口：

### 阶段检测

首先扫描 `docs/devdocs/` 实际文件（而非依赖 `00-context.md` 进度），按下表首个命中即路由。

**无 DevDocs 文件时**：

| 检测项 | 判定 | 路由建议 |
|------|------|---------|
| 已有脚手架 + 新需求意图 | `docs/prd/requirements/index.md` 已存在，且用户描述的是**与当前不同的新需求**（须先于下方 PRD 候选行判定，否则不可达） | 路由 `/prd`，由其[新建需求门禁](../prd/SKILL.md#新建需求门禁强约束)⚠️三选一（继续当前 / clear 清理后新建 / discard 后新建）；未确认 ⛔ 不覆盖 |
| PRD 候选（继续当前需求） | 检测 `docs/prd/requirements/index.md`（单需求脚手架，扁平唯一路径），且用户意图为继续/消费当前需求；存在则读 maturity；不存在则跳过 | 存在读 maturity；0 个跳过 |
| `maturity=ready` | 产品需求已就绪（继续当前需求） | 建议 `/requirements --from-prd docs/prd/requirements/index.md` |
| `maturity=idea/draft` | 产品需求包未就绪（继续当前需求） | 建议 `/prd` 继续完善需求 |
| 有 `src/`、`lib/`、`app/` 等代码 | Q1a：新项目还是已有项目 | 已有项目 → `/retrofit`；脚手架/模板 → 继续按输入类型路由 |
| 用户输入极短（<200 字、无结构） | 模糊想法 | 建议 `/prd` 探索需求 |
| 文件/URL/长文 | 大文档引用 | 建议 `/prd prd` 解析文档 |

**已有 DevDocs 文件时**：

| 检测项 | 路由建议 |
|------|---------|
| 有 `00-baseline.md` 且无 `01`~`04`（基线已建，尚无需求） | 有新需求 → `/feature`；补充背景 → `/requirements --context` |
| verify-report（`--impl` / 全部，通过） | `/sync` 或 `/compound` |
| 有代码提交 + 任务进行中 | 继续 `/dev-workflow` |
| 有 01~04 + readiness-report 通过 | `/dev-workflow` |
| 有 01~04 + readiness 未通过或缺失 | `/verify --readiness` |
| 有 01~03 | `/dev-tasks` |
| 有 01 + 02 | `/test-cases` |
| 仅 `01-requirements.md` | `/system-design` |
| `05-insights.md` 含 ⏳ 待确认条目 | `/insights` 确认后进入 system-design 或 dev-tasks |

⛔ 「基线态」必须排在表首。基线项目 `docs/devdocs/` 存在会进入这张表，但除这一行外**匹配不到任何行**——原表最短的一行是「仅 `01-requirements.md`」，基线项目会直接落空。

报告类文件（readiness-report、verify-report）应比其源文件更新，过期时建议重新验证。

ℹ️ 建议:AGENTS.md 缺「工作流路由」节(存量 DevDocs 项目)→ 建议 `/agent-memory --update` 补齐;不阻塞路由。
ℹ️ 建议:检测到 01(或 01+02)已产出 → 可 `/board` 生成可视化评审页面(人审需求/设计;不阻塞、不强制)。

### 一次性升级提示（阶段检测后）

阶段检测完成后、返回路由建议之前，执行 drift 轻量检查。**两类语义不同，勿混**（维护者注意：health 永不接回 ack）：

**A. 升级类 drift（一次性版本决策，受 `.devdocs-realign-ack` 控制）**

**schema drift**（产物模板）：检测各产物 `spec_version` 与各 skill 当前常量差距 → 提示 `/pipeline realign`

检测到 drift 且无 `.devdocs-realign-ack` 标记时，打印**一次性**轻量提示（不阻塞原路由）。规则见 [references/realign.md](references/realign.md) § 一次性升级提示。

**B. 健康类 drift（持续监控信号，baseline-aware，*不*受 `.devdocs-realign-ack` / `--no-realign` 控制）**

3. **health drift**（文档健康度）：路由时跑廉价探针（≤2s，仅 stat `.claude/rules/devdocs-state.md` 体积 + 该文件单行长度，**不**全量扫描、**不**碰 frontmatter/死链/ADR）→ 命中则一行非阻塞提示 `/pipeline realign --scope=health`（跑全量扫描）。

> **语义分叉（关键，勿退化）**：升级类是"版本落后→升级决策"，ack 后永久静默合理；健康类是"文档持续退化"的监控信号，**绝不挂 ack**——否则 state 文件涨到 209KiB 也只提醒一次就永久哑火。health 每次进入路由按 `.health-baseline.yml` 重评估：承认存量债、只报新增退化。探针信号、baseline 比对、会话内去重见 [references/realign.md](references/realign.md) § health drift 探针。

**`.devdocs-realign-ack` 读写责任**：读取发生在阶段检测后；**写入仅由 `pipeline realign` / `--no-realign` 执行完成时触发**（整仓决策）—— `feature F-XX realign` / `bugfix BUG-XX realign` 是定向局部对齐，**不写入 ack**（用户未对整仓做决策，下次进入 pipeline 若仍有 drift 仍应提示；若定向 realign 正好清空全部 drift，pipeline 入口自然 drift_count=0 不会提示）。失效条件见 [references/realign.md](references/realign.md)。标记文件入 git，协作者共享决策。

### 自适应 Harness 深度

根据变更影响面自动推荐流程深度，避免轻量任务被重流程拖累，同时确保高风险变更不遗漏验证。

| 档位 | 特征 | 流程深度 | 路由 |
|------|------|----------|------|
| **Lite** | 单文件改动、无新接口、配置变更、UI 微调 | requirements(增量) → dev-tasks → dev-workflow | `/feature "<描述>"`（说明是小改动） 或 `/pipeline bugfix` |
| **Standard** | 多文件改动、新接口、新模块 | 全流程（requirements → design → tests → tasks → dev） | `/pipeline feature` |
| **Deep** | 跨模块架构变更、安全相关、核心数据模型变更 | 全流程 + 强制独立审查 + 强制文档对齐验证 | `/pipeline feature`（说明是架构级变更） |

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
    │           └── 已有代码 → /retrofit（非 pipeline 管辖）
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

| 入口 | 适用边界 | 调用顺序 / 路由 | 必传摘要字段 |
|------|---------|----------------|-------------|
| `init` | 全新项目，从需求到开发的完整流程<br>⚠️ dev-workflow 返回 `partial`（里程碑待验证）时停在该步 | **发布状态提问**（见下注）→ `requirements` → `agent-memory --update`（治理委托，见下注）→ `system-design` → `test-cases` → `dev-tasks` → `verify --readiness` → `dev-workflow`（批量）→ `verify --docs --impl` → `sync` | `output_files`、`new_ids.features`、`new_ids.acceptance`、各阶段 `status` |
| `feature` | 已有项目追加新功能；按 Harness 自动选择 Lite/Standard/Deep<br>⚠️ dev-workflow 返回 `partial` 时停在该步 | `feature`（内置 requirements/design/tests/tasks + Step 4.5 readiness + Step 6 dev-workflow）→ `verify --docs --impl` → `sync` | `entry`、Harness 档位、影响面摘要、`output_files`、`new_ids` |
| `bugfix` | 修复 Bug；不改变 feature 入口语义 | 简单 Bug：`bugfix` → `verify --impl` → `sync`；复杂 Bug：`dev-tasks` → `dev-workflow` → `verify --impl` → `sync` | Bug 范围、复杂度判定、修复文件、验证结果 |
| `verify` | 任意阶段质量检查 | 有代码变更 → `verify --impl`；有文档变更 → `verify --docs`；有 UI 设计稿 → `verify --ui`；不确定 → 询问用户；再路由到对应 skill 修复 | 检查维度、问题摘要、建议修复 skill |
| `close` | 开发周期结束收尾（上线后需求终结） | `sync`（trace + audit）→ `compound`（知识沉淀）→ `onboard --update` → `prd clear`（清理当前需求脚手架，末步执行确保 why 记忆已沉淀）；health 探针命中 blocker 级时，二级强化：建议顺带 `realign --scope=health` 全量扫描 | 同步结果、沉淀文件、更新后的上下文摘要、脚手架清理结果 |
| `insights` | 外部洞察吸收<br>⚠️ dev-workflow 返回 `partial` 时停在该步 | `insights`（收集 + 用户确认 + 追加 01）→ 有架构变更则 `system-design` → `test-cases` → `dev-tasks` → `verify --readiness` → `dev-workflow` → `verify` → `sync`；简单改进则 `dev-tasks` → `dev-workflow` → `verify` → `sync` | 洞察确认结果、架构影响判定、变更链路 |
| `design` | 用户主动推送设计资产；pipeline 只做阶段检测和收集 | no-prd → 收集并提示先 `/prd` 或 `/requirements`；prd-ready → `requirements --update-design --target prd-index`；post-requirements/post-design → `requirements --update-design`; in-dev → `requirements --update-design` + 提示 `verify --ui`; post-tasks → `requirements --update-design` → `dev-tasks --backfill-design` | `design_context`、目标阶段、委托目标、UI 验证提示 |
| `backlog` | 暂缓任务池维护（park / close / supersede / list / init）| 委托 `backlog`，传入 `source_id` 与动作 | 条目状态迁移结果、当前池内清单 |
| `realign` | 规范升级后回扫已完成产物；不破坏原完成证据，仅追加差距补齐 | 扫描 frontmatter → 比对各 skill 当前常量 → Phase 1 B 类上游 → Phase 2 A 类主链路 → Phase 3 B 类旁路 → 汇总 yaml-summary-v1 | drift 数量、Phase 结果、确认项 |

### 入口私有约束

- **治理委托(init 链 `agent-memory --update`)**:`requirements` 完成(首次产生 `docs/devdocs/`)后即 `Task: /agent-memory --update`,确保工作流路由节尽早落盘(中断也已发货)。**结果分支适配**:此为可选治理步,不适用通用"failed+blockers → 用户决定"分支——`success` 正常记录;`partial`/`failed`/`interrupted` 保留原状态与 blockers、显示 ℹ️ 后**继续主链**。写入范围窄例外:仅允许 agent-memory 写其受管记忆文件(`AGENTS.md`/`CLAUDE.md` 导入行/`.claude/rules/devdocs-state.md`),其余业务文件仍禁止。
- **readiness 关卡**：`dev-tasks` 后必须调用 `verify --readiness`；检查 AC↔测试用例对齐、任务文件路径具体性、依赖无环、设计↔任务一致性。P1 阻塞则展示问题清单，修复后重试。
- **全量补充验证**：`dev-workflow` 批量模式内部已含逐任务 sync + compound；pipeline 后置 `verify → sync` 是全量验证 + 幂等补充同步，不再额外执行 compound。
- **上下文传递**：启动时可读 `docs/devdocs/00-context.md` 作参考，但阶段检测始终以 `docs/devdocs/` 实际文件为准。
- **Deep 模式**：跨模块 / 架构 / 安全变更时，dev-workflow 所有任务强制 `--review`，feature 完成后额外执行 `verify --docs`，并展示影响面摘要。
- **Sprint Contract 协调**：`test-cases` 产出的可执行验收契约作为 `dev-workflow` 输入；pipeline 只传摘要、文件路径、新增编号，不内联测试全文。
- **design 主动推送**：详细协议见 [../prd/references/design-context.md](../prd/references/design-context.md)；pipeline 不写文档，no-prd 不阻塞，且不中断当前 dev-workflow。
- **发布状态提问（init 首步，源头治理）**：`init` 开始时 AskUserQuestion **问一次**「这个项目发布过吗」。未发布 → ⛔ 不套 semver，用 Sprint / 阶段代号 / 待办池表达进度（⛔ 这里不要写「里程碑」——`M-XXX` 是 01 §2.5 的需求分段概念，同名会误读）；已发布 → semver 是真契约，正常使用。结论由 `agent-memory --update` 写进 AGENTS.md「约定」节，后续 skill 据此决定怎么表达进度。
  - 只问这一个问题，⛔ 不追问具体用哪种约定——那可以后面按需定，开工时多打断一次不值。
  - 理由：版本号和进度是**自己造的现状**，代码里读不出来，天然需要有人定。没有真实发布节点可依时，版本号只能当占位符用，被大量引用后回潮难防；在源头问一次的成本远低于事后清理。
  - 接手既有项目走 `retrofit`，同一个问题在 `00-baseline.md` §2.1 问，两条路径结论都落 AGENTS.md。
- **close 脚手架清理**：close 末步委托 `prd clear` 清理 `docs/prd/` 一次性脚手架；先 dry-run 出范围 + 影响（孤儿 / 未同步项默认不删），⚠️ 必须确认后 `--apply` 删除；无 `docs/prd/` 时静默跳过。pipeline 只委托不自己删文件（见 prd [清理脚手架](../prd/SKILL.md#清理脚手架close-收尾)）。
- **realign 协调机制**：realign 非续做信号；restructuring 差距必须 `⚠️ 必须确认`；additive 可直接补齐；二次运行幂等；`--headless` 必须显式 `--realign` 或 `--no-realign`。
- **工作区拓扑（`init`）**：`requirements` 完成后（首次产生 `docs/devdocs/`）执行 `Task: /workspace-topology reconcile`。该 skill 自己写 `AGENTS.md` 的 `workspace:` 块，**不经 `agent-memory` 代写**——`devdocs_frontmatter` 入参不再传 workspace 字段。无声明时它问一次 mode 与代码根并落声明，此后不再问。另在流程开头调一次 `/workspace-topology inspect`，把结果经握手的 `workspace_context` 下传给各原子 skill（见 [shared/constraints.md §3](../shared/constraints.md) `task/workspace-context`）。retrofit 场景的路径由 [retrofit/SKILL.md](../retrofit/SKILL.md) 自己承载。

### Sprint Contract 握手

pipeline 启动 `test-cases` 和 `dev-workflow` 时，保留跨 skill 协作的最小上下文：

| 来源 | 去向 | 必传内容 | 规则 |
|------|------|---------|------|
| `test-cases` | `dev-tasks` | UT/IT/E2E 编号、覆盖到的 AC、测试文件建议 | 只传摘要 + 文件路径，具体测试设计由下游自行读取 |
| `dev-tasks` | `verify --readiness` | 任务清单、依赖关系、任务 ↔ AC/测试映射 | readiness 失败时阻塞进入 dev-workflow |
| `verify --readiness` | `dev-workflow` | 通过状态、P1 阻塞清零证据、可执行任务范围 | 无通过证据不得启动开发执行 |
| `dev-workflow` | `sync` / `verify` | 已完成任务、修改文件、测试结果、trace 变更 | pipeline 后置全量验证，覆盖跨任务遗漏 |

### realign / layout 协调细节

`realign` 处理 spec_version 维度，由 pipeline 汇总 yaml-summary-v1。

| 维度 | 扫描源 | 调度 / 迁移阶段 | 输出 |
|------|--------|----------------|------|
| spec_version | 各产物 frontmatter + 各 skill `references/realign.md` 当前常量 | Phase 1 B 类上游 → Phase 2 A 类主链路 → Phase 3 B 类旁路 | drift 清单、逐 skill summary、remaining blockers |

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
    ├── Task: /requirements → YAML 摘要
    ├── Task: /system-design → YAML 摘要
    ├── Task: /test-cases → YAML 摘要
    ├── Task: /dev-tasks → YAML 摘要
    ├── Task: /verify --readiness → YAML 摘要
    ├── Task: /dev-workflow → YAML 摘要
    ├── Task: /verify → YAML 摘要
    └── Task: /sync → YAML 摘要
```

### 摘要传递

阶段间只传递 YAML 摘要 + 文件路径。编排 Agent **不读取**子技能的完整输出文档。

### 异常回退

子 Agent 返回 `status: failed` + `blockers` 时：
1. 展示阻塞项给用户
2. 询问用户处理方式（修复/跳过/终止）
3. **不自行读取文档排障**

子 Agent 返回 `status: partial` 时（⛔ 不得当成完成）：
1. 展示 `blockers` 与 `summary.details` 里的待确认事项
2. **⛔ 停在此处，不进入链路下一阶段**
3. 给出续做入口（`next_recommended`），由用户决定何时继续

> **`dev-workflow` 的里程碑段末**是这条分支最常见的来源：一段实现完成、等待用户实际使用验证。
> 它不是失败，但也**绝不能**当作开发阶段完成继续跑 `verify → sync` ——那等于绕过了用户验证这道门，而它正是这套机制存在的理由。
> 判据只看信封：`status: partial` + `details.milestones_pending` 非空。⛔ pipeline 不读产出文档、不读检查点文件。

### 上下文隔离

每个子 Agent 自行读取所需的前置文档（从 `docs/devdocs/` 文件系统），不依赖编排 Agent 传递全文。

## 约束

### DevDocs 6 阶段治理

pipeline 视角的主链路阶段固定为：

1. requirements：编码结构化需求与 AC
2. system-design：补齐技术设计与接口边界
3. test-cases：产出 UT/IT/E2E 与 Sprint Contract
4. dev-tasks：拆分可执行任务与依赖
5. dev-workflow：按任务执行开发与逐任务验证
6. verify/sync：全量验证、追溯同步和收尾

insights、design、realign 属于入口或治理分支，不改变 6 阶段主链路顺序；bugfix 可走独立快速路径或回落到 dev-tasks → dev-workflow。

### 阶段边界约束（全局规则）

DevDocs 工作流严格区分**文档阶段**和**编码阶段**：

| 阶段 | 技能 | 产出类型 | 允许编码 |
|------|------|----------|----------|
| 需求 | requirements | 文档 | ❌ |
| 设计 | system-design | 文档 | ❌ |
| 测试设计 | test-cases | 文档 | ❌ |
| 任务拆分 | dev-tasks | 文档 | ❌ |
| 项目改造 | retrofit | 文档 | ❌ |
| **开发执行** | **dev-workflow** | **代码** | **✅** |
| **Bug 修复** | **bugfix** | **代码** | **✅** |

- [ ] **⛔ 禁止继续：文档阶段不得产出实现代码，仅写入 `docs/devdocs/` 下的 Markdown 文档**（恢复方式：将代码产出移至 dev-workflow/bugfix 阶段）

### 编排约束

- [ ] **pipeline 仅负责路由和衔接，不复制任何原子 skill 的逻辑**
- [ ] **每个阶段必须委托给对应的原子 skill 执行**
- [ ] **阶段间传递的信息仅限：新增编号列表、状态摘要、文件路径**

### 提问式调度约束

- [ ] **优先使用阶段检测自动判断，无法判断时才提问**
- [ ] **兜底问答最多 3 个问题收敛到入口**
- [ ] **问题必须有明确的选项（不开放式提问）**
- [ ] 识别到 retrofit 场景时，路由到 `/retrofit` 并退出 pipeline
- [ ] **分轨提示基于变更规模，不引入额外术语**

### 上下文约束

- [ ] **优先读取 00-context.md 作为快速上下文（如存在且 < 24h）**
- [ ] pipeline 编排层不读取大量源代码（委托给子 skill）
- [ ] 每个阶段完成后展示简要摘要（< 10 行）

### 编排约束（子 Agent）

- [ ] **调用其他技能时必须通过 Task tool 启动子 Agent**
- [ ] **子 Agent 失败时展示阻塞项询问用户，不自行排障**
- [ ] **每个子 Agent 自行读取前置文档，编排层不传递全文**

## Skill 协作

| 入口 | 编排的 Skill 链 |
|------|----------------|
| init | requirements → system-design → test-cases → dev-tasks → **verify --readiness** → dev-workflow → verify → sync |
| feature | feature(含 readiness + dev-workflow) → verify → sync（深度档时 dev-workflow 强制独立审查 + verify 含 --docs） |
| bugfix | bugfix / (dev-tasks → dev-workflow) → verify → sync |
| verify | verify --docs/--impl/--ui |
| insights | 见下方 insights 流程图 |
| close | sync → compound → onboard --update → prd clear（脚手架清理，dry-run→⚠️确认→删） |
| design | 阶段检测 → 委托 requirements --update-design [→ dev-tasks --backfill-design] |
| realign | Phase 1 B 类上游：prd-parser/prd-brainstorm --realign（若存在）→ Phase 2 A 类主链路：requirements → system-design → test-cases → dev-tasks → dev-workflow --all → Phase 3 B 类旁路：insights/onboard（若存在）（详见 [references/realign.md](references/realign.md)） |

> **补充说明**：dev-workflow 批量模式内部会调用 `/test-run --trace` 执行全量测试 + 追溯验证，详见 `skills/dev-workflow/SKILL.md`。

### insights 入口流程

```text
/insights（收集 + 用户确认 + 追加 01-requirements.md）
    │
    ▼
评估是否涉及架构变更
    │
    ├── 有架构变更（新 API / 数据模型 / 新模块）
    │   └── /system-design → /test-cases → /dev-tasks
    │       → **verify --readiness** → /dev-workflow → /verify → /sync
    │
    └── 简单改进（纯配置 / 样式调整）
        └── /dev-tasks → /dev-workflow → /verify → /sync
```

## 子 Agent 摘要格式

当本 Skill 作为子 Agent 运行时，返回 yaml-summary-v1；完整 envelope 见 [../shared/constraints.md](../shared/constraints.md) § 2。pipeline 私有字段只放在 `summary.details`：

```yaml
summary:
  headline: "init 流程完成 2/5 阶段"
  details:
    entry: init | feature | bugfix | verify | close | insights | design
    harness_depth: Lite | Standard | Deep
    stages_completed:
      - { skill: requirements, status: success }
      - { skill: system-design, status: success }
    stages_remaining:
      - test-cases
    interrupt_reason: "用户选择退出"  # 仅中断时
```

| 字段 | 含义 |
|------|------|
| `entry` | 本次入口，必须对应运行模式之一 |
| `harness_depth` | feature / bugfix 场景的 Lite、Standard、Deep 判定 |
| `stages_completed` | 已完成阶段及子 Agent status |
| `stages_remaining` | 用户中断或 partial 时的剩余阶段 |
| `interrupt_reason` | 仅中断时记录用户选择或环境限制 |

`output_files`、`new_ids`、`next_recommended` 仍使用共享 envelope 字段；pipeline 只填文件路径、新增编号和下一建议 skill，不扩展字段语义。

## 下一步

pipeline 完成后，所有产出文档均已生成/更新。用户可：

- 继续下一轮 feature/bugfix
- 运行 `/onboard --read` 传递上下文给新 AI

> ⚠️ 新增功能开发时，不得跳过 test-cases、dev-tasks、verify --readiness 直接进入 dev-workflow。Bug 修复按 `/pipeline bugfix` 路径处理。
