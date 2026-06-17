# dev-workflow 重构 Plan A(核心执行模型)Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 ms-dev-workflow 从"spec 即门禁 + 层级固定流程强度"重构为"review_profile 三档 + 风险触发 + 质量地板恒定 + 独立审查可延后到批/sprint 边界",在不掉质量前提下大幅提速。

**Architecture:** 引入三档 `review_profile`(fast/guarded/audit)替代 🔴🟡🟢⚪ 层级开关(层级降为风险输入);5 条质量地板恒定 inline;独立对抗审查(Phase 1~3 + Phase 4)在 fast/guarded 延后,任务落 `review_pending`(全新任务状态,**不复用 `EXT_PENDING`**),批/sprint 边界经 `/ms-verify --review-drain` 集中清审;audit inline fail-fast。

**Tech Stack:** Markdown + YAML skill 定义。无 build/test/lint;验证靠 `rg`/`grep` 断言 + 行数 + 交叉引用一致性 + health-lint。

**权威来源:** [spec](../specs/2026-06-08-devdocs-repositioning-and-dev-workflow-redesign-design.md)(§1~§4 + §10 已 Codex T-131~135 通审)。**Plan B(记忆卡片层 §5/§8.6-7)不在本计划范围。**

**改动文件总览:**
- Create: 无(全部为现有文件修改)
- Modify: `skills/_shared/constraints.md`、`skills/dev-workflow/SKILL.md`、`skills/dev-workflow/references/{verification-flow,task-orchestration,execution-flow,auto-mode}.md`、`skills/dev-tasks/SKILL.md`、`skills/verify/SKILL.md`

**全局约束:** SKILL.md ≤ 500 行(硬约束),每个 commit 后核对。FUTURE 三态:本轮真正实装 runtime,不留 [FUTURE]。

---

## Phase 1 — 共享词汇 SSOT

### Task 1: 在 _shared/constraints.md 定义 review_profile / 质量地板 / review_pending

**Files:**
- Modify: `skills/_shared/constraints.md`(追加一节,放在现有 FUTURE 三态/realign 节之后)

- [ ] **Step 1: 追加 SSOT 章节**

在文件末尾追加以下内容(若已有 "## review_profile" 节则替换):

```markdown
## review_profile 与 review_pending(dev-workflow 核心,跨 skill SSOT)

### review_profile 三档
| 档 | 双 Agent 红绿 | 质量地板 | 前置验证 `/ms-verify --impl` | 独立审查(Phase 1~3 + Phase 4) |
|----|:---:|:---:|:---:|------|
| fast(默认) | ✓ | ✓ | — | 延后到批/sprint drain |
| guarded | ✓ | ✓ | inline 阻塞 | Phase 4 延后;Phase 1~3 风险触发则 inline |
| audit | ✓ | ✓ | inline 阻塞 | inline fail-fast(不延后) |

> review_profile 只改**独立审查的时机**,绝不降低质量地板。层级标签 🔴🟡🟢⚪ 降级为风险分类器的输入信号之一,不再是流程开关。

### 质量地板(5 条,所有档恒定 inline,不可协商)
1. 绿验 `skipped/todo=0`
2. 测试写成红验通过即冻结(实现不得改测试,疑似缺陷须 AskUserQuestion)
3. 声称 vs 实际 diff 一致
4. 行为型 AC 至少 1 条独立行为证据(不能只靠实现代码自证;无则显式豁免)
5. 受影响测试后置 `/ms-test-run --affected`

### review_pending(全新任务状态,严禁复用 EXT_PENDING)
- 含义:fast/guarded 任务代码已提交(Commit 1 已落盘),但延后的独立审查尚未做,**状态 ≠ 已完成**。
- 与续做信号 `INT_PENDING`/`EXT_PENDING`/`postcheck_pending` 独立:后三者是"未放行阻塞态",`review_pending` 是"已提交待集中审"。
- Commit 1 尾注:`Review-Batch-Id: <id>` / `Review-Due: <sprint:ID | due:YYYY-MM-DD>` / `Pending-Reason: deferred-fast | deferred-guarded`。
- 清算入口:`/ms-verify --review-drain`(批/sprint 边界集中跑延后审查)。
```

