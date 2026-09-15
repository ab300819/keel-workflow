---
title: 共享约束 SSOT
status: 协议层 SSOT —— 现状提取 + 标记为 [新增] 的跨切面规则
scope: 跨 skill 协议层共性
related:
  - AGENTS.md（yaml-summary-v1 原始定义）
  - skills/ms-prd/references/governance/prd-revision-policy.md（PRD 修订边界）
  - skills/workspace-topology/（工作区拓扑：入口、协议正文、迁移手册）
  - skills/_shared/runlog.md（运行日志：形状、纪律、判决点）
generated_at: 2026-05-18
spec_version: shared-constraints.v13
---

# 共享约束 SSOT

本文是 T-106 识别的重复规则的共享 SSOT 提取，用于后续 skill 引用切换。

- `doc/two-kinds`：本文有**两类**内容，必须始终可区分：
  - **现状提取**（起源，T-106）：仓库已有重复规则的共享 SSOT，不改变任何 skill 的行为。**无标记**。
  - **新增跨切面规则**：后续确立的、不属于任何单一 skill 的协议层规则。一律标 `[新增]`（见 `future/use-new`）。

  > 本条取代原 `doc/status-extraction`（「只整理已有规则，不引入新执行语义」）。该表述在 `§11 作用域匹配`、`§3 task/runlog-append` 等 6 条规则落地后已与实际不符，且**它没有阻止任何一次新增，只是让每次新增都要附一段例外说明**——一条被绕过 6 次的规则不是规则。

  新增的准入三条，**全部满足**才能进本文：

  1. **真跨 skill** —— 至少 2 个消费方，且它们的实现必须一致（只有 1 个消费方 = 该 skill 的私有规则）
  2. **不属于任何单一 skill** —— 归得进某个 skill 的按 `doc/private-rule-boundary` 退回该 skill；来自单个项目的按 `doc/project-rule-boundary` 退回项目侧
  3. **bump `spec_version`** —— 本文是协议层，新增即协议变更

  ⛔ **不得因为「不知道该放哪」而放进本文。** 那是协议层膨胀的唯一真实成因——它让本文从「消除重复」变成「制造依赖」。
- `doc/no-immediate-impact`：现有 `skills/*/SKILL.md` 不会因本文创建而自动改变；引用切换是后续独立任务。
- `doc/reference-over-copy`：已有详细 spec 优先保留在原位置，本文只声明协议层共性与指针。
- `doc/private-rule-boundary`：skill 私有规则不得提升到共享层；例如 Sprint Contract、verify P 级评分仍归各自 skill 或 references 文件维护。
- `doc/project-rule-boundary`：**项目实战发现不得提拔为 skill 级默认强制约束**。单项目的语言 / 框架 / 业务域细节（类名、字段名、分层契约、设计稿锚点、该项目的 commit 与编号）一律留在项目侧 `docs/devdocs/patterns/verify-blindspots.md` 等插件位，由消费方 skill 自动加载。判据：**规则的适用域必须 ≥ 它的强制域**——一个只在某语言/某业务成立的规则挂上 ⛔ 全局强制，会让所有不适用的项目误阻断，或迫使 agent 学会无视 ⛔ 标记（后者腐蚀全体系阻断标记的可信度）。skill 侧只保留语言与领域中立的判定 + 一句"插件位会被加载"。与 `doc/private-rule-boundary` 同向：前者管 skill→shared，本条管 project→skill。

## 1. 门控标记 SSOT

### 标准标记

| rule_id | 标记 | 标准语义 | 典型触发条件 | 恢复方式要求 |
|---|---|---|---|---|
| `gate/marker-set` | `⛔ 禁止继续` / `⚠️ 必须确认` / `ℹ️ 建议` | 共享层只承认这三类门控标记 | 所有 ms- skill 的阶段边界、确认点、建议项 | 不得扩展新标记，除非另开 spec bump |
| `gate/blocker-semantics` | `⛔ 禁止继续` | 硬阻塞；必须解除后才能继续 | 阶段边界、P1 阻塞、安全不变式、测试未通过不得提交等 | 必须写明可执行恢复方式 |
| `gate/confirm-semantics` | `⚠️ 必须确认` | 继续前需要用户确认或选择 | Inversion 问询、方案确认、不可自动判断的归类/迁移 | 必须写明等待用户确认的内容 |
| `gate/advice-semantics` | `ℹ️ 建议` | 推荐但可跳过，不阻塞当前流程 | P2/P3 建议、可选验证、后续优化 | 可给出恢复/后续动作，但不强制 |

### 硬规则

- `gate/two-senses` `[新增]`：`⛔` 有**两种合法语义**，此前从未写下，导致「43 / 302 条不合规」这类误判反复出现：
  - **门控**：`⛔ 禁止继续：<阻塞事实>` —— 流程在此停下，存在一个待解除的阻塞态，**必须附 recovery**
  - **禁令**：`⛔ <不得 / 禁止 / 严禁做某事>` —— 没有阻塞态，正确做法就是不做它，**不需要 recovery**（无从「恢复」）
  - ⛔ 不得因为一条 `⛔` 不是门控形式就判它不合规；也不得把禁令改写成门控来「补 recovery」——那会造出一个不存在的阻塞态。
- `gate/recovery-required`：每个**门控**（`⛔ 禁止继续`）必须附带 recovery；缺 recovery 的门控视为不合格。禁令不受此条约束。
- `gate/confirm-recovery-required`：每个 `⚠️ 必须确认` 必须说明用户需要确认什么，以及确认后的合法路径。
- `gate/advice-non-blocking`：`ℹ️ 建议` 不得写成阻塞条件；如必须阻塞，应升级为 `⛔` 或 `⚠️`。
- `gate/no-private-severity`：共享层不定义 P1/P2/P3、health score 等私有严重度；这些只可作为触发条件上下文，不可替代三类门控。
- `gate/difference-label`：若某 skill 对同一标记有更窄语义，引用本文时必须在本地标注“差异点”，不得悄悄覆盖共享定义。

### 推荐写法

```markdown
⛔ 禁止继续：<阻塞事实>
恢复方式：<解除阻塞的具体动作；包含命令、文件、确认人或下一 skill>
```

```markdown
⚠️ 必须确认：<需要用户决定的问题>
恢复方式：用户选择 <A/B/C> 后，继续执行对应分支；无确认时保持只读/不修改。
```

```markdown
ℹ️ 建议：<可选优化或后续动作>
后续：<可选，不影响当前流程完成>
```

