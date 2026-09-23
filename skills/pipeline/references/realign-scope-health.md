# Realign Scope Health（文档健康度主动审查）

> 用户入口：`/pipeline realign --scope=health [--target=<path>] [--dry-run|--apply] [--fix=<rule_id>]`
> 默认 `--dry-run`（只输出健康度报告）。

## 目录

- 定位
- 三大健康维度
- CLI 兼容
- Dry-run 阶段
- AskUserQuestion 触发点
- Apply 阶段
- 输出契约
- 与其他 scope 的边界
- 幂等性

## 定位

本文件定义 `--scope=health` 的执行接口，让 LLM 能按统一入口对 keel 文档体系做**主动健康度审查**，覆盖三大维度并把分散在 verify / sync 的检查能力收敛为单一报告。

与 `--scope=spec`（spec_version 差距补齐）/ `--scope=prd-mapping`（PRD ↔ keel 映射）正交：health 关注**当前规范下产物是否健康**，不做规范升级、不做目录迁移、不做 PRD 映射重组。

> **推/拉两个触发点**（解决"规则实装但没人跑"的断层）：
> - **拉（全量）**：用户显式 `/pipeline realign --scope=health` —— 本文件定义的完整 3 维扫描。
>   ⛔ project scope 的 11 条 lint rule 中 9 条**已有可执行实现**，先跑 [`../scripts/health-lint.py`](../scripts/health-lint.py)，
>   不要逐条人肉扫；余下 2 条（`design/adr-only-revision` / `submodule/pointer-drift`）仍按
>   [health-lint-implementation.md](health-lint-implementation.md) 的算法执行。
> - **推（轻量探针）**：pipeline 路由入口的 health drift 探针（≤2s，仅 stat `devdocs-state.md`），命中则一行非阻塞提示来跑全量。探针**不挂 `.devdocs-realign-ack`**（health 是持续监控信号非一次性升级决策），按 `.health-baseline.yml` 重评估。探针规则见 [realign.md § health drift 探针](realign.md#health-drift-探针阶段-3与-schema-drift-并列但语义不同)。
> - **二级强化**：`/pipeline close`（周期收尾）若探针命中 blocker 级，建议顺带跑一次全量 health。

引用关系：

| 文件 | 本 spec 的使用方式 |
|------|-------------------|
| [realign.md](realign.md) | 继承 realign 安全不变量、yaml-summary-v1 汇总方式 |
| [health-lint-implementation.md](health-lint-implementation.md) | 调用 [新增] lint rule；rule 清单以该文件 Rule 集表为权威 |
| `../../sync/references/health-scoring.md` | 6 类偏差评分作为子项 |
| `../../verify/SKILL.md` | 调用 `--schema-drift` / `--docs` / `--impl` 已有能力 |
| `../../agent-memory/templates/devdocs-state-template.md` | 占位 prose 边界约束（forbidden 字段） |
| `../../shared/constraints.md` | 继承 `⛔` / `⚠️` 门控、AskUserQuestion、yaml-summary-v1 |

## 三大健康维度

| 维度 | 检查内容 | 依赖能力 | 状态 |
|------|----------|----------|------|
| a 结构正确性 | frontmatter 必填字段、spec_version 当前性、设计文档 ADR ↔ 正文同期修订、子模块指针一致性（仅 shell 拓扑）、布局清单中未登记路径（`layout/unknown-path`）| verify --schema-drift（[现状]）+ `design/adr-only-revision`（[新增]）+ `submodule/pointer-drift`（[新增]，仅 shell）+ `layout/unknown-path`（[新增]）| [新增] |
| b 索引/链接正确性 | 编号引用文件存在性 + 追溯矩阵完整性 + 分册未在主文件登记（`layout/unregistered-split`）| sync trace（[现状]）+ `health/dead-link`（[新增]）+ `layout/unregistered-split`（[新增]）| [新增] |
| c 过大文档识别（含 state-hygiene 子项）| size 三档（byte 阈值 / 单行长度）+ state-hygiene（内嵌禁用模式）+ 布局清单体积上限（`layout/size-cap`）| `state/total-size-cap` + `state/line-length-cap` + `state/forbidden-content` + `layout/size-cap`（[新增]）| [新增] |

> **原维度 d「SSOT 遵从」与维度 e「三层分离自动检测」均已废弃**（不再保留为 FUTURE）：维度 d 依赖已删除的 layout.v2 ssot-lint，无检测对象；三层分离（决策/执行/数据）作为原则已由编号文件结构 + `state/*`、`design/adr-only-revision` 症状规则承载，无需独立的关键词扫描维度；审查时作**人工尺子**使用。权威见 [shared/constraints.md §9 分层记忆原则](../../shared/constraints.md#9-分层记忆原则决策--执行--数据三层分离)。
>
> [新增] rule 的算法与输出 schema 见 [health-lint-implementation.md](health-lint-implementation.md)（rule 清单与维度归属以该文件 Rule 集表为权威）。

## CLI 兼容

| 命令 | 行为 |
|------|------|
| `/pipeline realign --scope=health --dry-run` | 默认。扫描 + 评分，**业务产物零写入**，报告写入 `.health-report.md`（唯一例外）|
| `/pipeline realign --scope=health --apply` | 执行可自动修复项；不可自动项以 ⚠️ 列出，等待 AskUserQuestion |
| `/pipeline realign --scope=health --fix=<rule_id> --dry-run` | 仅扫描指定 rule，不修复 |
| `/pipeline realign --scope=health --fix=<rule_id> --apply` | 仅修复指定 rule 的违规项（例：`--fix=state/total-size-cap`）|
| `/pipeline realign --scope=health --target=<path>` | 指定项目根或 `docs/devdocs/` |
| `/pipeline realign --scope=health --baseline-init` | 初始化 baseline（存量项目首次落地用）|
| `/pipeline realign --scope=health --changed-only` | 仅扫 `git diff HEAD` 变更**文件**（增量模式，大仓推荐）|
| `/pipeline realign --scope=health --since-baseline` | 与 baseline 比对，只报告新增违规 |
| `/pipeline realign --scope=health --no-report-file` | 严格 dry-run；不写 `.health-report.md`，只输出 stdout |

**语义规则**：
- 未传 `--dry-run` 也未传 `--apply` → 一律视为 `--dry-run`（安全默认）。
- `--fix=<rule_id>` 必须配 `--dry-run` 或 `--apply`；单独 `--fix=` 视为 `--fix --dry-run`。
- `--dry-run` 的"零写入"指**业务产物零写入**；`.health-report.md`、`stdout` 输出不算业务产物。

## Dry-run 阶段

### 只读边界

dry-run **不写入任何业务产物**（不动 docs/devdocs/*.md、不动 git）。唯一允许写入的文件是：

```text
docs/devdocs/.health-report.md
```

若用户要求严格零写入（如 CI dry-run-strict 模式），可加 `--no-report-file`，只输出报告到 stdout；后续 `--apply` 必须重新生成 `.health-report.md`。

### 扫描范围

| 来源 | 用途 |
|------|------|
| `docs/devdocs/**/*.md` | 主扫描对象（A 类主链路 + B 类旁路） |
| `.claude/rules/devdocs-state.md` | 维度 c 中 `state-size` / `state-forbidden-content` 专属扫描 |
| `docs/prd/**/*.md`（若存在） | 维度 b 死链扫描（PRD↔keel 编号引用）⚠️ **未实现**：`health-lint.py` 的 `collect_files()` 只收 `docs/devdocs/`；需由 Agent 按算法补扫 |
| `docs/devdocs/**`（**全部文件**，含 `.yaml` / `.txt`，⛔ 跳过 `_archived/`）| `layout/*` 三条规则专属扫描（`collect_all()`，⛔ 与喂编号索引的 `collect_files()` 分开）|

### 执行步骤

1. 归一化 `repo_root` 与 `docs_root`。
2. 调用 `/verify --schema-drift`（只读），获取维度 a 数据。
3. 调用 `/sync` audit 计算（只读复用 `health-scoring.md`），获取既有 6 类偏差作为维度 b 子项。
4. 执行 health-lint [新增] rule（清单见 [health-lint-implementation.md](health-lint-implementation.md)）：
   - `state/total-size-cap` + `state/line-length-cap` + `state/forbidden-content` → 维度 c
   - `health/dead-link` → 维度 b
   - `id/unknown-prefix` → 维度 b（⚠️ 非阻断提示；check 计数单位为「出现过的 prefix 数」，⛔ 不按 occurrence 计，也 ⛔ 不与 dead-link 的引用组数相加）
   - `design/adr-only-revision` → 维度 a（基于 git 历史扫描最近 30 天 commit）
   - `submodule/pointer-drift` → 维度 a（仅 shell 拓扑；`inline` 报 not_applicable，判据见 health-lint-implementation.md 该 rule 的适用性门）
5. 加权评分输出（见下方"评分契约"）。
6. 写入 `.health-report.md`，stdout 打印摘要 + 下一步建议命令。

### Health Report 文件契约

`.health-report.md` 正文包含 yaml 代码块 + Markdown 报告，yaml 块必须包含：

```yaml
report_schema: realign-health-report.v1
scope: health
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
    unknown_prefixes: []          # id/unknown-prefix 聚合 finding（⚠️ 提示，不计入阻断）
    trace_gaps: []
  c_oversize:
    score: <0-100>
    violations:
      - rule_id: state/total-size-cap | state/line-length-cap
        file: <path>
        actual: <value>
        threshold: <value>
        severity: blocker | warning
        route_to_scope: health | spec | prd-mapping  # health scope 是否能直接修复
        route_recommended: <next 命令字符串，如 "/pipeline realign --scope=health --apply">
        route_note: <可选；解释为何跨 scope，如 "归档减量走 /sync --archive">
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
| health-lint 全部 rule（清单见 [health-lint-implementation.md](health-lint-implementation.md) Rule 集表；`submodule/pointer-drift` 仅 shell 拓扑适用）| `health` | health scope `--apply` 直接处理（`health/dead-link` 手动修复；`submodule/pointer-drift` 不可自动修复，分叉情形需 AskUserQuestion）|
| `schema_drift_count > 0` | `spec` | 补 frontmatter 走 spec scope |
| PRD↔keel 死链 | `prd-mapping` | 修复 mapping 走 prd-mapping scope |

### 评分契约

权重随激活维度自动归一：

| a | b | c |
|---|---|---|
| 0.30 | 0.40 | 0.30 |

- 单维度评分 = (1 - violations_count / total_checks) × 100；无 violations 时为 100。
- 跳过维度（status: skipped）权重不分摊到其他维度，从总和中剔除；其余维度按比例归一。
- `total_score` < 60 时报告头部以 ⚠️ 提示"建议立即处理"；< 40 时 ⛔ 提示"健康度不达标"。

## AskUserQuestion 触发点

| 决策 | 触发条件 | 问询要求 |
|------|----------|----------|
| 归档目标 | `state/total-size-cap` 违规 + 需要把内容拆出 | 展示拟归档段落 + 拟目标文件（task / ADR / archive），3 个候选 |
| state prose 修剪 | `state/forbidden-content` 检出 commit/LOC/codex 分数 | 展示违规片段 + 拟保留占位形态，确认动作 |
| 跨产物影响 | 维度 b 死链涉及多个产物 | 展示受影响产物列表，确认是否一并修复 |
| 待分类文件归属 | `layout/unknown-path` 检出 | 展示文件名 + 清单中相近的路径模式候选（≤3 个）+「移出 devdocs」选项；⛔ 判不出归属时不得代为猜测 |

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

#### Phase 1：布局改名与归档移位（`layout/*`）

- 仅两种动作，均为 `git mv`：**改名**（清单中有明确旧名→新名映射时）、**归档移位**（把 `*-archive.md` 移进 `archive/`）。
  ⚠️ 清单当前不提供旧名→新名映射列 ⇒ 改名分支暂无输入来源，待清单扩列后生效。
- ⛔ **改名必须同批更新所有指向它的引用**。实证：tm-reborn 的 `06-ui-hig-swiftui-checklist.md` 在 `04-dev-tasks.md:19` 被链接，只 `git mv` 即制造死链。
- ⛔ **仅移动无法闭合的项单列**：补登记（`unregistered-split`）要编辑正文、集中→资源目录转换是内容迁移——两者均超出「只改名 + 归档移位」授权，列清单逐项问用户。
- ⛔ `layout/unknown-path` **不自动动手**，一律走 `AskUserQuestion`。

#### Phase 2：维度 c 自动归档（state-size / size-cap）

- 对 `state/total-size-cap` 违规：将超长行按 task ID 拆出，明细落到 `04-dev-tasks-pNN.md` 或 ADR 对应文件（依据 manual_decision），主文件保留 ≤200 字符占位。
- `state/line-length-cap` 违规：换行重排，不删除内容。

#### Phase 3：维度 b 死链处理

- 死链 → 用户确认是否补建目标文件 / 删除引用 / 标 `[FUTURE]`。
- 孤立编号（仅在文档中被引用但无定义）→ 在产物中补登记，或删除该引用。

#### Phase 4：维度 a 结构补齐

- 委托 `/pipeline realign --scope=spec`（已有路径），不在本 scope 直接 bump frontmatter。

#### 复查（⛔ 必须执行）

apply 全部 Phase 完成后**重新全量 dry-run**，比对 `total_score` 与各 rule 计数。

⛔ 不接受「post-apply 估算总分」——实证：mic-en 的 `47252f3` 报告写的就是估算值，
而当次 apply 后 state 又涨回 58 KB，估算掩盖了未收敛的事实。

### Apply 失败处理

- 任一 Phase ⛔ → 暂停，提示 `git reset --hard <pre-apply-commit>` 或追加修复 commit。
- 不允许 amend 已提交 Phase 历史。

## 输出契约

`--dry-run` 与 `--apply` 完成后均返回 yaml-summary-v1：

```yaml
skill: pipeline
status: success | partial | failed | interrupted
summary:
  headline: "health audit completed, score=<X>"
  details:
    scope: health
    total_score: <0.00-100.00>
    dimensions_scored: [a, b, c]
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
  skill: pipeline
  args: <按违规分布动态生成，规则见下>
```

**`next_recommended` 生成规则**（避免误导用户以为 health 能修复跨 scope 违规）：

| 违规分布 | next_recommended.args |
|---|---|
| 仅 health 路由违规 | `"realign --scope=health --apply"` |
| 仅跨 scope 违规（无 health 路由） | 取占比最高的 scope，如 `"realign --scope=spec --apply"` |
| 混杂 health + 跨 scope | 数组形式：`["realign --scope=health --apply", "realign --scope=<跨 scope> --apply"]`，按拓扑顺序（spec → prd-mapping → health）排序 |
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
- 维度 c 中单文件 > 96 KiB（`layout/size-cap`）→ 仅报告，**不拆分**；历史内容归档走 `/sync --archive`，活跃内容走各 skill 拆分规则，四类双形态资源的集中文件建议转资源目录。
- 维度 b 的死链涉及 PRD ↔ keel 编号映射 → 由 `--scope=prd-mapping` 处理。
- 本 scope 自身只负责：可逆的小范围修复（state 修剪、引用替换、死链标注）。

## 幂等性

- 同一 plan 二次 dry-run 报告 `total_score` 应一致（除非源文件变化）。
- 同一 plan 二次 apply 已修复项必须跳过、不重复写入。
- `--fix=<rule_id>` 多次调用同一 rule 不应产生重复修复 commit。
