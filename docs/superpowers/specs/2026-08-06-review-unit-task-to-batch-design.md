# 独立审查输入从「单任务 diff」改为「drain 合并 diff」设计

> 状态：**第 2 稿已被双路独立审计部分证伪，待第 3 稿修订——勿按本稿实施** · 日期：2026-08-06
>
> 已知失效点（第 3 稿修正）：① 影响面漏 `task-orchestration.md`（505 行，9 处 audit 断言）；② §2.5 / §4 「断点续做流水线零改动」不成立，且步数应为 **6 步**非 5 步（Step 1/1.5/2/3/4/5）；③ 违反 `constraints.md:347` `enum/non-pass-blocks`；④ 合并 diff 无 commit range，按现契约（`verification-flow.md:420,432` 用未提交 diff）会拿到空 diff；⑤ verdict 复制进 N 个任务会夸大证据含义，应改批级 L2 证据 + 任务引用；⑥ §6 验证项 4 为空跑（改动前后恒真）。
> 定位：**dev-workflow S9 外审输入的 scope 改动**。不新增 Phase、不新增 skill、不新增概念、不新增 flag、不改状态机；净效果是删掉一整节强制规则 + 每批外审次数 N → 1

## 1. 问题

开发阶段独立审查的输入恒等于**单任务 diff**，从 `04-dev-tasks` 拆分那一刻锁死。五个可查证的后果：

| # | 症状 | 证据 |
|---|------|------|
| a | 审查清单显式钉在 diff 内，跨任务架构轨迹不可见 | `verification-flow.md:67/75/81/88`（注释/命名/日志/错误处理均"仅审本次 diff"）|
| b | ≥3 发现门槛 × N 任务 = 强制 3N 次向内修改压力 | `verification-flow.md:280-286` |
| c | 没有任何提问在要求减法，修复方向单向向上 | 见 §3.2 |
| d | 任务 commit + PASS 后冻结为公理，后续任务只能打补丁 | S11 每任务原子提交；`:465` audit 需 `EXT_REVIEWED` 才 Commit 1 |
| e | 单个 diff 上跑 3~5 轮外审 = 对审查者过拟合 | `max_rounds=3`，`--external-rounds` 上限 5 |

**`review_profile=fast` 不解决这个问题**：`verify/SKILL.md:34` 的 drain 是"收集所有 `review_pending` 任务，集中补跑"，失败矩阵第一行是「单任务 Blocker」（`verification-flow.md:560`）——逐任务回放，只挪时间不改 scope。

**净效应**：a+d 产生局部最优（N 个各自最优的任务实现合成全局烂摊子），b+c 产生单调 accretion，e 产生过拟合。三者独立，需分别处理。

### 为什么不新增机制

用"新增机制"治"机制过度增生"是同病相治。三条自我约束贯穿本方案：

1. Phase 4 的定义本就是「对 git diff 做外部第三方审查」，**diff 的范围是参数而非本质**——改参数，不加阶段
2. 需要的"批"概念**已经存在**，就是 drain 收集的 `review_pending` 集合——复用，不新建
3. 状态机 / 断点续做 / flag 数量三项**零增长**——这是本仓复杂度的真实承重点

## 2. 核心改动：外审输入 = drain 合并 diff

### 2.1 两层分工

| 层 | 输入 | 抓什么 | 时机 |
|---|------|--------|------|
| 任务级 Phase 1~3（内审，同进程角色演绎） | 单任务 diff | 局部质量：命名 / 注释 / 日志 / 错误处理 / 断言质量 / 覆盖 | 按 review_profile，见 §2.3 |
| 任务级质量地板 5 条 + `/ms-verify --impl` | 单任务 | 不可协商的正确性 | **恒定 inline**（本方案零改动）|
| **Phase 4（外审，独立进程/模型）** | **本次 drain 收集的 `review_pending` 任务合并 diff** | 全局连贯：抽象重复 / 边界错位 / 任务该合并或删除 / 坏抽象的补丁聚集 | drain 时一次 |

理由：外审最贵、独立性最强、也最容易过拟合。输入改成合并 diff，一次看完整轨迹——既降成本，又让它**有资格**提结构性意见（看不到 T-03..T-10 的人无法说"T-03 的抽象错了"）。任务级局部质量交给便宜的 Phase 1~3 内审，够用。

