---
name: ms-iteration-policy
description: 研发阶段命名策略横切 skill。Surface "semver 形式主义"反模式（未发布项目套 V<x.y.z>）并推荐敏捷三维度（Sprint + Milestone + Backlog）。当项目初始化、onboarding、改造时识别版本号占位（V0.9.x / V1.x）、版本号冻结绑大重构、Sprint 编号跨多版本累计等信号，主动 surface 给用户拍板。Triggers on "迭代策略"、"sprint 命名"、"版本号占位"、"semver 反模式"、"研发阶段"、"iteration policy"、"agile naming"。NOT for 已上线 production 的多版本并存项目（那里 semver 是真契约），不重新设计 INS/F/US/AC/T 等编号体系（仅治理 V 编号使用时机）。
metadata:
  patterns: [signal-detection, cross-cutting, anti-pattern-surface]
  interaction: surface-then-confirm
  handoff: yaml-summary-v1
reads_layout: [layout.v1, layout.v2]
writes_layout: layout.v1
reads_id_scheme: [id.v1, id.v2]
writes_id_scheme: id.v1
reads_traceability: [trace.v0, trace.v1]
writes_traceability: trace.v0
on_incompatible: warn
migration: /ms-pipeline realign --docs-layout
---

# 研发阶段命名策略（ms-iteration-policy）

> ℹ️ 本 skill 是治理框架的横切补充（FUTURE 表已声明，详见 [pipeline/references/layout/docs-layout-migration.md](../pipeline/references/layout/docs-layout-migration.md)）。与 `/ms-pipeline distill` 互补：distill 处理"已成型文档的蒸馏"；本 skill 处理"研发阶段命名的源头治理"——避免文档先污染再蒸馏的高成本路径。
>
> ℹ️ 编号双轨：本 skill 仅治理 `V<x.y.z>` semver 使用时机，**不涉及** layout.v1/v2 编号迁移（F/FEAT、T/TASK 等）。任何项目（v1 / v2）都可调用。

## 视角

研发流程教练。关注"研发期 vs 发布期"边界识别，避免命名形式主义演化成阻碍敏捷迭代的硬约束。

## 触发条件

| 时机 | 行为 |
|------|------|
| 项目初始化（`/ms-pipeline init`）| 默认建议 sprint-only，不主动套 semver |
| onboarding 扫描（`/ms-onboard --read`）| 识别反模式信号清单 → onboarding 摘要 surface |
| 已有项目改造（`/ms-retrofit`）| 评估是否需要废弃版本号驱动 |
| 新增 sprint / 增量需求 / 增量设计（`/ms-feature` / `/ms-system-design` / `/ms-dev-tasks`）| 遵循项目已建立约定，不主动套版本号 |
| 用户主动调用 `/ms-iteration-policy` | 全量扫描当前项目 + 反模式信号报告 |

## 核心原则

**未发布的项目分支不应使用 semver 作为研发期主追踪维度。** 强行套 semver 会演化出反模式。

未发布的判定（三条件**全满足**视为研发期）：

1. **未切 release tag**：`git tag` 列表为空，或最近 commit 无 `vX.Y.Z` 标签
2. **未实际发布**：`pom.xml` / `package.json` / `Cargo.toml` 等的版本号未对应任何 npm/maven/crates registry 公开版本
3. **未上线 production**：CI/CD 无生产环境部署记录，或用户明确确认未上线

研发期用 **Sprint + Milestone（可选）+ Backlog** 三维度足以追踪。`V<x.y.z>` 留给真发布时启用。

## 反模式识别清单

发现以下任一信号时，主动 surface 给用户拍板：

| 信号 | 含义 | 典型示例 | 检测算法 |
|------|------|----------|---------|
| **版本号字面化占位** | 状态行出现含字面 `x` 的版本号 | "V0.9.x P17"、"V1.x 候选"、"Vx.y.x" | 见下方 § 检测算法（signal 1）|
| **版本号被冻结绑大重构** | 某版本号被绑死等待某次重构完成 | "V1.0 候选 INS-012"、"V2.0 候选 Microservice 拆分" | 见下方 § 检测算法（signal 2）|
| **同版本号下挂多 Sprint** | sprint 节奏与版本号节奏脱钩 | V0.9.8 P11 + P12 + P13... | 见下方 § 检测算法（signal 3）|
| **Sprint 编号跨版本累计** | P 编号已是真追踪维度，V 编号是空标签 | P1~P17 跨 V0.5~V1.0 | 见下方 § 检测算法（signal 4）|
| **仓库无 release tag 但文档大量出现 `V<x.y.z>`** | 研发期形式主义信号 | `git tag` 为空 + 文档 grep 出 100+ 处版本号 | 见下方 § 检测算法（signal 5）|