## 2. yaml-summary-v1 envelope SSOT

### envelope 字段

所有 ms- skill 作为子 Agent 运行时，返回统一信封格式：

```yaml
skill: <ms-skill-name>
status: success | failed | interrupted | partial
summary:
  headline: "一句话总结"
  details: {}
blockers: []
output_files: []
new_ids: {}
next_recommended:
  skill: <ms-next-skill>
  args: ""
```

| rule_id | 字段 | 定义 |
|---|---|---|
| `yaml-summary/skill-name` | `skill` | 返回当前 skill 的 `name`，例如 `ms-requirements`。 |
| `yaml-summary/status-enum` | `status` | 完整值域固定为 `success` / `failed` / `interrupted` / `partial`。 |
| `yaml-summary/headline` | `summary.headline` | 一句话总结本次子 Agent 结果。 |
| `yaml-summary/private-details` | `summary.details` | skill 私有字段唯一承载位置。 |
| `yaml-summary/blockers` | `blockers` | 通用阻塞项列表；阻塞项应能映射到 `⛔` 或 `⚠️`。 |
| `yaml-summary/output-files` | `output_files` | 本次产出或修改的文件；只读模式下可为空。 |
| `yaml-summary/new-ids` | `new_ids` | 本次生成的编号；键名按产物类型命名。 |
| `yaml-summary/next-recommended` | `next_recommended` | 可选下一步 skill 与参数，不等同于自动执行授权。 |

### 保留字段边界

- `yaml-summary/reserved-fields`：`status`、`blockers`、`output_files`、`new_ids`、`next_recommended` 是保留字段，含义不得被 skill 私有化。
- `yaml-summary/details-only-private`：skill 私有统计、模式、评分、扫描范围、差距数量必须放入 `summary.details`。
- `yaml-summary/no-status-extension`：不得新增 `skipped`、`warning`、`noop` 等 status；需要表达时放入 `summary.details`。
- `yaml-summary/status-success`：`success` 表示请求范围内闭环完成，且没有未解决 `⛔`。
- `yaml-summary/status-failed`：`failed` 表示无法完成请求范围，且存在错误或硬阻塞。
- `yaml-summary/status-interrupted`：`interrupted` 表示流程被用户或环境中断，未到达可判定完成态。
- `yaml-summary/status-partial`：`partial` 表示完成了可执行部分，但仍有明确未完成范围、需确认项或环境限制。

## 3. Task tool / 子 Agent 委托规则

### 委托边界

- `task/delegation-scope`：编排层可通过 Task tool 委托原子 skill；被委托 skill 只处理明确输入，不扩展任务边界。
- `task/yaml-summary-required`：被委托的 ms- skill 必须以 yaml-summary-v1 返回结果。
- `task/no-implicit-apply`：子 Agent 的 `next_recommended` 只表示建议，不代表编排层可自动执行下一步。
- `task/private-fields-in-details`：子 Agent 私有输出必须放入 `summary.details`，避免污染编排层通用字段。
- `task/runlog-append` `[新增]`：编排层收到子 Agent 的 yaml-summary 后，**原样**追加一条到 `<docs_dir>/devdocs/.runlog.yaml`。**不设门禁**——写失败静默跳过，不得因此阻断流程；**子 Agent 不自行写入**。信封不改、字段不增，形状与判决点见 [runlog.md](runlog.md)。**本规则自带死期（2026-11-30），到期未读即作废。**

### success / failed 判定

- `task/success-contract`：子 Agent `success` 至少表示输入已处理、要求的产物或检查已完成、没有未解除 `⛔`。
- `task/failed-contract`：子 Agent `failed` 必须在 `blockers` 写明失败原因和 recovery。
- `task/partial-contract`：存在环境限制、仅完成 dry-run、只完成部分范围或等待用户确认时，优先使用 `partial`。
- `task/interrupted-contract`：用户取消、上下文中断或工具执行被停止时，使用 `interrupted`，并在 `summary.details` 记录已完成范围。

### 最小握手协议

编排层调用子 Agent 前，应传入最小上下文：

```yaml
skill: <target-ms-skill>
task: <明确任务>
mode: read | dry-run | apply | update
inputs: []
workspace_context: {}          # 可选，见 task/workspace-context
normalized_intent: {}          # 可选，见 task/intent-normalization
allowed_paths: []
expected_output: yaml-summary-v1
```

- `task/handshake-minimum`：`task`、`mode`、`inputs`、`allowed_paths`、`expected_output` 是推荐最小握手字段。
- `task/normalized-intent-shape` `[新增]`：`normalized_intent` 承载编排层归一化后的档位与授权，字段固定为：
  - `ceremony`: `fast` | `standard` | `deep` —— 交互详略（少确认 / 默认 / 逐步确认）
  - `review_profile`: `fast` | `guarded` | `audit` —— 独立审查时机
  - `unattended`: `true` | `false` —— 用户是否明确授权无人值守（缺省 `false`）
  - `granted_scope`: 一句话记录用户授权了什么，供 `task/consent-at-action` 判定「是否超范围」
  - 持久化位置：随断点检查点一同保存（v1 为 `docs/devdocs/.batch-checkpoint.json`），续做时原样恢复，⛔ 不重新推断。
- `task/workspace-context`：**编排层**在流程开头调一次 `/workspace-topology inspect`，把返回的 `workspace-context.v2` 经本字段下传（`mode`（`inline` | `shell` | `linked`）/ `workspace_root` / `docs_dir` / `code_roots` / `missing_code_roots`）。被委托 skill 从此字段读代码根与 docs 根，**不自行读取声明文件、不解析 `.gitmodules`**。三种 mode 下 `code_roots` 元素形状一致（`name` / `path` / `declared_path`，`path` 为解析后的绝对路径），**调用方不分支**。`missing_code_roots` 非空表示有声明了但解析不到的代码根，⚠️ 报告即可、不阻塞。字段缺失（用户单跑原子 skill、无编排层）时按 `inline` 缺省并 ℹ️ 提示。契约见 [../workspace-topology/SKILL.md](../workspace-topology/SKILL.md)。
- `task/mode-honored`：子 Agent 不得越过传入 `mode`；`read` / `dry-run` 不得产生写入。
- `task/intent-normalization` `[新增]`：**档位与授权类偏好词不作为用户必须打对的语法**（`--fast` / `--deep` 一类）。用户以自然语言表达意图，由**编排层**归一化后下传：
  - **适用范围 ≡ `task/normalized-intent-shape` 的字段集**（`ceremony` / `review_profile` / `unattended` / `granted_scope`）。⛔ 选阶段 / 选维度 / 选子集参数（`--impl` / `--docs` / `--readiness` / `--ui` / `--ut` / `--from-prd` 等）**不在本规则内**——它们是动词不是偏好词，归一化目标里没有对应字段，可在用户面文档作为可发现性入口列出。
  - 归一化结果写入本握手，**子 Agent 只读归一化字段，不得自行解读用户原话**；原话只进 runlog 的 `entry` 作审计线索
  - 歧义**只问一次**，答案落盘并随断点恢复一同持久化；反复追问等价于把记忆负担改成对话负担
  - ⛔ **授权不可由模型自行升格**。「跑快点」不等于授权无人值守提交；缺省取最保守档
  - 本范围内的协议参数（`--review-profile` / `--no-realign` / `--force-code-docs` 等）**保留**，但用户面文档 ⛔ 不得把它们呈现为必须输入的语法