**不需要定义"批"**：外审输入就是 drain 的既有输入。`review_pending` → drain 是唯一路径，无 per-path 分支，因此不存在"单任务执行会不会静默跳过外审"这类特例风险。

### 2.2 两个必答问题（防止合并审退化为逐个挑刺）

Phase 4 提示词强制包含，每轮逐条作答（答"无"合法，不得省略）：

**Q1｜有没有早期任务的决定，后续任务在给它打补丁——workaround 在哪里聚集？**

处置（对症状 d）：若判定问题在 `04-dev-tasks` 的拆分本身（任务边界错、任务多余、两任务该合一）——

- 相关任务保持 `review_pending` + 报告写明须重拆，交用户决定是否 `/ms-dev-tasks` 重拆
- **禁止在下游任务里就地打补丁**
- 阻断力来自**已存在的** `review_pending` 阻断 sprint close，不新增阻塞机制

**Q2｜如果从零实现这批 AC，哪些现存代码不会出现？**（含：有没有两个任务各造了同一个东西）

本方案唯一稳定产出"删"的提问方式。也替代了更复杂的 additive-only 轮次检测（见 §5.2）。

### 2.3 review_profile 三档

> Phase 4 外审对三档一致——drain 时一次，不受档位影响。故档位表**不再含 Phase 4 列**；档位只管任务级审查强度。

| 档 | 双 Agent 红绿 | 质量地板 5 条 | `/ms-verify --impl` | 任务级 Phase 1~3 内审 |
|----|:---:|:---:|:---:|------|
| fast（默认） | ✓ | ✓ inline | — | ⏳ 延后到 drain |
| guarded | ✓ | ✓ inline | ■ inline | 风险触发则 inline |
| audit | ✓ | ✓ inline | ■ inline | ■ 全部 inline |

`audit` 不再等于"每任务外审"，其 drain 外审**不可跳过**（未过阻断 sprint close）。这同时**删掉一个特例**：`review_pending` 从 fast/guarded 专属变为全档常态，audit 不再拥有自己的 inline 外审路径。

**不为旧行为新增 flag**：本仓 flag 已从 49 收敛到 20，为保留一个已被论证有害的行为而加 flag 是纯负债。确需单审某个任务 diff 的场景，`/adversarial-review` 支持独立调用（该 skill 本就以工作区 diff 为默认输入）。

### 2.4 状态与 trailer（**owner 不变**）

关键约束：**合并审改的是「审查输入」，不是「状态归属」**。两者必须分开，否则会往断点续做里加间接层。

`ext_review_state` 的 owner **仍是 task**。一次合并审产出的 verdict **直接写入参与本次 drain 的每个任务**：

- 合并审 `EXT_REVIEWED` → 参与任务各自落 `EXT_REVIEWED`，转 `已完成`
- Blocker 能归属到具体任务 → 只有该任务落非放行态，fix-forward
- Blocker 归属跨任务（无单一任务 owner）→ 相关任务全部保持 `review_pending`，走 §2.2 Q1 处置

`Review-Batch-Id` 保持原语义（记录该任务的审查属于哪一次 drain），**不承担状态继承职责**；唯一变化是从"延后必填"变为"全档必填"。

`INT_*` 不变。枚举值域不扩展（守 `enum/no-extension`）。状态机与 5 步断点续做检测流水线**零改动**——这是本节的设计目标，不是巧合。

## 3. 配套两条（治 accretion，与 §2 正交）

### 3.1 删除 ≥3 发现门槛

`verification-flow.md:280-286` 整节删除，替换为：允许 0 发现，但须给出一句可复核判据说明为何无发现。

理由：门槛的存在本身就是凑数激励，与其自辩的"目的不是凑数"矛盾。凑出的 ✅ 确认项挤占注意力，凑出的 Suggestion 被修成 accretion。

### 3.2 🔧 定义补一句，**不加 enum 值**

第 1 稿曾拟新增 🗑「删除/合并」路径。审计后判定该前提有误：🔧「Agent 可直接修复」**本就不排除删除**（删代码是一种直接修复），原规则「Blocker 只能是 🔧」限定的是"必须当场修不许延后"，而非"不许用删除来修"。

真正缺的不是 enum 值，是**没有任何提问在要求减法**——已由 §2.2 Q2 解决。

故仅在 `verification-flow.md:292-296` 路径表的 🔧 行补一句：**修复动作可以是删除或合并，不限于新增**。路径仍为三条，分级规则不动。

## 4. 影响面

