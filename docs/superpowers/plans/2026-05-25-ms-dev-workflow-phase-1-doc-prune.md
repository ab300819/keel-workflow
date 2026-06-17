> ⚠️ **历史归档(SUPERSEDED)**:本计划属 2026-05-25 速度优化路线的 Phase 1,已被 2026-06-08 重新定位重构取代(见 [2026-06-08-devdocs-repositioning-and-dev-workflow-redesign-design.md](../specs/2026-06-08-devdocs-repositioning-and-dev-workflow-redesign-design.md))。本文档内的 🔴 层级语义为**当时**模型,不代表当前 review_profile 模型,不作活跃规范。

# ms-dev-workflow Phase 1 实施计划:P0-A 文档收敛 + 累计删减审计

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 落地 ms-dev-workflow 速度优化的 Phase 1 — 文字澄清 + 5 项累计删减,无行为变更,作为 Phase 2(P1 并行化 + P2 批量合并)的前置准备。

**Architecture:** 纯文档编辑 + 静态验证。不涉及代码逻辑、不涉及行为变更。每文件独立 commit(7 任务、6 commit)。最终通过 grep + wc 验证唯一权威 + 净变化目标 -220 行(Phase 2 后再 +200 即净 -30)。

**Tech Stack:** Markdown + git。无 build/test/lint。

**Spec:** [docs/superpowers/specs/2026-05-25-ms-dev-workflow-speed-optimization-design.md](../specs/2026-05-25-ms-dev-workflow-speed-optimization-design.md)

---

## File Structure

| 文件 | 当前行数 | Phase 1 后预计 | 责任 |
|------|---------:|---------------:|------|
| skills/dev-workflow/SKILL.md | 393 | ~400 | 入口 + 语法表 + 关键约束 + spec_version |
| skills/dev-workflow/references/auto-mode.md | 283 | ~185 | 无人值守模式;不再重复 Phase 4 状态/重试 |
| skills/dev-workflow/references/verification-flow.md | 520 | ~458 | Phase 4 唯一权威;不再保留"已前移到 S8" 历史段 |
| skills/dev-workflow/references/execution-flow.md | 315 | ~289 | 不再重复转述 Phase 2-UI / Phase 4 |
| skills/dev-workflow/references/task-orchestration.md | 470 | ~458 | 不再重复转述 Phase 4 状态 |
| skills/dev-workflow/references/skeleton-examples.md | 248 | ~178 | 仅保留接口/测试骨架 + traceability.yml 风格的最小示例 |
| skills/dev-workflow/references/ui-quality-checklist.md | 91 | 91 | **不变** — 留作 Phase 2-UI 唯一权威 |
| skills/dev-workflow/references/realign.md | 122 | 122 | **不变** |
| **dev-workflow 总规模** | **2442** | **~2222** | 净 -220(Phase 1)|

> Phase 2 落地后预计 +200 → 净 -30 vs 当前基线(spec 目标)。

**约束**:
- `verification-flow.md:386-520` Phase 4 权威状态机**不动结构,仅允许添加澄清文字**
- `ui-quality-checklist.md` 已是 Phase 2-UI 唯一权威,**Phase 1 完全不动**
- 不引入新文件、不重命名、不动 frontmatter 之外的元数据

---

## Task 1:删 skeleton-examples.md 长实现示例(-70)

**Files:**
- Modify: `skills/dev-workflow/references/skeleton-examples.md:72-178`

**背景**:`@satisfies/@verifies` 与 layout.v2 外置追溯(`traceability.yml`)方向冲突,长示例是历史包袱。spec §6.1.2。

- [ ] **Step 1: Read 当前文件验证锚点**

Run: `sed -n '70,75p;176,182p' skills/dev-workflow/references/skeleton-examples.md`

Expected:第 72 行附近开始 "## 完整实现示例(Step 3-4)",约 178 行附近过渡到 "## 行为契约 → Test Agent 断言示例"。

- [ ] **Step 2: 用 Edit 工具删除 72-178 区间,替换为最小骨架示例 + 指针**

锚点定位用"## 完整实现示例" 章节标题到 "## 行为契约" 章节标题之间的整段。

