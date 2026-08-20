# 独立审查：修复延后外审 + （待定）输入从单任务改为合并批

> 状态：**第 4 稿 · 分两段** · 日期：2026-08-20（第 1~2 稿 08-06，第 3 稿 08-17，本稿按两段结构重写）
> - **第一段 §2 可立即执行**——三件互相独立的 bug 修复与负债清理，不依赖"局部最优值得治"这一判断
> - **第二段 §3 待第一段数据**——外审输入 task → batch，触发条件见 §3.1
> 前置：`_shared/constraints.md` §11 `作用域匹配` 已落地（65c7daa）

## 0. 为什么分两段

第 3 稿是单个整体方案（11 文件，含跨 skill SSOT 改动）。分段的依据是**成本结构**：

修复空 diff 本身就要建「按提交取 diff」的机制——定位 Commit 1 的 SHA、按提交取 diff、shell 模式逐 `code_root` 拼接、改 T2 通道契约。而合并审需要的是同一套机制从 `n=1` 跑成 `n=k`。

所以：
- 顺序对了，第二段的 diff 机制几乎免费
- 顺序错了，就是把一个**正在生效的 bug**（默认档外审在审空 diff）压在一场设计辩论后面

更关键的是分段**创造了一个观测点**：两路独立审计都指出"缺真实项目数据"，而缺数据的原因正是**延后外审从来没真正工作过**。第一段做完，per-task 外审第一次真跑起来；那时可以直接观察局部最优是否出现，而不是靠论证决定第二段做不做。

## 1. 问题

开发阶段独立审查的输入恒等于**单任务 diff**，从 `04-dev-tasks` 拆分那一刻锁死。

| # | 症状 | 归属 |
|---|------|------|
| a | 审查看不到跨任务架构轨迹，只能产出框内补丁 | 第二段 |
| b | ≥3 发现门槛 × N 任务 = 强制 3N 次向内修改压力 | **第一段** |
| c | 没有任何提问要求减法，修复方向单向向上 | 第二段 |
| d | 任务 commit + PASS 后冻结为公理，后续任务只能打补丁 | 第二段 |
| e | 单个 diff 上跑 3~5 轮外审 = 对审查者过拟合 | 第二段 |
| **f** | **延后外审（fast/guarded 走 drain）审的是空 diff** | **第一段** |

> 症状 d 的证据：drain 失败矩阵默认 **fix-forward、revert 仅限已落盘代码主动有害**——流程本身没有"推翻上游任务"的合法出口。（第 2 稿此处引错了门禁行，第 3 稿已更正。）

症状 f 是本轮审计的意外产物，也是唯一**当前正在生效**的缺陷，故排在最前。

---

# 第一段：可立即执行

三件事互相独立，任一可单独落地；建议同批提交因为都动 Phase 4 的调用面。

## 2.1 修复延后外审的空 diff（症状 f）

### 缺陷

Phase 4 调度器的 brief 使用「本任务 git diff」，T2 通道传 `uncommitted: true`。这在 **inline 触发（audit）时是正确的**——那时 Commit 1 尚未产生，工作区 diff 就是本任务改动。

但 `fast`/`guarded` 的外审**延后到 drain**：Commit 1 早已落盘，工作区 diff 为空。**默认档（fast）的延后外审等于没审。**

> 置信度标注：这是**规格层判断**——本仓是纯规格库，无运行时可实测。但规格照现文本执行就是这个结果。

### 修复：按触发模式分离 diff 源

| 触发模式 | diff 源 | 改动 |
|---------|--------|------|
| inline（audit，Commit 1 之前） | 工作区 diff | **不变**（今天是对的）|
| drain（fast/guarded，Commit 1 之后） | 该任务 Commit 1 的提交 diff | **新增** |

drain 侧的构造规则（不新增状态，全部复用已有 trailer）：