| 文件 | 改动 |
|------|------|
| `skills/_shared/constraints.md` | review_profile 三档表删 Phase 4 列（§2.3）；`Review-Batch-Id` 全档必填。**独立审查状态机不改** |
| `skills/dev-workflow/references/verification-flow.md` | 理念节 Phase 4 输入；新增两必答（§2.2）；**删** ≥3 门槛（§3.1）；🔧 补一句（§3.2）；drain 失败矩阵改合并审 |
| `skills/dev-workflow/references/execution-flow.md` | 强制程度矩阵 S9 两行 |
| `skills/dev-workflow/SKILL.md` | `--external-rounds` 语义（现作用于合并 diff）。**不新增 flag** |
| `skills/verify/SKILL.md` | `--review-drain` 从逐任务回放改合并审；`review_pending` 全档语义 |
| `skills/dev-tasks/SKILL.md` | review_profile 提议语义（档位现只管任务级强度）|
| `AGENTS.md` | 当前状态节 |
| spec_version | `devflow.v2` → `devflow.v3` |

**零改动面（显式声明，防实施时越界）**：独立审查状态机与值域、5 步断点续做检测流水线、双 Agent 隔离、质量地板 5 条、`/ms-verify --impl`、解决路径 enum、`Review-Batch-Id` 字段语义。

### 4.1 复杂度账

本方案治的是"机制过度增生"，因此自身必须能通过复杂度审计。第 2 稿账目：

| 减 | 增 |
|----|----|
| 删除 ≥3 发现门槛（整节，含凑数规则）| 两必答（提示词内容，零状态 / 零 flag / 零文件）|
| 外审 N 次 → 1 次（含 N-1 份 `round_history`、N-1 组状态转移）| Q1 处置 1 条判定规则（复用已有阻断）|
| 删特例：audit 不再有独立 inline 外审路径 | `--review-drain` 输入语义改动（改，非增）|
| 三档表删 1 列（Phase 4 全档一致，该列不携带信息）| |
| 不新增 flag（第 1 稿 `--external-per-task` 已砍）| |
| 不新增 enum 值（第 1 稿 🗑 路径已砍，前提有误）| |
| 不新增概念（第 1 稿 `batch` 已砍，复用 `review_pending` 集合）| |
| 不引入状态继承（第 1 稿双 owner 已消）| |
| 不新增 Phase | |

判断：**净减**。新增项全部是提示词内容与判定规则，不落在状态机 / Recovery / flag / enum / 概念这五类承重点上；这五项均零增长。

第 1 稿标注的残余风险（"单任务执行静默跳过外审"）在第 2 稿**从设计层面消失**——不再有 per-path 分支，`review_pending` → drain 是唯一路径。

## 5. 明确不做

### 5.1 不拆独立 skill
合并审是 Phase 4 的输入变化，不构成独立能力边界。

### 5.2 不做 additive-only 轮次检测
曾考虑：某轮修复若全为净增则不计入 `health_score` 收敛趋势，防止用加法刷分。**不做**——需新增 diff 增删比分析机制，复杂度不匹配收益；§2.2 Q2 以零新增机制的方式覆盖同一意图。同"health 维度 e 废弃"逻辑。

### 5.3 不改质量地板与双 Agent 隔离
5 条地板、测试冻结、信息屏障对所有档恒定 inline，本方案零触碰。审查输入上移不得成为降低正确性门槛的借口。

### 5.4 不合并 review_profile 三档
Phase 4 列删除后三档仅剩 2 个区分位（内审时机 × `--impl`），理论上可压到两档。**不做**——档位合并是用户面破坏性变更且需迁移，与本方案要解决的问题无关；属另一议题。

## 6. 验证

无自动化测试（规格库）。验证手段：

1. `grep -rn "至少报告 3 个发现\|≥ 3 项" skills/` → 0 命中
2. `grep -rn "单任务 Blocker" skills/` → 0 命中（drain 矩阵已改合并审）
3. `grep -rn "review_profile" skills/` → 三档表述与 §2.3 一致，无残留"audit 每任务外审"
4. `grep -rn "external-per-task\|🗑" skills/` → 0 命中（未引入新 flag / 新 enum 值）
5. `/ms-pipeline realign --scope=spec` → spec_version 一致性通过
6. 真实项目跑一次批量任务 + drain：确认 Phase 4 只触发 1 次、两必答均有作答、参与任务各自落 `EXT_REVIEWED`
