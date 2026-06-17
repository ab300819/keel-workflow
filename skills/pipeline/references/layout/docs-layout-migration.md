# Docs Layout Migration（layout v1 → v2 迁移矩阵）

> DevDocs 布局升级的执行规范。本文件定义 `layout.v1 → layout.v2` 的迁移规则、dry-run 输出契约、不可逆操作清单。
>
> 被 [layout-versioning-policy.md](layout-versioning-policy.md) 与 `skills/pipeline/SKILL.md § realign --scope=layout` 引用。

## ⚠️ 执行接口落地状态（FUTURE）

> **入口命名与调用语义权威归 [../realign-scope-layout.md](../realign-scope-layout.md)（`--scope=layout`；`--docs-layout` 为 legacy alias，保留 1 版本）**。本节仅作为各 [FUTURE] 命令**落地状态矩阵**的权威源：本治理框架的所有 layout 文件（含本文件 + 同目录其他 references + `templates/layout-migration-log.md`）的执行接口当前状态以本节为准，其他文件提及的命令默认按本节状态解读，**不重复标注 [FUTURE]**。

本治理框架定义了完整规范，**部分执行接口尚未实现**。当前框架处于"**仲裁层就绪 / 执行层待补**"阶段，可作为后续开发蓝图，但**不应直接调用未实现命令**。

### ✅ 已实现（治理框架声明完整）

- `skills/pipeline/SKILL.md` 已声明 `realign --scope=layout`（legacy alias: `--docs-layout`）+ layout drift 检测入口
- `skills/verify/SKILL.md` 已声明 `--layout-drift` 入口
- 9 个 A/B skill SKILL.md frontmatter 已加 8 字段 layout 兼容性声明
- 治理规范文件（本目录全部 references + `templates/layout-migration-log.md`）已完整

### 🚧 尚未实现（仅文档定义，执行需后续 sprint）

| 命令 | 状态 | 计划交付阶段 |
|------|------|------------|
| `/ms-pipeline realign --scope=layout` (dry-run + apply 迁移执行逻辑；legacy alias `--docs-layout`) | [FUTURE] 入口已声明，迁移执行逻辑待落地 | 本框架 #6 后续 |
| `/ms-pipeline realign --classify-ins` | [FUTURE] | 本框架 #6 后续 |
| `/ms-pipeline realign --rename-id` | [FUTURE] | 本框架 #6 后续（单条编号迁移辅助命令）|
| `/ms-pipeline realign --scope=layout --archive-v1` | [FUTURE] | 本框架 #6 后续 |
| `/ms-verify --layout-drift` | [FUTURE] 入口已声明，扫描逻辑待落地 | 本框架 #6 后续 |
| `/ms-verify --ssot-lint` | [FUTURE] | #3 SSOT lint 阶段交付（详见 [ssot-lint-implementation.md](ssot-lint-implementation.md)）|
| `/ms-sync --extract-trace` | [FUTURE] | #4 代码解耦阶段交付（详见 [code-decoupling-implementation.md](code-decoupling-implementation.md)）|
| `/ms-sync --refresh-traceability` | [FUTURE] | #4 代码解耦阶段交付 |
| `/ms-sync --multi-repo --discover` / `--merge` | [FUTURE] | layout.v3 候选 |
| `/ms-pipeline distill` (--action / --scope / --since / --dry-run / --apply) | [FUTURE] | #5 迭代蒸馏阶段交付（详见 [distillation-implementation.md](distillation-implementation.md)）|
| `/ms-iteration-policy` (--apply-migration --dry-run/--apply / --baseline-init/show / --strategy / --scan-only) | [FUTURE] skill spec 已起草，runtime 待落地 | 横切 skill（详见 [skills/iteration-policy/SKILL.md](../../../iteration-policy/SKILL.md)）|

### 调用未实现命令的预期行为

- 已声明入口的命令（pipeline/verify SKILL.md 中可见）：执行时 surface "[FUTURE] 命令入口已声明，执行逻辑待落地，详见 docs-layout-migration.md § 执行接口落地状态"
- 完全未实现命令：调用时 fail-safe（不会发生实际迁移）

