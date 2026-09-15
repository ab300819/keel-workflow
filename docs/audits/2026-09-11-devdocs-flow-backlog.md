# DevDocs 流程待办

> 2026-09-11 登记，2026-09-16 **两条均已判定并结清**。原取证保留备查。
>
> 与 [对象模型收敛设计](../superpowers/specs/2026-09-11-devdocs-object-model-convergence-design.md) 是**两条轴**：那份管编号对象与文档结构，本文管流程本身的暴露面与外部复用。

## 1. ~~用户面仍有子指令露出~~ —— 已结清：规则过宽，已收窄规则文本

**与现役规则直接冲突。** `_shared/constraints.md:162` 的 `task/intent-normalization` 明写：

> 协议参数（`--from-prd` / `--review-drain` / `--schema-drift` / `--force-code-docs` / `--review-profile` / `--no-realign` 等）**保留**，但**只存在于编排层与子 Agent 之间，用户无需知道它们存在**

### 取证（2026-09-11 实测）

**用户入口文档 `README.md`** 直接露出：`/ms-onboard --read`（2 处）· `/ms-dev-workflow --all` · `--readiness` · `--impl` · `--docs` · `--list`

**各 SKILL.md 的「运行模式 / 快速开始」节**（用户敲 `/<skill>` 时会读到）露出的子指令数：

| skill | 数量 | | skill | 数量 |
|---|---:|---|---|---:|
| `ms-verify` | 8 | | `ms-test-run` / `ms-prd-brainstorm` / `ms-compound` | 2 |
| `ms-sync` | 8 | | `ms-test-cases` / `ms-system-design` / `ms-retrofit` | 1 |
| `ms-pipeline` | 7 | | `ms-prd-parser` / `ms-feature` / `ms-dev-tasks` | 1 |
| `ms-requirements` / `ms-prd` / `ms-onboard` | 3 | | `ms-codebase-insight` / `ms-bugfix` | 1 |

**17 个 ms- skill 的用户面入口节都有。**

### 待判断的（⛔ 不要直接删）

1. **规则是不是过宽了？** `--readiness` / `--impl` / `--docs` 这类**选阶段**的参数，与 `--fast` / `--deep` 这类**选档位**的偏好词，性质可能不同。规则原文举的例子全是后者。前者删掉后用户怎么表达"我只想查实现正确性"？
2. 若确认要收，`/ms-pipeline` 的 8 个模式名（`init`/`feature`/`bugfix`/…）算不算子指令？它们是位置参数不是 flag，但同样要求用户记。
3. 收敛后编排层靠什么判断意图——`task/intent-normalization` 要求"归一化后下传"，但没写归一化的判据表。

⇒ **先判 1，再谈动手。** 判断结论应回写 `constraints.md:158` 那条规则本身（要么收窄规则，要么收窄暴露面）。

## 2. ~~根据 superpowers 优化 DevDocs 流~~ —— 已结清：6 对比对完成，原方向不成立

DevDocs 的多个阶段与 `superpowers` 插件的过程型 skill 职责重叠。需要逐对比对，判断是**重复实现**（应删一边）、**应当委托**（DevDocs 调 superpowers），还是**确实不同**（保留并写清边界）。

### 候选重叠对

| DevDocs 侧 | superpowers 侧 | 初判（⚠️ 未验证）|
|---|---|---|
| `ms-prd-brainstorm` | `brainstorming` | 都做需求探索 |
| `ms-dev-tasks` | `writing-plans` | 都做多步任务拆分 |
| `ms-dev-workflow` | `executing-plans` · `subagent-driven-development` · `test-driven-development` | 重叠最重的一处 |
| `ms-verify` | `verification-before-completion` | 都是完成前质量门 |
| `adversarial-review` | `requesting-code-review` · `receiving-code-review` | 都做外部审查 |
| `ms-bugfix` | `systematic-debugging` | 都是测试先行的缺陷流程 |

### 判据（比对时用）

- **删一边的条件**：两者的输入、产物、门控完全可互换，且没有 DevDocs 特有的追溯要求
- **委托的条件**：superpowers 侧的过程更完整，DevDocs 只需在前后补追溯写入
- **保留的条件**：DevDocs 侧承载了编号追溯 / yaml-summary 契约 / 断点恢复，superpowers 侧没有

⚠️ `superpowers:using-superpowers` 声明「process skills come first — they set the approach」。若这条成立，`ms-*` 里的过程部分本就该是委托而非自实现。**这个前提要先核实**，它决定整件事的方向。

⇒ 依赖第 1 条的结论：暴露面若要收敛，委托关系会一并变化，两件事应同批做。


---

## 3. 判定结论（2026-09-16）

### 3.1 第 1 条：规则过宽，已收窄规则文本

**不是口味题，规则自己的配套机制给了答案。** `task/intent-normalization` 要求"归一化后下传"，
而归一化的目标形状由 `task/normalized-intent-shape` 定义，字段**固定为 4 个**：
`ceremony` / `review_profile` / `unattended` / `granted_scope` —— **全是档位与授权**。

