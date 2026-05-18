# Layout Migration Log Template

> `/ms-pipeline realign --docs-layout` 执行时的日志模板。
>
> 写入位置：`docs/devdocs/.layout-migration-dryrun.md`（dry-run 阶段）+ `docs/devdocs/.layout-migration-applied.md`（apply 阶段，自动 commit）
>
> ⚠️ **执行接口当前状态**：本模板提及的所有迁移命令落地状态见 [skills/pipeline/references/layout/docs-layout-migration.md § 执行接口落地状态（FUTURE）](../references/layout/docs-layout-migration.md#-执行接口落地状态future)。本模板可作为后续落地的输出契约参考。
>
> ℹ️ 模板样例中出现的 `@satisfies` / `@verifies` 是 **layout.v1 legacy** 代码注释（作为本迁移工具的**输入对象**，由 dry-run 提取到 traceability.yml）。

## 模板（dry-run）

```markdown
---
type: layout-migration-dryrun
generated_at: "<ISO 时间戳>"
generator: ms-pipeline realign --docs-layout --dry-run
project_layout_from: layout.v1
project_layout_to: layout.v2
id_scheme_from: id.v1
id_scheme_to: id.v2
traceability_from: trace.v0
traceability_to: trace.v1
---

# Layout Migration Dry-Run Report

**项目**：`<project-name>`
**当前分支**：`<git-branch>`
**当前 commit**：`<git-rev-parse HEAD>`
**目标版本**：layout.v1 → v2 + id.v1 → v2 + trace.v0 → v1

## 摘要

| 维度 | 数量 |
|------|------|
| 文件操作（rename / move / create / delete）| `<n>` |
| aliases.yml 待写入条目 | `<n>` |
| 无法映射项（需人工干预）| `<n>` |
| 旧路径引用（cross-link 待修复）| `<n>` |
| traceability 漂移项 | `<n>` |
| **总变更点** | `<n>` |
| **可自动执行** | `<n>` |
| **需人工 review** | `<n>` |

## 1. 计划变更（File Operations Plan）

### 1.1 重命名 / 移动

| from | to | type | auto_fixable |
|------|----|------|--------------|
| docs/devdocs/05-bugfix-log.md | docs/devdocs/issues/index.md + 拆 77 files | split-to-folder | 需人工 review |
| docs/devdocs/04-dev-tasks.md | docs/devdocs/tasks/index.md + 拆 N files | split-to-folder | 需人工 review |
| docs/devdocs/00-context.md | docs/devdocs/context.md | move | ✅ |
| docs/devdocs/patterns/hygiene-decision-tree.md | docs/devdocs/patterns/PATTERN-001.md | rename | ✅ |
| ... | ... | ... | ... |

### 1.2 新建

- `docs/devdocs/aliases.yml`（空 schema 初始化）
- `docs/devdocs/traceability.yml`（空 schema 初始化）
- `docs/devdocs/index.md`（全局编号索引）
- `docs/devdocs/requirements/index.md`
- `docs/devdocs/design/decisions/`（目录）
- ...

### 1.3 删除

> ⚠️ 删除走 archive 外仓策略，本阶段不直接删除。所有 v1 文件迁移完成后，原文件由 `/ms-pipeline realign --docs-layout --archive-v1` 单独打包到外仓。

## 2. aliases.yml 待写入条目（Alias Map）

```yaml
# 待写入 docs/devdocs/aliases.yml
aliases:
  - { from: BUG-001, to: ISSUE-001, type: rename, since: "2026-05-15" }
  - { from: BUG-002, to: ISSUE-002, type: rename, since: "2026-05-15" }
  - ... (77 BUG → ISSUE)
  
  - { from: F-001, to: FEAT-001, type: rename, since: "2026-05-15" }
  - ... (N F → FEAT)
  
  - { from: T-001, to: TASK-001, type: rename, since: "2026-05-15" }
  - ... (N T → TASK)
  
  - { from: patterns/hygiene-decision-tree.md, to: patterns/PATTERN-001.md, type: rename-only-file, id_unchanged: PATTERN-001 }
  - ... (41 patterns rename-only-file)
```

**总计**：`<n>` 条 aliases 待写入。

## 3. 无法映射项（Unmappable Items）

需要人工归类 / 决策后才能继续。

| ID | 原因 | 建议操作 |
|----|------|--------|
| INS-001 | type=split 需人工归类（决策 / 经验 / 一次性） | `/ms-pipeline realign --classify-ins INS-001` |
| INS-002 | type=split 需人工归类 | `/ms-pipeline realign --classify-ins INS-002` |
| ... | ... | ... |

**总计**：`<n>` 项需人工干预。

## 4. 旧路径引用（Broken Cross-Links）

迁移后会失效的 cross-link 清单。

### 4.1 自动可修复

| source | line | 旧引用 | 新引用 | auto_fixable |
|--------|------|--------|--------|--------------|
| docs/devdocs/02-system-design.md | 1247 | `详见 04-dev-tasks-p11.md § T-107` | `详见 tasks/TASK-107.md` | ✅ |
| docs/devdocs/05-bugfix-log.md | 892 | `patterns/hygiene-decision-tree.md` | `patterns/PATTERN-001.md` | ✅ |
| ... | ... | ... | ... | ✅ |

**总计**：`<n>` 项可自动修复。

### 4.2 需人工 review

| source | line | 旧引用 | 问题 |
|--------|------|--------|------|
| docs/devdocs/00-context.md | 42 | `06-insights.md § INS-018` | INS-018 是 split，需先归类后再决定引用目标 |
| ... | ... | ... | ... |

**总计**：`<n>` 项需人工 review。

## 5. traceability 漂移项（Traceability Drift）

trace.v0 → v1 迁移时代码注释提取结果。

### 5.1 自动解析

| file | line | annotation | resolution |
|------|------|------------|------------|
| `trade/src/.../FundService.java` | 142 | `@satisfies AC-001` | 写入 traceability.yml（symbol: FundService#processSlip） |
| `trade/src/.../SlipMatcher.java` | 88 | `@verifies T-105` | 通过 aliases.yml 解析 T-105 → TASK-105，写入 trace |
| ... | ... | ... | ... |

**总计**：`<n>` 项自动解析。

### 5.2 需人工 review

| file | line | annotation | 问题 |
|------|------|------------|------|
| `trade/src/.../X.java` | 42 | `@satisfies AC-999` | AC-999 不存在于 requirements/ 或 aliases.yml |
| `trade/src/.../Y.java` | 88 | `@satisfies AC-001` | symbol 'OldName#method' 未找到（疑似已重命名）|
| ... | ... | ... | ... |

**总计**：`<n>` 项需人工 review。

## 6. 不可逆操作清单（Irreversible Operations）

⚠️ 以下操作执行后无法通过本工具自动回滚，**必须 git branch 隔离 + 用户显式确认**：

- [ ] 文件 split（04-dev-tasks.md → tasks/TASK-NNN.md）
- [ ] 文件 split（05-bugfix-log.md → issues/ISSUE-NNN.md）
- [ ] 文件 split + 编号 split（06-insights.md → ADR / PATTERN / NOTE）
- [ ] 文件合并（02-system-design.md + -api.md + -data.md → design/current.md）
- [ ] 目录结构重组（顶层 NN-XX 文件 → 子目录）

**回滚方式**：`git reset --hard <pre-migration-commit>` 或切回主分支。

## 7. 执行检查清单

apply 前必须确认：

- [ ] 在独立 git branch（非 main/master）
- [ ] 当前 commit 为干净状态（`git status` 无未提交变更）
- [ ] 所有 unmappable 项已处理（节 3 数量 = 0 或用户接受）
- [ ] 已审阅节 6 不可逆操作清单
- [ ] 已备份 `.layout-migration-dryrun.md`（本文件）
- [ ] mic-en 演练场景：已对照 codex review 反馈

## 8. 下一步

通过本 dry-run 报告后执行：

```bash
# 处理 unmappable（如有）
/ms-pipeline realign --classify-ins INS-001
/ms-pipeline realign --classify-ins INS-002
# ...

# 实际迁移
/ms-pipeline realign --docs-layout --apply

# 后置校验
/ms-verify --layout-drift
/ms-verify --ssot-lint

# 提交
git add docs/
git commit -m "chore(devdocs): migrate layout.v1 → v2 via /ms-pipeline realign"
```
```

## 模板（apply）

apply 阶段额外记录：

```markdown
---
type: layout-migration-applied
generated_at: "<ISO 时间戳>"
generator: ms-pipeline realign --docs-layout --apply
based_on: docs/devdocs/.layout-migration-dryrun.md
project_layout_from: layout.v1
project_layout_to: layout.v2
applied_commit: <git-rev-parse HEAD>
---

# Layout Migration Applied Report

**dry-run 报告**：`docs/devdocs/.layout-migration-dryrun.md`（迁移前的预期）
**实际执行差异**：与 dry-run 预期对比，列出偏差

## 实际执行 vs dry-run 预期

| 类别 | 预期 | 实际 | 差异 |
|------|------|------|------|
| 文件操作 | <n> | <n> | <差异> |
| aliases 条目 | <n> | <n> | <差异> |
| traceability 提取 | <n> | <n> | <差异> |

## 失败项（如有）

| 操作 | 失败原因 | 处理 |
|------|--------|------|
| ... | ... | ... |

## 后置校验结果

- `ms-verify --layout-drift`: ✅ / ❌
- `ms-verify --ssot-lint`: ✅ / ❌
- AGENTS.md devdocs frontmatter `upgraded_at`: 已更新到 `<日期>`

## 引用

- dry-run 报告：[.layout-migration-dryrun.md](.layout-migration-dryrun.md)
- 治理规范：[layout-versioning-policy.md](../../skills/pipeline/references/layout/layout-versioning-policy.md)
```

## 使用规则

- **dry-run 报告**位置：`docs/devdocs/.layout-migration-dryrun.md`（git ignored）
- **apply 报告**位置：`docs/devdocs/.layout-migration-applied.md`（自动 commit，作为迁移凭证）
- 报告文件名前缀 `.` 表示工具产物，不进入业务索引
- 每次 dry-run 覆盖上次报告；apply 报告 append-only（每次迁移追加新章节）