### 检测算法（避免 markdown 表格 `|` 转义干扰，独立列出可直接复制执行）

```bash
# signal 1: 版本号字面化占位
grep -rE '(V[0-9]+\.[0-9]+\.x|V[0-9]+\.x|Vx\.y\.[xz])' docs/

# signal 2: 版本号被冻结绑大重构（含 "V<x.y> 候选" 字样）
grep -rE 'V[0-9]+\.[0-9]+ 候选' docs/

# signal 3: 同 V 下挂多 P（伪代码 — runtime 实现按 V 分组聚合）
#   for each V in matches:
#     count = number of P-refs within 同上下文段落
#     if count >= 3: report

# signal 4: Sprint 跨 V 累计（伪代码）
#   p_range = max(P-refs) - min(P-refs)
#   v_minors = distinct minor versions in matches
#   if p_range >= 10 and len(v_minors) >= 2: report

# signal 5: 无 tag 但大量 V 引用
tag_count=$(git tag | wc -l)
v_count=$(grep -rE 'V[0-9]+\.[0-9]+(\.[0-9]+)?' docs/ | wc -l)
if [ "$tag_count" -eq 0 ] && [ "$v_count" -ge 100 ]; then echo "signal-5 hit"; fi
```

## 推荐三维度体系

| 维度 | 编号 | 用途 | 何时启用 |
|------|------|------|----------|
| **Sprint** | P1, P2, ..., Pxx | 开发批次（约 1-2 周一个），研发期主追踪维度 | 项目启动即用，累计递增，不重置 |
| **Milestone**（可选）| M1, M2, ... | 业务大节点回顾性标记（"MVP 全可用"、"trace 系统全收"）| sprint 关闭时回填，不强制每个 sprint 一个 |
| **Backlog** | 候选池条目 | 未排期 / 暂缓任务 / 大重构 | 自由进出，不绑版本号 |
| **V\<x.y.z\>** | semver | git tag + pom/package.json + 上线日 | **仅在真发布时启用，研发期不用** |

## Surface 话术模板

发现反模式信号时，**精确引用现状**（避免泛泛而谈），向用户提问：

```text
当前分支看起来还没有切过 release tag（`git tag` 列表为空 / 最近 commit 无 vX.Y.Z 标签）
也没上线 production，但文档大量出现 <具体示例：V0.9.x P17 INS-020、V1.0 候选 INS-012>。

这种"研发期套 semver"容易演化成几个问题：
- 版本号被冻结成占位（V1.0 一直等大重构完成）
- sprint 与版本号脱钩（同 V 下挂多 P）
- 编号体系不自洽（占位字符 V0.9.x 出现）

要不要改成敏捷迭代三维度（Sprint Pxx + Milestone Mxx 可选 + Backlog）？
`V<x.y.z>` 留给真发布时再启用。
```

### AskUserQuestion 选项

```yaml
question: "检测到 N 处 semver 形式主义信号。是否迁移到敏捷三维度？"
options:
  - label: "完整迁移（推荐）"
    description: "全量替换 V 引用为 Sprint Pxx；归档原 V 引用作历史快照"
  - label: "渐进迁移"
    description: "新增内容用 Pxx；旧 V 引用保留不动；6 个月后回看是否清理"
  - label: "暂不迁移"
    description: "已知反模式但当前不处理；写入 ADR 标记决策；下次 onboard 不再 surface"
  - label: "项目已发布 production，semver 是真契约"
    description: "假设错误；ms-iteration-policy 不再扫描本项目"
```

## 项目类型决策树

| 项目状态 | 推荐 |
|----------|------|
| 全新项目，尚未上线 | Sprint + Backlog（不引入 V 编号）|
| 单分支开发，未切 release tag | 同上，建议在 AGENTS.md / CLAUDE.md 明文约定 |
| 已切 release tag，但当前分支是 feature/dev | 仅在分支合入 main 切 tag 时用 V；分支内开发用 Sprint |
| 已部署 production，多版本并存 | 启用 semver，sprint 仅作内部排程辅助 |
| 接手项目发现已有 V 占位反模式 | surface 给用户拍板是否迁移到三维度 |

## 实施建议（用户接受迁移后）

1. **AGENTS.md / CLAUDE.md 顶部新增 `## 项目阶段约定` 段落**，明文定义三维度 + V 启用规则，防约定回潮
2. **归档文件不动**（`devdocs-state-archive.md` / 历史 PRD 目录），保留 V 前缀作历史快照 + 时间锚点
3. **ADR / INS / ADR/PATTERN/NOTE 决策链路保留历史 cross-ref**："决策于 P11（旧称 V0.9.8）" 形式，可追溯性优先
4. **git log 历史 commit message 不改**（rebase 成本高 + 历史 immutable）；新 commit 改约定
5. **拆分两阶段提交**：
   - 阶段 1 解绑版本号绑大重构 + 文件改名（~2h）
   - 阶段 2 全量去版本号驱动（~6-8h）

