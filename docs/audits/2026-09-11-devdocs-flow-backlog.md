# DevDocs 流程待办

> 2026-09-11 登记，2026-09-16 §1 / §2 **已判定并结清**（结论见 §3）。原取证保留备查。
>
> ⚠️ **§4 于 2026-09-16 登记**：4.1（死引用）与 4.2（守卫规则）当日即结清，**4.3~4.6 仍未决**。
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

**判据只有一条：同一条规则里两句话强度不一致。**
"不再作为用户必须打对的语法"（禁**强制**）vs "只存在于编排层与子 Agent 之间，
用户无需知道它们存在"（禁**文档**）。21 个 skill 违反的是后半句，没有一个违反前半句。
收窄 = 在这两句里选留前一句。

佐证 —— skill 自己已在做自然语言路由（`ms-verify`：`T-01 T-02 → 自动 --impl`、
`--impl "检查 AC" → LLM 自动聚焦`）。flag 已经是**可发现性**而非**强制语法**，
收窄只是让规则文本追上既成事实。

> ⚠️ **本节曾两度用"`normalized_intent` 只有 4 个字段 ⇒ 阶段参数没有落点"来论证，两次都被
> Codex 独立审查驳回（2026-09-16 R1/R2 F-009）**，已整段删除。驳回理由：4 字段只约束
> `normalized_intent` 这一个字段，握手里还有 `task` / `mode` / `inputs` 可以承载阶段意图
> ⇒ 该前提证不出"没有落点"，更证不出"规则自相矛盾"。
>
> 留作教训：**上面那条判据自始至终独立成立，不需要 4 字段这层脚手架。**
> 连续两轮为同一个多余论证打补丁，正是 [AGENTS.md](../../AGENTS.md) 「修改 skill」末条
> 说的形态：**"每轮审查都冒出新耦合是过拟合信号，不是继续加固的理由"** —— 塌缩掉那个维度，
> 不要再给它打补丁。

⇒ 原 §1 的问题 3（"归一化判据表还没写"）**仍然成立且未解决**，只是收窄后不再阻塞：
范围外的参数不需要判据表。

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


---

## 4. flag 的消费契约缺口（2026-09-11 登记）—— 4.1 / 4.2 已结清，4.3~4.6 未决

> 起因：`--impl` 这类子指令**没有解析器** —— skill 是 markdown，harness 把 flag 当 `args` 原样传给模型，模型读 SKILL.md 的表**对着认**。纯文本匹配。
>
> 推论：flag 打错、改名、删除，**没有任何东西会报错**。以下是实测出的后果。

### 4.1 ~~已实证 4 处死引用~~ —— 已修（2026-09-16）

15 行 shell 扫 `skills/` 下所有 `/<skill> --<flag>` 引用，回查目标 skill 目录是否存在该 flag：

| 死引用 | 发出方 | 严重度 |
|---|---|---|
| `/ms-requirements --incremental` | `ms-feature/references/full-mode-steps.md:36`（写「**必须委托给**」）· 同文件 `:176` · `ms-verify/SKILL.md:470` | 🔴 委托链断点。子 Agent 收到不存在的 flag 会自行编造解释 |
| `/ms-dev-workflow --task` | `ms-verify/templates/verify-report.md:162` | 🔴 **模板复制进用户项目**，教用户敲不存在的命令 |
| `/ms-test-cases --update` | `ms-verify/templates/verify-report.md:163` | 🔴 同上 |
| `/ms-dev-tasks --split` | `ms-verify/templates/verify-report.md:164` | 🔴 同上 |

**根因已定位**：`--incremental` 在 `a8f109a`（**「用户面 flag 收敛 49→20」**）中随生产方删除，改为 `ms-requirements/SKILL.md:54` 的「自动检测初始/增量模式」，但 **3 个消费方未同步**。

⇒ **那次收敛自己制造了死引用。** 这正是本仓吃过多次的「双删失效模式」：删了生产方漏了消费方，而无解析器 / 无 linter，静默通过。

**已修**：`9eb8941` 改掉全部 6 处 occurrence（上表 4 个 flag 名 / 3 个文件）。
守卫已落地，见 §4.2 —— 现在 `health-lint --skills-dir skills` 对本仓报 0 条。