### 当前可做与不可做

| 行为 | 是否可执行 |
|------|---------|
| 阅读治理规范作为开发蓝图 | ✅ |
| 在 AGENTS.md 顶部手动添加 `devdocs:` frontmatter 声明 layout.v2 | ✅ |
| 各 skill frontmatter 已声明 layout 兼容性字段（无运行时检查）| ✅ |
| 实际执行 `/ms-pipeline realign --scope=layout` 的迁移执行逻辑（legacy alias: `--docs-layout`）| ❌（命令实现待后续 sprint）|
| 实际执行 mic-en 项目的 layout.v1 → v2 迁移 | ❌（需要 dry-run 命令实现）|

## 适用范围

| 升级路径 | 本文件覆盖 |
|---------|---------|
| layout.v1 → layout.v2 | ✅ |
| id.v1 → id.v2 | ✅（layout 升级带动）|
| trace.v0 → trace.v1 | ✅（layout 升级带动）|
| layout.v2 → layout.v3 | ❌（待 v3 定稿）|

## 三阶段迁移流程

```text
Phase 1: 预扫描（read-only）
  └─ 输出 dry-run 报告 → 用户审阅

Phase 2: 编号 + 文件迁移（按 dry-run 批准项执行）
  ├─ 重命名 / 移动文件
  ├─ 写入 aliases.yml
  └─ 拆分 INS 等需要人工归类的项

Phase 3: 后置校验
  ├─ traceability.yml 提取（trace.v0 → v1）
  ├─ SSOT lint 跑一遍
  └─ 写入 AGENTS.md devdocs frontmatter (upgraded_at)
```

每阶段失败可独立回滚（git branch 隔离）。

## 迁移矩阵（v1 → v2）

### A 类：DevDocs 主链路产物

| v1 形态 | v2 目标 | 自动化级别 | 不可逆? | 风险 |
|---------|---------|-----------|--------|------|
| `01-requirements.md` （单文件累积）| `requirements/index.md` + `requirements/FEAT-NNN.md` + `STORY-NNN.md` + `AC-NNN.md` | 半自动（章节切分脚本 + 人工校对）| 是 | 中 |
| `01-requirements-stories.md` | 合并进上行 | 半自动 | 是 | 中 |
| `02-system-design.md` （单文件 3000+ 行）| `design/current.md`（保留当前态）+ `design/decisions/ADR-NNN.md`（拆 ADR）| **人工驱动** | 是 | **高** |
| `02-system-design-api.md` | 合并进 `design/current.md` 或独立 `design/api.md` | 半自动 | 是 | 中 |
| `02-system-design-data.md` | 合并进 `design/current.md` 或独立 `design/data.md` | 半自动 | 是 | 中 |
| `03-test-cases.md` | `tests/UT/index.md` + `tests/IT/index.md` + `tests/E2E/index.md` + 各 `<TYPE>-NNN.md` | 半自动 | 是 | 中 |
| `03-test-unit.md` / `03-test-integration.md` / `03-test-e2e.md` | 拆为 `tests/<TYPE>/<TYPE>-NNN.md` | 半自动 | 是 | 中 |
| `04-dev-tasks.md` （累积大表）| `tasks/index.md` + `tasks/TASK-NNN.md`（一任务一文件）| 半自动 | 是 | **高** |
| `04-dev-tasks-pXX.md` （sprint 拆分）| 合并进 `tasks/index.md` 按 sprint 分组 | 半自动 | 是 | 中 |
| `05-bugfix-log.md` （单文件 4000+ 行）| `issues/index.md` + `issues/ISSUE-NNN.md`（BUG-N → ISSUE-N）| 半自动 | 是 | 中 |
| `06-insights.md` （混 INS）| 人工归类 → `design/decisions/ADR-NNN.md` / `patterns/PATTERN-NNN.md` / `notes/NOTE-NNN.md` | **人工驱动** | 是 | **高** |