## 不在范围

- ❌ 不强制改 git log 历史 commit message
- ❌ 不强制改 PRD 历史目录命名（`docs/prd/V0.5/` 等）
- ❌ 不预先规定大重构何时升级 V1.0（留待真发布时拍板）
- ❌ 不改 pom.xml / package.json 的业务无关版本号字段
- ❌ 不重新设计 INS / F / US / AC / T / ADR / BUG / FEAT / STORY / TASK / ISSUE 等编号体系（仅治理 V 使用时机）
- ❌ 不处理 layout.v1/v2 编号迁移（属 #1 编号体系范围）

## 与 distill 的边界

| 处理对象 | distill | iteration-policy |
|---------|---------|------------------|
| 已成型文档的结构精简 | ✅ | ❌ |
| 多文件 → 少文件合并 | ✅ | ❌ |
| 反模式命名源头 surface | ❌ | ✅ |
| V → P 编号迁移 | ❌（distill 不处理 V）| ✅ |
| 防约定回潮（AGENTS.md 明文化）| ❌ | ✅ |

**触发顺序建议**：
1. 项目早期：`iteration-policy` 在 init/onboard 时 surface → 立约（防止文档被 V 污染）
2. 项目成长期：`distill` 周期蒸馏（处理 P 编号下累积的多 sprint 摘要）

iteration-policy 是**预防型**，distill 是**治疗型**。

## CLI 入口