- [ ] **Step 2: 验证**

Run: `rg -n "review_profile|review_pending|质量地板" skills/_shared/constraints.md`
Expected: 命中新增章节的标题与三处关键词。

- [ ] **Step 3: Commit**

```bash
git add skills/_shared/constraints.md
git commit -m "feat(shared-constraints): 新增 review_profile/质量地板/review_pending SSOT — Plan A Phase 1"
```

---

## Phase 2 — dev-workflow SKILL.md 核心模型替换

### Task 2: SKILL.md 引入 review_profile,层级降为风险输入

**Files:**
- Modify: `skills/dev-workflow/SKILL.md`(章节 "## 分层 TDD 模式" 的层级表 + "## 模式选择" 附近)

- [ ] **Step 1: 替换"分层 TDD 模式"层级表**

定位 `## 分层 TDD 模式` 下的"层级/标记/强制步骤/推荐步骤/可选步骤"表(SKILL.md:135 附近),整表替换为:

```markdown
所有任务遵循统一 11 步执行流程 + 5 条质量地板(恒定 inline);`review_profile` 只决定**独立审查(Phase 1~3 + Phase 4)的时机**:

| review_profile | 触发 | 双 Agent | 质量地板 | 前置验证 | Phase 1~3 | Phase 4 | 提交状态 |
|------|------|:---:|:---:|:---:|------|------|------|
| **fast**(默认) | 低风险(见风险分类器) | ✓ | ✓ | — | 延后 drain | 延后 drain | `review_pending` |
| **guarded** | 中风险 | ✓ | ✓ | `/ms-verify --impl` inline | 风险触发 inline 否则延后 | 延后 drain | `review_pending` |
| **audit** | 高风险 | ✓ | ✓ | `/ms-verify --impl` inline | **inline fail-fast** | **inline fail-fast** | 审过才提交 |

> 详细判据见 [verification-flow.md](references/verification-flow.md);风险分类器见 [task-orchestration.md](references/task-orchestration.md);共享定义见 [../_shared/constraints.md](../_shared/constraints.md)。
> 旧 🔴🟡🟢⚪ 层级标签**降级为风险分类器的输入信号之一**,不再独立决定流程强度。
```

- [ ] **Step 2: 替换原层级补充段(🟢 UI 层补充等)**

原"🟢 UI 层补充""核心逻辑/接口层"等基于层级的强制程度描述 → 改为指针:`> 各 review_profile 的 S1~S11 强制程度差异详见 [execution-flow.md](references/execution-flow.md)。UI 任务的 Phase 2-UI 自查仍按 [ui-quality-checklist.md](references/ui-quality-checklist.md)。`

- [ ] **Step 3: 验证 + 行数**

Run: `rg -n "review_profile|降级为风险" skills/dev-workflow/SKILL.md && wc -l skills/dev-workflow/SKILL.md`
Expected: 命中 review_profile 表;行数 ≤ 500。

- [ ] **Step 4: Commit**

```bash
git add skills/dev-workflow/SKILL.md
git commit -m "feat(dev-workflow): SKILL.md 层级强度模型 → review_profile 三档 — Plan A Phase 2"
```

### Task 3: SKILL.md 新增"质量地板"章节 + 三类机制区分

**Files:**
- Modify: `skills/dev-workflow/SKILL.md`(在"## 对抗式验证(可选)"之前插入)

- [ ] **Step 1: 插入质量地板章节**

