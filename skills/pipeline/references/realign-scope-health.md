# Realign Scope Health（文档健康度主动审查）

> 用户入口：`/ms-pipeline realign --scope=health [--target=<path>] [--dry-run|--apply] [--fix=<rule_id>]`
> 默认 `--dry-run`（只输出健康度报告）。

## 定位

本文件定义 `--scope=health` 的执行接口，让 LLM 能按统一入口对 DevDocs 文档体系做**主动健康度审查**，覆盖四大维度并把分散在 ms-verify / ms-sync / ssot-lint 的检查能力收敛为单一报告。

与 `--scope=spec`（spec_version 差距补齐）/ `--scope=layout`（layout.v1→v2 迁移）/ `--scope=prd-mapping`（PRD ↔ DevDocs 映射）正交：health 关注**当前规范下产物是否健康**，不做规范升级、不做目录迁移、不做 PRD 映射重组。

> **推/拉两个触发点**（解决"规则实装但没人跑"的断层）：
> - **拉（全量）**：用户显式 `/ms-pipeline realign --scope=health` —— 本文件定义的完整 4 维扫描。
> - **推（轻量探针）**：ms-pipeline 路由入口的 health drift 探针（≤2s，仅 stat `devdocs-state.md`），命中则一行非阻塞提示来跑全量。探针**不挂 `.devdocs-realign-ack`**（health 是持续监控信号非一次性升级决策），按 `.health-baseline.yml` 重评估。探针规则见 [realign.md § health drift 探针](realign.md#health-drift-探针阶段-3与-schema-drift-并列但语义不同)。
> - **二级强化**：`/ms-pipeline close`（周期收尾）若探针命中 blocker 级，建议顺带跑一次全量 health。

引用关系：

| 文件 | 本 spec 的使用方式 |
|------|-------------------|
| [realign.md](realign.md) | 继承 realign 安全不变量、yaml-summary-v1 汇总方式 |
| [health-lint-implementation.md](health-lint-implementation.md) | 调用 5 条 [新增] lint rule（state/total-size-cap / state/line-length-cap / state/forbidden-content / health/dead-link / design/adr-only-revision）；rule 清单以该文件 Rule 集表为权威，layout.v1+v2 通用 |
| [layout/ssot-lint-implementation.md](layout/ssot-lint-implementation.md) | layout.v2 启用后追加 `ssot/no-restatement` 等 [FUTURE] rule 到维度 d（数量与清单以该文件 rule 表为权威，当前 12 条）；v1 项目跳过 |
| `../../sync/references/health-scoring.md` | 6 类偏差评分（layout.v1 legacy）作为子项 |
| `../../verify/SKILL.md` | 调用 `--schema-drift` / `--docs` / `--impl` 已有能力 |
| `../../agent-memory/templates/devdocs-state-template.md` | 占位 prose 边界约束（forbidden 字段） |
| `../../_shared/constraints.md` | 继承 `⛔` / `⚠️` 门控、AskUserQuestion、yaml-summary-v1 |

## 四大健康维度

| 维度 | 检查内容 | 依赖能力 | 状态 |
|------|----------|----------|------|
| a 结构正确性 | frontmatter 必填字段、spec_version 当前性、设计文档 ADR ↔ 正文同期修订 | ms-verify --schema-drift（[现状]）+ `design/adr-only-revision`（[新增]）| [新增] |
| b 索引/链接正确性 | 编号引用文件存在性 + 追溯矩阵完整性 | ms-sync trace（[现状]）+ `health/dead-link`（[新增]）| [新增] |
| c 过大文档识别（含 state-hygiene 子项）| size 三档（byte 阈值 / 单行长度）+ state-hygiene（内嵌禁用模式）| `state/total-size-cap` + `state/line-length-cap` + `state/forbidden-content`（[新增]）| [新增] |
| d SSOT 遵从 | 占位/索引不复制权威源内容 | `ssot/no-restatement` | [FUTURE] (layout.v2 才启用) |

> 本轮（layout.v1 项目可立即用）：维度 a/b/c 实装。维度 d 在 layout.v1 下报 `skipped: requires layout.v2 ssot-lint`；layout.v2 启用后自动激活。
>
> **原维度 e「三层分离自动检测」已废弃**（不再保留为 FUTURE）：三层分离（决策/执行/数据）作为原则在 layout.v1 已由编号文件结构 + `state/*`、`design/adr-only-revision` 症状规则承载，无需独立的关键词扫描维度；审查时作**人工尺子**使用。权威见 [_shared/constraints.md §9 分层记忆原则](../../_shared/constraints.md#9-分层记忆原则决策--执行--数据三层分离)。
>
> [新增] rule 的算法与输出 schema 见 [health-lint-implementation.md](health-lint-implementation.md)（rule 清单与维度归属以该文件 Rule 集表为权威）。

## CLI 兼容

| 命令 | 行为 |
|------|------|
| `/ms-pipeline realign --scope=health --dry-run` | 默认。扫描 + 评分，**业务产物零写入**，报告写入 `.health-report.md`（唯一例外）|
| `/ms-pipeline realign --scope=health --apply` | 执行可自动修复项；不可自动项以 ⚠️ 列出，等待 AskUserQuestion |
| `/ms-pipeline realign --scope=health --fix=<rule_id> --dry-run` | 仅扫描指定 rule，不修复 |
| `/ms-pipeline realign --scope=health --fix=<rule_id> --apply` | 仅修复指定 rule 的违规项（例：`--fix=state/total-size-cap`）|
| `/ms-pipeline realign --scope=health --target=<path>` | 指定项目根或 `docs/devdocs/` |
| `/ms-pipeline realign --scope=health --baseline-init` | 初始化 baseline（存量项目首次落地用）|
| `/ms-pipeline realign --scope=health --changed-only` | 仅扫 `git diff HEAD` 变更行（增量模式，大仓推荐）|
| `/ms-pipeline realign --scope=health --since-baseline` | 与 baseline 比对，只报告新增违规 |
| `/ms-pipeline realign --scope=health --no-report-file` | 严格 dry-run；不写 `.health-report.md`，只输出 stdout |

**语义规则**：
- 未传 `--dry-run` 也未传 `--apply` → 一律视为 `--dry-run`（安全默认）。
- `--fix=<rule_id>` 必须配 `--dry-run` 或 `--apply`；单独 `--fix=` 视为 `--fix --dry-run`。
- `--dry-run` 的"零写入"指**业务产物零写入**；`.health-report.md`、`stdout` 输出不算业务产物。

`--target` 归一化沿用 `--scope=layout` 同款规则（详见 [realign-scope-layout.md](realign-scope-layout.md) § "--target 归一化"）。

## Dry-run 阶段

### 只读边界

dry-run **不写入任何业务产物**（不动 docs/devdocs/*.md、不动 traceability.yml、不动 aliases.yml、不动 git）。唯一允许写入的文件是：

```text
docs/devdocs/.health-report.md
```

若用户要求严格零写入（如 CI dry-run-strict 模式），可加 `--no-report-file`，只输出报告到 stdout；后续 `--apply` 必须重新生成 `.health-report.md`。

### 扫描范围

| 来源 | 用途 |
|------|------|
| `docs/devdocs/**/*.md` | 主扫描对象（A 类主链路 + B 类旁路） |
| `.claude/rules/devdocs-state.md` | 维度 c 中 `state-size` / `state-forbidden-content` 专属扫描 |
| `docs/prd/**/*.md`（若存在） | 维度 b 死链扫描（编号跨 PRD 引用） |
| `traceability.yml` / `aliases.yml`（若存在） | 维度 b 编号引用核对 |

### 执行步骤

1. 归一化 `repo_root` 与 `docs_root`。
2. 调用 `/ms-verify --schema-drift`（只读），获取维度 a 数据。
3. 调用 `/ms-sync` audit 计算（只读复用 `health-scoring.md`），获取既有 6 类偏差作为维度 b 子项。
4. 执行 health-lint 5 条 [新增] rule（详见 [health-lint-implementation.md](health-lint-implementation.md)）：
   - `state/total-size-cap` + `state/line-length-cap` + `state/forbidden-content` → 维度 c
   - `health/dead-link` → 维度 b
   - `design/adr-only-revision` → 维度 a（基于 git 历史扫描最近 30 天 commit）
5. 若项目为 layout.v2 → 追加 ssot-lint 调用获取维度 d 数据；layout.v1 → 维度 d 报 `skipped: requires layout.v2`。
6. 加权评分输出（见下方"评分契约"）。
7. 写入 `.health-report.md`，stdout 打印摘要 + 下一步建议命令。

### Health Report 文件契约

`.health-report.md` 正文包含 yaml 代码块 + Markdown 报告，yaml 块必须包含：

```yaml
report_schema: realign-health-report.v1
scope: health
target_layout: layout.v1 | layout.v2
repo_root: <absolute-or-relative-path>
docs_root: docs/devdocs
generated_at: <iso-timestamp>
source_git_commit: <sha>           # 生成报告时 HEAD commit
generated_from_dirty_state: <bool> # 生成时工作区是否有未提交变更
report_hash: <sha256>              # 上述全部字段（除 report_hash 本身）的序列化 sha256
total_score: <0.00-100.00>

dimensions:
  a_structure:
    score: <0-100>
    schema_drift_count: <N>
    legacy_count: <N>
    adr_only_revision_commits: []  # design/adr-only-revision 命中的 commit 列表
    findings: []
  b_index_links:
    score: <0-100>
    dead_links: []
    orphan_ids: []
    trace_gaps: []
  c_oversize:
    score: <0-100>
    violations:
      - rule_id: state/total-size-cap | state/line-length-cap | ssot/current-md-size
        file: <path>
        actual: <value>
        threshold: <value>
        severity: blocker | warning
        route_to_scope: health | spec | layout | prd-mapping  # health scope 是否能直接修复
        route_recommended: <next 命令字符串，如 "/ms-pipeline realign --scope=layout --apply">
        route_note: <可选；解释为何跨 scope，如 "current.md >1500 拆分由 layout scope 处理">
  d_ssot:
    score: <0-100>
    restatement_findings: []

auto_fixable:
  - rule_id: <rule>
    file: <path>
    proposed_action: <describe>

manual_decisions:
  - id: <stable-id>
    kind: archive-target | restatement-extract | state-prose-trim
    prompt: <AskUserQuestion prompt>
    options: []
    status: pending
```

字段规则：

- `auto_fixable` 列出 `--apply` 可直接处理的项。
- `manual_decisions` 必须在 `--apply` 前完成 AskUserQuestion，否则 ⛔。
- `total_score` 保留两位小数；权重见下。
- 每条 violation 必须含 `route_to_scope`；非 `health` 路由的违规由 health 仅报告、不修复，由 `next_recommended` 引导对应 scope。

`route_to_scope` 取值规则：

| 违规 rule | route_to_scope | 修复路径 |
|----|----|----|
| `state/*`（3 条）/ `health/dead-link`（手动修复）/ `design/adr-only-revision` | `health` | health scope `--apply` 直接处理 |
| `ssot/*` (`current-md-size` / `file-size-cap` / `modules-size-cap`) | `layout` | 拆分走 layout scope |
| `schema_drift_count > 0` | `spec` | 补 frontmatter 走 spec scope |
| 跨 PRD 死链 | `prd-mapping` | 修复 mapping 走 prd-mapping scope |

### 评分契约

权重随激活维度自动归一：

| 场景 | a | b | c | d |
|------|---|---|---|---|
| layout.v1（本轮可用）| 0.30 | 0.40 | 0.30 | — |
| layout.v2（d 启用）| 0.25 | 0.30 | 0.25 | 0.20 |

- 单维度评分 = (1 - violations_count / total_checks) × 100；无 violations 时为 100。
- 跳过维度（status: skipped）权重不分摊到其他维度，从总和中剔除；其余维度按比例归一。
- `total_score` < 60 时报告头部以 ⚠️ 提示"建议立即处理"；< 40 时 ⛔ 提示"健康度不达标"。

## AskUserQuestion 触发点

| 决策 | 触发条件 | 问询要求 |
|------|----------|----------|
| 归档目标 | `state/total-size-cap` 违规 + 需要把内容拆出 | 展示拟归档段落 + 拟目标文件（task / ADR / archive），3 个候选 |
| 引用提取 | `ssot/no-restatement` 检出长段落复制 | 展示原段落 + 权威源路径，确认替换为引用 |
| state prose 修剪 | `state/forbidden-content` 检出 commit/LOC/codex 分数 | 展示违规片段 + 拟保留占位形态，确认动作 |
| 跨产物影响 | 维度 b 死链涉及多个产物 | 展示受影响产物列表，确认是否一并修复 |

`--apply` 遇到 `pending` 决策必须暂停问询；headless 场景不得跳过，只能返回 `status: partial` 或 `interrupted`。

## Apply 阶段

### 入口前置条件

`--apply` 必须满足：

1. 工作区洁净。
2. 存在 `.health-report.md` 且 `report_schema=realign-health-report.v1`。
3. **report 防 stale**（参考 `.realign-plan.md` 的 `plan_hash` 设计）：
   - `report_hash` 校验通过（重算 sha256 与文件中存储值一致）。
   - `source_git_commit` 等于当前 HEAD（或差距 ≤ 由 `--max-commits-drift=N` 控制，默认 0）。
   - `generated_from_dirty_state=true` 时必须 `⚠️ 必须确认`，提示用户报告基于未提交变更，可能与当前状态不一致。
4. `manual_decisions` 中 `status=pending` 项已全部解答（或显式 `--skip-manual`，仅修复 `auto_fixable`）。

任一失败 → `⛔ 禁止继续`，错误码 `health/report-stale`。恢复方式：重新 dry-run（生成新 report）或补齐决策。

### 修复路径

按维度顺序、每项独立 commit：

#### Phase 1：维度 c 自动归档（state-size / size-cap）

- 对 `state/total-size-cap` 违规：将超长行按 task ID 拆出，明细落到 `04-dev-tasks-pNN.md` 或 ADR 对应文件（依据 manual_decision），主文件保留 ≤200 字符占位。
- 对 `ssot/current-md-size` 违规：触发 layout.v2 拆分（委托 `--scope=layout`），本 scope 不直接执行 v1→v2 迁移。
- `state/line-length-cap` 违规：换行重排，不删除内容。

#### Phase 2：维度 d 引用替换（no-restatement）

- 将复制段落替换为指向权威源的引用链接。
- 保留原段落首句作为锚点摘要（≤100 字符）。

#### Phase 3：维度 b 死链处理

- 死链 → 用户确认是否补建目标文件 / 删除引用 / 标 `[FUTURE]`。
- 孤立编号（仅在代码或仅在文档）→ 写入 `traceability.yml` 或在产物中补登记。

#### Phase 4：维度 a 结构补齐

- 委托 `/ms-pipeline realign --scope=spec`（已有路径），不在本 scope 直接 bump frontmatter。

### Apply 失败处理

- 任一 Phase ⛔ → 暂停，提示 `git reset --hard <pre-apply-commit>` 或追加修复 commit。
- 不允许 amend 已提交 Phase 历史。

## 输出契约

`--dry-run` 与 `--apply` 完成后均返回 yaml-summary-v1：

```yaml
skill: ms-pipeline
status: success | partial | failed | interrupted
summary:
  headline: "health audit completed, score=<X>"
  details:
    scope: health
    total_score: <0.00-100.00>
    dimensions_scored: [a, b, c]      # layout.v1；v2 追加 d
    dimensions_skipped: [d]            # layout.v1 下 d 需 v2 ssot-lint
    violations_by_severity:
      blocker: <N>
      warning: <N>
    auto_fixed: <N>
    manual_pending: <N>
    report_file: docs/devdocs/.health-report.md
blockers: []
output_files:
  - docs/devdocs/.health-report.md
new_ids: {}
next_recommended:
  skill: ms-pipeline
  args: <按违规分布动态生成，规则见下>
```

**`next_recommended` 生成规则**（避免误导用户以为 health 能修复跨 scope 违规）：

| 违规分布 | next_recommended.args |
|---|---|
| 仅 health 路由违规 | `"realign --scope=health --apply"` |
| 仅跨 scope 违规（无 health 路由） | 取占比最高的 scope，如 `"realign --scope=layout --apply"` |
| 混杂 health + 跨 scope | 数组形式：`["realign --scope=health --apply", "realign --scope=<跨 scope> --apply"]`，按拓扑顺序（spec → layout → prd-mapping → health）排序 |
| 0 违规 | `null` |

状态语义：

| status | 含义 |
|--------|------|
| `success` | dry-run 报告生成完毕或 apply 全部修复完成 |
| `partial` | apply 部分完成，仍有 `manual_pending` 或 skipped Phase |
| `failed` | 扫描或修复出错，已给出回滚指引 |
| `interrupted` | 用户暂停 AskUserQuestion 或主动取消 |

## 与其他 scope 的边界

- 维度 a 的 spec_version 差距 → 仅报告，**不补齐**；补齐走 `--scope=spec`（沿用现有 realign 主流程）。
- 维度 c 中 `current-md-size` ≥ 1500 行 → 仅报告，**不拆分**；拆分走 `--scope=layout`。
- 维度 b 的死链涉及 PRD ↔ DevDocs 编号映射 → 由 `--scope=prd-mapping` 处理。
- 本 scope 自身只负责：可逆的小范围修复（state 修剪、引用替换、死链标注）。

## 幂等性

- 同一 plan 二次 dry-run 报告 `total_score` 应一致（除非源文件变化）。
- 同一 plan 二次 apply 已修复项必须跳过、不重复写入。
- `--fix=<rule_id>` 多次调用同一 rule 不应产生重复修复 commit。