- `task/consent-at-action` `[新增]`：**超出用户已授权范围**的不可逆 / 外发 / 降低验证强度 / 写入版本控制的持久决策，一律在**动作发生的那一刻**确认，不依赖入口 flag。
  - ⛔ 判据是**范围**不是动作类型：用户授权「无人值守跑完」时，提交代码就是被授权的工作本身，不重复确认（与 `confirm/no-need-explicit-request` 一致）；而「这次先别升级」被落成永久静默的 `.devdocs-realign-ack`，是**授权范围外**的持久决策，必须当场确认。
  - 入口处的一个词不能替代就地确认——它反映不了用户看到中间结果后的判断，也覆盖不了执行中途才暴露的不可逆性。- `task/blocker-propagation`：子 Agent 返回 `failed` 或含 `⛔` blocker 时，编排层必须停止对应分支并 surface recovery。

## 4. FUTURE 执行状态标注规范

### 三态语义

| rule_id | 标注 | 语义 | 是否阻塞当前运行 |
|---|---|---|---|
| `future/state-current` | `[现状]` | 当前已实现或当前行为描述 | 不阻塞 |
| `future/state-new` | `[新增]` | 本次或本阶段新增的已生效规则/字段/文档 | 不阻塞，但需说明影响范围 |
| `future/state-future` | `[FUTURE]` | 已声明但执行接口或 runtime 逻辑尚未落地 | 不得被当作已可执行能力 |

### 使用规则

- `future/use-current`：描述当前仓库实际行为、当前默认路径、已存在命令时，用 `[现状]`。
- `future/use-new`：描述本次新增的规范文本、字段或产物，且已在本仓库落地时，用 `[新增]`。
- `future/no-live-path-cost` [新增]：`[FUTURE]` **只许**表示**能力边界**（「本 skill 不做这件事」，永久有效、无到期日）。⛔ **不许**表示**待建工程**——「入口已声明、逻辑待落地」只有两个去处：现在做，或删掉入口。
  - **封存不得在现役路径上留痕**：想清楚了但暂不做的东西，只许以一句备注存在于设计文档或 `spec_version_notes`；⛔ 不许声明命令入口、不许加 frontmatter 字段、不许在正文写「v1 这样 / v2 [FUTURE] 那样」的双轨句。
  - 判据是**税**——这条封存有没有让现役读者付成本。付了就是非法，无论意图多合理。
  - 依据：layout.v2 挂了三个多月、一次没跑过，代价是 40 处双轨句 + 80 行 frontmatter 分摊到 10 个现役 skill；而 worktree 并行同样是封存，只有设计文档里一句备注，零税。
- `future/no-runtime-assumption`：`[FUTURE]` 不阻塞阅读 spec，但阻塞实际调用；调用时应 fail-safe 或提示执行逻辑待落地。

## 5. 用户确认 / AskUserQuestion 规则

### 必须确认

- `confirm/destructive-change`：删除、覆盖、重命名、移动文件或其他不可逆操作前，必须使用 AskUserQuestion 或等价用户确认。
- `confirm/cross-boundary`：跨阶段、跨 skill 职责边界、跨目录边界或跨 allowed paths 的写入，需要用户确认。
- `confirm/restructuring`：realign 的 restructuring 差距必须展示 before/after 并逐项确认。
- `confirm/ambiguous-input`：输入模糊且会影响编号、范围、设计方向或迁移策略时，必须确认。
- `confirm/multi-active-candidate`：存在多个 active 候选、多个可用 PRD、多个归类目标或多个迁移分支时，必须让用户选择。

### 不需要确认

- `confirm/no-need-small-recoverable`：小范围、可恢复、已在用户明确请求范围内的文档补齐，可不额外确认。
- `confirm/no-need-readonly`：只读扫描、dry-run 报告、缓存命中展示不需要确认。
- `confirm/no-need-explicit-request`：用户已明确要求执行且操作可恢复、范围清晰时，不重复询问同一授权。

### headless 模式

- `confirm/headless-fail-safe`：无交互能力时，遇到必须确认项不得默认继续；应返回 `partial` 或 `failed`，并列出待确认问题。
- `confirm/headless-report`：headless 输出必须包含可复制给用户的问题、选项、默认安全行为和 recovery。
- `confirm/no-assumed-consent`：沉默、超时或缺少 AskUserQuestion 工具不等于用户同意。

### 怎么问（不只是何时问）[新增]

以上规则管**何时**必须确认，本组管**怎么呈现**——否则确认发生了，用户仍然拿不到能决策的信息。

- `confirm/plain-options` [新增]：**选项必须让没有本次对话的人看懂，且每个选项必须写「不选它会怎样」。**

  | 要求 | 反例（本仓真实发生） |
  |---|---|
  | ⛔ 不用只在本次推理中出现过的词 | 「制品型需求 vs 行为型需求」——用户没有这套词汇表；他自己给的「非编码类任务」既准确又已接上体系里的 `TDD 模式 ⚪ 不适用` |
  | ⛔ 不用内部术语代替解释 | 「消费方计数边界过窄」「声明层与执行层不一致」 |
  | **每个选项写具体后果**，具体到能感知 | ✅「会把正常完成的审查判成截断，白重跑一轮」<br>❌「存在健康度风险」 |
  | 先给结论再给依据 | 用户问「能不能工作」，第一句必须是「能」或「不能」 |

  > **判据来自 [doc-organization 原则 5](../doc-organization/SKILL.md)**：写的人当时全知全能，看不出哪些词需要解释；**AI 每次都是「当时全知」的那一方，所以这个问题会系统性恶化，没有任何环节会让写的人自己发现**。该 skill 只管文档，本条把同一判据搬到**交互通道**（AskUserQuestion 与给用户的答复）。
  >
  > **自检**：把自己造的词全删掉，这段话还成立吗？不成立 → 说明在用术语替代解释。
  >
  > ⚠️ **一个说法自相矛盾时（例：「非编码类任务被强制走 TDD」），先怀疑自己的框架，⛔ 不要当成待办记下来。**