替换为以下精简内容(~37 行,layout.v2 风格):

```markdown
## 完整实现示例(Step 3-4)

> ⚠️ 仅展示骨架→实现的最小过渡。完整业务实现示例不再保留于本 skill;追溯标注请参考所在项目的 `traceability.yml`(layout.v2)或保留的 `@satisfies/@verifies` 注释(layout.v1 legacy,不新增)。

### 接口实现(最小骨架填充示意)

```typescript
// layout.v2:不写 @satisfies 注释,追溯统一通过 traceability.yml
export class CreateOrderService {
  async execute(input: CreateOrderInput): Promise<Order> {
    // Impl Agent 在此填充最小实现以让 Test Agent 写的测试转绿
    // 业务逻辑 / 边界 / 异常,由测试断言驱动
    throw new Error('TODO(T-XX): replace with minimal implementation');
  }
}
```

### 测试骨架填充(Test Agent 产出)

```typescript
describe('CreateOrderService', () => {
  // skip/todo 标记仅用于 S3 骨架阶段;S4 写完断言后必须移除
  it.todo('should create order with valid input (AC-001)');
  it.todo('should reject input with missing customer (AC-002)');
});
```

> 实战场景请参考 layout.v2 项目的 `traceability.yml` schema 与对应测试文件命名约定。
```

- [ ] **Step 3: 行数验证**

Run: `wc -l skills/dev-workflow/references/skeleton-examples.md`

Expected:从 248 行降到 ~178 行(±5)。

- [ ] **Step 4: 验证 layout.v1 标注未被误删(头部 71 行仍保留)**

Run: `sed -n '1,71p' skills/dev-workflow/references/skeleton-examples.md | grep -E "@requirement|@satisfies|@verifies|@testcase"`

Expected:至少 1 处 layout.v1 标注示例仍在头部章节(legacy 兼容文档)。

- [ ] **Step 5: Commit**

```bash
git add skills/dev-workflow/references/skeleton-examples.md
git commit -m "$(cat <<'EOF'
refactor(dev-workflow): trim skeleton-examples layout.v1 long impl example (-70)

- 删除 72-178 区间的完整实现示例
- 替换为 layout.v2 风格的最小骨架填充示意(~37 行)
- layout.v1 @satisfies/@verifies 注释示例保留于头部 1-71 行

Phase 1 of dev-workflow speed optimization (累计删减 1/5)
See: docs/superpowers/specs/2026-05-25-ms-dev-workflow-speed-optimization-design.md §6.1.2

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2:压缩 auto-mode.md(-98)

**Files:**
- Modify: `skills/dev-workflow/references/auto-mode.md:91-121`(删 Phase 4 状态/重试重复转述,-28)
- Modify: `skills/dev-workflow/references/auto-mode.md:166-268`(压缩交付报告大模板,-70)

**背景**:auto-mode.md:91-121 的 Phase 4 状态机是 verification-flow.md:386-520 的转述,删除后改为 2-3 行指针;166-268 的交付报告假设"每任务 Commit 2",与 P2 末尾合并冲突,压缩为字段清单。spec §6.1.1 + §6.1.5。

- [ ] **Step 1: Read 当前两个区段验证锚点**

Run: `sed -n '89,123p;164,270p' skills/dev-workflow/references/auto-mode.md`

Expected:91-121 包含 Phase 4 状态字段说明;166-268 包含成功/失败交付报告大模板。

- [ ] **Step 2: 用 Edit 替换 91-121 区间为指针(从大到小做,先做 166-268 以免行号漂移)**

先把 166-268 交付报告整段(约 100 行)替换为以下精简版(~30 行):

```markdown
## 交付报告(批量末尾)

批量结束时输出单一交付报告,字段如下(成功/失败共用 schema):

| 字段 | 含义 |
|------|------|
| `batch_id` | 本次批量的 Batch-Id 标识(Phase 2 引入后强制;Phase 1 期间为空)|
| `tasks_done` | 已完成任务列表(含 Commit 1 sha)|
| `tasks_pending` | 未完成任务 + 失败原因(中断/Blocker/超时)|
| `phase_4_summary` | Phase 4 外审 verdict 汇总(EXT_REVIEWED / EXT_PENDING / EXT_UNRESOLVED / EXT_BLOCKED)|
| `resume_command` | 续做命令(完整 CLI,可复制执行)|