1. 用 Commit 1 的 `Review-Batch-Id: <id>` trailer + 提交标题中的任务编号（`<type>(T-XX): ...`）定位该任务 Commit 1 的 SHA。
2. 外审输入 = 该 Commit 1 的 diff。**Commit 2 是纯文档提交，不入外审输入。**
3. ⛔ T2 通道的 `uncommitted: true` **仅对 inline 有效**；drain 侧须传入显式 diff 内容或 commit 范围。此为 `adversarial-review/references/external-reviewer-integration.md` 的契约改动。
4. **`workspace_mode: shell`**：Commit 1 按 `code_root` 拆成 N 个子模块 commit（见 `_shared/workspace-mode.md` N+1 仓提交协议）。drain 侧须**逐 code_root 定位并拼接**；外壳仓 Commit 2（文档 + 指针 bump）不参与。
5. diff 为空（任务无代码变更）→ 记 `drain.empty_diff`，跳过 Phase 4 但**不判 `EXT_REVIEWED`**——无审查即无证据。

### 诚实标注：本段引入一个分支

分离 diff 源意味着 Phase 4 有两条输入路径。这是 **+1 个可出错点**，且 shell 模式的逐 `code_root` 拼接是新的实现复杂度。

第二段会把它收回去（所有档统一走 drain → 只剩一条提交侧路径）。**若第二段不做，这个分支永久保留**——这是第一段单独落地的已知代价。

## 2.2 删除 skip 参数族（症状：纯负债）

`verification-flow.md` 自陈「`EXT_PENDING` 在所有放行路径下都为 ⛔ 阻塞 Commit 1，无例外」。既然 skip 后照样阻塞，它与「不跑外审 → `EXT_UNRESOLVED`」在**阻塞性与恢复动作上完全等价**，差别只有尾注里那句 reason——可写进 commit body。

这一族存在的唯一效果是把"现在必须做"改造成"事后要补的债"。

| 删除项 | 数量 |
|--------|------|
| `--skip-review-reason` / `--skip-external-review-reason` | 2 flag |
| `INT_PENDING` / `EXT_PENDING` | 2 enum 值 |
| `Skip-Review-Reason:` / `Skip-External-Review-Reason:` | 2 commit trailer |
| 「双 skip 非法组合」规则 + 相关自辩段 | 1 规则 |
| Step 1.5 [D1]/[D2] 的 **skip 分支** | 2 续做分支 |

> [D1]/[D2] 的 **profile 条件分支**（"audit 任务须…；fast/guarded 由 [F] 覆盖"）属第二段，本段不动。
>
> `constraints.md` 中 `review_pending` 定义的"严禁复用 `EXT_PENDING`"一句随该 enum 值删除而失效，需一并清理。

足迹：40 处命中 / 9 文件（见 §2.4）。

## 2.3 删除 ≥3 发现门槛（症状 b）

整节删除，替换为：**允许 0 发现，但须给出一句可复核判据说明为何无发现**。

门槛的存在本身就是凑数激励，与其自辩的"目的不是凑数"矛盾。凑出的 ✅ 确认项挤占注意力，凑出的 Suggestion 被修成 accretion。

同时在解决路径表 🔧 行补一句：**修复动作可以是删除或合并，不限于新增**。**不新增 enum 值**——第 1 稿曾拟加 🗑，审计后判定前提有误（🔧「可直接修复」本就不排除删除）。

## 2.4 第一段影响面

| 文件 | 改动 |
|------|------|
| `_shared/constraints.md` | `int/ext_review_state` 删 2 值；Commit trailers 删 2 项；`review_pending` 定义清理"严禁复用 EXT_PENDING" |
| `dev-workflow/SKILL.md` | 删 2 flag + 尾注模板 2 行 + skip 参数表；放行条件表述随 enum 收缩调整 |
| `dev-workflow/references/verification-flow.md` | Phase 4 brief 分 inline/drain 两源（§2.1）；EXT 真值表删 `EXT_PENDING` 行；**删** ≥3 门槛；🔧 补一句；drain 失败矩阵新增 `drain.empty_diff` |
| `dev-workflow/references/task-orchestration.md` | Step 1.5 [D1]/[D2] 删 skip 分支；`INT_PENDING` 续做行 |
| `dev-workflow/references/execution-flow.md` | 步骤状态追踪表 S9 两行的 enum 值域 |
| `dev-workflow/references/auto-mode.md` | 2 处 skip 决策策略 |
| `verify/SKILL.md` | 2 处 skip 引用；`--review-drain` 的 diff 源说明 |
| `adversarial-review/references/external-reviewer-integration.md` | T2 通道 `uncommitted: true` 契约（§2.1 条 3）；1 处 skip 引用 |
| `pipeline/references/layout/ssot-lint-implementation.md` | 4 处 skip 引用 |
| `AGENTS.md` | 当前状态节 |
| spec_version | `devflow.v2` → `v3`；`shared-constraints.v3` → `v4` |