> 误报 1 处（已排除）：`ms-requirements/references/context-mode.md:29` 的 `/ms-retrofit --baseline-update`，原文是「**不**为基线补全新建…一类的入口」，是反例不是引用。

### 4.2 ~~提案~~：`flag/dangling-reference` 作为 health-lint 第 9 条规则 —— 已落地（2026-09-16）

检测**机械可判**（本次用 15 行 shell 完成），与 `id/unknown-prefix` 同属「b 索引/链接」维度。

与既有 `id/prefix-consumption-contract`（2026-09-15 落地）**完全同构** —— 那条管编号前缀的消费契约，这条管 flag 的。两者的失效模式也同一个：生产方改了，消费方不知道。

**已落地**（2026-09-16）：登记时的阻塞前提「672 行规格 + 0 行代码」已不成立 ——
`skills/ms-pipeline/scripts/health-lint.py`（`c4ef86d` 起，纯 stdlib）实现了规格 12 条 rule 中的 10 条
（未实现：`design/adr-only-revision` · `submodule/pointer-drift`），
`flag/dangling-reference` 是其中之一（`7ed5527`）。它**只扫 skill 库不扫用户项目**，
入口 `--skills-dir`。

⚠️ 该实现随后被 codex 独立审查查出 8 处缺陷（`10ac085` 已修），其中一条让
`health/dead-link` 在追溯矩阵行上完全失效 —— **「有 linter」不等于「linter 是对的」**，
本条的守卫价值以那次修复为准。

### 4.3 ⏸️ 未决（⛔ 不是「判定不做」）：减少子指令 —— 靶子只有 `ms-verify`

**superpowers 把维度拆成 skill 数量，DevDocs 把维度压进 flag。**

```
superpowers:  brainstorming / writing-plans / executing-plans / subagent-driven-development   ← 4 个 skill
DevDocs 写法: /plan --brainstorm | --write | --execute | --subagent                            ← 1 个 skill 4 个 flag
```

| | superpowers | DevDocs |
|---|---:|---:|
| skill 数 | 14 | 21 |
| SKILL.md 均行 | 241 | 355 |
| 典型 | 每个 skill 一件事 | `ms-verify` **451 行**装 4 个维度 |

**这直接影响触发准确度**：`ms-verify` 的 description 是「文档一致性、实现正确性、UI 对齐**或**开发就绪状态」—— 四件事 OR 在一起，天然模糊；superpowers 每个 description 只说一件事。

⇒ **flag 把四个锐利的触发面压成了一个钝的。** 与 [2026-08-28 软触发漏检](2026-08-28-skill-soft-trigger-miss-brief.md) 是同一问题的另一面：那份查的是「描述写不清」，这里是「描述天然装不下」。

#### 实测：这件事比「架构分歧」小得多（2026-09-16 复量）

| skill | 行数 | 模式数 | 性质 |
|---|---:|---:|---|
| **`ms-verify`** | **483** | **6** | 🔴 六个**不同动作**（查文档 / 查实现 / 查 UI / 查就绪 / 清算延后审查 / drift）|
| `ms-test-run` | 296 | 5 | ✅ 同一动作的**范围选择**（跑哪层测试），合理 |
| `ms-requirements` | 421 | 3 | 数据源不同，合理 |
| `ms-sync` / `ms-prd` | 322 / 360 | 2 | 轻 |
| **`ms-dev-workflow`** | 422 | **0** | ✅ **本仓已有的无 flag 反例** —— 用位置参数 `T-03` / `F-001` |

⇒ **靶子只有 `ms-verify` 一个**，不是全仓架构改造。`ms-dev-workflow` 证明无 flag 形态在本仓可行。

#### 关键历史：它们本来就是独立 skill，是被合并进来的

`b010c5a`（2026-03-10）**同一提交**内：新建 `devdocs-pipeline`，同时
`devdocs-verify (3-in-1)` 合并并删除 `devdocs-review` / `devdocs-requirements-alignment` /
`devdocs-ui-alignment`。

合并理由未写入 commit，但从 `ms-pipeline` 自陈定位可推：**降低用户面对 13 个原子 skill 的认知负担**。

⚠️ **当初的合并理由已经弱化**：
- 合并优化的是**用户的选择成本**；
- 代价落在**模型的触发准确度**（description 把四件事 OR 在一起）；
- 而 `ms-pipeline` **现在正是干「替用户选」这件事的** ⇒ 用户选择成本已由编排层承担。