- `confirm/scope-inflation` [新增]：**改动面超出用户诉求一个数量级时，必须停下来确认，⛔ 不得先做完再汇报。**

  判据（任一命中即停）：

  | 信号 | 例 |
  |---|---|
  | 用户点名改 N 处，实际要改 ≥10N 处 | 用户说「改 `ms-dev-tasks` 一条硬约束」，实际在改 36 个文件 |
  | 为满足诉求而**新造概念** | 先列出现有字段 / 状态 / 编号并逐个排除，排除不掉才造。本仓实证：`CK-XXX`（其实是既有的「测试方法」字段）、`FACT-XXX`、`Pending-<宿主编号>`（其实是既有的 `needs review` 块）三个自造概念全被审查否决 |
  | 症状被升级成「体系缺少某个一等公民」 | 用户描述的是一处挂靠失败，不是缺少一等公民 |

  > **为什么必须当场停**：扩张后的方案会被外部审查**认真加固**——审查者审的是我给它的东西，我给的是加戏后的版本，它就把戏加固得更结实，**轮次越多陷得越深**。本仓实证：7 轮审查、消费方 4→37、其中 4 轮打的是与用户诉求无关的既存问题，最终全量缩回。
  >
  > 与 [[doc/project-rule-boundary]]、[[doc/private-rule-boundary]] 同向：那两条挡「不该提拔的规则」，本条挡「不该扩张的改动面」。

## 6. 只读 / dry-run 规则

### 只读边界

- `readonly/no-source-mutation`：标称只读的 skill 不得修改业务源代码、DevDocs 主链路产物或用户未授权文件。
- `readonly/codebase-insight`：`ms-codebase-insight` 的核心职责是只读分析代码库；其生成 `docs/codebase-insight.md` 属于该 skill 自身输出，不等同于修改被分析代码。
- `readonly/onboard-read-mode`：`ms-onboard --read` 必须只读取现有上下文，不扫描、不写入。
- `readonly/onboard-update-mode`：`ms-onboard --update` 是更新模式，会生成或覆盖 `docs/devdocs/00-context.md`；不得被描述为只读模式。
- `readonly/violation-handling`：只读模式中发现需要写入时，必须停止写入，改为输出建议、diff 草案或 `⚠️ 必须确认`。

### dry-run / apply 命名

- `dry-run/default-non-mutating`：`--dry-run` 表示只输出计划、影响范围、风险、待确认项，不写文件。
- `dry-run/apply-mutating`：`--apply` 表示执行已确认的变更；若存在不可逆或跨边界动作，仍需确认。
- `dry-run/fix-default`：自动修复类命令默认应先 dry-run，只有明确 `--apply` 才写入。
- `dry-run/report-required`：dry-run 输出必须足以让用户判断是否 apply，至少包含目标文件、操作类型、风险或不可自动项。

### 差异提示

- `readonly/difference-generated-artifacts`：部分“只读分析”skill 会写入自身分析产物；引用本文时需区分“不改被分析对象”和“完全不写文件”。

## 7. 恢复方式（Recovery）格式规范

### 适用范围

- `recovery/blocker-required`：每个**门控**（`⛔ 禁止继续`）必须附 recovery；**禁令**形式的 `⛔` 不受此条约束（判据见 §1 `gate/two-senses`）。
- `recovery/confirm-required`：每个 `⚠️` 必须附 recovery 或确认路径。
- `recovery/advice-optional`：`ℹ️` 可附后续动作，但不要求。

### 最小字段

| rule_id | 字段 | 要求 |
|---|---|---|
| `recovery/action` | 动作 | 说明解除阻塞的具体操作。 |
| `recovery/owner` | 执行者 | 说明由用户、当前 skill、编排层或后续 skill 执行。 |
| `recovery/evidence` | 验证 | 说明完成后如何确认阻塞已解除。 |
| `recovery/next-step` | 下一步 | 说明解除后从哪里继续。 |

### 模板

```markdown
⛔ 禁止继续：<阻塞事实>
恢复方式：
- 动作：<具体修复/补充/确认>
- 执行者：<用户 / 当前 skill / 编排层 / 后续 skill>
- 验证：<命令、文件、检查点或确认结果>
- 下一步：<解除后继续的 skill、阶段或命令>
```

```markdown
⚠️ 必须确认：<待确认问题>
恢复方式：
- 用户选择：<合法选项 A/B/C>
- 默认安全行为：无确认时保持只读或停止写入
- 下一步：按用户选择执行对应分支
```

- `recovery/no-vague-fix`：不得只写“修复后继续”“联系用户”等泛化恢复方式；必须让下一位 Agent 能执行或转述。
- `recovery/link-to-source`：若 recovery 依赖详细规范，应链接到对应 `references/*.md`，不复制长篇内容。
- `recovery/inline-shorthand`：**规范文件**（SKILL.md / `references/*.md` / `templates/*.md`）的短门控条目允许**行内或紧邻下一行**的 `恢复方式：<具体动作>` 单字段简写（动作仍须满足 `no-vague-fix`）；**运行时输出**（⛔/⚠️ 触发的阻塞报告、yaml-summary `blockers` 字段）禁用简写，必须使用上方完整模板（四字段）。两种形态不互替。

## 8. realign / spec_version SSOT 引用

### 最小共性

- `realign/policy-reevaluation`：realign 表示规范升级后的 policy re-evaluation，不等同于中断续做。
- `realign/frontmatter-source`：A/B 类产物通过 frontmatter 的 `spec_version` 与 skill 当前常量比较来识别 legacy / drift / current。
- `realign/current-constant-location`：当前 `spec_version` 常量放在各 skill 的 `references/realign.md` 顶部“当前 spec_version”小节。
- `realign/migration-matrix-location`：版本差距与迁移项放在各 skill 的 `references/realign.md` Migration Matrix。
- `realign/no-business-rewrite`：realign 只补齐规范结构差距，不新增或修改业务内容。
- `realign/idempotent`：二次运行无新差距应 no-op。

