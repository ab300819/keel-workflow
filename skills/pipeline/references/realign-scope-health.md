# Realign Scope Health（文档健康度主动审查）

> 用户入口：`/ms-pipeline realign --scope=health [--target=<path>] [--dry-run|--apply] [--fix=<rule_id>]`
> 默认 `--dry-run`（只输出健康度报告）。

## 定位

本文件定义 `--scope=health` 的执行接口，让 LLM 能按统一入口对 DevDocs 文档体系做**主动健康度审查**，覆盖五大维度并把分散在 ms-verify / ms-sync / ssot-lint 的检查能力收敛为单一报告。

与 `--scope=spec`（spec_version 差距补齐）/ `--scope=layout`（layout.v1→v2 迁移）/ `--scope=prd-mapping`（PRD ↔ DevDocs 映射）正交：health 关注**当前规范下产物是否健康**，不做规范升级、不做目录迁移、不做 PRD 映射重组。

引用关系：

| 文件 | 本 spec 的使用方式 |
|------|-------------------|
| [realign.md](realign.md) | 继承 realign 安全不变量、yaml-summary-v1 汇总方式 |
| [health-lint-implementation.md](health-lint-implementation.md) | 调用 4 条 [新增] lint rule（state/total-size-cap / state/line-length-cap / state/forbidden-content / health/dead-link），layout.v1+v2 通用 |
| [layout/ssot-lint-implementation.md](layout/ssot-lint-implementation.md) | layout.v2 启用后追加 `ssot/no-restatement` 等 8 条 [FUTURE] rule 到维度 d；v1 项目跳过 |
| `../../sync/references/health-scoring.md` | 6 类偏差评分（layout.v1 legacy）作为子项 |
| `../../verify/SKILL.md` | 调用 `--schema-drift` / `--docs` / `--impl` 已有能力 |
| `../../agent-memory/templates/devdocs-state-template.md` | 占位 prose 边界约束（forbidden 字段） |
| `../../_shared/constraints.md` | 继承 `⛔` / `⚠️` 门控、AskUserQuestion、yaml-summary-v1 |

## 五大健康维度

| 维度 | 检查内容 | 依赖能力 | 状态 |
|------|----------|----------|------|
| a 结构正确性 | frontmatter 必填字段、spec_version 当前性、设计文档 ADR ↔ 正文同期修订 | ms-verify --schema-drift（[现状]）+ `design/adr-only-revision`（[新增]）| [新增] |
| b 索引/链接正确性 | 编号引用文件存在性 + 追溯矩阵完整性 | ms-sync trace（[现状]）+ `health/dead-link`（[新增]）| [新增] |
| c 过大文档识别 | devdocs-state.md byte 阈值 / 单行长度 / 内嵌禁用模式 | `state/total-size-cap` + `state/line-length-cap` + `state/forbidden-content`（[新增]）| [新增] |
| d SSOT 遵从 | 占位/索引不复制权威源内容 | `ssot/no-restatement` | [FUTURE] (layout.v2 才启用) |
| e 三层分离 | 决策（ADR）/ 执行（设计/代码）/ 数据（DTO/Schema）章节关键词混杂检测 | 启发式正则扫描 | [FUTURE] |

> 本轮（layout.v1 项目可立即用）：维度 a/b/c 实装。维度 d 在 layout.v1 下报 `skipped: requires layout.v2 ssot-lint`；layout.v2 启用后自动激活。维度 e 待 keyword baseline 定义后启用。
>
> 维度 b/c 的 4 条 [新增] rule 算法与输出 schema 见 [health-lint-implementation.md](health-lint-implementation.md)。

## CLI 兼容

| 命令 | 行为 |
|------|------|
| `/ms-pipeline realign --scope=health --dry-run` | 默认。扫描 + 评分 + 报告，零写入 |
| `/ms-pipeline realign --scope=health --apply` | 仅执行**可自动修复**项；不可自动项以 ⚠️ 列出，等待 AskUserQuestion |
| `/ms-pipeline realign --scope=health --fix=<rule_id>` | 仅修复指定 rule 的违规项（例：`--fix=state/total-size-cap`） |
| `/ms-pipeline realign --scope=health --target=<path>` | 指定项目根或 `docs/devdocs/` |

未传 `--apply` 时一律视为 dry-run。

`--target` 归一化沿用 `--scope=layout` 同款规则（详见 [realign-scope-layout.md](realign-scope-layout.md) § "--target 归一化"）。

## Dry-run 阶段

### 只读边界

dry-run 不写入任何业务产物。唯一允许写入的文件是：

```text
docs/devdocs/.health-report.md
```

若用户要求严格零写入，可只输出报告到 stdout；后续 `--apply` 必须重新生成 `.health-report.md`。

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
6. 维度 e 当前 skipped（输出 `pending: keyword baseline 待 P2 落地`）。
7. 加权评分输出（见下方"评分契约"）。
8. 写入 `.health-report.md`，stdout 打印摘要 + 下一步建议命令。

### Health Report 文件契约

`.health-report.md` 正文包含 yaml 代码块 + Markdown 报告，yaml 块必须包含：

```yaml
report_schema: realign-health-report.v1
scope: health
target_layout: layout.v1 | layout.v2
repo_root: <absolute-or-relative-path>
docs_root: docs/devdocs
generated_at: <iso-timestamp>
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
  d_ssot:
    score: <0-100>
    restatement_findings: []
  e_layer_separation:
    status: skipped
    reason: "keyword baseline 待 P2 落地"

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

### 评分契约

权重随激活维度自动归一：

| 场景 | a | b | c | d | e |
|------|---|---|---|---|---|
| layout.v1（本轮可用）| 0.30 | 0.40 | 0.30 | — | — |
| layout.v2（d 启用）| 0.25 | 0.30 | 0.25 | 0.20 | — |
| layout.v2 + e [FUTURE] | 0.20 | 0.25 | 0.20 | 0.15 | 0.20 |

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
3. `manual_decisions` 中 `status=pending` 项已全部解答（或显式 `--skip-manual`，仅修复 `auto_fixable`）。

任一失败 → `⛔ 禁止继续`，恢复方式：重新 dry-run 或补齐决策。

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
    dimensions_scored: [a, b, c, d]
    dimensions_skipped: [e]
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
  args: "realign --scope=health --apply"
```

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