```markdown
## 质量地板(所有 review_profile 恒定 inline,不可降)

无论档位高低,5 条不变量永远 inline 生效(定义见 [../_shared/constraints.md](../_shared/constraints.md)):绿验 `skipped/todo=0` / 测试冻结 / 声称vs实际 diff 一致 / 行为型 AC 至少 1 条独立证据 / 受影响测试后置。

> **三类机制区分(关键,勿混)**:
> 1. **质量地板**(上述 5 条)——所有档 inline。
> 2. **前置验证 `/ms-verify --impl`**(AC↔实现语义一致)——属"前置验证门",Blocker inline 阻塞提交;guarded/audit 跑,fast 不跑。
> 3. **独立对抗审查**(Phase 1~3 + Phase 4)——**唯一可延后**的部分,fast/guarded 延后到 drain,audit inline。
>
> "review_profile 只改独立审查时机"成立:地板与前置验证永远 inline,不在延后范围。
```

- [ ] **Step 2: 验证**

Run: `rg -n "质量地板|三类机制" skills/dev-workflow/SKILL.md`
Expected: 命中新章节。

- [ ] **Step 3: Commit**

```bash
git add skills/dev-workflow/SKILL.md
git commit -m "feat(dev-workflow): SKILL.md 新增质量地板 + 三类机制区分 — Plan A Phase 2"
```

### Task 4: SKILL.md 运行模式语法表加 review_profile 相关 flag

**Files:**
- Modify: `skills/dev-workflow/SKILL.md`(运行模式"### 语法"表)

- [ ] **Step 1: 在语法表追加行**

```markdown
| 强制档位 | `--review-profile=<fast\|guarded\|audit>` | 覆盖风险分类器自动判档;仅允许**升档**或带理由降档(降档写 `Profile-Downgrade-Reason:` 尾注) |
| 关闭延后 | `--no-defer-review` | 强制本次独立审查 inline(等价临时 audit 审查时机),用于不想留 `review_pending` 的场景 |
```

- [ ] **Step 2: 验证 + 行数**

Run: `rg -n "review-profile|no-defer-review" skills/dev-workflow/SKILL.md && wc -l skills/dev-workflow/SKILL.md`
Expected: 命中两行;行数 ≤ 500。

- [ ] **Step 3: Commit**

```bash
git add skills/dev-workflow/SKILL.md
git commit -m "feat(dev-workflow): SKILL.md 语法表加 --review-profile/--no-defer-review — Plan A Phase 2"
```

---

## Phase 3 — verification-flow.md:review_pending + drain

### Task 5: verification-flow.md 新增 review_pending 状态 + drain 失败矩阵

**Files:**
- Modify: `skills/dev-workflow/references/verification-flow.md`(新增一节,放在 EXT 状态机章节之后)

- [ ] **Step 1: 追加 drain 与 review_pending 章节**

```markdown
## 延后审查与 review_pending(fast/guarded)

### review_pending 状态
- fast/guarded 任务 Commit 1 落盘后,独立审查(Phase 1~3 + Phase 4)未做 → 任务标 `review_pending`(**全新状态,严禁复用 `EXT_PENDING`**——后者是 Phase 4 主动跳过的阻塞态,所有放行路径阻塞)。
- Commit 1 尾注:`Review-Batch-Id` / `Review-Due`(格式 `sprint:<id>` 或 `due:YYYY-MM-DD`,默认落盘日+3 工作会话)/ `Pending-Reason: deferred-fast|deferred-guarded`。
- 转移:`review_pending` --(drain 无 Blocker)--> `已完成`;有 Blocker → fix-forward(见下)。

### `/ms-verify --review-drain` 集中清审
收集所有 `review_pending` 任务,按延后档位补跑 Phase 1~3 + Phase 4(复用 embedded-headless T1→T2 通道),逐任务出 verdict。

**drain 失败矩阵:**

| 场景 | 任务状态 | 退出 | 报告字段 |
|------|---------|:---:|---------|
| 单任务 Blocker | 保持 `review_pending` + fix-forward 入队 | 非0 | `drain.blockers[]` |
| 部分通过 | 过的转 `已完成`,未过保持 `review_pending` | 非0 | `drain.passed`/`drain.pending` |
| T1/T2 全失败 | 保持 `review_pending`(EXT_UNRESOLVED) | 非0 | `drain.channel_failure` |
| L2 yaml 无效 | 保持 `review_pending` | 非0 | `drain.invalid_evidence` |
| 用户中断 | 已处理落定,余下保持 `review_pending` | 130 | `drain.interrupted_at` |
| headless fail-fast | 保持 `review_pending` | 非0 | `drain.headless_halt` |

> 共性:**任何非全通过 → 阻断 sprint close**。

### post-commit Blocker 恢复
- 默认 **fix-forward**:开修复任务追加新 commit,不 revert(原子提交已落盘)。
- revert 仅限"已落盘代码主动有害且 fix-forward 无法快速处理",罕见,须 AskUserQuestion 确认。
- 全部 fix-forward + 重新 drain 通过前,阻断 sprint close。
```

