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

## 详细文档

- 共享约束 SSOT：[../_shared/constraints.md](../_shared/constraints.md)
- pipeline 治理 SSOT：[references/realign.md](references/realign.md)、[references/realign-scope-layout.md](references/realign-scope-layout.md)、[references/layout/](references/layout/)

> 本 skill 遵循共享约束 SSOT：门控标记、yaml-summary-v1、Task 委托、用户确认、Recovery 格式、只读 / dry-run、FUTURE 三态、realign / spec_version 见 [skills/_shared/constraints.md](../_shared/constraints.md)。本文件只描述 ms-pipeline 编排私有规则。

## 运行模式 / 入口语法

```bash
/ms-pipeline                → 提问式调度（自动判断）
/ms-pipeline init           → 新项目全流程
/ms-pipeline feature        → 新功能开发（自动检测 Harness 深度）
/ms-pipeline bugfix         → Bug 修复
/ms-pipeline verify         → 质量检查
/ms-pipeline close          → 周期收尾
/ms-pipeline insights       → 外部洞察吸收
/ms-pipeline design         → 设计稿到达/更新（主动推送）
/ms-pipeline realign        → 规范升级入口（统一 realign 维度）
```

子命令内部参数（如 `feature --deep`）仍由对应入口透传和解释，不作为 pipeline 顶层入口暴露。

### realign 参数语法

```bash
/ms-pipeline realign [--scope=<spec|layout|prd-mapping|health>] [--target=<path>] [--dry-run|--apply] [--fix=<rule_id>]
/ms-pipeline realign --no-realign
```

| 参数 | 说明 |
|------|------|
| `--scope=spec` | 默认值；处理 spec_version 维度 |
| `--scope=layout` | 文档体系版本升级（layout.v1→v2，含编号/目录/追溯重组），执行接口见 [references/realign-scope-layout.md](references/realign-scope-layout.md) |
| `--scope=prd-mapping` | 处理 PRD 映射维度 |
| `--scope=health` | 文档健康度主动审查（5 维度 / health-lint rule，清单见 [references/health-lint-implementation.md](references/health-lint-implementation.md)，layout.v1+v2 通用），执行接口见 [references/realign-scope-health.md](references/realign-scope-health.md) |
| `--target=<path>` | 限定回扫目标路径 |
| `--dry-run` | 只出差距报告，**业务产物零写入**；scope=health 允许写 `.health-report.md` 作报告载体 |
| `--apply` | 执行已确认的迁移 / 补齐动作 |
| `--fix=<rule_id>` | 仅 scope=health；仅修复指定 rule 的违规（须配 `--dry-run` 或 `--apply`，未配视为 `--dry-run`）|
| `--no-realign` | 拒绝升级提示，写入 `.devdocs-realign-ack`（`--headless` 时必需） |
| `--docs-layout` | deprecated alias，等价于 `--scope=layout`，下一版本移除 |

## 提问式调度（智能引导）

无参数调用时，通过阶段感知 + 智能引导收敛到合适的入口：

### 阶段检测

首先扫描 `docs/devdocs/` 实际文件（而非依赖 `00-context.md` 进度），按下表首个命中即路由。

**无 DevDocs 文件时**：