**零改动面**：质量地板 5 条、双 Agent 隔离与信息屏障、测试冻结与 diff 安全网、红验基线比较、`/ms-verify --impl`、解决路径 enum 值域、修复安全网、`review_profile` 三档表、`enum/non-pass-blocks`、L2 证据粒度。

**不碰** `review_profile` 三档语义与 `enum/non-pass-blocks`——那是第二段。

## 2.5 第一段验证

每项都有改动前基线，非恒真：

1. `grep -rn "至少报告 3 个发现" skills/` → 0（改前 1）
2. `grep -rn "skip-review-reason\|skip-external-review-reason\|INT_PENDING\|EXT_PENDING" skills/` → 0（改前 40 处 / 9 文件）
3. `grep -rn "uncommitted: true" skills/` → 仅 inline 路径保留，drain 路径 0 命中
4. `/ms-pipeline realign --scope=spec` → spec_version 一致性通过
5. **真实项目**：跑一个 fast 档任务至 Commit 1 → 跑 drain → 确认外审收到**非空 diff**，且 L2 yaml 记录的改动与该任务 Commit 1 一致
6. **shell 工作区**：在 `workspace_mode: shell` 项目上重复第 5 项，确认逐 `code_root` 拼接且不含外壳仓文档提交

> 验证项 5 同时是第二段的**数据采集点**：第一次拿到真实的延后外审输出。

---

# 第二段：外审输入 task → batch（待第一段数据）

## 3.1 触发条件

第一段落地并在真实项目跑过 ≥1 个批次后，观察延后外审的实际产出：

| 观察结果 | 决策 |
|---------|------|
| 出现跨任务问题被漏判（后续任务给早期任务的抽象打补丁，而逐任务外审全 PASS） | **做第二段** |
| 逐任务外审已能捕获主要问题，未见跨任务盲区 | **不做**，第一段的 diff 源分支作为永久代价接受 |
| 外审发现数显著偏低或全是框内微调 | 倾向做——这是局部最优的特征信号 |

**不做也是合法结局**：那样省下整个 `constraints.md` SSOT 改动，并留下已修好的延后外审。

## 3.2 外审输入 task → batch

Phase 4 输入从「单任务 Commit 1 的 diff」改为「本次 drain 全部 `review_pending` 任务 Commit 1 的 diff 并集」。

复用第一段建好的按提交取 diff 机制，`n=1` → `n=k`；若批内提交与其他工作交错，**以 trailer 命中的 SHA 集合为准逐个取 diff 后拼接**，不用简单的 `A^..B` 范围（会裹入无关提交）。

**不需要定义"批"**：就是 drain 的既有输入（`review_pending` 集合）。

**收回第一段的分支**：所有档统一走 drain 后，inline 路径消失，Phase 4 只剩一条提交侧 diff 源。§2.1 的 +1 分支在此 −1。

## 3.3 两个必答问题

Phase 4 提示词强制包含，每轮逐条作答（答"无"合法，不得省略）。二者都只在合并视角下成立，故属第二段。

**Q1｜有没有早期任务的决定，后续任务在给它打补丁——workaround 在哪里聚集？**

处置（对症状 d）：若判定问题在 `04-dev-tasks` 的拆分本身——相关任务保持 `review_pending` + 报告写明须重拆，交用户决定是否重拆；**禁止在下游任务里就地打补丁**。阻断力来自**已存在的** `review_pending` 阻断 sprint close，不新增阻塞机制。