### B 类：辅助产物

| v1 形态 | v2 目标 | 自动化级别 | 不可逆? |
|---------|---------|-----------|--------|
| `00-context.md` | `context.md`（移到顶层）| 自动 | 否 |
| `patterns/<slug>.md` | `patterns/PATTERN-NNN.md` + aliases.yml 记 rename-only-file | 自动 | 是 |
| `sop/*.md` | 保留 `sop/`（v2 不强制改名）| 无操作 | - |
| `sql/*.md` | 保留 `sql/`（v2 不强制改名）| 无操作 | - |

### C 类：归档与状态

| v1 形态 | v2 目标 | 自动化级别 |
|---------|---------|-----------|
| `*-archive.md` 系列 | 移到 `archive/<type>/` 外仓（如 `<project>-docs-archive`）| 人工 |
| `devdocs-state.md` | 留在 `.claude/rules/`（不进 docs/devdocs）| 无操作 |
| `04-dev-tasks-v1.0-candidates.md` | `tasks/backlog.md`（命名脱离版本号）| 半自动 |

### D 类：代码追溯

| v1 形态 | v2 目标 | 自动化级别 | 不可逆? |
|---------|---------|-----------|--------|
| 代码内 `@satisfies AC-XXX` / `@verifies T-XXX` 注释 | `docs/devdocs/traceability.yml` | `/ms-sync --extract-trace` [FUTURE] 自动提取 + 人工 review | **否**（**禁止新增**；legacy retained 允许保留直到 layout.v3）|

## dry-run 5 项输出契约

`/ms-pipeline realign --scope=layout --dry-run`（legacy alias: `--docs-layout`）必须输出以下 5 项，缺一不可：

### 1. 计划变更（File Operations Plan）

```yaml
file_operations:
  rename:
    - { from: docs/devdocs/05-bugfix-log.md, to: docs/devdocs/issues/index.md + 77 files }
  create:
    - docs/devdocs/aliases.yml
    - docs/devdocs/traceability.yml
    - docs/devdocs/requirements/index.md
    - ...
  delete:
    - (none, 删除走 archive 外仓)
  move:
    - { from: docs/devdocs/00-context.md, to: docs/devdocs/context.md }
```

### 2. alias 映射（Alias Map）

```yaml
aliases_to_write:
  - { from: BUG-001, to: ISSUE-001, type: rename, since: "2026-05-15" }
  - { from: F-001, to: FEAT-001, type: rename, since: "2026-05-15" }
  - { from: T-001, to: TASK-001, type: rename, since: "2026-05-15" }
  - { from: patterns/hygiene-decision-tree.md, to: patterns/PATTERN-001.md, type: rename-only-file }
  - ...

total_aliases: 254
```

### 3. 无法映射项（Unmappable Items）

需要人工干预的项目，dry-run 必须列出且**禁止自动迁移**：

```yaml
unmappable:
  - id: INS-018
    reason: "type=split 需要人工归类（决策 / 经验 / 一次性）"
    suggestion: "运行 /ms-pipeline realign --classify-ins INS-018"
  - id: INS-019
    reason: "type=split 需要人工归类"
  - id: T-105 + T-106
    reason: "疑似 merge 候选（同 commit 关联），需用户确认"
```

### 4. 旧路径引用（Broken Cross-Links）

迁移后会失效的 cross-link：

```yaml
broken_links:
  - source: docs/devdocs/02-system-design.md:1247
    references: "详见 04-dev-tasks-p11.md § T-107"
    expected_new: "详见 tasks/TASK-107.md"
    auto_fixable: true

  - source: docs/devdocs/05-bugfix-log.md:892
    references: "patterns/hygiene-decision-tree.md"
    expected_new: "patterns/PATTERN-001.md"
    auto_fixable: true

  - source: docs/devdocs/00-context.md:42
    references: "06-insights.md § INS-018"
    expected_new: "(split, 需人工归类)"
    auto_fixable: false

total_broken: 1247
auto_fixable: 1192
manual_review: 55
```