### spec_version bump

- `realign/bump-required-structure`：修改模板必填章节、字段、结构或硬校验规则时，必须 bump `spec_version`。
- `realign/template-frontmatter-minimum`：A/B 类产物模板的 frontmatter 最小字段为 `generated_by` / `spec_version` / `generated_at`（`updated_at` 等可选）；字段语义以本条为权威，各模板只保留 yaml 字段块 + 一行指针，不重复解释字段用途。
- `realign/no-bump-copyedit`：仅改文案措辞、参考链接、交互步骤顺序时，不 bump。
- `realign/bump-sync-three-places`：bump 时同步更新 `references/realign.md` 当前常量、Migration Matrix、模板 frontmatter 示例。
- `realign/restructuring-confirm`：restructuring 级差距必须 AskUserQuestion 逐项确认。

### 升级入口统一

- `realign/single-entry`：所有文档体系升级与健康度审查动作统一通过 `/ms-pipeline realign [--scope=<spec|prd-mapping|health>]` 入口，不再以散落 flag 形式暴露给用户。
- `realign/scope-enum-authority`：scope 枚举白名单与执行接口指针位于 `skills/ms-pipeline/references/realign.md` § scope 专用执行接口；新增 scope 需 bump `realign.md` 的 `spec_version` 并同步 Migration Matrix。当前白名单：`spec` / `prd-mapping` / `health`。
- `realign/no-direct-user-call`：各 skill 内部 `--realign` 子动作（如 `/ms-system-design --realign=layer3-only`）属编排实现细节，不作为用户面命令暴露；用户面只承认 `/ms-pipeline realign` 入口。
- `realign/deprecated-alias-one-version`:已存在的旧入口保留一个版本作为 deprecated alias，并在 SKILL.md 文档与运行时输出标注 deprecated；下一版本移除。

### 指针

- `realign/shared-contract-pointer`：跨 skill realign 共性见 `skills/ms-pipeline/references/realign.md`。
- `realign/skill-specific-pointer`：各 skill 细则见 `skills/<skill>/references/realign.md`，本文不复制具体矩阵。
- `realign/health-execution-pointer`：`--scope=health` 执行接口见 `skills/ms-pipeline/references/realign-scope-health.md`。
- `realign/prd-revision-pointer`：PRD 修订边界见 `skills/ms-prd/references/governance/prd-revision-policy.md`。

## 9. 分层记忆原则（决策 / 执行 / 数据三层分离）

> 本节是对**既有文件结构 + 现役规则**的归并命名，不新增运行时强制（与本文件头部 `status: 协议层 SSOT —— 现状提取 + 标记为 [新增] 的跨切面规则` 一致）。"不应混写"是**原则目标**，强制力来自现役 symptom rules（仅覆盖**部分**症状）+ 人工 review（**主要**承载）。

DevDocs 的"记忆"分三层，**原则上不应混写进同一文件 / 章节**：

| 层 | 内容 | v1 落点（权威位置） |
|----|------|--------------------|
| 决策层 | 为什么这么定（取舍、约束、ADR） | `02-system-design.md` 的 ADR / 设计决策 |
| 执行层 | 现在做什么、做到哪（任务、状态） | `04-dev-tasks*.md` + `.claude/rules/devdocs-state.md` |
| 数据层 | 可追溯的事实（编号、链路、矩阵） | 追溯矩阵 / traceability / 编号体系 |

- `layered-memory/v1-structural`：编号文件结构已为三层提供各自的 owner 位置（上表），原则的**结构基础已存在**；但这是位置约定，**不等于自动强制**。
- `layered-memory/symptom-rules`：现役 rule 只能捕捉**部分典型退化症状**——`state/total-size-cap`、`state/line-length-cap`（执行状态膨胀塞爆一个文件）、`design/adr-only-revision`（决策被就地改写、与正文混编）；**不能通用检测三层混写**（短决策理由塞进 state、数据明细塞进任务文件、非 ADR 章节混写都可能不触发）。把"抓文件膨胀"等同于"抓三层混写"是夸大。
- `layered-memory/review-lens`：因此三层分离**主要靠人工 review lens 承载，不是自动兜底**。审查时发现某文件同时承载两层以上内容（典型：state 文件里塞决策理由或数据明细），即提示拆到对应层。
- `layered-memory/no-auto-detection`：**不做**"关键词扫描自动判定章节混杂"——即原 health 维度 e / Plan B 检测面。该方向已**废弃**（`[废弃]`，原标 [FUTURE]）：复杂度不匹配收益，skill 宜简。**不再保留为 FUTURE 触发项**。

## 10. 工作区拓扑（inline / shell / linked）

> 本节**仅声明跨 skill 共性与指针**。完整协议正文、入口与迁移手册归 [workspace-topology](../workspace-topology/SKILL.md) —— 该维度是**仓库级事实**，不是 DevDocs 事实，故不住在本文。