**Q2｜如果从零实现这批 AC，哪些现存代码不会出现？**（含：有没有两个任务各造了同一个东西）

本方案唯一稳定产出"删"的提问方式。替代更复杂的 additive-only 轮次检测（§5.2）。

## 3.4 review_profile 三档 + `enum/non-pass-blocks`

Phase 4 对三档一致（drain 时一次），故档位表**删 Phase 4 列**；档位只管任务级审查强度。

| 档 | 双 Agent 红绿 | 质量地板 5 条 | `/ms-verify --impl` | 任务级 Phase 1~3 内审 |
|----|:---:|:---:|:---:|------|
| fast（默认） | ✓ | ✓ inline | — | ⏳ 延后到 drain |
| guarded | ✓ | ✓ inline | ■ inline | 风险触发则 inline |
| audit | ✓ | ✓ inline | ■ inline | ■ 全部 inline |

`audit` 不再等于"每任务外审"，其 drain 外审**不可跳过**（未过阻断 sprint close）。这**删掉一个特例**：`review_pending` 从 fast/guarded 专属变为全档常态。

**连带改写 `enum/non-pass-blocks`**：原文锁定"非放行态一律阻塞 **audit 档 Commit 1**"。audit 外审延后后该条不成立，改为：非放行态阻塞**任务转 `已完成`**；Commit 1 的放行条件收敛为质量地板 5 条 + `/ms-verify --impl`（guarded/audit）。

**不为旧行为新增 flag**（本仓 flag 已从 49 收敛到 20）。确需单审某任务 diff，`/adversarial-review` 支持独立调用。

## 3.5 批级 L2 证据

`ext_review_state` 的 owner **仍是 task**——批级是「审查过程」与「证据」的粒度，不是「状态」的粒度。

| | 第一段后 | 第二段 |
|---|------|--------|
| L2 权威证据 | `audit/<T-XX>-external-review.yaml`，每任务一份 | `audit/<batch-id>-external-review.yaml`，**每次 drain 一份** |
| 任务如何关联 | 自持 | 经已有的 `Review-Batch-Id` trailer 引用 |

一次合并审只产生一份证据。让 verdict 复制进 N 个任务、各自落 `EXT_REVIEWED` 会**夸大证据含义**——该状态的定义是"该任务有 L2 可读的审查证据"，而合并审可能只深入看了其中一部分。

**批级 L2 须含 `covered_tasks` 清单**（唯一 schema 增项）：N 份文件换 1 份 + 1 字段，净减；没有它无法防止"任务声称获得了它没得到的覆盖"。

**Step 1.5 [D2] 校验口径随之改**：从"本任务 L2 可读"改为"本任务 `Review-Batch-Id` 指向的批级 L2 可读，**且本任务在其 `covered_tasks` 内**"。

## 3.6 [D1]/[D2] 折叠（额外减法）

[D1]/[D2] 现在带 profile 条件分支（"**audit 任务**须…；fast/guarded 由 [F] 覆盖"）。所有档统一走 `review_pending` → drain 后，**这两个分支可整个删除并折叠进 [F]**。

这是第 2 稿与两路审计都没算到的一笔——不是"漏算改动量"，是"漏算了一笔额外减法"。

## 3.7 第二段影响面

除第一段已列文件外新增/加深：

| 文件 | 改动 |
|------|------|
| `_shared/constraints.md` | review_profile 三档表删 Phase 4 列；`enum/non-pass-blocks` 改写；`Review-Batch-Id` 全档必填 |
| `dev-workflow/references/verification-flow.md` | Phase 4 输入改合并（§3.2）；两必答；L2 改批级 + `covered_tasks`；drain 失败矩阵首行「单任务 Blocker」拆为可归属 / 跨任务两行 |
| `dev-workflow/references/task-orchestration.md` | [D1]/[D2] 删 profile 分支折叠进 [F]；`:166-168`/`:227`/`:230` 的"audit inline Phase 4"语义（**第 2 稿整个漏了本文件**）|
| `dev-workflow/references/execution-flow.md` | 强制程度矩阵 Phase 4 行 |
| `verify/SKILL.md` | `--review-drain` 改合并审；`review_pending` 全档语义 |
| `dev-tasks/SKILL.md` | review_profile 提议语义（档位只管任务级强度）|