选阶段参数（`--impl` / `--docs` / `--readiness` / `--ui`）在归一化目标里**没有落点**。
一条要求归一化的规则，却没给这类参数定义归一化后的形状 ⇒ **规则文本的适用范围超出了它自己设计的机制。**

这同时答了原 §1 的问题 1 与问题 3：不是"归一化判据表还没写"，是这类参数根本不在该规则的设计意图内。

第二条独立证据 —— skill 自己已在做自然语言路由（`ms-verify`：`T-01 T-02 → 自动 --impl`、
`--impl "检查 AC" → LLM 自动聚焦`）。flag 是**可发现性**不是**强制语法**，
而规则禁的原文是"不再作为用户**必须打对**的语法"。

**真正的缺陷在规则内部**：同一条里两句强度不一致 —— "不再作为必须打对的语法"（禁强制）
vs "只存在于编排层与子 Agent 之间，用户无需知道它们存在"（禁文档）。21 个 skill 违反的是后半句。

**已落地**：`_shared/constraints.md` 的 `task/intent-normalization` 收窄适用范围至
`normalized-intent-shape` 的字段集，并把末条改为"不得呈现为必须输入的语法"。
5 个消费方全为 `ceremony` 引用本规则，收窄与全部消费方一致，**用户面 21 个 skill 与 README 不动**。

原问题 2（`ms-pipeline` 的 8 个模式名算不算子指令）在收窄后**自动合法** —— 同属选模式。

⚠️ 残留一处，**判为合法例外未改**：`ms-pipeline:78` 的 `--no-realign` 会写永久静默文件
`.devdocs-realign-ack`，而 `task/consent-at-action` 明写"入口处的一个词不能替代就地确认"；
但 `--headless` 下无人可就地确认，入口 flag 是唯一通道。

### 3.2 第 2 条：6 对全部比对完成，"该删一边 / 该委托"的方向不成立

**前提先证伪**：原文推断"`using-superpowers` 声明 process skills come first ⇒ ms-* 的过程部分本就该委托"。
该 skill 同时写着「User instructions (CLAUDE.md, AGENTS.md, direct requests) take precedence over skills」，
**前提不支持这个方向**。

| 对 | 判定 |
|---|---|
| `ms-verify` ↔ `verification-before-completion` | **正交**。前者管"验什么"（四维 + P 级），后者 120 行全是"敢不敢说验过了"的反合理化表。无产物冲突 |
| `ms-dev-workflow` ↔ `executing-plans` | **那边空**。64 行，自陈"有子 Agent 就别用我" |
| `ms-prd-brainstorm` ↔ `brainstorming` | **已事实委托**。产物目录 `docs/superpowers/specs/` 本仓一直在用 |
| `ms-dev-tasks` ↔ `writing-plans` | **真缺口**，见 3.3 |
| `adversarial-review`(498) ↔ `requesting-code-review`(95) | **两个层级**。那 95 行的内核是"别自己看 diff，派子 Agent，只收结论"（保编排者上下文预算），DevDocs 已有（yaml-summary） |
| `ms-bugfix`(469) ↔ `systematic-debugging`(283) | **门在，但条件触发**。`ms-bugfix:101` 根因诊断门只在"原因不明"时必过，判据是入口自判；systematic-debugging 的 Iron Law 无条件，且明写 *"Don't skip when: Issue seems simple"* |

**0 对是"重复实现该删一边"。**

### 3.3 未做：`writing-plans` 的 Interfaces 块（⚠️ 无失败证据，未达 ROI 门槛）

`writing-plans` 要求每个任务声明 `Consumes` / `Produces`（相邻任务的精确函数名与类型），
理由原文：*"A task's implementer sees only their own task; this block is how they learn the names
and types neighboring tasks use."*

`ms-dev-workflow` 是**双 Agent 隔离 + 子 Agent 分派**，隔离比 superpowers 更强，
但 `task-template.md` 的跨任务信息只有 `**依赖** | T-01`（任务编号）与
`**涉及文件** | src/services/xxx.ts`（路径）—— **没有签名**。

⚠️ **无真实失败证据**，属结构比对发现的缺口而非撞到的墙，按 [AGENTS.md](../../AGENTS.md) ROI 门槛暂不改。
顺带记录：模板的"Review 要点"自身是占位文案（"业务逻辑是否正确""错误处理是否完善"），
正是 `writing-plans` `No Placeholders` 点名禁止的形状。

### 3.4 数量纠正

**`ms-*` 实为 21 个，不是原文各处写的 17 个**（`ls -d skills/ms-*/` 实测）。

### 3.5 触发可靠性

原 §2 隐含的"DevDocs 触发不可靠"已单独立项调研并判定暂不做，
见 [2026-08-28 skill 软触发漏检](2026-08-28-skill-soft-trigger-miss-brief.md) §调研结论。