- `workspace/single-entry`：工作区拓扑的唯一入口是 `/workspace-topology`（`inspect` / `reconcile` / `migrate`）。
- `workspace/default-inline`（id 沿用历史命名，语义已反转）：**`inline` 不是兜底默认，它需要正面证据。** 无声明时**问用户**定出 `mode` 与代码根（见 [workspace-topology/SKILL.md § 无声明时：问，不猜](../workspace-topology/SKILL.md#无声明时问不猜)），答案落声明后不再问。⛔ 不做自动判定——仓库形状是产品决策。已落声明的项目行为完全不变。
- `workspace/context-over-declaration`：需要代码根路径或 docs 根的 skill 从握手的 `workspace_context` 读（见 §3 `task/workspace-context`），**⛔ 不得自行读取声明文件或解析 `.gitmodules`**。
- `workspace/pointer`：协议正文（校验全表、零污染、N+1 仓提交、gitlink 排除）见 [workspace-topology/references/protocol.md](../workspace-topology/references/protocol.md)；迁移与故障处置见 [references/migration.md](../workspace-topology/references/migration.md)。

## 11. 作用域匹配（评审边界 ≥ 影响边界）`[新增]`

> 本节是**原则声明 + 人工 review lens**，不建检测器，强制力等级同 §9。它是本文**第一个规范性（而非现状提取）小节**——约束未来的门怎么设计，不只是给已有结构命名；按 `doc/two-kinds` 属「新增跨切面规则」类，故标 `[新增]`。
>
> **适用范围**：DevDocs 流程 skill（`ms-*`）+ `dev-flow`。独立 skill（`e2e-test-flow` / `prior-art-scan` / `code-quality` / `adversarial-review` 等）不在强制范围内。

与本文件的 SSOT 前提**对偶**：SSOT 约束「事实边界 ≡ 文件边界」（防同一事实散落多处）；本节约束「评审边界 ≥ 影响边界」（防决策被小于其影响的视野判定）。两者合起来是**边界对齐**。

核心命题：

> **局部最优 = 优化的作用域 < 决策的影响域。**
> 看不到影响域的门，结构上只能产出局部答案——这不是审查者不努力，是输入决定的。

- `scope/gate-coverage`：设计任何门（审查 / 验证 / 确认）时，其**观察范围必须 ≥ 被判定对象的影响范围**。典型违反：只看单任务 diff 却要判定抽象是否正确（影响域=整个模块）；只看 `02` 却要判定设计决策（影响域=`02`+`03`+`04`+代码）。
- `scope/subtraction-check`：任何"新增"决策须能回答**"从零开始还会不会加它"**。局部优化默认是加法的——每条 finding 都靠"加"来消解，无反向压力即单调增生。
- `scope/upstream-veto`：每个门必须能把问题**判回上游**，而非就地打补丁。否则上游一经放行即成公理，并被下游每一轮加固。
- `scope/task-boundary-is-source`：`04-dev-tasks` 的任务边界决定下游每个门能看到多宽，是全流程的**作用域源头**。拆分时须考虑"这样拆会不会让下游的门瞎掉"——拆错则后续所有审查注定局部。
- `scope/design-time-only`：**本准则约束「门的设计」，不约束「每次执行」**。不要求每个任务重新审视整个架构（那是成本爆炸，也是本准则最易被滥用的方向：「我在做全局优化」可正当化任意范围膨胀）。设计门时让输入覆盖判定范围；执行照旧原子、增量。
- `scope/not-delivery-granularity`：约束**判断依据**，不改**交付粒度**。仍然每任务原子提交，只是审的时候看全景。
- `scope/review-lens`：强制力主要来自人工 / agent review lens 三问——(1) 这个门看得到它要判的东西的影响范围吗？(2) 这一轮的"加"，从零开始还会加吗？(3) 问题在上游时，这个门能判回去吗？
- `scope/no-auto-detection`：**不做**"门 scope vs 影响域"的自动检测——不可 grep，硬做即以增生治增生。同 §9 `layered-memory/no-auto-detection` 结论。

## 编号标识与扫描（跨 skill）

### `CON` 标识登记 [新增]

| 项 | 内容 |
|---|---|
| 标识 | `CON-XXX`（Constraint 约束）—— **非编码类需求**：改配置 / 加资源 / 调元数据 / 改文案 / 删权限声明，没有可写测试的业务逻辑。承载上架合规、日志规约、安全基线、构建守卫 |
| 权威源 | `docs/devdocs/01-requirements.md` §6 约束表 |
| owner | `ms-requirements`（生成）+ `ms-dev-tasks`（关联） |
| 阶段映射 | `NFR-XX`（PRD）→ `CON-XXX`（DevDocs） |
| 边界 | ⛔ `CON` **不进 `F → US → AC` 链**。有用户可观测行为的需求必须走 `F+AC`，⛔ 不得写成 CON 规避 AC |
| 类别不是命名空间 | 合规 / 性能 / 日志规约 / 安全 **是 `类别` 字段的值**，⛔ 不各开编号体系 |

### `CON` 的消费边界 [新增]

> ⛔ **`CON` 是局部约定，不是全局一等公民。除上表两个 owner 外，其余 skill 不拥有 CON，因此不对它作判断。**

| 消费方 | 对 `CON` 的行为 |
|---|---|
| `ms-dev-workflow` | 任务标 `TDD 模式 = ⚪ 不适用` 时按该档执行（**字段本已存在**），⛔ 不解析 CON 的类别与语义，只执行任务卡的「测试方法 / 验收标准」 |
| `ms-verify` / `ms-sync` / `ms-test-run` / `ms-test-cases` / `ms-board` / `ms-system-design` / `health-lint` 计分 | ⛔ **既不拦也不报**。`CON` 不进它们的覆盖率、孤立判据、健康分、覆盖门 |
| `health-lint` `id-reference-check` | **仅**把 `CON-` 纳入已知编号前缀（否则会把合法引用误报为未定义编号）。这是防误报，⛔ 不是治理 |

**为什么划这条线**：把 `CON` 注入全部消费方需要改约 36 处，且同一执行事实分散在强制矩阵 / 主循环 / 子 Agent 协议 / 完成流程 / auto-mode / 模板 / CLAUDE.md，**没有单一执行 SSOT**；本仓又无 runner / CI 防止再次分歧。经 7 轮外部审查判定**不会稳定收敛**，故收回边界。

**代价（明说）**：CON 没有自动治理——没写验证方式、验证方式与守卫脚本分叉、CON 无对应任务，这些**不会被任何门发现**。它保住的是「配置类任务不编造 AC 就能挂上追溯」这一件事。

### `M` 标识登记 [新增]

| 项 | 内容 |
|---|---|
| 标识 | `M-XXX`（Milestone 里程碑）—— **逻辑组织概念**：把多个 `F-XXX` 分成可交付的段，一段做完停下来由用户实际使用验证，通过才进下一段 |
| 权威源 | `docs/devdocs/01-requirements.md` §2 功能点表的「归属里程碑」列（**唯一**）。§2.5 里程碑表只登记 `M-XXX` 与目标句，⛔ 不重复列成员 |
| owner | `ms-requirements`（划分）+ `ms-dev-workflow`（分段执行与停点） |
| 可选性 | ⛔ **不是强制概念**。按需求规模决定用不用；不划分时全流程行为与无 M 完全一致 |
| 边界 | ⛔ `M` **不进 `F → US → AC` 链**，不进追溯矩阵、不进覆盖率、不是执行单元（⛔ 无 `M-XXX` 任务指定符） |
| 解决的问题 | F 全做完、单测全过，但连起来用全是问题——「点没问题不代表线没问题」 |

### `M` 的消费边界 [新增]

> ⛔ **`M` 是组织标签，不是追溯对象。除上表两个 owner 外，其余 skill 不拥有 M，因此不对它作判断。**

| 消费方 | 对 `M` 的行为 |
|---|---|
| `ms-verify --readiness` | **仅**检出「跨 M 反向依赖」（M1 的任务依赖 M2 的任务）并提示重划——那是划分错误，⛔ 不自动兜底。其余维度不看 M |
| `ms-sync` | 归档时 **M 未验收通过的 F ⛔ 不归档**（否则唯一成员源先于验收消失）；⛔ 不维护 M 的状态，人验事实住在检查点 |
| `ms-backlog` | 接受 `M-XXX` 作 `source_id`，承接该段冒出、尚无任何编号的新需求 |
| `ms-test-run` / `ms-test-cases` / `ms-board` / `ms-system-design` / `health-lint` 计分 | ⛔ **既不拦也不报**。`M` 不进它们的覆盖率、孤立判据、健康分、覆盖门 |
| `health-lint` 已知编号前缀 | ⛔ **不纳入**。已核实 `M-001` 不与任何现有前缀词边界匹配，既不误报也不漏报；纳入等于把 M 提成治理对象，与「逻辑组织概念」定位相悖。代价：`M-002` 打成 `M-020` 无人发现 |

**为什么划这条线**：`M` 若进追溯链，`F → US → AC` 要变成 `M → F → US → AC`，全部下游消费方都要改——这正是 `CON` 那次收回边界的同一个坑。它只需在两个 owner 之间成立。

### `id/prefix-consumption-contract` [新增]

**新开一个项目级追溯前缀，必须同时写下它的消费契约。⛔ 不禁止局部标识——禁的是"造了编号却没人消费"。**

`health-lint` `id-reference-check` 的白名单是 `F` / `US` / `AC` / `CON` / `T` / `T-RF` / `ADR` / `INS` / `BUG` / `UT` / `IT` / `E2E` / `Journey`（`M` 已登记但 ⛔ 故意不入，理由见上节）。**白名单外的编号 `health/dead-link` 不查、`state/max-id-stale` 不推上界**——这是覆盖边界，⛔ 不等于"白名单外的编号非法"。

新开前缀时，在**产物内首次定义处**写清三件事：

| 项 | 内容 |
|---|---|
| 作用域 | 项目级（全局唯一、可跨文件引用）还是宿主级（`§4.2 R-3` 这类，⛔ 不跨宿主引用）|
| 消费方 | 谁读它。**至少一个真实消费方**——没有消费方的编号是纯噪音，不如写成散文 |
| 检查归属 | 进不进 `dead-link`。要进 ⇒ 按 `CON` / `M` 的形制在本文登记 + 进白名单；不进 ⇒ 明说"由人工核对"，接受它无机器校验 |

⛔ **不得把「用什么工具验证」当作分类依据。** `git diff` / PR 评审 / `grep` 只是执行手段；对象是行为需求就走 `F+AC`，是非编码需求才走 `CON`（`ms-dev-tasks` SKILL.md:187~191 的既有边界）。⛔ 也不得反过来因为"能自动化"就把一条人工判据升格成新测试类型——`tar-rubric.md` 的可测试判据原文即「可通过自动化**或手动**测试验证」。

> **为什么只要契约、不要禁令**：前缀的语义看名字猜不出来。本仓实测：`ai-code` 的 `R-1~R-4` 看着像风险清单，实为重定向安全判定规则（origin 严格相等 / 编译期白名单前缀 / 拒绝残留百分号编码，`02-system-design.md:395`）；`B-10` 看着像并行批次，实为"白名单放宽 + 回归范围"的登记条目（`:1467`）；`GAP-` / `BLK-` 是**当前闭环内**的阻塞事实，与 `ms-backlog` 的"暂时不进入当前闭环"暂缓池语义不同。⇒ 一张"按前缀名归并到既有槽位"的映射表会逐条判错，把设计规则塞进 backlog。
>
> 真实缺陷不是"存在自造前缀"，而是**造完没有消费契约**：`ai-code` 的 `D-`(853，决策) 与 `ADR-`(282) 并存，自造那套引用量是官方的 3 倍，两者边界从未写下。⇒ 治理点在"说清楚谁消费"，不在"不许造"。
>
> ⛔ **不写"单字母前缀一律不可用"**：`grep -owE 'T-[0-9]+|C-[0-9]+'` 对 `AC-001 UT-001 IT-001 T-001 C-001` 只输出 `T-001` / `C-001`，无幻影——`-w` 已经解决字面包含。[[id/scan-word-boundary]] 挡的是**裸 `grep -o`**，不是单字母本身。单字母的真实代价是可读性（`§0.2 E-10` 必须带宿主才不歧义），那是作用域字段该说的事。
>
> 机器侧只有一条**非阻断 ⚠️ 提示** `health-lint` `id/unknown-prefix`：报出白名单外的前缀候选供人工判断消费边界，⛔ 不判违规、⛔ 不给归并建议。
>
> 与 [[confirm/scope-inflation]] 的边界：本条**只**要求声明契约。把它扩成封闭集合 + 归宿表 + 禁令，正是那条规则里「症状被升级成体系缺少某个一等公民」的形态——本条第一版就是这么写的，经外部审查逐条证伪后收回。
>
> 消费方：产出编号的 skill（`ms-requirements` / `ms-system-design` / `ms-dev-tasks` / `ms-test-cases` / `ms-bugfix` / `ms-insights`）+ `health-lint` `id/unknown-prefix`。

### `id/scan-word-boundary` [新增]

**扫描编号必须整词匹配 + 数值序比较。**

```sh
# ✅ 正确：-w 整词匹配（'-' 非词构成字符），-n 数值序
grep -owhE 'T-[0-9]+' <files> | sed 's/T-//' | sort -n | tail -1

# ⛔ 错误：裸 -o + 字典序
grep -oh 'T-[0-9]\{2\}' <files> | sort | tail -1
```

两类失效，**都已在本仓实测复现**：

| 陷阱 | 症状 |
|---|---|
| **前缀字面包含** | `UT-001` / `IT-001` 内含 `T-001` → 裸 `grep -o 'T-[0-9]+'` 产出幻影 `T` 编号。同理 `AC-001` 内含 `C-001`（这也是制品型标识取 `CON` 而非 `C` 的原因之一）|
| **字典序 ≠ 数值序** | `sort \| tail -1` 会判 `T-9 > T-106` |

⛔ **前后单边界的写法同样不可用**：`(^\|[^[:alnum:]_])T-[0-9]+([^[:alnum:]_]\|$)` 会**消耗边界字符**，`T-01,T-02,T-03` 只匹配到 `T-01` 与 `T-03`（实测）。用 `-w`。

> **为什么进本文而 `skip/numbering-unique` 仍成立**：那条跳过的是**续编策略**（各对象的来源与 SSOT 不同，确实不能统一）；本条是**扫描方法的机械陷阱**，对每种编号类型完全一致，且语言与领域中立。两者不冲突。
>
> 消费方：`ms-requirements`（编号续编，含 `M-XXX`）/ `ms-dev-tasks` / `ms-bugfix` / `ms-test-cases`（编号续编）+ `agent-memory` devdocs-state 模板（推导命令）+ `health-lint` `id-reference-check` / `state/max-id-stale`（上界推导）。

## 差异点与跳过项

### 已标注语义差异点

- `diff/readonly-generated-output`：`ms-codebase-insight` 是只读分析，但会写自身分析产物；`ms-onboard` 同时有 `--read` 与 `--update`，不能统一成“永不写入”。
- `diff/numbering-scope`：编号唯一/续编规则在 FR、F、US、AC、UT、IT、E2E、T、INS 等对象间来源和续编策略不同，不能在本文强行统一。

### 本次跳过的规则

- `skip/numbering-unique`：编号唯一/续编**策略**只保留指针，不提升为共享细则；理由是 PRD 编号、DevDocs 编号、测试编号和任务编号各有不同 SSOT 与链路。
  > ⚠️ 不要与 `id/scan-word-boundary`（§编号标识与扫描）混淆：那条管**怎么扫**（机械陷阱，各类型一致），本条跳过的是**扫到之后按什么策略续编**（各类型不同）。
- `skip/sprint-contract`：Sprint Contract 不提升；理由是 `ms-dev-workflow` 私有执行契约。
- `skip/verify-scoring`：verify P 级评分、health score 不提升；理由是 `ms-verify` 私有评估模型。

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
4. **每条被本任务满足的需求至少 1 条独立证据**(不能只靠实现代码自证;无则显式豁免)：
   - 行为型 `AC` → 独立行为证据(测试 / `--ui --live` 截图 / 显式豁免记录)
   - 制品型 `CON`（`档 = 可执行`）→ **验证命令红→绿两次实际输出**
   - 制品型 `CON`（`档 = 人工`）→ **人工核对留证**：谁、何时、观察到什么。⛔ 不接受「已检查」三字
   > 原文只写「行为型 AC」，`CON` 引入后会**落出证据要求之外**——制品型任务本来最容易只靠"我改了配置"自证。
5. 受影响测试后置 `/ms-test-run --affected`

### review_pending(任务状态)
- 含义:fast/guarded 任务代码已提交(Commit 1 已落盘),但延后的独立审查尚未做,**状态 ≠ 已完成**。
- 与 `INT_UNRESOLVED`/`EXT_UNRESOLVED`/`postcheck_pending` 独立:后者是"审过但未通过 / 未放行阻塞态",`review_pending` 是"尚未审,已提交待集中审"。
- 任务台账字段(`04-dev-tasks.md` 条目):`batch: <id>` / `due: <sprint:ID | YYYY-MM-DD>` / `pending_reason: deferred-fast | deferred-guarded`。⛔ 不写 commit 尾注——主体是任务不是 commit。
- 清算入口:`/ms-verify --review-drain`(批/sprint 边界集中跑延后审查)。

### 独立审查状态机枚举（canonical 值域；跨 skill 协议）

| 枚举 | 值域 | 放行态 | 语义 |
|------|------|--------|------|
| `int_review_state` | `INT_REVIEWED` / `INT_UNRESOLVED` | `INT_REVIEWED` | Phase 1~3 内置角色演绎结果；UNRESOLVED=审查未通过或综合报告缺失 |
| `ext_review_state` | `EXT_REVIEWED` / `EXT_UNRESOLVED` / `EXT_BLOCKED` | `EXT_REVIEWED` | Phase 4 外部对抗审查结果；UNRESOLVED=未通过或 L2 证据缺失，BLOCKED=熔断终态 |

- `enum/no-extension`：消费方（ms-verify / adversarial-review / dev-workflow 全部 references）不得扩展枚举值或私有化语义。
- `enum/no-skip-channel`：**审查不提供跳过通道**。原 `INT_PENDING`/`EXT_PENDING`（对应已删除的 `--skip-review-reason` / `--skip-external-review-reason`）与 `*_UNRESOLVED` 在阻塞性和恢复动作上完全等价，差别仅一句 reason（写 commit body 即可），保留只会把"现在必须做"改造成"事后要补的债"。
- `enum/non-pass-blocks`：非放行态一律 ⛔ 阻塞 audit 档 Commit 1；fast/guarded 延后语义见上方 review_pending。
- 判定规则（真值表/优先级/L2 证据协议/T1→T2 降级链）为**执行细节**，权威见 [dev-workflow verification-flow.md](../ms-dev-workflow/references/verification-flow.md)；本节只锁定值域与放行语义。

### 任务台账协议（流程状态的唯一载体；跨 skill 字段语义）

⛔ **流程状态不写 commit 尾注。** commit 只承载「一个不知道 DevDocs 存在的维护者能读懂并用上」的信息；批次 ID、降档理由、豁免登记对他是纯噪音，且这些字段的语义主体是**任务**不是 commit。

| 字段 | 适用 | 语义 |
|---------|------|------|
| `commits` | Commit 1 落盘后 | `<repository>@<full-sha>`，可多条；考古索引，⛔ 不作门控依据 |
| `batch` / `due` / `pending_reason` | fast/guarded 延后必填 | 见上方 review_pending |
| `ext_review_state` | audit Phase 4 必填 | 由 L2 yaml 派生 |
| `skip_trace_reason` | 单任务 `--skip-trace` | 跳过后置 trace 校验的原因 |
| `exploration_mode` | 探索模式 | `true` + 证据/豁免原因登记 |
| `profile_downgrade_reason` | 带理由降档时 | 降档理由（升档不需要） |

> 字段呈现与填写时机见 [dev-workflow SKILL.md §任务台账](../ms-dev-workflow/SKILL.md)；消费方：`/ms-verify --review-drain`（按 `batch`/`due` 清算）、断点续做 Step 1.5 证据复核。
>
> ⛔ **门控状态绑任务编号，考古索引绑 commit。** squash / rebase 改 hash 时 `commits` 失效（回到代码事实重建），门控不受影响。