## 3.8 第二段验证

1. `grep -rn "单任务 Blocker" skills/` → 0
2. `grep -c "audit" skills/dev-workflow/references/task-orchestration.md` → 显著低于改前的 9
3. `grep -rn "review_profile" skills/` → 三档表述与 §3.4 一致，无残留"audit 每任务外审"
4. **真实项目**：跑一批任务 + drain → Phase 4 只触发 1 次、两必答均有作答、合并 diff 非空、批级 L2 的 `covered_tasks` 覆盖全部参与任务
5. **单任务路径**：执行单任务至 Commit 1 → 确认落 `review_pending` 而非直接 `已完成`

---

## 4. 复杂度账（分段）

| | 减 | 增 |
|---|----|----|
| **第一段** | ≥3 门槛整节；2 flag；2 enum 值；2 trailer；双 skip 规则；2 续做分支 | Phase 4 双 diff 源分支（+1 可出错点，含 shell 逐 code_root 拼接）|
| **第二段** | 外审 N 次 → 1 次（含 N-1 份 round_history）；L2 证据 N 份 → 1 份；audit 独立 inline 外审路径（特例）；三档表 1 列；[D1]/[D2] profile 条件分支；**收回第一段的双 diff 源分支** | 两必答（提示词文本）；Q1 处置 1 条判定规则（复用已有阻断）；批级 L2 的 `covered_tasks` 1 字段 |

两段合计在承重点上净减：flag −2、enum −2、trailer −2、续做分支 −4、概念 ±0、双 diff 源 ±0。

**只做第一段**：承重点净减 flag −2 / enum −2 / trailer −2 / 续做分支 −2，代价是永久保留双 diff 源分支。

## 5. 明确不做

### 5.1 不拆独立 skill
合并审是 Phase 4 的输入变化，不构成独立能力边界。

### 5.2 不做 additive-only 轮次检测
需新增 diff 增删比分析机制，复杂度不匹配收益；§3.3 Q2 以零新增机制覆盖同一意图。同 `layered-memory/no-auto-detection` 逻辑。

### 5.3 不改质量地板与双 Agent 隔离
审查输入变化不得成为降低正确性门槛的借口。

### 5.4 不合并 review_profile 三档
两路审计都独立提出可压到两档，但**两路也都把它列为自己最没把握的一条**（信心 45% / "需用户拍板"），共同理由是缺真实项目数据。属另一议题。

### 5.5 不动 EXT 四态收缩为两态
第一段删 `EXT_PENDING` 后已是三态；进一步收缩需确认实现方是否按 enum 分派恢复动作，本仓无运行时代码可验，codex 自评信心亦低。

## 6. 附：第 2 稿被证伪的 6 点（存档）

保留以防第 5 稿重犯。第 2 稿经 codex + 独立子 Agent 双路审计：

| # | 错处 | 现处置 |
|---|------|--------|
| 1 | 影响面漏 `task-orchestration.md`（505 行、9 处 audit 断言）| §2.4 / §3.7 均已列 |
| 2 | 声称"断点续做流水线零改动"，而 [D2] 就在其中——自相矛盾 | 承认必改；且改动是**删分支**（§3.6）|
| 3 | 步数写成 5 步（实为 6 步）| 已随 8b14cd4 全仓统一 |
| 4 | 违反 `enum/non-pass-blocks` | §3.4 连带改写该条 |
| 5 | 合并 diff 无 commit range，会拿到空 diff | 升级为**第一段首要项**（§2.1）|
| 6 | verdict 复制进 N 任务夸大证据；验证项 4 为空跑 | §3.5 改批级 L2；§2.5/§3.8 验证项全部带改前基线 |