- [ ] **Step 2: 验证**

Run: `rg -n "review-drain|drain 失败矩阵|fix-forward" skills/dev-workflow/references/verification-flow.md`
Expected: 命中新章节三处关键词。

- [ ] **Step 3: Commit**

```bash
git add skills/dev-workflow/references/verification-flow.md
git commit -m "feat(dev-workflow): verification-flow 新增 review_pending + drain 失败矩阵 — Plan A Phase 3"
```

### Task 6: verification-flow.md 标注三类机制 + Phase 延后语义

**Files:**
- Modify: `skills/dev-workflow/references/verification-flow.md`(Phase 1~4 章节开头)

- [ ] **Step 1: 在 Phase 章节开头插入延后说明**

```markdown
> **延后语义**:Phase 1~3(内置角色演绎)+ Phase 4(外部对抗)是**独立审查**,在 `review_profile=fast/guarded` 时延后到 `/ms-verify --review-drain` 集中执行,任务期间任务标 `review_pending`。`audit` 档 inline fail-fast(同今天 🔴)。质量地板与 `/ms-verify --impl` 前置验证**不延后,始终 inline**。
```

- [ ] **Step 2: 验证**

Run: `rg -n "延后语义|独立审查" skills/dev-workflow/references/verification-flow.md`
Expected: 命中。

- [ ] **Step 3: Commit**

```bash
git add skills/dev-workflow/references/verification-flow.md
git commit -m "docs(dev-workflow): verification-flow 标注 Phase 延后语义 — Plan A Phase 3"
```

---

## Phase 4 — task-orchestration.md:状态机 + 传播闸 + 主循环

### Task 7: task-orchestration.md Step 1.5 新增 [F] review_pending 分支

**Files:**
- Modify: `skills/dev-workflow/references/task-orchestration.md`(Step 1.5 块,约 :87-96)

- [ ] **Step 1: 在 Step 1.5 [E] 之后插入 [F] 分支**

```markdown
        ├── [F] review_pending 检测:Commit 1 带 `Pending-Reason: deferred-*` 且无对应 drain verdict → 任务为 `review_pending`,**非"已完成"**,不得跳过;须经 `/ms-verify --review-drain` 转 `已完成`
```

并把 `A~E 全部可复核` 判据行改为 `A~F 全部可复核(含 [F] 无未清 review_pending)`。

- [ ] **Step 2: 续做信号表新增 review_pending 行**

在续做模式信号表(:123-137)追加:

```markdown
| fast/guarded 延后审查未 drain(`review_pending`,Commit 1 带 deferred-* 尾注) | 代码已提交 | `/ms-verify --review-drain` 集中清审 | ms-verify(编排器调度) |
```

- [ ] **Step 3: trace 从提交门降为惰性索引(spec §1.2)**

把 Step 1.5 `[C] trace 矩阵已同步` 分支从"硬门"降为"惰性索引":改为 `[C] trace 矩阵作为索引按需维护——缺失不阻塞放行,记 trace_pending 供后续 /ms-sync 增量补齐(不再是提交前阻塞门)`。同步在主循环 Commit 2 说明处标注:`trace 同步可延后/增量,不阻塞 Commit 1`。保留追溯矩阵本身(DevDocs 核心优势),仅改其门控角色。