极简示例:

```yaml
delivery_report:
  batch_id: ""              # Phase 2 引入后填充 B-<timestamp>-<seq>
  tasks_done: [T-01, T-02]
  tasks_pending:
    - id: T-03
      reason: "Phase 4 EXT_UNRESOLVED after 3 rounds"
  resume_command: "/ms-dev-workflow T-03~T-05 --headless"
```

> 完整字段语义见 [SKILL.md 子 Agent 摘要格式章节](../SKILL.md#子-agent-摘要格式) + yaml-summary-v1 ([shared constraints §2](../../_shared/constraints.md))。
```

然后再处理 91-121 Phase 4 状态/重试转述,替换为以下 3 行指针:

```markdown
### Phase 4 在 headless 下的状态机

> Phase 4 状态字段(`ext_review_state` / `EXT_REVIEWED` / `EXT_PENDING` / `EXT_UNRESOLVED` / `EXT_BLOCKED`)、轮次控制(`max_rounds`)、降级链(T1 → T2)、真值表全部由 [verification-flow.md Phase 4 章节](verification-flow.md#phase-4-外部对抗审查) 权威定义。本文件不再重复转述。Headless 下仅追加:任一 `EXT_PENDING` / `EXT_UNRESOLVED` / `EXT_BLOCKED` → fail-fast,输出 `resume_command`。
```

- [ ] **Step 3: 行数验证**

Run: `wc -l skills/dev-workflow/references/auto-mode.md`

Expected:从 283 行降到 ~185 行(±5)。

- [ ] **Step 4: 验证唯一权威**

Run: `grep -cE "ext_review_state|EXT_REVIEWED|max_rounds" skills/dev-workflow/references/auto-mode.md`

Expected:≤ 5 处(仅文字提及/指针,不再有详细状态机定义)。

- [ ] **Step 5: Commit**

```bash
git add skills/dev-workflow/references/auto-mode.md
git commit -m "$(cat <<'EOF'
refactor(dev-workflow): compress auto-mode.md delivery report + dedupe Phase 4 (-98)

- 91-121: Phase 4 状态/重试转述改为单一指针 (verification-flow.md 唯一权威, -28)
- 166-268: 交付报告大模板压缩为字段清单 + 极简示例 (-70)
- 为 Phase 2 引入 Batch-Id 预留字段位置

Phase 1 of dev-workflow speed optimization (累计删减 2/5)
See: spec §6.1.1, §6.1.5

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3:精简 verification-flow.md(-62)

**Files:**
- Modify: `skills/dev-workflow/references/verification-flow.md:154-163`(Phase 2-UI 指针化,-10)
- Modify: `skills/dev-workflow/references/verification-flow.md:249-317`(删 "已前移到 S8" 机制原文,-40)
- Modify: `skills/dev-workflow/references/verification-flow.md` Phase 4 真值表区段(加 P0-A EXT_PENDING ⛔ 澄清,+10 行)

**净变化**:-40 -10 +10 = **-40 行**(spec §6.1.3 + §6.1.4 + §3.1)

**背景**:154-163 Phase 2-UI 转述与 ui-quality-checklist.md 重复;249-317 "已前移到 S8" 是历史残留;Phase 4 真值表需明确 P0-A "EXT_PENDING 在所有放行路径都为 ⛔"(P0-A 修订)。**Phase 4 状态机结构本身不动**(386-520 权威区)。

- [ ] **Step 1: Read 三个修订区段**

Run: `sed -n '152,165p;247,320p' skills/dev-workflow/references/verification-flow.md`

Expected:154-163 包含 Phase 2-UI 描述;249-317 包含"已前移到 S8 / 已收口到 S8 / Phase 1~3 不再单独做 AC 完备性表" 类描述。

- [ ] **Step 2: 从大到小做修订,先处理 249-317(-40 行)**

锚点定位用相关章节标题(预期内容含 "声称 vs 实际验证" 或 "AC 完备性已前移"),保留 "AC 完备性见 [S8](../SKILL.md#s8-完成检查约束)" 的 3-5 行指针。

替换原 68 行为:

```markdown
### Phase 1~3 与 S8 AC 完备性表的关系

S8 AC 完备性表 / 类型×证据矩阵 / 声称-vs-diff 交叉验证已是所有层级强制,见 [SKILL.md §完成检查约束](../SKILL.md#完成检查约束)。Phase 1~3 不重复执行 AC 表,只在 Phase 3 综合报告中复用 S8 产出的判定结果。

详细 AC 类型分类、证据矩阵、可复核判据见 [SKILL.md 同章节末尾说明 + AC 完备性表模板](../SKILL.md#完成检查约束)。
```

- [ ] **Step 3: 处理 154-163(-10 行)Phase 2-UI 指针化**

替换原 10 行为:

```markdown
### Phase 2-UI(仅 🟢 UI 层任务)

🟢 UI 层在 Phase 2 之后追加的 UI 质量自查(静态代理指标 + 与 `/ms-verify --ui` 边界)由 [ui-quality-checklist.md](ui-quality-checklist.md) 唯一权威定义。本文件不重复转述。
```

- [ ] **Step 4: P0-A 真值表澄清(+10 行)**

定位 Phase 4 真值表区段(预期在第 400-460 行附近,grep 关键词 "EXT_PENDING" + "真值表"),在真值表末尾添加:

```markdown
> **P0-A 澄清**:`EXT_PENDING` 在所有放行路径下都为 ⛔ 阻塞 Commit 1,无例外。`--skip-external-review-reason="<原因>"` 仅登记跳过原因 + 自动标 `EXT_PENDING` + 留 `Skip-External-Review-Reason:` 尾注,**不构成 Commit 1 放行**。补跑 Phase 4 达成 `EXT_REVIEWED` 后方可进入 Commit 1。
```

- [ ] **Step 5: 行数验证**

Run: `wc -l skills/dev-workflow/references/verification-flow.md`

Expected:从 520 行降到 ~480 行(净 -40,±5)。

- [ ] **Step 6: 验证 Phase 4 状态机结构未被误改**

Run: `grep -cE "ext_review_state|EXT_REVIEWED|EXT_PENDING|EXT_UNRESOLVED|EXT_BLOCKED" skills/dev-workflow/references/verification-flow.md`

Expected:≥ 15 处(权威定义区仍完整)。

- [ ] **Step 7: Commit**

```bash
git add skills/dev-workflow/references/verification-flow.md
git commit -m "$(cat <<'EOF'
refactor(dev-workflow): trim verification-flow.md + P0-A truth table clarify (-40 net)

- 154-163: Phase 2-UI 指针化 (ui-quality-checklist.md 唯一权威, -10)
- 249-317: 删 "已前移到 S8" 机制原文, 改为 S8 指针 (-40)
- Phase 4 真值表追加 P0-A 澄清: EXT_PENDING 在所有放行路径下都为 ⛔ (+10)
- Phase 4 状态机结构(386-520权威区)保持不动

Phase 1 of dev-workflow speed optimization (累计删减 3/5 + P0-A 真值表澄清)
See: spec §6.1.3, §6.1.4, §3.1

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4:精简 execution-flow.md(-28)

**Files:**
- Modify: `skills/dev-workflow/references/execution-flow.md:106-131`(Phase 2-UI 指针化,-16)
- Modify: `skills/dev-workflow/references/execution-flow.md:253-259`(Phase 4 引用化,-12)

**背景**:spec §6.1.4 + §6.1.5。Phase 2-UI 和 Phase 4 都已有唯一权威文件,本文件改为指针。

- [ ] **Step 1: Read 两个修订区段**

Run: `sed -n '104,133p;251,261p' skills/dev-workflow/references/execution-flow.md`

Expected:106-131 包含 "🟢 UI 层旁路补充" / Phase 2-UI 描述;253-259 包含 Phase 4 状态/重试/外审引用。

- [ ] **Step 2: 替换 106-131(-16 行,从大到小)**

锚点 "### 🟢 UI 层旁路补充" 到下一个 `### ` 标题之间的内容,替换为:

```markdown
### 🟢 UI 层旁路补充

🟢 UI 层在统一 11 步流程之上追加 Phase 2-UI(UI 质量自查),完整审查清单 + 与 `/ms-verify --ui` 边界 + UI 验收清单生成规则见 [ui-quality-checklist.md](ui-quality-checklist.md)。本文件不重复转述。
```

- [ ] **Step 3: 替换 253-259(-12 行)**

锚点为提及 Phase 4 状态字段的段落,替换为:

```markdown
### Phase 4 外部对抗审查在 S9 中的位置

S9 阶段触发 Phase 4 时,状态字段(`ext_review_state`)、轮次控制(`max_rounds`/`--external-rounds`)、降级链(T1 codex CLI → T2 codex-mcp)、真值表与 L2 证据协议均由 [verification-flow.md Phase 4 章节](verification-flow.md#phase-4-外部对抗审查) 权威定义。本文件不重复。
```

- [ ] **Step 4: 行数验证**

Run: `wc -l skills/dev-workflow/references/execution-flow.md`

Expected:从 315 行降到 ~287 行(±5)。

- [ ] **Step 5: Commit**

```bash
git add skills/dev-workflow/references/execution-flow.md
git commit -m "$(cat <<'EOF'
refactor(dev-workflow): dedupe execution-flow.md Phase 2-UI + Phase 4 references (-28)

- 106-131: Phase 2-UI 转述改为单一指针 (ui-quality-checklist.md 唯一权威, -16)
- 253-259: Phase 4 状态/重试转述改为单一指针 (verification-flow.md 唯一权威, -12)

Phase 1 of dev-workflow speed optimization (累计删减 4/5)
See: spec §6.1.4, §6.1.5

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5:精简 task-orchestration.md(-12)

**Files:**
- Modify: `skills/dev-workflow/references/task-orchestration.md:137-148`(Phase 4 引用化,-12)

**背景**:spec §6.1.5。task-orchestration.md 不应保留 Phase 4 状态机的副本。

- [ ] **Step 1: Read 修订区段**

Run: `sed -n '135,150p' skills/dev-workflow/references/task-orchestration.md`

Expected:137-148 包含 Phase 4 状态/重试在批量编排中的转述。

- [ ] **Step 2: 替换 137-148**

替换为:

```markdown
### Phase 4 状态在批量编排中的处理

批量编排器在每任务完成 S9 后读取 `ext_review_state`,任一非 `EXT_REVIEWED` 状态导致该任务进入 `Step 1.5 [D2]` 拦截(详见本文件 Step 1.5 章节)。Phase 4 状态字段定义、真值表见 [verification-flow.md Phase 4 章节](verification-flow.md#phase-4-外部对抗审查)。
```

- [ ] **Step 3: 行数验证**

Run: `wc -l skills/dev-workflow/references/task-orchestration.md`

Expected:从 470 行降到 ~458 行(±3)。

- [ ] **Step 4: Commit**

```bash
git add skills/dev-workflow/references/task-orchestration.md
git commit -m "$(cat <<'EOF'
refactor(dev-workflow): dedupe task-orchestration.md Phase 4 references (-12)

- 137-148: Phase 4 状态/重试转述改为单一指针 (verification-flow.md 唯一权威)
- 保留批量编排器读取 ext_review_state 的本地行为描述

Phase 1 of dev-workflow speed optimization (累计删减 5/5 完成)
See: spec §6.1.5

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6:SKILL.md P0-A 修订 + `--single-commit` + 关键约束 + spec_version 1.1(+~10 行)

**Files:**
- Modify: `skills/dev-workflow/SKILL.md:62-69`(语法表加 `--single-commit`)
- Modify: `skills/dev-workflow/SKILL.md:67`(`--skip-external-review-reason` 行加 "不放行"提示)
- Modify: `skills/dev-workflow/SKILL.md:215`(EXT_PENDING/EXT_BLOCKED ⛔ 行加交叉引用)
- Modify: `skills/dev-workflow/SKILL.md:249`(Skip 参数收紧表同步追加"不放行")
- Modify: `skills/dev-workflow/SKILL.md:362`(提交模板 `Skip-External-Review-Reason` 尾注注释)
- Modify: `skills/dev-workflow/SKILL.md` frontmatter(`spec_version: 1.1` + 标记 [FUTURE])
- Modify: `skills/dev-workflow/SKILL.md` 顶部(关键约束:权威文件唯一)

**背景**:spec §3 P0-A 全部修订 + §6.2 关键约束 + §7.1 spec_version。

- [ ] **Step 1: 加 `--single-commit` 行(SKILL.md:62-69 语法表)**

定位 `--auto-commit` 行(第 62 行),在其后插入:

```markdown
| 单次提交 | `--single-commit` | 代码+文档合并为单次提交;适合无文档变更或后续 `/ms-sync` 已合并 |
```

- [ ] **Step 2: SKILL.md:67 加"不放行"提示**

定位包含 `--skip-external-review-reason` 的语法表行,在描述末尾追加:

```markdown
⚠️ 不构成 Commit 1 放行,需后续补跑 Phase 4 达成 `EXT_REVIEWED` 才能完成任务(详见[对抗式验证 §Skip 参数](#对抗式验证可选))。
```

- [ ] **Step 3: SKILL.md:215 加交叉引用**

定位 EXT_PENDING/EXT_BLOCKED ⛔ 阻塞行,末尾追加:

```markdown
（语义详见 [对抗式验证 §Skip 参数收紧](#对抗式验证可选)）
```

- [ ] **Step 4: SKILL.md:249 Skip 参数表同步追加**

定位 `--skip-external-review-reason` 行(在"Skip 参数收紧"表内),约束列末尾追加:

```markdown
;⚠️ 仅登记 pending,不构成放行
```

- [ ] **Step 5: SKILL.md:362 提交模板注释明确**

定位:
```markdown
Skip-External-Review-Reason: <仅 🔴 任务使用 --skip-external-review-reason 时填写>
```

替换为:
```markdown
Skip-External-Review-Reason: <仅 🔴 任务使用 --skip-external-review-reason 时填写;留作补跑追溯,Commit 1 仍要求 ext_review_state=EXT_REVIEWED>
```

- [ ] **Step 6: SKILL.md frontmatter 加 spec_version(标 [FUTURE])**

定位 frontmatter 区域(第 5-17 行 metadata 块),在 `migration:` 行后追加(若不存在则在 metadata 块末尾追加):

```yaml
spec_version: 1.1
spec_version_notes: |
  1.1 = P0-A 文档收敛 + 累计审计删减 (Phase 1)
        P1 S9 并行化、P2 批量 Batch-Id trailer 标记 [FUTURE],待 Phase 2 实施
```

- [ ] **Step 7: 在 SKILL.md 顶部"开发工作流"章节后(约 19-23 行)添加关键约束**

定位 "# 开发工作流" 标题后第一个 markdown 引用块的位置(SKILL.md:21-27 共享约束 SSOT 引用),在该块末尾追加新段落:

```markdown
> **权威文件唯一原则**(spec_version 1.1 起强制):
> - Phase 4 / 并行调度 / `diff_hash` / 重跑机制 → [verification-flow.md](references/verification-flow.md) 唯一权威
> - Step 1.5 各分支 / `sync_pending` / Batch-Id 识别 → [task-orchestration.md](references/task-orchestration.md) 唯一权威
> - Phase 2-UI 审查清单 → [ui-quality-checklist.md](references/ui-quality-checklist.md) 唯一权威
> - 其他文件(SKILL.md / auto-mode.md / execution-flow.md) **仅允许 2-3 行指针引用**,严禁重复转述。违反此原则视为复杂度退化,必须 revert。
```

- [ ] **Step 8: 验证 SKILL.md 行数**

Run: `wc -l skills/dev-workflow/SKILL.md`

Expected:从 393 行升到 ~403 行(±3)。

- [ ] **Step 9: P0-A 5 处文字一致性验证**

Run: `grep -n "不构成 Commit 1 放行\|不构成放行\|留作补跑追溯" skills/dev-workflow/SKILL.md`

Expected:**至少 4 处匹配**(Step 2/3/4/5 各 1 处)。如缺失,补回再 commit。

- [ ] **Step 10: spec_version 字段验证**

Run: `grep -A2 "spec_version" skills/dev-workflow/SKILL.md`

Expected:`spec_version: 1.1` + notes 出现在 frontmatter。

- [ ] **Step 11: 关键约束验证**

Run: `grep -c "权威文件唯一原则" skills/dev-workflow/SKILL.md`

Expected:1 处。

- [ ] **Step 12: SKILL.md ≤ 500 行硬约束验证**

Run: `awk 'NR<=500{c++} END{print c}' skills/dev-workflow/SKILL.md && wc -l skills/dev-workflow/SKILL.md`

Expected:实际行数 ≤ 500。当前预计 ~403 < 500,通过。

- [ ] **Step 13: Commit**

```bash
git add skills/dev-workflow/SKILL.md
git commit -m "$(cat <<'EOF'
docs(dev-workflow): P0-A semantic + --single-commit visible + spec_version 1.1 bump

P0-A 文档收敛:
- 62-69 语法表新增 --single-commit (原本仅在第 276 行 "约束" 单提)
- 67/215/249/362 四处统一 --skip-external-review-reason 语义:
  不构成 Commit 1 放行, 仅登记 pending, 留作补跑追溯
- 真值表加 EXT_PENDING ⛔ 澄清 (verification-flow.md 已在前一 commit 落地)

新增关键约束(spec_version 1.1 起):
- 顶部"权威文件唯一原则":Phase 4/Step 1.5/Phase 2-UI 各自单一权威
- SKILL.md/auto-mode.md/execution-flow.md 仅允许指针引用, 严禁转述
- 违反视为复杂度退化, 必须 revert

spec_version: 1.0 → 1.1 (P1 并行化、P2 Batch-Id 标记 [FUTURE])

Phase 1 of dev-workflow speed optimization (P0-A 完成)
See: spec §3, §6.2, §7.1

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7:Phase 1 全局静态验证(不 commit)

**Files:**
- Read-only: 所有 dev-workflow 文件

**目的**:在所有 6 个 commit 落地后,做最终静态验证,确认 Phase 1 完整达成。

- [ ] **Step 1: 总行数验证**

Run: `wc -l skills/dev-workflow/SKILL.md skills/dev-workflow/CLAUDE.md skills/dev-workflow/references/*.md`

Expected:total 在 2200-2240 之间(Phase 1 目标净 -220 行,允许 ±10 误差)。

- [ ] **Step 2: 唯一权威验证(Phase 4)**

Run:
```bash
grep -lE "ext_review_state.*=|^.*EXT_REVIEWED.*=|max_rounds.*:" skills/dev-workflow/references/*.md | sort -u
```

Expected:仅 `verification-flow.md` 一个文件命中详细定义(其他文件最多有指针文本,不出现定义符 "=" 或 ":")。

- [ ] **Step 3: 唯一权威验证(Phase 2-UI)**

Run: `grep -lE "静态代理指标|Phase 2-UI 审查清单" skills/dev-workflow/references/*.md`

Expected:仅 `ui-quality-checklist.md` 命中(其他改为指针)。

- [ ] **Step 4: P0-A 一致性验证(跨文件)**

Run: `grep -nE "Skip-External-Review-Reason|EXT_PENDING.*放行|不构成 Commit 1" skills/dev-workflow/SKILL.md skills/dev-workflow/references/verification-flow.md`

Expected:SKILL.md ≥ 4 处, verification-flow.md ≥ 1 处, 全部表述一致(都明确"不放行")。

- [ ] **Step 5: spec_version 验证**

Run: `grep -A2 "spec_version" skills/dev-workflow/SKILL.md`

Expected:`spec_version: 1.1`。

- [ ] **Step 6: 关键约束位置验证**

Run: `grep -n "权威文件唯一原则" skills/dev-workflow/SKILL.md`

Expected:行号 < 30(在文件顶部章节内)。

- [ ] **Step 7: Phase 4 状态机权威区完整性**

Run: `wc -l skills/dev-workflow/references/verification-flow.md && sed -n '380,395p' skills/dev-workflow/references/verification-flow.md`

Expected:总行数 ~480,Phase 4 章节标题在第 380 行附近且后续状态机完整。

- [ ] **Step 8: 工作树状态**

Run: `git status --short skills/dev-workflow/`

Expected:空(全部 commit 已落盘)。

- [ ] **Step 9: commit 计数**

Run: `git log --oneline -10 skills/dev-workflow/ | head -10`

Expected:最近 6 个 commit 全部以 `refactor(dev-workflow):` 或 `docs(dev-workflow):` 开头,且属于 Phase 1。

- [ ] **Step 10: 触发 ms-pipeline realign --scope=spec 自检(可选,只读)**

Run: `echo "Phase 1 落地后,用户应手动跑: /ms-pipeline realign --scope=spec 验证 1.0 → 1.1 spec 迁移提示是否生效"`

> 这一步是给用户的提示,不强制 plan 内执行。

---

## Self-Review

### 1. Spec coverage(逐 spec 章节核对)

| Spec 章节 | 实施 Task |
|-----------|-----------|
| §3.1 `--skip-external-review-reason` 语义收敛 | Task 6 Step 2-5,Task 3 Step 4 |
| §3.2 `--single-commit` 进语法表 | Task 6 Step 1 |
| §6.1.1 auto-mode.md 交付报告压缩 | Task 2 |
| §6.1.2 skeleton-examples.md 长示例删除 | Task 1 |
| §6.1.3 verification-flow.md "已前移到 S8" 删除 | Task 3 |
| §6.1.4 Phase 2-UI 多处重复转述 | Task 3 + Task 4 |
| §6.1.5 Phase 4 状态多文件重复 | Task 2 + Task 4 + Task 5 |
| §6.2 关键约束(权威文件唯一) | Task 6 Step 7 |
| §7.1 spec_version 1.1 bump | Task 6 Step 6 |
| §10.1 Phase 1 验收(净变化 -220, SKILL ≤500) | Task 7 全部 |

**所有 Phase 1 相关 spec 章节均有对应 Task 覆盖**。

### 2. Placeholder scan

- 无 TBD/TODO
- 所有删除/编辑都给出了**具体替换文字**(不是"按 spec 改")
- 所有 grep / wc 命令都给出了**期望输出**

### 3. Type consistency

- 文档类 plan,无类型 / 函数签名
- 跨 task 的命名一致性:`权威文件唯一原则` / `EXT_REVIEWED` / `Batch-Id` 等术语在所有 task 中拼写一致

### 4. 行号漂移风险

由于多个 task 修改同一文件不同区段,行号会漂。Plan 内已采用 **"从大行号到小行号"** 顺序(Task 2 / Task 3),Task 6 SKILL.md 内部多处编辑也是从下往上做,降低行号漂移风险。

---

## 边界与回滚

- Phase 1 任一 commit 失败 → 立即 `git reset --hard HEAD~N` 回滚到 Phase 1 开始前(9dd04fa 后的 main HEAD)
- 不允许 `--amend`(spec 已写明)— 失败必须新 commit 修复
- Phase 1 落地后,**至少观察 1 个实际代码项目任务无回归**,才进 Phase 2 plan 撰写

---

## 完成判据(Phase 1)

执行此 plan 后,以下条件全部满足:

- [ ] 6 个 commit 全部落入 main(可被 `git log --oneline skills/dev-workflow/` 验证)
- [ ] dev-workflow 总行数 2200-2240(Task 7 Step 1 验证)
- [ ] SKILL.md ≤ 500 行(Task 6 Step 12)
- [ ] Phase 4 唯一权威在 verification-flow.md(Task 7 Step 2)
- [ ] Phase 2-UI 唯一权威在 ui-quality-checklist.md(Task 7 Step 3)
- [ ] P0-A 表述在 SKILL.md + verification-flow.md 完全一致(Task 7 Step 4)
- [ ] spec_version 1.1 已写入 frontmatter(Task 7 Step 5)
- [ ] 关键约束在 SKILL.md 顶部(Task 7 Step 6)
- [ ] 工作树洁净(Task 7 Step 8)
