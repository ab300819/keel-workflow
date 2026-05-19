---
title: 共享约束 SSOT
status: 现状提取，不引入新规则
scope: 跨 skill 协议层共性
related:
  - AGENTS.md（yaml-summary-v1 原始定义）
  - skills/prd/references/governance/prd-index-ssot.md（PRD 编号 SSOT）
  - skills/pipeline/references/layout/*（DevDocs 治理 SSOT）
generated_at: 2026-05-18
spec_version: shared-constraints.v1
---

# 共享约束 SSOT

本文是 T-106 识别的重复规则的共享 SSOT 提取，用于后续 skill 引用切换。

- `doc/status-extraction`：本文只整理仓库已有重复规则，不引入新的 status、标记、流程类别或执行语义。
- `doc/no-immediate-impact`：现有 `skills/*/SKILL.md` 不会因本文创建而自动改变；引用切换是后续独立任务。
- `doc/reference-over-copy`：已有详细 spec 优先保留在原位置，本文只声明协议层共性与指针。
- `doc/private-rule-boundary`：skill 私有规则不得提升到共享层；例如 Sprint Contract、verify P 级评分、具体 layout 迁移算法仍归各自 skill 或 references 文件维护。

## 1. 门控标记 SSOT

### 标准标记

| rule_id | 标记 | 标准语义 | 典型触发条件 | 恢复方式要求 |
|---|---|---|---|---|
| `gate/marker-set` | `⛔ 禁止继续` / `⚠️ 必须确认` / `ℹ️ 建议` | 共享层只承认这三类门控标记 | 所有 ms- skill 的阶段边界、确认点、建议项 | 不得扩展新标记，除非另开 spec bump |
| `gate/blocker-semantics` | `⛔ 禁止继续` | 硬阻塞；必须解除后才能继续 | 阶段边界、P1 阻塞、安全不变式、测试未通过不得提交等 | 必须写明可执行恢复方式 |
| `gate/confirm-semantics` | `⚠️ 必须确认` | 继续前需要用户确认或选择 | Inversion 问询、方案确认、不可自动判断的归类/迁移 | 必须写明等待用户确认的内容 |
| `gate/advice-semantics` | `ℹ️ 建议` | 推荐但可跳过，不阻塞当前流程 | P2/P3 建议、可选验证、后续优化 | 可给出恢复/后续动作，但不强制 |

### 硬规则

- `gate/recovery-required`：每个 `⛔ 禁止继续` 必须附带 recovery；缺 recovery 的 `⛔` 视为不合格门控。
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
allowed_paths: []
expected_output: yaml-summary-v1
```

- `task/handshake-minimum`：`task`、`mode`、`inputs`、`allowed_paths`、`expected_output` 是推荐最小握手字段。
- `task/mode-honored`：子 Agent 不得越过传入 `mode`；`read` / `dry-run` 不得产生写入。
- `task/blocker-propagation`：子 Agent 返回 `failed` 或含 `⛔` blocker 时，编排层必须停止对应分支并 surface recovery。

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
- `future/use-future`：命令入口、runtime 检测、迁移执行、自动修复、CI 集成等尚未实现时，必须标 `[FUTURE]`。
- `future/no-runtime-assumption`：`[FUTURE]` 不阻塞阅读 spec，但阻塞实际调用；调用时应 fail-safe 或提示执行逻辑待落地。
- `future/source-of-truth`：layout 系列 FUTURE 执行状态以 `skills/pipeline/references/layout/docs-layout-migration.md` 的“执行接口落地状态（FUTURE）”为指针，不在本文复制。

### 差异提示

- `future/difference-layout-id-trace`：layout/id/trace 双轨包含大量 skill 私有上下文；共享层只统一 `[FUTURE]` 标注语义，不统一具体迁移算法、编号前缀或 trace 写入规则。

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

- `recovery/blocker-required`：每个 `⛔` 必须附 recovery。
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
- `realign/no-bump-copyedit`：仅改文案措辞、参考链接、交互步骤顺序时，不 bump。
- `realign/bump-sync-three-places`：bump 时同步更新 `references/realign.md` 当前常量、Migration Matrix、模板 frontmatter 示例。
- `realign/restructuring-confirm`：restructuring 级差距必须 AskUserQuestion 逐项确认。

### 升级入口统一

- `realign/single-entry`：所有文档体系升级动作统一通过 `/ms-pipeline realign [--scope=<spec|layout|prd-mapping>]` 入口，不再以散落 flag 形式暴露给用户。
- `realign/scope-enum-authority`：scope 枚举白名单与执行接口指针位于 `skills/pipeline/references/realign.md` § scope 专用执行接口；新增 scope 需 bump `realign.md` 的 `spec_version` 并同步 Migration Matrix。
- `realign/no-direct-user-call`：各 skill 内部 `--realign` 子动作（如 `/ms-system-design --realign=layer3-only`）属编排实现细节，不作为用户面命令暴露；用户面只承认 `/ms-pipeline realign` 入口。
- `realign/deprecated-alias-one-version`:已存在的旧入口（如 `/ms-pipeline realign --docs-layout`）保留一个版本作为 deprecated alias，并在 SKILL.md 文档与运行时输出标注 deprecated；下一版本移除。
- `realign/iteration-policy-internal`：`ms-iteration-policy` 是横切治理 skill，由 `/ms-pipeline realign --scope=layout` 编排调度，不作为用户直接调用入口；详见 `skills/iteration-policy/SKILL.md`。

### 指针

- `realign/shared-contract-pointer`：跨 skill realign 共性见 `skills/pipeline/references/realign.md`。
- `realign/skill-specific-pointer`：各 skill 细则见 `skills/<skill>/references/realign.md`，本文不复制具体矩阵。
- `realign/layout-pointer`：layout/id/trace 治理见 `skills/pipeline/references/layout/*`。
- `realign/layout-execution-pointer`：`--scope=layout` 执行接口见 `skills/pipeline/references/realign-scope-layout.md`。
- `realign/prd-index-pointer`：PRD 编号 SSOT 见 `skills/prd/references/governance/prd-index-ssot.md`。

## 差异点与跳过项

### 已标注语义差异点

- `diff/layout-id-trace`：layout/id/trace 双轨在不同 skill 中混有读写布局、编号前缀、trace 来源等私有上下文；本文只统一 `[FUTURE]` 与“引用而非复制”的协议层表达。
- `diff/readonly-generated-output`：`ms-codebase-insight` 是只读分析，但会写自身分析产物；`ms-onboard` 同时有 `--read` 与 `--update`，不能统一成“永不写入”。
- `diff/numbering-scope`：编号唯一/续编规则在 FR、F、US、AC、UT、IT、E2E、T、INS 等对象间来源和续编策略不同，不能在本文强行统一。

### 本次跳过的规则

- `skip/numbering-unique`：编号唯一/续编只保留指针，不提升为共享细则；理由是 PRD 编号、DevDocs 编号、测试编号和任务编号各有不同 SSOT 与链路。
- `skip/layout-algorithm`：layout 拆分、aliases、traceability 写入、SSOT lint 算法不提升；理由是已有 `skills/pipeline/references/layout/*` 专门治理。
- `skip/sprint-contract`：Sprint Contract 不提升；理由是 `ms-dev-workflow` 私有执行契约。
- `skip/verify-scoring`：verify P 级评分、health score 不提升；理由是 `ms-verify` 私有评估模型。