- [ ] **Step 4: 验证**

Run: `rg -n "\[F\] review_pending|review_pending.*drain|A~F|trace.*索引按需" skills/dev-workflow/references/task-orchestration.md`
Expected: 命中 [F] 分支、信号表行、判据行、trace 惰性索引改动。

- [ ] **Step 5: Commit**

```bash
git add skills/dev-workflow/references/task-orchestration.md
git commit -m "feat(dev-workflow): task-orchestration Step1.5 加 [F] review_pending + trace 降为惰性索引 — Plan A Phase 4"
```

### Task 8: task-orchestration.md --all 解析规则 + 传播闸

**Files:**
- Modify: `skills/dev-workflow/references/task-orchestration.md`(解析流程 :28;依赖解析 :39 附近)

- [ ] **Step 1: 修订 --all 解析规则**

把 :28 的 `└── --all → 收集所有 状态≠已完成 的任务` 替换为:

```markdown
   └── --all → 收集所有 状态∈{待开发,进行中} 的任务（dev 执行跳过 review_pending，不重跑；review_pending 由 /ms-verify --review-drain 专门收集）
```

- [ ] **Step 2: 依赖解析新增传播闸小节**

在 "## 2. 依赖解析" 末尾追加:

```markdown
### 累积风险传播闸(review_pending)

上游任务处于 `review_pending` 时限制下游传播半径:
- 下游**仅允许低风险叶子任务(fast)**继续;
- 下游一旦触及公共 API / schema / 迁移 / 权限 / 安全 / 跨模块契约 → **进入前强制先 `/ms-verify --review-drain`**;
- 硬阈值:`pending ≤ 3`、`pending 依赖深度 ≤ 1`、`sprint 关闭前 pending = 0`;
- 超数量 / 依赖深度 / `Review-Due` 超期 → **强制 drain**(不静默升 audit)。`Review-Due` 超期判定:有 sprint→sprint close 时;无 sprint→`当前日期 > due` 或 `pending 计数 > 3` 任一。
```

- [ ] **Step 3: 验证**

Run: `rg -n "review_pending|传播闸|强制 drain|pending ≤ 3" skills/dev-workflow/references/task-orchestration.md`
Expected: 命中修订的 --all 行 + 传播闸小节。

- [ ] **Step 4: Commit**

```bash
git add skills/dev-workflow/references/task-orchestration.md
git commit -m "feat(dev-workflow): task-orchestration --all 跳过 review_pending + 传播闸 — Plan A Phase 4"
```

### Task 9: task-orchestration.md 主循环 + 后置加入 drain

**Files:**
- Modify: `skills/dev-workflow/references/task-orchestration.md`(主循环 :195-209;后置校验块 :213-226;被覆盖规则)

- [ ] **Step 1: 主循环步骤 6~6.9 改为按 review_profile 分支**

把主循环步骤 6/6.5/6.9 替换为:

```text
│  6. 完成检查(S8)+ 质量地板 5 条 + 前置验证(guarded/audit 跑 /ms-verify --impl)│
│  6.5 独立审查分支(按 review_profile):                       │
│     ├── audit → Phase 1~3 + Phase 4 inline fail-fast,审过才提交 │
│     └── fast/guarded → 跳过 inline 独立审查,标 review_pending  │
│  6.9 Commit 1(代码;fast/guarded 带 Review-Batch-Id/Review-Due/Pending-Reason 尾注)│
```

- [ ] **Step 2: 后置校验块追加 batch drain**

在后置测试校验块之后插入:

```text
┌─ batch/sprint review drain ─────────────────────────────────┐
│  触发:批量跑完编排器宣告完成前自动 drain;或传播闸跳闸强制 drain │
│  执行:/ms-verify --review-drain 收集本批 review_pending 集中清审 │
│  结果:全通过→相关任务转已完成;有 Blocker→fix-forward+阻断 sprint close │
│  headless:自动 drain(不"告警"等人);drain 失败→fail-fast 输出续做命令 │
└──────────────────────────────────────────────────────────────┘
```

