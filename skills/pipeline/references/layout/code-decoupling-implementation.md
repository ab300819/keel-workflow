# Code Decoupling Implementation（#4 代码解耦实施规范）

> 把 [layout-metadata-schema.md § traceability.yml schema](layout-metadata-schema.md#4-traceabilityyml-schematracev1) 的 trace.v1 声明从"schema 层"落实到"执行层"：CLI 入口、抽取算法、写入 API、legacy 注释保留窗口、多仓聚合策略。
>
> 与 [folder-organization-implementation.md](folder-organization-implementation.md) / [ssot-lint-implementation.md](ssot-lint-implementation.md) 同级：本文件治理**代码侧追溯机制**，解决"DevDocs 不污染代码注释"的根本约束。

## ⚠️ 执行接口当前状态

本文件描述的 `/ms-sync --extract-trace` / `--refresh-traceability` / `--multi-repo` 均依赖 [FUTURE] 接口，详见 [docs-layout-migration.md § 执行接口落地状态（FUTURE）](docs-layout-migration.md#-执行接口落地状态future)。

当前阶段（#4 spec 起草）**只产出规范**，runtime 实现由后续阶段落地。`ms-sync` 现有 `--archive` / `--all` 等子命令保持不变；`--extract-trace` 等作为新增子命令，未实现前不可调用。

## 定位

| 治理对象 | 文件 |
|---------|------|
| trace.v1 schema 声明 | [layout-metadata-schema.md § 4](layout-metadata-schema.md#4-traceabilityyml-schematracev1) |
| legacy 注释禁止新增检测 | [ssot-lint-implementation.md § baseline 机制](ssot-lint-implementation.md#baseline-管理) |
| **本文件**：traceability 写入 API + 抽取算法 + legacy 保留窗口 + 多仓聚合 | code-decoupling-implementation.md |
| 编号体系前置依赖 | [id-scheme-implementation.md](id-scheme-implementation.md) |

## 根本原则

**代码是唯一事实源，DevDocs 是辅助**。`@satisfies` / `@verifies` 注释污染代码（公共项目场景下不可接受），改为**外置 traceability.yml**承载追溯关系。

### 不可接受的代码内污染

```typescript
// ❌ layout.v1 模式（注释侵入代码）
/**
 * @satisfies AC-001
 * @verifies UT-001
 */
function validateEmail(email: string): boolean { ... }
```

### layout.v2 目标态

```yaml
# docs/devdocs/traceability.yml（外置追溯）
links:
  - id: AC-001
    kind: implements
    repo: main
    path: src/services/user.ts
    symbol: validateEmail
    commit: abc1234
    tests: [UT-001]
```

```typescript
// ✅ layout.v2 模式（代码干净）
function validateEmail(email: string): boolean { ... }
```

## CLI 入口

`/ms-sync` 既有命令体系扩展，加入 3 个新子命令：

| 命令 | 行为 |
|------|------|
| `/ms-sync --extract-trace` | **一次性迁移命令**：从 layout.v1 代码 `@satisfies` / `@verifies` 注释抽取，生成 trace.v1 link 写入 `traceability.yml`。仅 layout.v1 → v2 迁移期间用 |
| `/ms-sync --extract-trace --dry-run` | 列出将提取的 link 但不写入；可与 `--apply` 配合 |
| `/ms-sync --extract-trace --apply` | 实际写入 `traceability.yml`；自动备份原文件到 `_archived/traceability-pre-extract-<timestamp>.yml` |
| `/ms-sync --refresh-traceability` | 刷新过期 link 的 commit + lines 字段；不修改 id/path/symbol |
| `/ms-sync --refresh-traceability --rule <stale-only / all>` | 范围控制：仅刷新 stale 或全量刷新 |
| `/ms-sync --multi-repo --discover` [FUTURE] | layout.v3 候选：扫描子模块发现独立 `.devdocs-trace.yml` 并聚合 |
| `/ms-sync --multi-repo --merge` [FUTURE] | layout.v3 候选：合并子模块 trace 到主仓 traceability.yml |

### 退出码

| 退出码 | 含义 |
|--------|------|
| 0 | 成功（无 stale / 无冲突）|
| 1 | 成功但有 warning（stale links / 软校验失败）|
| 2 | 有 P0 错误（schema 不匹配 / aliases.yml 中 id 不存在 / path 不可访问）|
| 3 | sync 自身运行错误 |

## 从代码注释抽取算法

### 扫描范围

- 默认扫描白名单文件类型（**与 symbol 提取规则同步收敛**）：`.ts` / `.tsx` / `.js` / `.jsx` / `.py` / `.go` / `.java`
- Ruby / Rust / Kotlin / Swift / C# 等语言**不在 v1 支持范围**（symbol 规则未定义，强制扫描会产生大量 `confidence: low` fallback）；后续 spec bump 增加语言支持时同步扩展 symbol 规则
- 排除目录（硬编码）：`node_modules` / `dist` / `build` / `target` / `vendor` / `.git` / `.venv` / `__pycache__` / `coverage` / `.next` / `.gradle` / `out` / `bin` / `obj`
- 用户可通过 `.extract-trace-ignore`（gitignore 语法）追加排除规则

### 注释模式匹配

支持的注释形式：

```typescript
/**
 * @satisfies AC-001
 * @verifies UT-001, IT-005
 */

// @satisfies FEAT-001
function foo() {}

# Python 风格
# @satisfies AC-001
def bar(): pass

# Go / Java / 类 C
// @satisfies AC-001
// @verifies UT-001
```

正则模式：
- `@satisfies\s+([A-Z]+-\d{3,})(?:\s*,\s*([A-Z]+-\d{3,}))*`
- `@verifies\s+([A-Z]+-\d{3,})(?:\s*,\s*([A-Z]+-\d{3,}))*`

### symbol 提取算法

从注释邻近代码（注释下方 3 行内）提取 symbol：

| 语言 | symbol 格式 | 提取规则 |
|------|-----------|---------|
| TypeScript/JavaScript | `<file-stem>:<export-name>` 或 `<ClassName>#<methodName>` | grep `export\s+(function\|const\|class)\s+(\w+)` + `(\w+)\s*\(` |
| Python | `<module>.<ClassName>.<method>` | grep `def\s+(\w+)` / `class\s+(\w+)` |
| Go | `<package>.<FuncName>` 或 `<Receiver>.<Method>` | grep `func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\(` |
| Java | `<ClassName>#<methodName>` | grep `(?:public\|private\|protected)?\s+\w+\s+(\w+)\s*\(` |

提取失败时 fallback：`<path>:line-<注释行号>`。

### kind 推断

- `@satisfies` → `kind: implements`
- `@verifies` → `kind: verifies`
- 注释中含 TODO/FIXME/XXX 引用编号 → `kind: mentions`

### 抽取冲突处理

| 冲突类型 | 处理 |
|---------|------|
| 同一 (id, kind, symbol, path) 已存在 | 保留旧 link，新增 link 标 `confidence: low` + `notes: "duplicate during extract"` |
| id 不在 aliases.yml 或 index.md | 报 `extract-trace/unknown-id` 错误，跳过该 link，写入报告 |
| path 已删除（代码已重构）| 报 `extract-trace/path-missing`，**不写入 traceability.yml**；改为写入 `_archived/extract-trace-orphans-<timestamp>.yml`（保留排查信息但不污染主 schema）|
| symbol 提取失败 | fallback `<path>:line-N`，标 `confidence: low` + `notes: "symbol-fallback"` |

> ⛔ **kind 枚举只能是 `implements` / `verifies` / `mentions`**（trace.v1 schema 硬约束）。失效/过期/废弃语义通过 `confidence: low` + `notes` 表达，或移入 `_archived/` 留痕；**禁止**新增 `kind: deprecated` / `kind: stale` 等枚举外值。

### dry-run 报告格式

```markdown
# Extract Trace Report (dry-run)

- **Repo**: main
- **Scope**: 全量扫描
- **Files scanned**: 234
- **Total comments matched**: 487
- **Will write**: 480 links
- **Skipped**: 7 (unknown id / path missing)

## Will Write
- AC-001 implements src/services/user.ts:validateEmail (line 42-58, commit abc1234)
- UT-001 verifies tests/unit/user.test.ts:test_validateEmail (line 12-30, commit abc1234)
...

## Skipped
- src/legacy/old.ts:42 - `@satisfies AC-999` (id not found)
- src/refactored/new.ts:15 - `@verifies UT-002` (path resolves but symbol "removed_func" not found in current commit)
```

## 写入 API

`traceability.yml` 不应手编（schema 严格）。提供两类写入入口：

### 1. 编排层调用（自动触发）

| 调用方 | 时机 | 行为 |
|--------|------|------|
| `ms-dev-workflow` Commit 2 | 任务完成 + Code Commit 完成后 | 写入当前任务关联的 link（id + kind + repo + path + symbol + commit） |
| `ms-sync --extract-trace` | 一次性迁移 | 批量写入提取的 link |
| `ms-sync --refresh-traceability` | 用户触发 / 定期任务 | 刷新 stale link 的 commit + lines |
| `ms-pipeline realign --scope=layout` | layout 升级 | 初始化空 traceability.yml + frontmatter |

### 2. 手动编辑（受限）

仅允许编辑的字段：
- `notes` — 人工备注
- `confidence` — 升级判断（low → medium → high）
- `tests` — 关联测试编号补充

**禁止手编**：
- `id` / `kind` / `repo` / `path` / `symbol` / `commit` — 由 API 维护，手编会导致 schema lint 不通过

### 写入冲突解决

API 内部按以下优先级解决：

```text
1. 唯一性键：(id, kind, repo, path, symbol) 五元组
   理由：同一 (id, repo, path, symbol) 可同时有 implements + verifies + mentions 三种 kind；
        若仅按 4 元组判定会误覆盖。
2. 已存在 link，按 git ancestor 关系（不直接比较 hash 大小）：
   - new.commit 是 existing.commit 的 descendant（在同 repo 内 git merge-base --is-ancestor existing new == 0）→ 更新 commit + lines
   - 同 commit → no-op
   - new.commit 是 existing.commit 的 ancestor → 拒绝写入，报 `traceability/stale-write`
   - 无 ancestor 关系（不同分支历史）→ AskUserQuestion 让用户选择保留哪一个 + 写入决策记录到 _archived/
3. 不存在 → append 新 link
```

> ⚠️ commit ancestor 比较**仅限同 repo 内**；跨 repo 的 commit hash 不可直接比较。多仓项目的 ancestor 比较走子模块本地 git，由调用方在 walk submodules 时分别检查。

### API 接口（伪代码）

```typescript
// 由 ms-sync / ms-dev-workflow 内部调用
interface TraceabilityWriter {
  writeLink(link: TraceLink, mode: 'create' | 'update' | 'upsert'): WriteResult;
  removeLink(filter: { id, repo, path, symbol }): RemoveResult;
  refreshStale(filter?: { repo? }): RefreshResult;
  initEmpty(layout: 'layout.v2'): InitResult;
}
```

具体实现细节 [FUTURE]；本规范仅定义接口契约。

## legacy 注释保留窗口

### 时序

| layout 版本 | 代码注释 `@satisfies` / `@verifies` 行为 |
|------------|----------------------------------------|
| layout.v1 | ✅ 主要追溯机制 |
| layout.v2 | ⚠️ legacy retained：保留现有注释不报错；**禁止新增**（`ssot/legacy-annotation-additions` baseline 检测）|
| layout.v3 | ⛔ 完全删除：lint 报错；强制 `traceability.yml` 唯一追溯源 |

### v2 → v3 迁移路径（informational，非本阶段承诺）

`/ms-sync --strip-legacy-annotations` [FUTURE，layout.v3 阶段] 用于批量删除代码内 legacy 注释：

```text
1. 全量扫描代码注释
2. 对比 traceability.yml：若 (id, path, symbol) 已存在则可安全删除
3. 若不存在 → 先写入 traceability.yml 再删除注释
4. 生成 commit："chore: strip legacy @satisfies/@verifies annotations (layout.v3)"
```

### 兼容性窗口长度

- layout.v2 → v3 升级**至少间隔 1 个项目周期**（默认 ≥ 6 个月）
- 项目可通过 AGENTS.md `devdocs.legacy_annotation_grace_period: "2026-12-31"` 显式设置截止日期
- 截止日期前 30 天，`ms-verify --layout-drift` 报 P1 warning 提醒迁移

## 多仓库聚合

### layout.v2（当前）

**单文件主仓策略**：

```text
main-repo/
  docs/devdocs/traceability.yml         # 唯一 traceability，含跨子模块全部 link
  submodule-a/                          # git submodule，代码仓
  submodule-b/                          # git submodule，代码仓
```

`traceability.yml` 通过 `repo` 字段区分跨子模块 link：

```yaml
links:
  - id: FEAT-001
    repo: submodule-a
    path: services/user.ts
    ...
  - id: FEAT-002
    repo: submodule-b
    path: api/order.go
    ...
```

**优点**：简单，无聚合开销。
**缺点**：主仓 + 子模块的 commit 关系手动维护；submodule update 后需手动 `--refresh-traceability`。

### layout.v3 候选（informational）

**子模块独立 trace + 主仓聚合**：

```text
main-repo/
  docs/devdocs/traceability.yml         # 聚合文件，自动从子模块合并
  submodule-a/
    .devdocs-trace.yml                  # 子模块自己的 trace
  submodule-b/
    .devdocs-trace.yml
```

`/ms-sync --multi-repo --merge` [FUTURE] 自动 walk 所有 git submodule，读 `.devdocs-trace.yml`，merge 到主仓 `traceability.yml`：

```text
merge 规则（按完整 link key 合并，不按 id 覆盖）：
  - 唯一性键沿用写入 API 的五元组 (id, kind, repo, path, symbol)
  - 子模块产出的 link 由其 `.devdocs-trace.yml` 自带 `repo: <submodule-name>` 字段（不再 prefix path）
  - 同一 id 跨多 repo 的不同 link 均合法保留（前端 + 后端实现同一 FEAT）；不互相覆盖
  - 同 repo + 同 (id, kind, path, symbol) 重复 → 走"写入冲突解决"的 ancestor 规则（commit 比较仅限同 repo）
  - 跨 repo 的 commit hash 不可比较；不同 repo link 永远 coexist
  - 主仓自有 link 与子模块同 key link 冲突：主仓优先（手动维护权重更高）
```

### 跨语言项目

多语言项目（如前后端混合）按 `repo` 字段区分，所有抽取算法对每种语言独立运行：

```yaml
links:
  - id: FEAT-001
    repo: frontend
    path: src/pages/LoginPage.tsx
    symbol: LoginPage:default
  - id: FEAT-001
    repo: backend
    path: src/main/java/.../LoginController.java
    symbol: LoginController#login
```

同一 id 关联多语言实现是合法的。

## 与 ssot-lint 集成

### ssot/legacy-annotation-additions 自动修复

[ssot-lint-implementation.md § 自动修复支持矩阵](ssot-lint-implementation.md#自动修复支持矩阵) 把此 rule 标 `❌ 不支持`，原因是修复涉及"写入 traceability.yml + 删除注释"两步动作。本文件提供完整修复路径：

```text
ssot/legacy-annotation-additions 修复流程（半自动）：

1. lint 检出违规行
   src/services/user.ts:42 - 新增 `@satisfies AC-001` 注释
   
2. AskUserQuestion 询问用户（三个合法选项 + 一个受控豁免）：
   a. 写入 traceability.yml + 删除注释（推荐）
   b. 不追溯，仅删除注释
   c. 受控豁免：仅在确有不能立即修复的特殊情况时使用，需指定 expiry + 关联 ISSUE
   
3. 用户选 a → 调用 TraceabilityWriter.writeLink + git apply patch 删除注释
4. 用户选 b → git apply patch 删除注释（不写 trace；适用于临时 prototype 代码）
5. 用户选 c → 写入 `.ssot-lintignore-waivers.yml`：
   ```yaml
   waivers:
     - file: src/services/user.ts
       line: 42
       rule: ssot/legacy-annotation-additions
       expiry: "2026-06-30"        # 必填，max +90 天
       issue: ISSUE-042            # 必填，关联到追踪 ISSUE
       reason: "<原因>"             # 必填
   ```
   - expiry 过期后 lint 自动恢复报错
   - 任何 waiver 必须有未关闭的 ISSUE 关联（lint 同步检查 ISSUE 状态，已关闭则 waiver 失效）

> ⛔ **禁止"仅记录，保留注释"作为正常选项**：layout.v2 期间 `ssot/legacy-annotation-additions` 是硬约束；保留注释会破坏 baseline diff 语义。任何保留必须走 c 的受控豁免，不能默默忽略。
```

### baseline 语义（明确不同步任务用不同基线）

`ssot/legacy-annotation-additions` 和 `extract-trace` 使用 baseline commit 的方式**不同**，必须区分：

| 操作 | 扫描对象 | baseline 用途 |
|------|---------|--------------|
| `extract-trace` 一次性迁移 | **当前 working tree 的全量 legacy 注释**（不依赖 baseline 时间窗）| 仅用于"标记本次抽取的起点 commit"，写入 traceability.yml 各 link 的 `commit` 字段 |
| `extract-trace --since <commit>` | 仅扫描自 `<commit>` 以来变化文件中的 legacy 注释 | 用户显式指定增量抽取范围（非默认行为）|
| `ssot/legacy-annotation-additions` lint | git diff `baseline-commit..HEAD` 的新增 `+` 行 | 用 baseline 区分 "升级前 legacy 保留" vs "升级后新增违规" |

> ⚠️ **不要把这两者混为一谈**：`extract-trace` 默认全量扫描当前代码（迁移场景），lint 默认 diff 模式（守门场景）。让两者共享同一 baseline commit 仅在用户显式 `extract-trace --since <baseline>` 时成立。

### 衔接迁移流程

典型 layout.v1 → v2 迁移序列：

```text
1. /ms-pipeline realign --scope=layout
     ├── 创建 baseline (commit B0)
     ├── 调用 ms-sync --extract-trace --dry-run（全量扫描 B0 时刻代码）
     ├── AskUserQuestion 确认
     └── 调用 ms-sync --extract-trace --apply（写入 traceability.yml）

2. 后续开发：
     ├── ssot/legacy-annotation-additions 以 B0 为 baseline，diff 模式检查新增
     └── 任何新增违规 → 走 § 半自动 fix 流程
```

## 验证规则

`ms-verify --layout-drift` [FUTURE] 应额外检测：

| 检测项 | 触发 | 严重度 |
|--------|------|--------|
| `traceability.yml` 缺失 | 文件不存在 | P0 |
| schema version 不匹配 | `version: trace.v0` 在 layout.v2 项目 | P0 |
| 链接 id 不在 index | id 不存在于 `aliases.yml` 或对应 `<type>/index.md` | P0 |
| 链接 path 不可达 | path 在当前 commit 不存在 | P1 |
| 链接 symbol 失效 | path 存在但 symbol 提取失败 | P1 |
| 链接 commit 过期 | git_log_count(commit, HEAD) > 30 | P1 (stale) |
| layout.v2 代码新增 legacy 注释 | 见 ssot-lint | P1 |

## frontmatter 升级规则（条件性）

各 skill `writes_traceability` 字段保持 `trace.v0`（当前 transitional state）。**升级到 trace.v1 的触发条件（必须 1+2+3+4 全满足）**：

1. 本文件 + layout-metadata-schema.md 已 FINAL-GO ✅
2. `ms-sync --extract-trace` / `--refresh-traceability` SKILL.md 已加双轨说明 ⏳
3. Runtime 抽取算法 + 写入 API [FUTURE] 已实现 ⏳
4. 至少 1 个 v2 项目已成功跑过完整 v0→v1 迁移 ⏳

> ⛔ **禁止仅凭 1+2 升级**：满足 1+2 仅代表 spec 准备完成，runtime 行为仍是 trace.v0（依赖代码注释）。提前升级会触发"声明先行陷阱"。必须 1+2+3+4 全满足才可改：
>
> ```yaml
> writes_traceability: trace.v0   # 当前
> writes_traceability: trace.v1   # 仅当 1+2+3+4 全满足后升级
> ```
>
> 恢复方式：发现提前升级时，立即回退到 `trace.v0` 并补齐 3/4 条件。

`writes_layout: layout.v2` 升级时**强制同步**升级 `writes_traceability: trace.v1`（按 [layout-versioning-policy.md § 版本号依赖关系](layout-versioning-policy.md#版本号依赖关系) 的强依赖：`layout.v2 → trace.v1`）。

## 历史项目兼容（mic-en 等）

- **mic-en 等 layout.v1 项目**：维持代码注释追溯，**不动**现有 636 处 `@satisfies` / `@verifies`
- 用户主动调用 `/ms-pipeline realign --scope=layout` [FUTURE] 时：
  1. `realign` 内部调用 `/ms-sync --extract-trace --dry-run` 预览
  2. AskUserQuestion 用户确认
  3. `--apply` 写入 traceability.yml + 保留代码注释（layout.v2 期间）
- 本阶段（#4）**不执行** mic-en 迁移；仅完成 spec

## 性能与边界

| Repo 规模 | extract-trace 全量预期 | refresh-traceability |
|-----------|---------------------|---------------------|
| < 1000 文件 | < 10s | < 2s |
| 1000-10000 文件 | < 60s | < 10s |
| > 10000 文件 | 推荐 `--multi-repo` 拆分 | 推荐 `--rule stale-only` |

### 不支持的边界

- ❌ 二进制文件：跳过
- ❌ 编译产物（min.js / .pyc 等）：跳过
- ❌ Symlinks：按目标文件解析；循环 symlink 报 `extract-trace/symlink-cycle`
- ❌ 非 UTF-8 文件：报 `extract-trace/encoding-error` 跳过
- ❌ 字符串内的伪注释：**必须用词法级解析（Tree-sitter / language-server）排除**；不允许纯 regex 扫描（会误匹配字符串中的 `@satisfies` 字面量）。无 Tree-sitter 支持的语言不在白名单

## 与其他阶段的接口

| 阶段 | 接口点 |
|------|-------|
| #1 编号体系 | 抽取算法识别全部 11 类编号前缀（FEAT/STORY/AC/TASK/ISSUE/ADR/PATTERN/NOTE/UT/IT/E2E）；aliases.yml 自动解析旧编号 → 新编号 |
| #2 文件夹组织 | traceability.yml 落点 `docs/devdocs/traceability.yml` 在 core tree 中；index.md 引用 link 编号时 lint 检查 |
| #3 SSOT lint | `ssot/legacy-annotation-additions` 检测（baseline 机制）+ 半自动 fix 流程在本文件定义 |
| #5 迭代蒸馏 | 本文件 § extract-trace dry-run 报告可作为蒸馏期 legacy 数量统计源；蒸馏后 stale link 清理由 #5 定义 |

## 引用关系

| 引用本文件的位置 | 引用目的 |
|------------|---------|
| `skills/sync/SKILL.md` § `--extract-trace` / `--refresh-traceability` | 子命令文档化（待 #4 落地后加）|
| `skills/dev-workflow/SKILL.md` § Commit 2 | 单 link 写入触发点 |
| `skills/pipeline/SKILL.md` § realign | `--scope=layout` 内部调用 extract-trace |
| `ssot-lint-implementation.md` § ssot/legacy-annotation-additions | 修复流程引用本文件 |

## 变更日志

| 日期 | 变更 |
|------|------|
| 2026-05-18 | 初始版本（#4 代码解耦实施规范）|
