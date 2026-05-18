# Distillation Implementation（#5 迭代蒸馏实施规范）

> 把"每次迭代完蒸馏文档，代码是唯一事实源，devdocs 只是辅助"原则落实到执行层：定义蒸馏触发器、13 类蒸馏动作、CLI 入口、安全门、频率建议。
>
> 与 [folder-organization-implementation.md](folder-organization-implementation.md) / [ssot-lint-implementation.md](ssot-lint-implementation.md) / [code-decoupling-implementation.md](code-decoupling-implementation.md) 同级：本文件**统筹**其他 spec 预留的蒸馏触发点，提供统一执行入口。

## ⚠️ 执行接口当前状态

本文件描述的 `/ms-pipeline distill` 子命令依赖 [FUTURE] 接口，详见 [docs-layout-migration.md § 执行接口落地状态（FUTURE）](docs-layout-migration.md#-执行接口落地状态future)。

当前阶段（#5 spec 起草）**只产出规范**，runtime 实现由后续阶段落地。`ms-pipeline` 现有 8 个 entry points 保持不变；`distill` 作为第 9 个新增入口，未实现前不可调用。

## 定位

| 治理对象 | 文件 |
|---------|------|
| 文档拆分触发器（current.md/modules/file-size cap）| [folder-organization-implementation.md](folder-organization-implementation.md) + [ssot-lint-implementation.md](ssot-lint-implementation.md) |
| 代码追溯过期清理 | [code-decoupling-implementation.md § refresh-traceability](code-decoupling-implementation.md) |
| INS 拆 3 类回扫 | [id-scheme-implementation.md § INS 拆 3 类](id-scheme-implementation.md#ins-拆-3-类人工归类机制) |
| **本文件**：蒸馏触发器 + 13 类动作 + CLI 编排 + 安全门 + 频率 | distillation-implementation.md |

## 根本原则

**蒸馏 ≠ 归档**：
- **蒸馏（distillation）**：知识压缩 + 结构优化（多文件 → 少文件 / 多 NOTE → 1 PATTERN / 历史 sprint 折叠摘要）
- **归档（archive）**：已完成项目搬移到 `_archived/`（搬走 ≠ 蒸馏）

蒸馏后的**有效产物**仍在主目录（如 `patterns/`、`design/modules/`、`tasks/index.md`），只是更精炼。

### `_archived/` 写入例外（不违反"产物留主目录"边界）

蒸馏过程可写 `_archived/` 的情况限定为以下三类**非产物**输出：

| 类型 | 文件 | 用途 |
|------|------|------|
| 蒸馏报告 | `_archived/distill-report-<timestamp>.md` | 留痕；仅 `--apply` 时写入；`--dry-run` 不写文件 |
| 回滚日志 | `_archived/distill-rollback-<timestamp>.log` | 失败时的恢复信息 |
| Orphan quarantine | `_archived/traceability-orphans-<timestamp>.yml` | 孤儿 link 隔离（不是删除）|

这些是**运维产物**（diagnostics / rollback support），不是知识产物。知识产物（PATTERN/ADR/合并后的文件）必须留主目录。

## CLI 入口

| 命令 | 行为 |
|------|------|
| `/ms-pipeline distill` | 全量蒸馏：按 13 类动作扫描 + AskUserQuestion 逐项确认 |
| `/ms-pipeline distill --dry-run` | 列出待蒸馏项 + 预计影响范围；**输出到 stdout（可重定向到 CI artifact）**；不修改任何文件（含 `_archived/`）|
| `/ms-pipeline distill --apply` | 自动执行已确认的蒸馏动作（仍按动作类型分阻断/告警/自动）|
| `/ms-pipeline distill --action <name1[,name2]>` | 仅跑指定动作；支持逗号分隔多值；name 取自下表字典 |
| `/ms-pipeline distill --since <date>` | 增量蒸馏：仅处理文件 frontmatter `updated_at >= <date>` 的项；不使用 git 时间 |
| `/ms-pipeline distill --scope <type1[,type2]>` | 仅扫指定类型；type ∈ `requirements / design / tests / tasks / issues / patterns / notes`（对应 layout.v2 core tree 7 类目录）|
| `/ms-pipeline distill --headless` | 非交互模式：强人工动作跳过 + 真实错误保留退出码（见 § Headless 模式限制）|
| `/ms-pipeline distill --format json` | 报告输出 JSON 形态（详见 § 蒸馏报告 / JSON 输出）|

### `--action` 字典（13 个合法值）

| name | 所属类别 | 安全级 |
|------|---------|--------|
| `current-md-split` | 文件拆分 | 强人工 |
| `module-size-split` | 文件拆分 | 强人工 |
| `file-size-split` | 文件拆分 | 拒绝执行（仅 surface）|
| `patterns-merge` | 知识合并 | 强人工 |
| `notes-promote` | 知识合并 | 半自动 |
| `sprint-fold` | 历史压缩 | 自动 |
| `issues-archive` | 历史压缩 | 自动 |
| `stale-link-cleanup` | 追溯清理 | 半自动 |
| `orphan-link-purge` | 追溯清理 | 自动 |
| `ins-reclassify` | 编号回扫 | 强人工 |
| `alias-consolidation` | 编号回扫 | 自动 |
| `index-rebuild` | 索引刷新 | 自动 |
| `cross-ref-validate` | 索引刷新 | 自动 |

> ⚠️ 共 **13 个 action**（拆分 3 + 合并 2 + 历史 2 + 追溯 2 + 编号 2 + 索引 2）。`--action` 拼写非字典值 → 报 `distill/unknown-action` 退出 2。

### 退出码

| 退出码 | 含义 |
|--------|------|
| 0 | 无可蒸馏项 / 全部已完成 |
| 1 | 部分动作 user-skipped 但成功 |
| 2 | 有动作执行失败（rollback）|
| 3 | distill 自身运行错误 |

## 13 类蒸馏动作

### 分类总览

| 类别 | 动作 | 默认风险等级 | 触发频率建议 |
|------|------|------------|------------|
| 文件拆分 | `current-md-split` / `module-size-split` / `file-size-split` | 中（需人工确认拆分边界）| 触发 lint 时 |
| 知识合并 | `patterns-merge` / `notes-promote` | 高（涉及内容仲裁）| 月度 |
| 历史压缩 | `sprint-fold` / `issues-archive` | 低（结构性）| 每 sprint 完成 |
| 追溯清理 | `stale-link-cleanup` / `orphan-link-purge` | 中 | 季度 |
| 编号回扫 | `ins-reclassify` / `alias-consolidation` | 高 | 仅 layout.v2 升级后 1 次 |
| 索引刷新 | `index-rebuild` / `cross-ref-validate` | 低 | 每次 distill |

### 文件拆分类

#### `current-md-split`（design/current.md 拆分到 modules/）

**触发**：`ssot/current-md-size` lint 报警（行数 > 1500）

**执行**：
1. 解析 `design/current.md` 的 H2 章节
2. 按章节聚类（基于章节名 + 引用的 FEAT/AC 编号 + 调用关系）→ 推荐模块划分
3. AskUserQuestion 用户确认模块划分（强制人工确认）
4. 拆分到 `design/modules/<module-name>.md` + 更新 `design/modules/index.md`
5. `current.md` 改写为模块导航 + 跨模块上下文

**安全门**：⛔ 不允许 `--apply` 自动跳过 AskUserQuestion；拆分边界必须人工确认。

#### `module-size-split`（design/modules/<name>.md ≥ 800 行二次拆分）

**触发**：`ssot/modules-size-cap` lint 报警（[ssot-lint-implementation.md § SSOT 强约束清单](ssot-lint-implementation.md#ssot-强约束清单落地到-3-ssot-lint)）

**执行**：
1. 解析 `design/modules/<name>.md` 的 H2 章节
2. 推荐二次拆分边界：按子模块（如 `<name>-frontend.md` / `<name>-backend.md`）或按职责（如 `<name>-api.md` / `<name>-data.md`）
3. AskUserQuestion 用户确认拆分命名
4. 拆分后：保留原 `<name>.md` 作为该模块导航 + 引用新子文件；或彻底拆分（需用户决策）
5. 更新 `design/modules/index.md`

**安全门**：⛔ 拆分边界必须人工确认；不允许 `--apply` 跳过 AskUserQuestion。

#### `file-size-split`（任意编号文件超 3000 行拆分）

**触发**：`ssot/file-size-cap` lint 报警

**执行**：
1. 检测文件类型
2. 若是编号 owner 文件（如 `FEAT-001.md` ≥ 3000 行）→ 报错并 surface "编号文件不应超 3000 行，建议拆分功能或改写为 modules/ 引用"
3. 若是 index 类文件 → 拒绝执行（index 不应超大；检查是否漏 sprint-fold）

**安全门**：⛔ 不自动拆分编号文件；只 surface 建议。

### 知识合并类

#### `patterns-merge`（多个相似 PATTERN 合并）

**触发**：
- `patterns/index.md` 中按引用度排序后，发现 ≥ 2 个 PATTERN 引用度都 ≥ 5 且关键词重叠 ≥ 60%
- 用户手动指定：`/ms-pipeline distill --action patterns-merge`

**执行**：
1. 对所有 PATTERN 计算关键词指纹（基于标题 + § 适用场景）
2. 聚类：相似度 ≥ 80% 推荐合并
3. AskUserQuestion 用户确认每组合并：
   a. 合并为新 PATTERN（旧 PATTERN 编号 deprecated + 写 aliases.yml）
   b. 保持独立（标 `notes: distinct-but-similar`）
   c. 跳过本次
4. 合并后：merged PATTERN 继承所有旧 PATTERN 的 `links.related` + 标 `merged_from: [PATTERN-XXX, PATTERN-YYY]`

**安全门**：⛔ 内容仲裁必须人工；不允许自动 merge。

#### `notes-promote`（NOTE 升级到 PATTERN/ADR）

**触发**：
- NOTE 在 `links.related` 中被引用 ≥ 3 次 → 候选升 PATTERN
- NOTE 内容含决策关键词（"决定" / "选择" / "trade-off"）→ 候选升 ADR
- 用户手动触发

**执行**：
1. AskUserQuestion 用户选择升级目标：
   a. 升 PATTERN（自动归类到 `patterns/PATTERN-NNN.md`）
   b. 升 ADR（自动归类到 `design/decisions/ADR-NNN.md`）
   c. 保持 NOTE
   d. 关闭（NOTE 已过时）
2. 升级后：旧 NOTE 编号 deprecated + aliases.yml 写映射

**安全门**：⛔ 升级路径必须人工；可参考关键词推荐但不强制。

### 历史压缩类

#### `sprint-fold`（已完成 sprint 折叠到 tasks/index.md）

**触发**：
- 一个 sprint 全部 TASK 标 `status: done`
- 距离当前 sprint ≥ 2 个 sprint（避免折叠刚完成的）

**执行**：
1. 对每个待折叠 sprint：
   a. 提取所有 TASK 的 summary（≤ 120 字 / TASK）
   b. 生成 sprint 总结段（含 TASK 列表 + 累计统计）
   c. 写入 `tasks/index.md` 的"历史 Sprint（折叠）"段（`<details>` 包裹）
2. TASK owner 文件**保留**（不删除，仅从当前 sprint 段移除）

**安全门**：✅ 可 `--apply` 自动执行（结构性 + 可逆）。

#### `issues-archive`（已修复 ISSUE 归档摘要）

**触发**：ISSUE 标 `status: done` 且 closed 时间 > 30 天

**执行**：
1. 提取 ISSUE 关键字段（标题 / 修复 commit / 关联 TASK）写入 `issues/index.md` 的"已修复 Issues"段
2. ISSUE owner 文件**保留**（用于后续模式分析）

**安全门**：✅ 自动执行。

### 追溯清理类

#### `stale-link-cleanup`（清理过期 traceability link）

**触发**：
- traceability.yml 中存在标 `stale` 的 link（commit 距 HEAD > 30 commits）

**执行**：
1. 调用 `/ms-sync --refresh-traceability --rule stale-only`（详见 [code-decoupling-implementation.md](code-decoupling-implementation.md)）
2. 若 symbol 仍可定位 → 更新 commit + lines
3. 若 symbol 已消失（代码删除）→ AskUserQuestion：
   a. 删除 link（代码功能确实删除）
   b. 保留并标 `confidence: low + notes: symbol-removed`
   c. 跳过

**安全门**：⛔ 删除 link 必须人工确认；不自动删除。

#### `orphan-link-purge`（清理孤儿 link）

**触发**：traceability.yml 中 link.id 不存在于任何 `<type>/index.md` 或 aliases.yml

**执行**：
1. 移到 `_archived/traceability-orphans-<timestamp>.yml` 留痕
2. 从主 traceability.yml 删除

**安全门**：✅ 自动执行（孤儿 link 无引用价值，移到 _archived 仍可追溯）。

### 编号回扫类

#### `ins-reclassify`（v2 升级后历史 INS 拆 3 类）

**触发**：仅 layout.v1 → layout.v2 升级时由 `realign --docs-layout` 调用一次；后续 distill 默认跳过

**执行**：
1. 扫描所有 v1 INS-XXX 编号
2. AskUserQuestion 逐个询问归类（ADR / PATTERN / NOTE，参考关键词推荐）
3. 拆分到对应目录 + 写 aliases.yml 映射

**安全门**：⛔ 必须人工逐个确认；不自动归类。

#### `alias-consolidation`（aliases.yml 历史条目合并）

**触发**：aliases.yml 条目数 > 200（阈值可配置）或用户手动触发

**执行**：
1. 检测 chain alias（A → B → C）
2. 自动合并为直接 alias（A → C，标 `consolidated_at`）
3. 保留 B → C 不动（防止 B 仍在外部引用）

**安全门**：✅ 自动执行（chain → direct 是无损变换）。

### 索引刷新类

#### `index-rebuild`（重建各类型 index.md）

**触发**：每次 distill 默认执行；或用户手动 `--action index-rebuild`

**执行**：
1. 对每个 `<type>/index.md`：
   a. 扫描目录下所有编号 owner 文件
   b. 提取 frontmatter (id/status/summary/owner_section)
   c. 重建索引表 + 更新统计
2. tasks/index.md 特殊处理：保留 sprint 分组结构 + 当前 sprint 不变

**安全门**：✅ 自动执行（幂等操作）。

#### `cross-ref-validate`（验证 links.{parents,children,related}）

**触发**：每次 distill 默认执行

**执行**：
1. 扫描所有编号文件 frontmatter `links` 字段
2. 检查每个引用 id 是否存在
3. 不存在 → 报 `distill/dangling-ref` 写入报告，不自动清理

**安全门**：✅ 自动执行（只检测不修改）。

## 触发策略

### 自动触发

| 时机 | 触发动作 | 阻断/告警 |
|------|---------|----------|
| 每个 sprint 完成（`tasks/index.md` `current_sprint` 切换时）| `sprint-fold` + `index-rebuild` + `cross-ref-validate` | 不阻断；写入 sprint summary commit |
| `ssot-lint` 报 `ssot/current-md-size` / `ssot/modules-size-cap` / `ssot/file-size-cap` | surface 推荐对应动作（`current-md-split` / `module-size-split` / `file-size-split`）| 不自动执行（必须用户确认）|
| `/ms-pipeline realign --docs-layout` 完成 | `ins-reclassify`（仅 v1→v2 时）| 阻断 realign 完成直至全部 INS 归类完成 |
| 每月（CI 定时任务推荐）| `--dry-run` 报告 → stdout / CI artifact（**不写文件系统**）| 仅报告，不执行；只有 `--apply` 才写 `_archived/` |

### 手动触发

用户主动调用 `/ms-pipeline distill [flags]`。推荐周期：

| 频率 | 推荐动作组合 |
|------|-----------|
| 每 sprint 完成 | `--action sprint-fold,index-rebuild,cross-ref-validate` |
| 月度 | `--action patterns-merge,notes-promote` + `--dry-run` 先看预览 |
| 季度 | 全量 `--dry-run` → 用户挑选执行 |
| 半年 | 全量 `--apply`（评估是否需要更大结构调整）|

## 安全门设计

### 动作分级

| 级别 | 行为 | 适用动作 |
|------|------|---------|
| **自动** | `--apply` 直接执行 | `sprint-fold` / `issues-archive` / `orphan-link-purge` / `alias-consolidation` / `index-rebuild` / `cross-ref-validate` |
| **半自动** | `--apply` 触发 AskUserQuestion 逐项确认 | `stale-link-cleanup` / `notes-promote`（候选推荐 + 用户选）|
| **强人工** | `--apply` 仍必须 AskUserQuestion；不允许 headless 模式跳过 | `current-md-split` / `module-size-split` / `patterns-merge` / `ins-reclassify` |
| **拒绝执行** | surface 建议不操作 | `file-size-split`（编号文件超 3000 行）|

### Headless 模式限制

⛔ `--headless` flag 下：
- 自动级动作正常执行
- 半自动级动作降级为 dry-run + 写入 pending 报告
- 强人工级动作直接跳过 + 写入 skipped 报告
- **退出码语义**：仅在"全部 skipped 是预期行为"时 clamp 到 ≤ 1；**真实运行错误必须保留原退出码**：
  | 场景 | headless 退出码 |
  |------|----------------|
  | 全部 auto 动作成功 + 半自动/强人工跳过 | 0 |
  | 全部 auto 动作成功 + 跳过项写入 pending 报告 | 1 (warn) |
  | 任一 auto 动作执行失败 | **2**（保留）|
  | distill 自身错误（rollback / git / 权限）| **3**（保留）|

  规则：clamp 仅对"非错误的跳过"生效；任何 auto 级别失败或运行时错误必须保留原退出码，不能被 headless 模式吞掉。

### 回滚机制

每次 `--apply` 前自动创建临时分支：

```text
1. 前置检查（fail-fast）：
   a. clean worktree 检查：git diff/diff --cached 非空 → 阻断，提示先 commit 或 stash
   b. git submodule 状态检查：未初始化 → 阻断
   c. git hook 检查：若 pre-commit hook 调用 ms-verify / lint / distill → 阻断防循环（设置环境变量 MS_DISTILL_RUNNING=1，hook 检测到则跳过）
2. 创建临时分支：distill-<timestamp>
3. 执行各动作 + 各动作完成后逐个 commit（粒度：1 action = 1 commit，commit message 含 action name）
4. 全部成功 → merge 回主分支（--no-ff 保留临时分支 history）
5. 任一失败 → rollback 到 distill 开始前 + 删除临时分支
```

### 中断处理（SIGINT / Ctrl-C）

| 阶段 | SIGINT 行为 |
|------|----------|
| 前置检查中 | 立即 abort，无副作用 |
| 临时分支已建 + 部分动作完成 | 保留临时分支（用户可后续 `--resume` 继续 [FUTURE]）；不自动 rollback；surface "已完成 N 个 action，临时分支保留为 distill-<timestamp>" |
| merge 进行中 | merge --abort + 删除临时分支 |
| **任何阶段** | 必须在退出前清理 `MS_DISTILL_RUNNING` 环境变量（防止下次 hook 误判）|

### 与 git hook 的反循环

⛔ distill `--apply` 启动时设置 `MS_DISTILL_RUNNING=1`：
- pre-commit hook 配置应检查此变量，若存在则**跳过** ms-verify / ssot-lint / distill 触发
- 退出前（含异常退出）必须 unset 此变量
- 若用户的 pre-commit hook 未做检查 → distill 报 `distill/hook-loop-risk` 阻断（强制用户更新 hook 或显式 `--no-hook-check` 跳过）

⛔ **禁止** distill 直接修改主分支（必须经临时分支）；rollback 信息写入 `_archived/distill-rollback-<timestamp>.log`。

## 蒸馏报告

### 标准报告（Markdown）

```markdown
# Distillation Report

- **Date**: 2026-05-18
- **Trigger**: scheduled-monthly | manual | sprint-end
- **Mode**: dry-run | apply
- **Scope**: full | --action X | --scope Y
- **Verdict**: PASS | PARTIAL | FAIL

## Actions Executed

### sprint-fold (auto, ✅)
- Folded sprint-10, sprint-11 (12 tasks total)
- Updated tasks/index.md
- Commit: abc1234

### patterns-merge (manual, ⏭️ skipped)
- 3 candidates found: [PATTERN-001, PATTERN-005], [PATTERN-008, PATTERN-012]
- User skipped due to "need more usage data"

### stale-link-cleanup (semi-auto, 🟡 partial)
- 15 stale links found
- 12 refreshed (commit updated)
- 3 marked confidence:low (symbols removed)
- Commit: def5678

## Skipped
- ins-reclassify: 不适用（layout.v2 升级已完成）
- file-size-split: 0 violations

## Cross-Ref Validation
- 0 dangling refs

## Next Recommended
- Schedule patterns-merge review in 2 weeks (insufficient usage data)
- Consider current-md-split: design/current.md is 1340 lines (approaching 1500 limit)
```

### JSON 输出（`--format json`）

类似 ssot-lint，含 `schema_version`/`exit_code`/`actions[]`（每个 action 的 status/findings/commit）。

## 与编排层集成

### ms-pipeline 入口扩展

`ms-pipeline` SKILL.md 在 `distill` 下作为新增 entry point 文档化：

```markdown
## distill（[FUTURE]）

迭代蒸馏：知识压缩 + 结构优化。详见 [pipeline/references/layout/distillation-implementation.md](references/layout/distillation-implementation.md)。

| flag | 行为 |
|------|------|
| `--action <name>` | 仅跑指定动作 |
| `--scope <type>` | 仅扫指定类型 |
| `--since <date>` | 增量蒸馏 |
| `--dry-run / --apply` | 双确认 |

⚠️ **入口在 v1/v2 项目都可调用**；具体动作按兼容表降级（v2-only 动作如 `current-md-split` / `module-size-split` 在 v1 项目跳过 + 写入 skipped 报告）。详见 § 历史项目兼容。
```

### yaml-summary 集成

```yaml
skill: ms-pipeline
status: success | partial | failed
summary:
  headline: "Distillation: 5 actions executed, 2 skipped"
  details:
    distill:
      mode: apply
      actions_executed: 5
      actions_skipped: 2
      actions_failed: 0
      commits: [abc1234, def5678]
      rollback_available: true
```

## 频率与节奏建议

### 项目周期推荐

| 项目阶段 | distill 频率 | 重点动作 |
|---------|-----------|---------|
| 起步期（< 3 sprint）| 暂不需要 | — |
| 成长期（3-10 sprint）| 每 sprint 末（auto）| sprint-fold / index-rebuild |
| 成熟期（10-50 sprint）| 每月（manual review）| + patterns-merge / notes-promote |
| 稳定期（> 50 sprint）| 每季度（重大调整）| + current-md-split / patterns 重新归类 |

### 反模式

- ❌ 每天 distill：过于频繁，浪费 AskUserQuestion 时间
- ❌ 一年不 distill：累计技术债 / `current.md` 超过 5000 行
- ❌ headless 模式跑强人工级动作：会跳过所有内容仲裁
- ❌ distill --apply 不看 dry-run：可能误合并不该合并的 PATTERN

## frontmatter 升级规则（条件性）

`ms-pipeline` 本身无 `writes_layout` 字段（编排层不写产物）。但 distill 调用的下游 skill 仍按各自 frontmatter 规则：

- `ms-sync --refresh-traceability` → 受 `writes_traceability` 约束
- 文件拆分 → 受 `writes_layout` 约束
- 编号合并 → 受 `writes_id_scheme` 约束

任何下游 skill 升级到 v2 前，对应的 distill 动作仍按 v1 路径执行（如 sprint-fold 仍写 `04-dev-tasks.md` 而非 `tasks/index.md`）。

## 历史项目兼容（mic-en 等）

- **mic-en 等 layout.v1 项目**：distill 仍可用，但动作降级：
  - `sprint-fold` 写入 `04-dev-tasks.md` 的"历史 Sprint"段（v1 单文件）
  - `patterns-merge` 仍可用（patterns/ 目录在 v1/v2 都存在）
  - `current-md-split` 不适用（v1 无 `design/modules/`）
  - `stale-link-cleanup` 仍可用（traceability.yml 在 v1 也允许存在）
- 用户主动调用 `/ms-pipeline distill` 即可（不需要先升级到 v2）

## 与其他阶段的接口

| 阶段 | 接口点 |
|------|-------|
| #1 编号体系 | `ins-reclassify` 是 v1→v2 升级时的强制动作（id-scheme-implementation.md § INS 拆 3 类机制 的批量执行入口）|
| #2 文件夹组织 | `current-md-split` 实施 design/modules 一次拆分；`module-size-split` 实施 modules/<name>.md 二次拆分；`sprint-fold` 维护 tasks/index.md sprint 分组；`index-rebuild` 维护各 index.md |
| #3 SSOT lint | 三个蒸馏触发器（current-md-size / modules-size-cap / file-size-cap）来自 lint，分别对接 `current-md-split` / `module-size-split` / `file-size-split`；蒸馏完成后自动跑 lint 验证 |
| #4 代码解耦 | `stale-link-cleanup` / `orphan-link-purge` 调用 `ms-sync --refresh-traceability`；distill 报告通过调用 `/ms-sync --extract-trace --dry-run` 获取 legacy 注释统计（matched / skipped / remaining 计数），写入报告的 `legacy_annotation_progress` 段；v2 升级后 legacy 注释剩余数 = 0 即可宣告 trace.v1 迁移完成 |

## 引用关系

| 引用本文件的位置 | 引用目的 |
|------------|---------|
| `skills/pipeline/SKILL.md` § distill | 入口文档化（待 #5 落地后加）|
| `folder-organization-implementation.md` § 与其他阶段的接口 | 蒸馏触发点反向引用 |
| `ssot-lint-implementation.md` § 跨阶段接口 | 蒸馏触发器引用 |
| `code-decoupling-implementation.md` § 与其他阶段的接口 | 蒸馏期 stale link 清理引用 |

## 变更日志

| 日期 | 变更 |
|------|------|
| 2026-05-18 | 初始版本（#5 迭代蒸馏实施规范）|