- [ ] **Step 3: 追加 review_pending 被覆盖规则**

在 "### Realign 与续做的边界" 之后追加:

```markdown
### review_pending 被新需求覆盖
**禁止原地覆盖**。新需求触及同一 `review_pending` 任务 → 要么先 `/ms-verify --review-drain`(转已完成或 fix-forward)再改,要么创建依赖/替代任务并保留原 pending 审查链路(原 `Review-Batch-Id` 不丢)。
```

- [ ] **Step 4: 验证**

Run: `rg -n "review_profile|review drain|review_pending 被新需求覆盖" skills/dev-workflow/references/task-orchestration.md`
Expected: 命中主循环分支、drain 块、覆盖规则。

- [ ] **Step 5: Commit**

```bash
git add skills/dev-workflow/references/task-orchestration.md
git commit -m "feat(dev-workflow): task-orchestration 主循环按 profile 分支 + batch drain + 覆盖规则 — Plan A Phase 4"
```

---

## Phase 5 — execution-flow.md 按 profile 的强制程度

### Task 10: execution-flow.md 强制程度矩阵改为 review_profile 轴

**Files:**
- Modify: `skills/dev-workflow/references/execution-flow.md`(强制程度矩阵)

- [ ] **Step 1: 替换强制程度矩阵的轴**

把现有以"层级(🔴🟡🟢⚪)"为列的 S1~S11 强制程度矩阵,整表替换为以 `review_profile` 为列(■必须 / ○推荐 / ⏳延后到 drain):

```markdown
| 步骤 | fast | guarded | audit |
|------|:---:|:---:|:---:|
| S1 读任务 / S1.5 Contract | ■ | ■ | ■ |
| S2/S3 骨架 + 测试骨架(双 Agent) | ■ | ■ | ■ |
| S4-S7 红绿重构(测试冻结) | ■ | ■ | ■ |
| 质量地板 5 条 | ■ | ■ | ■ |
| S8 完成检查(AC 完备表) | ■(证据摘要) | ■ | ■(完整矩阵) |
| S9 前置验证 `/ms-verify --impl` | ○ | ■ | ■ |
| S9 Phase 1~3 内审 | ⏳ defer | ⏳ defer(风险触发则 ■) | ■ inline |
| S9 Phase 4 外审 | ⏳ defer | ⏳ defer | ■ inline |
| S10 自描述 / S11 Commit 1 | ■ | ■ | ■ |
| UI Phase 2-UI 自查(仅 UI 任务) | 按 ui-quality-checklist.md(不随 profile 变) | 同 | 同 |

> ⏳ defer = 延后到 `/ms-verify --review-drain`,任务期间标 `review_pending`。
> 层级标签 🔴🟡🟢⚪ 仅作风险分类器输入决定 review_profile,不再直接决定本矩阵强制程度。
```

- [ ] **Step 2: 验证**

Run: `rg -n "review_profile|defer|⏳" skills/dev-workflow/references/execution-flow.md`
Expected: 命中新矩阵列头与 defer 标记。

- [ ] **Step 3: Commit**

```bash
git add skills/dev-workflow/references/execution-flow.md
git commit -m "feat(dev-workflow): execution-flow 强制程度矩阵改 review_profile 轴 — Plan A Phase 5"
```

---

## Phase 6 — auto-mode.md headless 下的 drain

### Task 11: auto-mode.md 决策表加 drain 触发 + review_pending 交付字段

**Files:**
- Modify: `skills/dev-workflow/references/auto-mode.md`(决策策略表 + 交付报告模板)

- [ ] **Step 1: 决策表追加 drain 决策**

```markdown
| batch 完成 / pending 超阈值 / Review-Due 到期 | **自动 `/ms-verify --review-drain`**(不"告警"等人);drain 失败 → fail-fast 输出续做命令 | 保证 review_pending 不在 headless 下永久堆积 |
```