> ⚠️ 全部 CLI 命令均 [FUTURE]（spec 已起草，runtime 待实现，详见 [pipeline/references/layout/docs-layout-migration.md § 执行接口落地状态](../pipeline/references/layout/docs-layout-migration.md#-执行接口落地状态future)）。

| 命令 | 行为 |
|------|------|
| `/ms-iteration-policy` [FUTURE] | 全量扫描当前项目 + 反模式信号报告 |
| `/ms-iteration-policy --scan-only` [FUTURE] | 仅扫描，不 surface AskUserQuestion |
| `/ms-iteration-policy --apply-migration --dry-run` [FUTURE] | **默认模式**：列出将替换的文件 + 行号 + 新旧文本对比，不修改任何文件 |
| `/ms-iteration-policy --apply-migration --apply` [FUTURE] | 实际执行迁移（必须先跑 dry-run；不带 `--dry-run` 显式 `--apply` 视为非法参数）|
| `/ms-iteration-policy --strategy <full-migrate \| incremental \| defer \| not-applicable>` [FUTURE] | 直接指定策略跳过 AskUserQuestion |
| `/ms-iteration-policy --baseline-init` [FUTURE] | 写入当前状态作 baseline（仅初次或显式重置）|
| `/ms-iteration-policy --baseline-show` [FUTURE] | 显示当前 baseline 内容 |

### baseline 文件

位置：`docs/devdocs/_archived/iteration-policy-baseline-<commit-short>.yml`

```yaml
---
version: iteration-policy-baseline.v1
created_at: "2026-05-18T10:00:00+08:00"
git_commit: abc1234567890def
git_branch: main
signals_detected:
  - rule: placeholder-version
    count: 234
    sample_files: ["docs/devdocs/04-dev-tasks.md", ...]
  - rule: frozen-version-refactor
    count: 12
    sample_files: [...]
strategy_decision: incremental | full-migrate | defer | not-applicable
notes: "user 决定 defer，3 个月后回看"
---
```

后续扫描：
- `--scan-only` 报告中 `new_violations` 字段只列 baseline 之后新增的违规
- 防止历史项目老警告轰炸（接手项目的 onboarding 体验）
- 防约定回潮：迁移后 baseline 重置（signals_detected 各 count 应为 0），新增 V 引用立即报错

### 迁移安全网（apply 必备）

`--apply-migration --apply` 执行前自动检查：

```text
1. 前置检查（fail-fast）：
   a. clean worktree 检查：git diff/diff --cached 非空 → 阻断，提示先 commit 或 stash
   b. baseline 文件存在：缺失则阻断，提示先 `--baseline-init`
   c. 必须有 dry-run 历史输出（来自上次 `--dry-run`，写到 `_archived/iteration-policy-dry-run-<timestamp>.md`）
2. 创建临时分支：iteration-policy-<timestamp>
3. 按阶段执行（默认两阶段拆分）：
   阶段 1: 解绑版本号绑大重构 + 文件改名 (~2h)
   阶段 2: 全量 grep 替换 V → P (~6-8h)
4. 每阶段完成后逐个 commit（粒度：1 stage = 1 commit）
5. 全部成功 → merge 回主分支（--no-ff 保留 history）
6. 任一失败 → rollback 到迁移开始前 + 删除临时分支 + 写日志到 `_archived/iteration-policy-rollback-<timestamp>.log`
```

### 中断处理

| 阶段 | SIGINT 行为 |
|------|----------|
| 前置检查中 | 立即 abort，无副作用 |
| 临时分支已建 + 部分阶段完成 | 保留临时分支（用户可后续手动检查/合并）；不自动 rollback |
| 任何阶段 | 必须清理临时环境（与 #5 distill 同模式）|

### 退出码

| 退出码 | 含义 |
|--------|------|
| 0 | 无信号 / 已 baseline 后无新增 |
| 1 | 检测到 1-2 类信号（warn）|
| 2 | 检测到 3+ 类信号（surface 推荐迁移）|
| 3 | 迁移失败（rollback 已执行；详见 `_archived/iteration-policy-rollback-*.log`）|
| 4 | 前置检查失败（dirty worktree / 缺 baseline / 缺 dry-run 历史）|

## yaml-summary 集成（yaml-summary-v1 信封）

```yaml
skill: ms-iteration-policy
status: success | failed | interrupted | partial
summary:
  headline: "检测 4 类信号，用户选完整迁移；已完成阶段 1"
  details:
    severity: warn | info | none      # warn 放 details，不放顶层 status
    project_phase: dev | release-candidate | production
    signals_detected:
      - placeholder-version           # V0.9.x 占位
      - frozen-version-refactor       # V1.0 候选
      - cross-version-sprints         # P 跨 V 累计
      - no-tag-but-v-refs             # 无 tag + 大量 V
    counts:
      v_references: 2034
      affected_files: 87
      sprint_range: "P1 ~ P17"
    user_decision: full-migrate | incremental | defer | not-applicable
    migration_stage: 1 | 2 | done
blockers: []                          # 通用：阻塞项列表（如 dirty worktree）
output_files:                          # 通用：产出/修改的文件
  - docs/devdocs/_archived/iteration-policy-baseline-abc1234.yml
  - docs/devdocs/_archived/iteration-policy-dry-run-2026-05-18T10-00-00.md
new_ids: {}                            # 通用：本 skill 不分配新编号（不属 id.v1/v2 体系）
next_recommended:                      # 顶层字段
  skill: ms-iteration-policy
  args: "--apply-migration --apply"
```

**关键对齐点**（与其他 ms- skill 一致）：
- `status` 只能是 4 个保留值（`success` / `failed` / `interrupted` / `partial`）；warn/info 等放 `summary.details.severity`
- `blockers` / `output_files` / `new_ids` / `next_recommended` 均为顶层保留字段
- skill 私有字段（signals_detected / counts / user_decision 等）放 `summary.details`

## 迁移工作量参考

> 一个跨 17 sprint / 半年研发期的项目，~2,000 处 V 引用 / 80+ 文件，全量迁移工作量 7-10h（拆两阶段：解绑大重构 ~2h + 全量去版本号 ~6-8h）。

| 项目规模 | 全量迁移工作量 |
|----------|--------------|
| < 5 sprint / < 20 文件 | < 2h |
| 5-15 sprint / 20-50 文件 | 3-6h |
| 15-30 sprint / 50-100 文件 | 7-10h |
| 30+ sprint / 100+ 文件 | 12h+，**强烈推荐渐进迁移** |

## 关联反模式

- 版本号驱动 vs 敏捷迭代驱动
- 大重构绑死版本号（V<x.0> 候选反模式）
- Sprint 节奏 vs 版本号节奏脱钩
- 占位字符（V0.9.x、Vx.y.x）作正式状态标签

## 历史项目兼容

- **mic-en 等 layout.v1 项目**：iteration-policy 可正常使用（不依赖 layout.v2）
- 任何 layout 版本都可调用（writes_layout 保持 v1，不会触发 layout drift）
- 迁移后 AGENTS.md 顶部加 `## 项目阶段约定` 段，与 `devdocs` frontmatter 独立

## 与治理框架的接口

| 阶段 | 接口点 |
|------|-------|
| #6 治理框架 | 本 skill 不修改三层版本号（layout/id/trace）；仅治理 `V<x.y.z>` semver 命名 |
| #1 编号体系 | 本 skill 的 P/M 编号与 id.v1/v2 的 F/STORY/T/TASK 完全独立；不冲突 |
| #2 文件夹组织 | 迁移时若项目已是 layout.v2，AGENTS.md `## 项目阶段约定` 段独立于 `devdocs` frontmatter |
| #5 迭代蒸馏 | 互补关系（详见 § 与 distill 的边界）|

## 参考

详细背景案例：本 skill 起源于一次实际项目讨论（master 分支从未切 release tag、未上线 production，但文档累计 ~2,000 处 V 引用），完整原始洞察归档于 `_archived/iteration-policy-genesis.md`（项目内）。
