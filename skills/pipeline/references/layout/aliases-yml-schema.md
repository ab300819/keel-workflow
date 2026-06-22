# aliases.yml Schema（编号别名映射）

> 治理 DevDocs 编号迁移的兼容载体。文件位置：`docs/devdocs/aliases.yml`（单文件版，必须存在即使空）。
>
> 本文件被 [layout-versioning-policy.md](layout-versioning-policy.md) 与 [layout-metadata-schema.md](layout-metadata-schema.md) 引用。
>
> ⚠️ **执行接口当前状态**：本文件提及的 `/ms-pipeline realign --scope=layout` 等命令落地状态见 [docs-layout-migration.md § 执行接口落地状态（FUTURE）](docs-layout-migration.md#-执行接口落地状态future)。

## 定位

`aliases.yml` 解决三类编号变更的兼容问题：

| 类型 | 场景 | 示例 |
|------|------|------|
| **rename** | 编号前缀改名 | `BUG-001` → `ISSUE-001` |
| **split** | 编号语义拆分到多个新编号 | `INS-018` → `ADR-022` + `PATTERN-022` |
| **merge** | 多个旧编号合并为一个新编号 | `T-105` + `T-106` → `TASK-105` |
| **rename-only-file** | 仅文件名改变（编号不变）| `patterns/hygiene-decision-tree.md` → `patterns/PATTERN-001.md` |

**核心契约**：
- 历史 commit / docs / 代码注释中引用旧编号时，工具链通过 aliases.yml 自动解析到新编号
- 不需要 hard-rewrite 历史

## Schema

### 完整 schema 定义（alias.v1）

```yaml
---
version: alias.v1
project_layout: layout.v2
generated_at: "2026-05-15T10:00:00Z"
last_modified: "2026-05-15T10:00:00Z"
---

aliases:
  # rename 类型（编号改名）
  - from: BUG-001
    to: ISSUE-001
    type: rename
    since: "2026-05-15"
    reason: "BUG → ISSUE 对齐 GitHub/GitLab Issue 社区标准"
    bidirectional: true                    # 双向解析（旧→新 + 新→旧 lookup）

  # 文件名 only rename（编号本身不变，仅文件位置/命名变）
  - from: patterns/hygiene-decision-tree.md
    to: patterns/PATTERN-001.md
    type: rename-only-file
    since: "2026-05-15"
    id_unchanged: PATTERN-001               # 编号本身（用于 rename-only-file）

  # split 类型（一编号拆为多个）
  - from: INS-018
    to: ADR-022
    type: split
    sub: decision                            # split 子类型
    since: "2026-05-15"
    reason: "INS-018 含决策语义部分迁移到 ADR-022"

  - from: INS-018
    to: PATTERN-022
    type: split
    sub: pattern
    since: "2026-05-15"
    reason: "INS-018 含经验沉淀部分迁移到 PATTERN-022"

  - from: INS-018
    to: NOTE-018
    type: split
    sub: note
    since: "2026-05-15"
    reason: "INS-018 含一次性观察部分迁移到 NOTE-018"

  # merge 类型（多编号合并）
  - from: T-105
    to: TASK-105
    type: merge
    since: "2026-05-15"
  - from: T-106
    to: TASK-105
    type: merge
    since: "2026-05-15"
    reason: "T-105 + T-106 合并为单一 TASK-105"
```

### 字段语义

| 字段 | 类型 | 必填 | 说明 |
|------|------|----|------|
| `from` | str | ✅ | 旧编号 或 旧文件路径（rename-only-file 类型用文件路径）|
| `to` | str | ✅ | 新编号 或 新文件路径 |
| `type` | enum | ✅ | `rename` / `split` / `merge` / `rename-only-file` |
| `since` | ISO date | ✅ | 变更生效日期 |
| `sub` | str | type=split 时必填 | split 子分类标识 |
| `id_unchanged` | str | type=rename-only-file 时必填 | 不变的编号本身 |
| `reason` | str | 推荐 | 变更理由（≤200 字）|
| `bidirectional` | bool | 可选，默认 true | 是否双向解析 |
| `deprecated` | bool | 可选，默认 false | 标记该 alias 已废弃，不再解析 |

### 校验规则

#### 严格校验

1. `version` 必须为 `alias.v1`
2. `from` 不可为空，每个 `from` 在同一 type 下只能出现一次（split/merge 例外，可多次）
3. `to` 必须存在于对应 `<type>/index.md`（除非 `deprecated: true`）
4. `since` 必须为有效 ISO 日期（YYYY-MM-DD）
5. `type=split` 时必须有 `sub` 字段
6. `type=rename-only-file` 时 `from` 和 `to` 都必须是文件路径（含 `/`）

#### 软校验（warn 不 block）

7. `reason` 缺失时 warn（建议补全便于审计）
8. 同一 `from` 出现 ≥ 3 次 split 时 warn（split 过细可能设计问题）
9. `from` 与 `to` 跨编号类型（如 `INS → ADR`）必须 `type=split` 或 `type=rename`，不能是裸编号映射

## 解析逻辑

### lookup 算法

```text
输入: 引用编号 ref_id (如 "BUG-001" 或 "INS-018")
  │
  ├─ 1. 在 <type>/index.md 中查找 ref_id（直接匹配）
  │     找到 → 返回当前编号 + 文件路径
  │
  ├─ 2. 未找到 → 在 aliases.yml 中查找 from == ref_id
  │     ├─ rename → 返回 to + recurse lookup(to)
  │     ├─ split → 返回所有 (sub, to) 列表，需调用方决定走哪个 sub
  │     ├─ merge → 返回 to + recurse lookup(to)
  │     └─ rename-only-file → 返回 id_unchanged + 新文件路径
  │
  └─ 3. 都未找到 → surface "未知编号 ref_id"
```

### split 类型的歧义处理

`type=split` 单一旧编号映射到多个新编号。lookup 时返回所有 sub 选项：

```yaml
# 输入 ref_id = "INS-018"，aliases.yml 返回：
matches:
  - { to: ADR-022, sub: decision }
  - { to: PATTERN-022, sub: pattern }
  - { to: NOTE-018, sub: note }
```

调用方场景：
- **docs cross-link**：列出所有 sub 选项让用户选
- **commit message 历史回放**：尝试匹配上下文语义；不可判定时 warn
- **ms-verify 报告**：标注 split 关系，不视为错误

### bidirectional 反向解析

`bidirectional: true`（默认）支持新编号反查旧编号：

```text
查询: "ISSUE-001 的历史编号是？"
返回: BUG-001（来自 aliases.yml 反查）
```

用途：git log 检索 / 历史 PR 关联 / 老文档 cross-link 兼容。

## 维护规则

### 谁写入 aliases.yml

| 触发场景 | 执行者 | 写入时机 |
|---------|------|--------|
| `/ms-pipeline realign --scope=layout` | pipeline | 升级时批量生成 |
| `/ms-pipeline realign --rename-id ID-OLD ID-NEW` | pipeline | 单条 rename |
| 手工编辑 | 维护者 | 特殊修正（需要 git review）|

**禁止**：A/B 类 skill 不应自行写入 aliases.yml（避免散乱），统一通过 pipeline 入口。

### 维护原则

1. **append-only**：已存在的 alias 不修改不删除（保证历史可追溯）
2. **deprecated 标记**：废弃的 alias 标 `deprecated: true`，lookup 时跳过但保留记录
3. **版本注释**：每次批量升级时在文件顶部更新 `last_modified`
4. **审计要求**：每条 alias 建议带 `reason`（便于半年后追溯）

### 增量更新示例

新增一条 rename：

```diff
 aliases:
+  - from: F-042
+    to: FEAT-042
+    type: rename
+    since: "2026-05-15"
+    reason: "F → FEAT 对齐 id.v2"
   - from: BUG-001
     to: ISSUE-001
     ...
```

更新 `last_modified` 字段 + git commit。

## 边界与限制

### 不解决的问题

aliases.yml **不**解决以下场景：

- ❌ 代码内的旧编号引用（注释、变量名）—— 这些走 traceability.yml 或 `/ms-sync --refresh-traceability` [FUTURE]
- ❌ 跨 alias.v1 → alias.v2 的 schema 演进（见下方 alias.v1 → v2 升级规则）
- ❌ 第三方系统（如 Jira / GitLab）的编号同步
- ❌ commit message 中旧编号的批量改写（git log 是 immutable，只能通过 lookup 解析）

### 性能考虑

- aliases.yml 单文件，建议 ≤ 10000 条 entry（超过考虑分文件升级到 alias.v2）
- lookup 性能：O(n)，n 为 entry 数（首次启动 skill 时加载到内存）
- 工具链应缓存 lookup 结果（同一会话内 alias map 不变）

## alias.v1 自身演进规则

### alias.v1 → alias.v2 升级触发条件

| 触发 | 影响 |
|------|------|
| 文件分裂（如按类型拆为多个 yaml）| schema 变化 → bump v2 |
| 新增字段（如 `priority` / `sub-sub` 类型）| 非破坏新增 → 可保持 v1 |
| 删除字段 / 改字段语义 | 破坏性变化 → bump v2 |
| 解析算法变化（如增加 `context` 参数）| 解析协议变化 → bump v2 |

### 升级路径

`alias.v1 → alias.v2` 同样走 `/ms-pipeline realign --scope=layout`（aliases.yml schema 是 layout 治理的一部分）。

### 不可跳跃升级

❌ `alias.v1 → alias.v3` 不允许，必须 `v1 → v2 → v3`。

## 引用关系

| 引用本文件的位置 | 引用目的 |
|---------|----|
| `skills/pipeline/SKILL.md` § realign | 编号迁移机制 |
| `layout-versioning-policy.md` | id.v2 兼容路径 |
| `layout-metadata-schema.md` | 编号清单 alias 字段 |
| `docs-layout-migration.md` | v1 → v2 迁移产生 alias 条目 |
| 所有 A/B 类 skill | 编号解析依赖 |

## 变更日志

| 日期 | 变更 | 触发 |
|------|------|------|
| 2026-05-15 | 初始版本 (alias.v1) | DevDocs 治理体系升级（6 大支柱 #6）|