| 检测项 | 判定 | 路由建议 |
|------|------|---------|
| 已有脚手架 + 新需求意图 | `docs/prd/requirements/index.md` 已存在，且用户描述的是**与当前不同的新需求**（须先于下方 PRD 候选行判定，否则不可达） | 路由 `/ms-prd`，由其[新建需求门禁](../prd/SKILL.md#新建需求门禁强约束)⚠️三选一（继续当前 / clear 清理后新建 / discard 后新建）；未确认 ⛔ 不覆盖 |
| PRD 候选（继续当前需求） | 检测 `docs/prd/requirements/index.md`（单需求脚手架，扁平唯一路径），且用户意图为继续/消费当前需求；存在则读 maturity；不存在则跳过 | 存在读 maturity；0 个跳过 |
| `maturity=ready` | 产品需求已就绪（继续当前需求） | 建议 `/ms-requirements --from-prd docs/prd/requirements/index.md` |
| `maturity=idea/draft` | 产品需求包未就绪（继续当前需求） | 建议 `/ms-prd` 继续完善需求 |
| 有 `src/`、`lib/`、`app/` 等代码 | Q1a：新项目还是已有项目 | 已有项目 → `/ms-retrofit`；脚手架/模板 → 继续按输入类型路由 |
| 用户输入极短（<200 字、无结构） | 模糊想法 | 建议 `/ms-prd` 探索需求 |
| 文件/URL/长文 | 大文档引用 | 建议 `/ms-prd prd` 解析文档 |

**已有 DevDocs 文件时**：

| 检测项 | 路由建议 |
|------|---------|
| verify-report（`--impl` / 全部，通过） | `/ms-sync` 或 `/ms-compound` |
| 有代码提交 + 任务进行中 | 继续 `/ms-dev-workflow` |
| 有 01~04 + readiness-report 通过 | `/ms-dev-workflow` |
| 有 01~04 + readiness 未通过或缺失 | `/ms-verify --readiness` |
| 有 01~03 | `/ms-dev-tasks` |
| 有 01 + 02 | `/ms-test-cases` |
| 仅 `01-requirements.md` | `/ms-system-design` |
| `05-insights.md` 含 ⏳ 待确认条目 | `/ms-insights` 确认后进入 system-design 或 dev-tasks |

报告类文件（readiness-report、verify-report）应比其源文件更新，过期时建议重新验证。

ℹ️ 建议:AGENTS.md 缺「工作流路由」节(存量 DevDocs 项目)→ 建议 `/agent-memory --update` 补齐;不阻塞路由。
ℹ️ 建议:检测到 01(或 01+02)已产出 → 可 `/ms-board` 生成可视化评审页面(人审需求/设计;不阻塞、不强制)。

### 一次性升级提示（阶段检测后）

阶段检测完成后、返回路由建议之前，执行 drift 轻量检查。**两类语义不同，勿混**（维护者注意：health 永不接回 ack）：

**A. 升级类 drift（一次性版本决策，受 `.devdocs-realign-ack` 控制）**

1. **schema drift**（产物模板）：检测各产物 `spec_version` 与各 skill 当前常量差距 → 提示 `/ms-pipeline realign`
2. **layout drift**（治理层）：检测 AGENTS.md devdocs frontmatter 是否存在 + `docs_layout_version` 是否在各 skill `reads_layout` 范围 → 提示 `/ms-pipeline realign --scope=layout`

检测到 drift 且无 `.devdocs-realign-ack` 标记时，打印**一次性**轻量提示（不阻塞原路由）。**layout drift 强阻塞场景**（skill `on_incompatible: block` 触发）会直接拒绝执行，不走"一次性提示"软路径。schema drift 规则见 [references/realign.md](references/realign.md) § 一次性升级提示；layout scope 执行接口见 [references/realign-scope-layout.md](references/realign-scope-layout.md)，检测时机见 [references/layout/layout-versioning-policy.md](references/layout/layout-versioning-policy.md)。

**B. 健康类 drift（持续监控信号，baseline-aware，*不*受 `.devdocs-realign-ack` / `--no-realign` 控制）**

3. **health drift**（文档健康度）：路由时跑廉价探针（≤2s，仅 stat `.claude/rules/devdocs-state.md` 体积 + 该文件单行长度，**不**全量扫描、**不**碰 frontmatter/死链/ADR）→ 命中则一行非阻塞提示 `/ms-pipeline realign --scope=health`（跑全量扫描）。

> **语义分叉（关键，勿退化）**：升级类是"版本落后→升级决策"，ack 后永久静默合理；健康类是"文档持续退化"的监控信号，**绝不挂 ack**——否则 state 文件涨到 209KiB 也只提醒一次就永久哑火。health 每次进入路由按 `.health-baseline.yml` 重评估：承认存量债、只报新增退化。探针信号、baseline 比对、会话内去重见 [references/realign.md](references/realign.md) § health drift 探针。

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

| 入口 | 适用边界 | 调用顺序 / 路由 | 必传摘要字段 |
|------|---------|----------------|-------------|
| `init` | 全新项目，从需求到开发的完整流程 | `ms-requirements` → `agent-memory --update`（治理委托，见下注）→ `ms-system-design` → `ms-test-cases` → `ms-dev-tasks` → `ms-verify --readiness` → `ms-dev-workflow`（批量）→ `ms-verify --docs --impl` → `ms-sync` | `output_files`、`new_ids.features`、`new_ids.acceptance`、各阶段 `status` |
| `feature` | 已有项目追加新功能；按 Harness 自动选择 Lite/Standard/Deep | `ms-feature`（内置 requirements/design/tests/tasks + Step 4.5 readiness + Step 6 dev-workflow）→ `ms-verify --docs --impl` → `ms-sync` | `entry`、Harness 档位、影响面摘要、`output_files`、`new_ids` |
| `bugfix` | 修复 Bug；不改变 feature 入口语义 | 简单 Bug：`ms-bugfix` → `ms-verify --impl` → `ms-sync`；复杂 Bug：`ms-dev-tasks` → `ms-dev-workflow` → `ms-verify --impl` → `ms-sync` | Bug 范围、复杂度判定、修复文件、验证结果 |
| `verify` | 任意阶段质量检查 | 有代码变更 → `ms-verify --impl`；有文档变更 → `ms-verify --docs`；有 UI 设计稿 → `ms-verify --ui`；不确定 → 询问用户；再路由到对应 skill 修复 | 检查维度、问题摘要、建议修复 skill |
| `close` | 开发周期结束收尾（上线后需求终结） | `ms-sync`（trace + audit）→ `ms-compound`（知识沉淀）→ `ms-onboard --update` → `ms-prd clear`（清理当前需求脚手架，末步执行确保 why 记忆已沉淀）；health 探针命中 blocker 级时，二级强化：建议顺带 `realign --scope=health` 全量扫描 | 同步结果、沉淀文件、更新后的上下文摘要、脚手架清理结果 |
| `insights` | 外部洞察吸收 | `ms-insights`（收集 + 用户确认 + 追加 01）→ 有架构变更则 `ms-system-design` → `ms-test-cases` → `ms-dev-tasks` → `ms-verify --readiness` → `ms-dev-workflow` → `ms-verify` → `ms-sync`；简单改进则 `ms-dev-tasks` → `ms-dev-workflow` → `ms-verify` → `ms-sync` | 洞察确认结果、架构影响判定、变更链路 |
| `design` | 用户主动推送设计资产；pipeline 只做阶段检测和收集 | no-prd → 收集并提示先 `/ms-prd` 或 `/ms-requirements`；prd-ready → `ms-requirements --update-design --target prd-index`；post-requirements/post-design → `ms-requirements --update-design`; in-dev → `ms-requirements --update-design` + 提示 `ms-verify --ui`; post-tasks → `ms-requirements --update-design` → `ms-dev-tasks --backfill-design` | `design_context`、目标阶段、委托目标、UI 验证提示 |
| `realign` | 规范升级后回扫已完成产物；不破坏原完成证据，仅追加差距补齐 | spec_version：扫描 frontmatter → 比对各 skill 当前常量 → Phase 1 B 类上游 → Phase 2 A 类主链路 → Phase 3 B 类旁路 → 汇总 yaml-summary-v1；layout scope：扫描 AGENTS.md devdocs frontmatter → 比对 `writes_layout` → 三阶段迁移 | drift 数量、Phase 结果、确认项、layout/id/trace 差距 |

### 入口私有约束

- **治理委托(init 链 `agent-memory --update`)**:`ms-requirements` 完成(首次产生 `docs/devdocs/`)后即 `Task: /agent-memory --update`,确保工作流路由节尽早落盘(中断也已发货)。**结果分支适配**:此为可选治理步,不适用通用"failed+blockers → 用户决定"分支——`success` 正常记录;`partial`/`failed`/`interrupted` 保留原状态与 blockers、显示 ℹ️ 后**继续主链**。写入范围窄例外:仅允许 agent-memory 写其受管记忆文件(`AGENTS.md`/`CLAUDE.md` 导入行/`.claude/rules/devdocs-state.md`),其余业务文件仍禁止。
- **readiness 关卡**：`dev-tasks` 后必须调用 `ms-verify --readiness`；检查 AC↔测试用例对齐、任务文件路径具体性、依赖无环、设计↔任务一致性。P1 阻塞则展示问题清单，修复后重试。
- **全量补充验证**：`dev-workflow` 批量模式内部已含逐任务 sync + compound；pipeline 后置 `verify → sync` 是全量验证 + 幂等补充同步，不再额外执行 compound。
- **上下文传递**：启动时可读 `docs/devdocs/00-context.md` 作参考，但阶段检测始终以 `docs/devdocs/` 实际文件为准。
- **Deep 模式**：跨模块 / 架构 / 安全变更时，dev-workflow 所有任务强制 `--review`，feature 完成后额外执行 `ms-verify --docs`，并展示影响面摘要。
- **Sprint Contract 协调**：`ms-test-cases` 产出的可执行验收契约作为 `ms-dev-workflow` 输入；pipeline 只传摘要、文件路径、新增编号，不内联测试全文。
- **design 主动推送**：详细协议见 [../prd/references/design-context.md](../prd/references/design-context.md)；pipeline 不写文档，no-prd 不阻塞，且不中断当前 dev-workflow。
- **close 脚手架清理**：close 末步委托 `ms-prd clear` 清理 `docs/prd/` 一次性脚手架；先 dry-run 出范围 + 影响（孤儿 / 未同步项默认不删），⚠️ 必须确认后 `--apply` 删除；无 `docs/prd/` 时静默跳过。pipeline 只委托不自己删文件（见 ms-prd [清理脚手架](../prd/SKILL.md#清理脚手架close-收尾)）。
- **realign 协调机制**：realign 非续做信号；restructuring / layout 差距必须 `⚠️ 必须确认`；additive 可直接补齐；二次运行幂等；`--headless` 必须显式 `--realign` 或 `--no-realign`；layout scope 升级需先跑 `--dry-run` + 独立 git branch 演练，执行接口见 [references/realign-scope-layout.md](references/realign-scope-layout.md)。
- **layout / id / trace 三层版本共性**：pipeline 是 SSOT 来源。三层版本号宪法见 [references/layout/layout-versioning-policy.md](references/layout/layout-versioning-policy.md)，元数据 schema 见 [references/layout/layout-metadata-schema.md](references/layout/layout-metadata-schema.md)，aliases 见 [references/layout/aliases-yml-schema.md](references/layout/aliases-yml-schema.md)，迁移矩阵和不可逆操作见 [references/layout/docs-layout-migration.md](references/layout/docs-layout-migration.md)。
- **工作区拓扑（`init`）**：`ms-requirements` 完成后（首次产生 `docs/devdocs/`）执行 `Task: /workspace-topology reconcile`。该 skill 自己写 `AGENTS.md` 的 `workspace:` 块，**不经 `agent-memory` 代写**——`devdocs_frontmatter` 入参不再传 workspace 字段。无声明时它问一次 mode 与代码根并落声明，此后不再问。另在流程开头调一次 `/workspace-topology inspect`，把结果经握手的 `workspace_context` 下传给各原子 skill（见 [_shared/constraints.md §3](../_shared/constraints.md) `task/workspace-context`）。retrofit 场景的路径由 [retrofit/SKILL.md](../retrofit/SKILL.md) 自己承载。

### Sprint Contract 握手

pipeline 启动 `ms-test-cases` 和 `ms-dev-workflow` 时，保留跨 skill 协作的最小上下文：

| 来源 | 去向 | 必传内容 | 规则 |
|------|------|---------|------|
| `ms-test-cases` | `ms-dev-tasks` | UT/IT/E2E 编号、覆盖到的 AC、测试文件建议 | 只传摘要 + 文件路径，具体测试设计由下游自行读取 |
| `ms-dev-tasks` | `ms-verify --readiness` | 任务清单、依赖关系、任务 ↔ AC/测试映射 | readiness 失败时阻塞进入 dev-workflow |
| `ms-verify --readiness` | `ms-dev-workflow` | 通过状态、P1 阻塞清零证据、可执行任务范围 | 无通过证据不得启动开发执行 |
| `ms-dev-workflow` | `ms-sync` / `ms-verify` | 已完成任务、修改文件、测试结果、trace 变更 | pipeline 后置全量验证，覆盖跨任务遗漏 |

### realign / layout 协调细节

`realign` 默认处理 spec_version 维度；`--scope=layout` 处理治理层 layout/id/trace 维度，执行接口见 [references/realign-scope-layout.md](references/realign-scope-layout.md)。两者都由 pipeline 汇总 yaml-summary-v1。

| 维度 | 扫描源 | 调度 / 迁移阶段 | 输出 |
|------|--------|----------------|------|
| spec_version | 各产物 frontmatter + 各 skill `references/realign.md` 当前常量 | Phase 1 B 类上游 → Phase 2 A 类主链路 → Phase 3 B 类旁路 | drift 清单、逐 skill summary、remaining blockers |
| docs_layout_version | AGENTS.md devdocs frontmatter + skill `writes_layout` / `reads_layout` | Phase 1 预扫描 → Phase 2 编号 + 文件迁移 → Phase 3 后置校验 | layout 差距、确认项、aliases、traceability 校验 |

layout scope dry-run 必输出 5 项契约：

1. `file_ops`：文件移动、复制、删除、重命名计划
2. `aliases`：旧路径到新路径的兼容映射
3. `unmappable`：无法自动定位或安全迁移的对象
4. `broken_links`：迁移后可能断裂的引用
5. `trace_drift`：编号、任务、代码追溯关系差距

Phase 2 只执行 dry-run 批准项；Phase 3 必做 traceability 提取、SSOT lint、AGENTS.md `upgraded_at` 写入。详细迁移矩阵见 [references/layout/docs-layout-migration.md](references/layout/docs-layout-migration.md)。

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
| close | sync → compound → onboard --update → ms-prd clear（脚手架清理，dry-run→⚠️确认→删） |
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

当本 Skill 作为子 Agent 运行时，返回 yaml-summary-v1；完整 envelope 见 [../_shared/constraints.md](../_shared/constraints.md) § 2。pipeline 私有字段只放在 `summary.details`：

```yaml
summary:
  headline: "init 流程完成 2/5 阶段"
  details:
    entry: init | feature | bugfix | verify | close | insights | design
    harness_depth: Lite | Standard | Deep
    stages_completed:
      - { skill: ms-requirements, status: success }
      - { skill: ms-system-design, status: success }
    stages_remaining:
      - ms-test-cases
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
- 运行 `/ms-onboard --read` 传递上下文给新 AI

> ⚠️ 新增功能开发时，不得跳过 test-cases、dev-tasks、verify --readiness 直接进入 dev-workflow。Bug 修复按 `/ms-pipeline bugfix` 路径处理。