- [ ] **Step 2: 交付报告模板加 review 字段**

在交付报告模板追加:`review_pending: [T-XX, ...]`、`drain_result: {passed, pending, blockers}`、`sprint_close_blocked: <bool>`。

- [ ] **Step 3: 验证**

Run: `rg -n "review-drain|review_pending|drain_result" skills/dev-workflow/references/auto-mode.md`
Expected: 命中决策行 + 报告字段。

- [ ] **Step 4: Commit**

```bash
git add skills/dev-workflow/references/auto-mode.md
git commit -m "feat(dev-workflow): auto-mode headless 自动 drain + 交付报告 review 字段 — Plan A Phase 6"
```

---

## Phase 7 — ms-dev-tasks 拆分时提议 review_profile

### Task 12: ms-dev-tasks 输出 review_profile + 风险信号

**Files:**
- Modify: `skills/dev-tasks/SKILL.md`(任务分层/任务字段章节)

- [ ] **Step 1: 任务字段新增 review_profile 提议 + 风险信号**

在任务定义字段中,把原"层级标记 🔴🟡🟢⚪"保留为风险输入,并新增 `review_profile` 提议字段。加入风险分类器判据:

```markdown
### review_profile 初始提议(风险分类器)
拆分时为每个任务提议初始 `review_profile`(dev-workflow 执行时可按实际 diff 升档):
- **audit** 信号(任一):不可逆数据变更/schema 迁移、安全/认证/权限/密钥、PII/隐私/合规、钱/支付、外部不可逆副作用(邮件/短信/webhook/队列/三方写)、共享核心 API 或反向依赖计数 ≥ 5 的模块、复杂算法、线上事故热修、并发/事务、依赖/lockfile/运行时升级、CI/测试框架/质量门自身、生产配置/IaC/部署/特性开关/限流/缓存/重试/幂等/超时、序列化/DTO/协议兼容、高流量热路径、依赖链根节点。
- **guarded** 信号(任一):有分支的新行为、公开/对外接口、跨模块契约、行为边界不清的新测试。
- **fast**(默认):配置(仅非运行时·非安全·非部署)、文案、样式、有覆盖的内部重构、文档、无下游叶子。
- 组合规则:命中 ≥2 个 guarded 信号 或 预估 diff > 150 行/触及 > 5 文件 → 升 audit。
- 治理:不确定默认 guarded;层级标签 🔴🟡🟢⚪ 仅作输入之一。
```

- [ ] **Step 2: 验证**

Run: `rg -n "review_profile|audit 信号|反向依赖计数" skills/dev-tasks/SKILL.md && wc -l skills/dev-tasks/SKILL.md`
Expected: 命中;行数 ≤ 500。

- [ ] **Step 3: Commit**

```bash
git add skills/dev-tasks/SKILL.md
git commit -m "feat(ms-dev-tasks): 拆分时提议 review_profile + 风险分类器 — Plan A Phase 7"
```

---

## Phase 8 — ms-verify 新增 --review-drain 入口

### Task 13: ms-verify 加 --review-drain flag

**Files:**
- Modify: `skills/verify/SKILL.md`(flag 表 + 维度自动检测)

- [ ] **Step 1: flag 表追加 --review-drain**

```markdown
| `--review-drain` | 收集所有 `review_pending` 任务,集中补跑延后的独立审查(Phase 1~3 + Phase 4),按 [dev-workflow verification-flow drain 失败矩阵](../dev-workflow/references/verification-flow.md) 出 verdict 并更新任务状态;全通过转已完成,有 Blocker 走 fix-forward 并阻断 sprint close |
```

- [ ] **Step 2: 说明与 dev-workflow 的边界**

加一句:`> --review-drain 复用 dev-workflow S9 Phase 1~3/Phase 4 的 embedded-headless 通道,是 fast/guarded 延后审查的清算入口;单任务 inline 审查仍由 dev-workflow 内部触发。`