### 5. traceability 漂移项（Traceability Drift）

trace.v0 → v1 迁移时无法匹配的代码注释：

```yaml
traceability_drift:
  - file: trade/src/.../FundService.java:142
    annotation: "@satisfies AC-999"
    issue: "AC-999 不存在于 requirements/ 或 aliases.yml"
    action: required_manual_review

  - file: trade/src/.../SlipMatcher.java:88
    annotation: "@satisfies AC-001"
    issue: "symbol 'SlipMatcher#matchByFiveTuple' 未找到（疑似已重命名）"
    action: required_manual_review

  - file: ...
    annotation: "@verifies T-105"
    issue: "T-105 在 aliases.yml 标 merge 到 TASK-105，自动解析"
    action: auto_resolved

total_drift: 636
auto_resolved: 581
manual_review: 55
```

### dry-run 报告输出位置

- 默认：标准输出 + 写入 `docs/devdocs/.layout-migration-dryrun.md`（git ignored）
- 用户审阅后通过 `/ms-pipeline realign --scope=layout --apply` 执行实际迁移

## 不可逆操作清单

### 必须 dry-run 后用户显式确认的操作

| 操作 | 风险 | 安全网 |
|------|------|--------|
| **删除文件** | 信息丢失 | 通过 git branch 隔离 + 实际操作前 commit |
| **文件合并** | 章节混淆 | dry-run 必须输出 before/after 章节预览 |
| **编号 split** | 多映射歧义 | 必须人工归类（不可自动）|
| **编号 merge** | 历史合并丢失 | 必须人工确认（dry-run 标 `auto_fixable: false`）|
| **目录移动覆盖** | 同名文件覆盖 | dry-run 检测冲突 + 强制改名或拒绝 |
| **代码注释删除**（@satisfies / @verifies）| 追溯链路破坏 | **禁止新增**注释，**legacy retained 允许保留直到 layout.v3**；traceability.yml 与 legacy 注释**并存**期内 |

### 自动可执行的操作（dry-run 标 `auto_fixable: true`）

- 文件 rename（同目录）
- 文件 move（不覆盖目标）
- aliases.yml 追加（不修改既有 entry）
- traceability.yml 自动提取（已有 entry 不覆盖）
- AGENTS.md devdocs frontmatter 字段更新

## 演练流程（推荐）

### 使用 git branch 隔离

```bash
# 1. 创建演练分支
git checkout -b devdocs-layout-v2-migration

# 2. 跑 dry-run（不修改文件）
/ms-pipeline realign --scope=layout --dry-run

# 3. 审阅 .layout-migration-dryrun.md
# 4. 处理 unmappable 项（人工归类 INS / merge 候选）
/ms-pipeline realign --classify-ins INS-018  # 单条归类
# ... 重复直到 unmappable = 0

# 5. 跑实际迁移
/ms-pipeline realign --scope=layout --apply

# 6. 跑后置校验
/ms-verify --layout-drift

# 7. 跑 SSOT lint
/ms-verify --ssot-lint                       # v2 lint 全套规则

# 8. 提交 + 切回主分支前先 review
git diff main..devdocs-layout-v2-migration

# 失败回滚：
git checkout main
git branch -D devdocs-layout-v2-migration
```

### 失败回滚机制

| 失败阶段 | 回滚方式 |
|---------|---------|
| Phase 1（dry-run）| 不需要回滚（read-only）|
| Phase 2（迁移执行中）| `git reset --hard HEAD~1` 或切回主分支 |
| Phase 3（后置校验失败）| 同上；保留 dry-run 报告排错 |
| `aliases.yml` 写错 | 手工编辑修正 + 重跑 Phase 3 校验 |

## INS 拆分的人工归类机制

`INS-NNN` 在 v1 含三种语义，v2 必须拆分。归类机制：

### 自动建议 + 人工确认流程

```bash
/ms-pipeline realign --classify-ins INS-018
```