⇒ 这不是「superpowers 那样更好」，是**本仓自己的前提变了**。

#### 状态：⏸️ 未决，⛔ 不是判定不做

**未满足 ROI 门槛**：没有任何记录表明 `ms-verify` 真的误触发或漏触发过。

**且有独立的推迟理由**：[role-contract 台账](2026-08-31-role-contract-backlog.md) 明写
`ms-verify`「**它是验收方本身，改造它等于改验收标准，须最后动**」。

**重新评估的触发条件**：集中验证中观察到 `ms-verify` 误触发 / 漏触发，或用户实际报告
「想查 X 结果它查了 Y」。届时最小切入是拆 `ms-verify`，⛔ 不是全仓拆 flag。

### 4.4 顺带登记：`ms-pipeline` 治理委托在项目早期有空档

`ms-pipeline/SKILL.md:233`：`init` 链在 **`ms-requirements` 完成后**才委托 `agent-memory --update` 落盘工作流路由节，且该步 `failed` / `partial` 时**显示 ℹ️ 后继续主链**。

⇒ 项目早期（requirements 未完成，或该治理步失败时）**AGENTS.md 的工作流路由节不存在** —— 而那恰是最容易走错流程的阶段。

来源：2026-09-16 Codex 独立调研。⚠️ **未评估影响面**，也无真实失败证据。

### 4.5 待验：插件安装后模板里的裸名是否仍可解析（2026-09-16）

用户决定改用 **Plugin Marketplace** 安装（原 npx）。插件安装的 skill 带命名空间
（本会话直接可见：`superpowers:brainstorming` / `ponytail:ponytail` 是带前缀的，
npx 装的 `ms-pipeline` 是裸名）。

**风险面已量化**：

| 位置 | 处数 | 性质 | 影响 |
|---|---:|---|---|
| `skills/*/templates/` | **72 / 20 文件** | **会复制进用户项目，用户照着敲** | 🔴 真风险 |
| `skills/*/SKILL.md` + `references/` | 1151 | 给模型看的指路，模型自行解析到带前缀项 | 低 |

⛔ **未验证**：插件装完后用户敲裸名 `/ms-sync` 到底还能不能解析。
只观察到列表显示带前缀，**没有证据表明裸名失效**。

⇒ **装完后一条命令即可测**，⛔ 不要在验证前批量改写那 72 处。
若确认裸名失效，改动面是 20 个模板文件；若仍可解析，本条直接关闭。

模板清单（按处数）：`ms-verify/verify-report.md`(11) · `ms-dev-tasks/task-template.md`(8) ·
`agent-memory/memory-template.md`(7) · `prior-art-scan/report-template.md`(6) ·
`ms-verify/readiness-report.md`(5) · `ms-retrofit/retrofit-report-template.md`(5) ·
`agent-memory/best-practices.md`(5) · 其余 13 个文件各 1~4 处。

### 4.6 未验：`_shared` 的 skill 名不符合部分客户端的命名规则（2026-09-16）

`skills/_shared/SKILL.md` 的 `name: _shared` 以下划线开头。Codex 本轮调研指出
它**不符合 OpenCode 官方文档的名称正则**（[opencode.ai/docs/skills/#validate-names](https://opencode.ai/docs/skills/#validate-names)）。

⛔ **未验证**是被拒、被跳过，还是仍可作为普通引用文件使用。

- 它本就声明「不是一个可调用的流程」，只是被其他 skill 以 `../_shared/constraints.md`
  相对路径引用的**约束 SSOT 载体**。若客户端只是不把它注册为 skill，引用路径仍然成立 ⇒ 无影响。
- 若客户端**拒绝整个 skill 目录**，则 `constraints.md` 不会被复制，所有引用它的 skill 全部断链 ⇒ 严重。

⛔ **不要未经验证就为此全仓改名** —— 目录名 ≡ frontmatter `name` 是本仓的安装约定
（见 [AGENTS.md](../../AGENTS.md)），改名会波及全部跨 skill 引用。

⇒ 用户已决定改用 Plugin Marketplace（Claude Code），该路径下未观察到问题；
本条仅在**扩展到 OpenCode 等客户端**时才需要结论。