- [ ] **Step 3: 验证**

Run: `rg -n "review-drain" skills/verify/SKILL.md && wc -l skills/verify/SKILL.md`
Expected: 命中;行数 ≤ 500。

- [ ] **Step 4: Commit**

```bash
git add skills/verify/SKILL.md
git commit -m "feat(ms-verify): 新增 --review-drain 延后审查清算入口 — Plan A Phase 8"
```

---

## Phase 9 — 一致性收尾

### Task 14: 交叉引用一致性 + spec_version bump + health 自检

**Files:**
- Modify: `skills/dev-workflow/SKILL.md`(frontmatter spec_version + 权威文件唯一原则)
- Verify: 全 dev-workflow + ms-verify + ms-dev-tasks + _shared

- [ ] **Step 1: bump spec_version 并更新 notes**

SKILL.md frontmatter `spec_version: 1.1` → `2.0`,`spec_version_notes` 追加:`2.0 = 重新定位(代码SSOT/文档记忆)+ review_profile 三档替代层级 + 质量地板恒定 + 独立审查延后 drain + review_pending 状态(Plan A)`。

- [ ] **Step 2: 更新"权威文件唯一原则"指针**

把权威文件唯一原则补充:`review_profile/drain/review_pending → verification-flow.md + task-orchestration.md;风险分类器 → ms-dev-tasks。`

- [ ] **Step 3: dead-link / 残留层级开关 扫描**

Run:
```bash
rg -n "层级.*固定|层级=.*强度|🔴 自动触发" skills/dev-workflow/ skills/dev-tasks/SKILL.md
rg -n "EXT_PENDING" skills/dev-workflow/references/*.md   # 确认 review_pending 未误并入 EXT_PENDING 语义
rg -no "references/[a-z-]+\.md" skills/dev-workflow/SKILL.md | sort -u   # 链接目标存在性人工核对
wc -l skills/dev-workflow/SKILL.md   # ≤ 500
```
Expected: 无"层级=固定强度"残留(全部已改 review_profile);`EXT_PENDING` 仅出现在其原 Phase 4 语义处,未与 review_pending 混用;所有链接目标文件存在;SKILL.md ≤ 500。

- [ ] **Step 4: 若有 health-lint 入口则跑一次**

Run: `rg -l "health-lint|scope=health" skills/pipeline/ 2>/dev/null | head` — 若存在,按 `/ms-pipeline realign --scope=health` 文档自检 state/* + dead-link + 三层分离。人工核对本次新增章节符合"SKILL.md 仅指针、权威在 references"原则。

- [ ] **Step 5: Commit**

```bash
git add skills/dev-workflow/SKILL.md
git commit -m "chore(dev-workflow): spec_version 2.0 bump + 权威指针 + 一致性收尾 — Plan A Phase 9"
```

---

## 验收(Plan A 完成判据)

- [ ] `review_profile` 三档在 SKILL.md + _shared 一致定义,层级标签已降为风险输入(无"层级=固定强度"残留)。
- [ ] 质量地板 5 条恒定 inline,三类机制区分清晰。
- [ ] `review_pending` 为独立新状态,Step 1.5 [F] 检测,`--all` 跳过,drain 转已完成;**未与 `EXT_PENDING` 混用**。
- [ ] `/ms-verify --review-drain` 入口存在,drain 失败矩阵 + fix-forward + sprint close 阻断完整。
- [ ] 传播闸(pending≤3/深度≤1/超期强制 drain)+ headless 自动 drain 落地。
- [ ] ms-dev-tasks 拆分提议 review_profile,风险分类器判据可执行(反向依赖计数/diff 阈值)。
- [ ] 所有 SKILL.md ≤ 500 行;无 dead-link。
- [ ] (建议)交 Codex 通审整套改动 diff(adversarial-review / codex-mcp),确认与 spec §1~§4+§10 一致、无新仪式回潮。