工具行为：
1. 读取 `06-insights.md § INS-018` 内容
2. 用 LLM 提取关键词，按以下规则建议归类：
   - 含"决定" / "选择" / "trade-off" / "ADR" → 建议 ADR
   - 含"模式" / "复用" / "经验" → 建议 PATTERN
   - 含"观察" / "一次性" / "现象" → 建议 NOTE
3. surface 建议 + 提取的关键段落预览
4. **AskUserQuestion**：让用户确认或选择其他归类
5. 用户确认后：
   - 写入新文件（`design/decisions/ADR-NNN.md` / `patterns/PATTERN-NNN.md` / `notes/NOTE-NNN.md`）
   - 写入 `aliases.yml`（type=split, sub 对应）
   - 标记 `INS-018` 在原 `06-insights.md` 为 `[已迁移 → ADR-022 / PATTERN-022 / NOTE-018]`

### 批量归类

```bash
/ms-pipeline realign --classify-ins --batch
```

逐条触发上述流程，可中断（标记当前进度，后续 resume）。

## PATTERN 编号分配规则

`patterns/<slug>.md` → `patterns/PATTERN-NNN.md` 编号分配按引用度排序：

```text
排序规则：
  Primary key: 被其他文档引用次数（rg -l patterns/<slug> docs/）
  Secondary key: 创建时间（git log first commit）
```

mic-en 示例（按引用度排序，截取前 5）：

| slug | 引用次数 | 新编号 |
|------|--------|--------|
| hygiene-decision-tree | 13 | PATTERN-001 |
| cross-screen-shared-data-source-convention | 9 | PATTERN-002 |
| com-id-binding-paths | 8 | PATTERN-003 |
| direct-function-vs-pattern-over-engineering | 7 | PATTERN-004 |
| pre-release-refactor-bridge-decision | 5 | PATTERN-005 |

`aliases.yml` 写入：

```yaml
- { from: patterns/hygiene-decision-tree.md, to: patterns/PATTERN-001.md, type: rename-only-file, id_unchanged: PATTERN-001 }
- ...
```

文件内 frontmatter 同步：

```yaml
---
id: PATTERN-001
slug: hygiene-decision-tree                  # 保留人类可读的 slug
type: pattern
status: active
summary: "..."
---
```

## ID 重新分配 vs 保留原编号

| 旧编号 | 新编号 | 重新分配? |
|--------|--------|---------|
| `BUG-001` | `ISSUE-001` | 否（数字保留）|
| `F-001` | `FEAT-001` | 否（数字保留）|
| `T-001` | `TASK-001` | 否（数字保留）|
| `INS-018` (split) | `ADR-022` / `PATTERN-022` / `NOTE-018` | **是**（split 时新分配，沿用类型递增序）|

**原则**：rename 类型保留数字，split / merge 类型按新类型现有最大编号 +1。

## 与 ms-iteration-policy 的协调

DevDocs layout 迁移**强制依赖** `ms-iteration-policy` 检测：

- 若项目同时存在 stage naming 反模式（如 V0.9.x 字面占位）→ surface 警告
- 推荐先跑 `/ms-iteration-policy` 处理 stage naming 反模式，再跑 layout 迁移
- 否则迁移日志会混入版本号占位（如 `INS-018 V0.9.x → ADR-022 V0.9.x`）

## 引用关系

| 引用本文件的位置 | 引用目的 |
|---------|----|
| `skills/pipeline/SKILL.md` § `realign --scope=layout` | 主入口（`--docs-layout` 为 legacy alias）|
| `layout-versioning-policy.md` | 升级路径 |
| `aliases-yml-schema.md` | alias 条目生成规则 |
| `skill-compatibility-matrix.md` | 兼容性影响 |
| `templates/layout-migration-log.md` | dry-run 报告模板 |

## 变更日志

| 日期 | 变更 | 触发 |
|------|------|------|
| 2026-05-15 | 初始版本（v1 → v2 矩阵）| DevDocs 治理体系升级（6 大支柱 #6）|
