# Realign Scope Layout（layout.v1 → layout.v2 执行接口）

> 用户入口：`/ms-pipeline realign --scope=layout [--target=<path>] [--dry-run|--apply]`。
> 旧入口 `/ms-pipeline realign --docs-layout` 保留一个版本作为 alias，并标记 deprecated。

## 定位

本文件只定义 `--scope=layout` 的执行接口，让 LLM 能按步骤完成 layout.v1 → layout.v2 文档体系迁移。迁移分类仍以 [layout/docs-layout-migration.md](layout/docs-layout-migration.md) 为权威源；本文件不复制迁移矩阵、不新增编号体系、不修改其他 scope 的 realign 契约。

状态仲裁：`docs-layout-migration.md` 继续作为治理规范源；`--scope=layout` 的 dry-run / apply 执行细节以本文件为现状 spec。旧文档内的 `--docs-layout` 表述按 deprecated alias 解读。

引用关系：

| 文件 | 本 spec 的使用方式 |
|------|-------------------|
| [realign.md](realign.md) | 继承 realign 安全不变量、`.devdocs-realign-ack`、yaml-summary-v1 汇总方式 |
| [layout/docs-layout-migration.md](layout/docs-layout-migration.md) | 读取 A/B/C/D 类迁移分类、不可逆操作、编号保留规则 |
| [layout/folder-organization-implementation.md](layout/folder-organization-implementation.md) | 读取 layout.v2 目录、owner 文件、index、SSOT 规则 |
| [layout/aliases-yml-schema.md](layout/aliases-yml-schema.md) | 写入 `aliases.yml` 的 schema 与 append-only 规则 |
| [layout/code-decoupling-implementation.md](layout/code-decoupling-implementation.md) | 写入 `traceability.yml` 与 legacy 注释保留窗口 |
| [layout/ssot-lint-implementation.md](layout/ssot-lint-implementation.md) | post-validation 的 `--ssot-lint` 规则与退出码 |
| [layout/distillation-implementation.md](layout/distillation-implementation.md) | INS 归类动作的人工确认语义 |
| `../../_shared/constraints.md` | 继承 `⛔` / `⚠️` 门控、AskUserQuestion、yaml-summary-v1 共享规则 |

## CLI 兼容

| 命令 | 行为 |
|------|------|
| `/ms-pipeline realign --scope=layout --dry-run` | 只生成迁移 plan，不执行迁移 |
| `/ms-pipeline realign --scope=layout --apply` | 按 plan 分 Phase 执行迁移 |
| `/ms-pipeline realign --scope=layout --target=<path>` | 指定项目根目录或 `docs/devdocs/` 目录 |
| `/ms-pipeline realign --docs-layout` | alias 到 `--scope=layout`，一个版本内保留，输出 deprecated 提示 |

若未显式传 `--dry-run` 或 `--apply`，`--scope=layout` 默认执行 dry-run，不做迁移。

`--target` 归一化规则：

1. 若 `<path>` 本身是 `docs/devdocs/`，以其为 `docs_root`，其上两级为 `repo_root`。
2. 若 `<path>/docs/devdocs/` 存在，以 `<path>` 为 `repo_root`。
3. 若未传 `--target`，以当前工作目录向上查找最近的 `docs/devdocs/`。
4. 找不到 `docs/devdocs/` 时 `⛔ 禁止继续`。恢复方式：传入正确 `--target` 或先运行 `/ms-pipeline init`。

## Dry-run 阶段

### 输入

dry-run 的主输入是当前项目 `docs/devdocs/`。LLM 必须自动检测 layout.v1 产物，包括但不限于：

- `00-context.md`
- `01-requirements.md` / `01-requirements-stories.md`
- `02-system-design*.md`
- `03-test-*.md` / `03-test-cases.md`
- `04-dev-tasks*.md`
- `05-bugfix-log.md`
- `06-insights.md`
- `patterns/<slug>.md`

trace 相关项可按 [layout/code-decoupling-implementation.md](layout/code-decoupling-implementation.md) 只读扫描 repo 代码注释；无法扫描时必须把对应 probe 写入 `validation_probes`，不能假装已完成。

### 只读边界

dry-run 不写入迁移产物，不创建目录，不改 `aliases.yml` / `traceability.yml` / frontmatter / ack / log / git commit。唯一允许写入的文件是：

```text
docs/devdocs/.realign-plan.md
```

若用户要求严格零写入，LLM 可以只输出 plan 到 stdout，但后续 `--apply` 必须要求用户提供或重新生成 `.realign-plan.md`。

### 执行步骤

1. 归一化 `repo_root` 与 `docs_root`。
2. 读取 [layout/docs-layout-migration.md](layout/docs-layout-migration.md) 的 A/B/C/D 类迁移分类。
3. 扫描 `docs_root` 的 layout.v1 文件、现有 v2 目录、`aliases.yml`、`traceability.yml`。
4. 为每个 v1 文件生成目标动作：
   - 自动：确定性 move / rename / create / archive。
   - 半自动：可切分但需用户确认边界。
   - 人工：INS 归类、编号歧义、PRD 引用影响、文件名冲突。
5. 根据 [layout/aliases-yml-schema.md](layout/aliases-yml-schema.md) 生成候选 alias，不修改现有文件。
6. 根据 [layout/code-decoupling-implementation.md](layout/code-decoupling-implementation.md) 生成候选 trace 条目。
7. 输出 `.realign-plan.md`，并在 stdout 打印 plan 摘要与下一步命令。
8. **工作区模式核对**：读 `AGENTS.md` 的 `workspace_mode`。
   - 无字段且仓内存在 `.gitmodules` → 在 plan 中列为「可选项：未声明工作区模式」，dry-run 展示，**不自动改**
   - 有 `workspace_mode: shell` → 跑 `workspace/fail-closed` 全表校验，失配项进 plan 的修复清单
   - 有 `workspace_mode: inline` → 无操作

### Plan 文件契约

`.realign-plan.md` 必须是 Markdown 文件，正文包含一个 `yaml` 代码块。yaml 块必须包含以下字段：

```yaml
plan_schema: realign-layout-plan.v1
scope: layout
source_layout: layout.v1
target_layout: layout.v2
repo_root: <absolute-or-relative-path>
docs_root: docs/devdocs
generated_at: <iso-timestamp>
plan_hash: <sha256-of-yaml-without-plan_hash>

file_ops:
  create: []
  move: []
  rename: []
  split: []
  archive: []

id_aliases:
  write: []
  ambiguous: []

trace_changes:
  write: []
  unresolved: []

prd_mapping_changes:
  write: []
  affected_refs: []

manual_decisions:
  - id: <stable-decision-id>
    kind: ins-classification | id-alias-ambiguity | prd-cross-reference | file-name-conflict
    prompt: <AskUserQuestion prompt>
    options: []
    required_before_phase: 2 | 3 | 4
    status: pending

validation_probes:
  - name: schema-drift
    command: /ms-verify --schema-drift
    phase: 6
  - name: ssot-lint
    command: /ms-verify --ssot-lint
    phase: 6
```

字段规则：

- `file_ops` 必须列出所有会改动路径的动作；不得用省略号替代。
- `id_aliases.write` 必须遵守 `alias.v1` schema；不在本文件定义新前缀。
- `trace_changes.write` 必须包含 `id/path/symbol/source` 或标入 `unresolved`。
- `prd_mapping_changes` 仅记录受影响项；无影响时写空数组。
- `manual_decisions.status` 在 dry-run 中只能是 `pending`。
- `validation_probes` 至少包含 `schema-drift` 与 `ssot-lint`。

## AskUserQuestion 触发点

以下决策必须触发 `⚠️ 必须确认`，不得自动选择默认值：

| 决策 | 触发条件 | 问询要求 |
|------|----------|----------|
| INS 归类 | 任意 `INS-NNN` 需要拆到 ADR / PATTERN / NOTE | 展示 INS 原文摘要、推荐归类、3 个固定选项 |
| 编号映射歧义 | 旧编号可映射到多个新编号，例如 `F-01 → FEAT-001` 或 `FEAT-005` | 展示候选来源、引用次数、推荐理由 |
| PRD 引用受影响 | PRD mapping 或 `docs/prd/**` 引用旧 DevDocs 编号/路径 | 展示受影响引用、旧引用、新引用候选 |
| 文件名冲突 | 目标路径已存在且内容不是同一 owner | 展示两个文件摘要，提供改名/合并/停止选项 |
| 工作区模式迁移 | 用户显式要求 inline → shell | 走 [workspace-shell.md § inline → shell 迁移](layout/workspace-shell.md#inline--shell-迁移) 的七步流程，第 2 步 dry-run 计划必须确认后才动文件 |

`--apply` 遇到未确认决策时必须暂停并逐项问询。headless 场景不得跳过这些项；只能返回 `status: interrupted` 或 `partial`。

## Apply 阶段

### 入口前置条件

`--apply` 必须满足：

1. 工作区洁净。
2. 存在 `docs/devdocs/.realign-plan.md`，且 `plan_schema=realign-layout-plan.v1`。
3. `plan_hash` 校验通过。
4. `source_layout=layout.v1` 且 `target_layout=layout.v2`。
5. 若存在 `.realign-applied.log`，必须进入中断恢复流程。

任一条件失败时 `⛔ 禁止继续`。恢复方式：修复工作区、重新 dry-run，或按中断恢复规则继续。

### Phase 1：备份 / checkpoint

动作：

1. 创建独立迁移分支：`devdocs-layout-v2-<timestamp>`；若已在该分支则复用。
2. 创建 checkpoint commit（允许 empty commit），记录为 `checkpoint_commit`。
3. 初始化 `docs/devdocs/.realign-applied.log`。
4. 写入 Phase 1 completed 记录并单独 commit。

失败处理：`⛔ 停止`，提示 `git reset --hard <checkpoint_commit>` 或切回原分支。

### Phase 2：文件操作

动作：

1. 按 plan 的 `file_ops.create/move/rename/split/archive` 执行。
2. 新建 layout.v2 目录与 index 文件，目录结构以 [layout/folder-organization-implementation.md](layout/folder-organization-implementation.md) 为准。
3. v1 大文件不硬删除，移入 `docs/devdocs/_archived/layout-v1-<timestamp>/`。
4. 文件名冲突必须先完成 AskUserQuestion；未确认则停止。
5. 写入 `.realign-applied.log` Phase 2 记录并单独 commit。

失败处理：`⛔ 停止`，提示 `git reset --hard <checkpoint_commit>`；不得自动 amend Phase 1 commit。

### Phase 3：编号映射

动作：

1. 写入或追加 `docs/devdocs/aliases.yml`。
2. `rename` 类型保留数字，例如 `F-001 → FEAT-001`、`T-001 → TASK-001`。
3. `split` / `merge` 类型按 [layout/docs-layout-migration.md](layout/docs-layout-migration.md) 的编号规则处理。
4. INS 归类与编号歧义必须先完成 AskUserQuestion。
5. 写入 `.realign-applied.log` Phase 3 记录并单独 commit。

失败处理：`⛔ 停止`，提示 `git reset --hard <checkpoint_commit>`；需要修正 alias 时使用新 commit，不允许 amend 已提交历史。

### Phase 4：trace 重组

动作：

1. 写入或追加 `docs/devdocs/traceability.yml`。
2. 从 legacy `@satisfies` / `@verifies` 注释生成 trace.v1 条目；legacy 注释在 layout.v2 期间保留，不在本 Phase 删除。
3. 写入 layout.v2 baseline 元数据，供 `ssot/legacy-annotation-additions` 使用。
4. PRD 引用受影响时必须 AskUserQuestion。
5. 写入 `.realign-applied.log` Phase 4 记录并单独 commit。

失败处理：`⛔ 停止`，提示 `git reset --hard <checkpoint_commit>`；不得把无法解析的 trace 静默丢弃，必须写入 unresolved 或停止。

### Phase 5：frontmatter 升级

动作：

1. 为拆出的 owner 文件写入当前产物 `spec_version`。
2. 为编号文件写入 layout metadata schema 要求的 `id/type/status/summary/links` 等字段。
3. 更新项目级 DevDocs frontmatter：`docs_layout_version: layout.v2`、`id_scheme: id.v2`、`traceability_version: trace.v1`、`upgraded_from`、`upgraded_at`。
4. 保留 `.devdocs-realign-ack` 机制；dry-run 不写 ack，apply 完成或用户选择 no-realign 时按 [realign.md](realign.md) 更新 ack。
5. 修复 `workspace_mode` / `code_roots` 失配（如 name 已从 `.gitmodules` 移除）：按 `workspace/fail-closed` 提示的方向修正，**每项 AskUserQuestion 确认**。
6. 写入 `.realign-applied.log` Phase 5 记录并单独 commit。

失败处理：`⛔ 停止`，提示 `git reset --hard <checkpoint_commit>`；不得只升级声明而保留 v1 输出结构。

### Phase 6：post-validation

动作：

1. 执行 plan 中所有 `validation_probes`。
2. 至少运行：
   - `/ms-verify --schema-drift`
   - `/ms-verify --ssot-lint`
3. 若可用，追加运行 `/ms-verify --layout-drift`。
4. P0 / block 结果使迁移状态为 `failed` 或 `partial`；P1 warning 可写入 summary。
5. 写入 `.realign-applied.log` Phase 6 记录并单独 commit。

失败处理：`⛔ 停止`，提示 `git reset --hard <checkpoint_commit>`。如果用户选择保留部分成果继续修复，只能追加修复 commit，不允许 amend 已提交历史。

## `.realign-applied.log` 契约

文件位置：

```text
docs/devdocs/.realign-applied.log
```

append-only，推荐 YAML lines：

```yaml
- phase: 1
  status: completed
  commit: <commit-sha>
  checkpoint_commit: <commit-sha>
  plan_hash: <plan-hash>
  completed_at: <iso-timestamp>
  notes: "checkpoint created"
```

每条记录必须包含 `phase/status/commit/plan_hash/completed_at`。失败记录必须额外包含 `error` 与 `recovery`。

## 中断恢复

恢复入口仍是：

```bash
/ms-pipeline realign --scope=layout --apply
```

执行步骤：

1. 读取 `.realign-plan.md` 与 `.realign-applied.log`。
2. 校验 `plan_hash` 一致；不一致则 `⛔ 禁止继续`，恢复方式是重新 dry-run 或回滚。
3. 找出 `status=completed` 的最高 Phase。
4. 对已完成 Phase 做只读校验；校验通过则跳过。
5. 从下一个 Phase 继续执行。
6. 若日志显示某 Phase `failed`，必须先 AskUserQuestion：继续修复 / 回滚到 checkpoint / 停止。

幂等规则：已完成 Phase 不重复写文件、不重复生成 alias、不重复 commit。

## 回滚

回滚依赖 Phase 1 的独立分支与 checkpoint commit：

```bash
git reset --hard <checkpoint_commit>
```

规则：

- 回滚命令只由用户或执行者显式运行；LLM 不自动 reset。
- `⛔` 失败时必须提示 checkpoint commit 与当前已完成 Phase。
- 不允许自动 `git commit --amend`、`git rebase` 或改写已提交 Phase 历史。
- 需要修正时使用后续修复 commit；若用户要求完全撤销，使用 checkpoint reset。

## 输出契约

`--apply` 成功、失败或中断后，返回 yaml-summary-v1：

```yaml
skill: ms-pipeline
status: success | partial | failed | interrupted
summary:
  headline: "layout realign completed"
  details:
    scope: layout
    phases_completed: [1, 2, 3]
    phases_skipped: []
    files_renamed: 12
    aliases_written: 8
    manual_decisions: 3
    checkpoint_commit: <commit-sha>
    plan_file: docs/devdocs/.realign-plan.md
    applied_log: docs/devdocs/.realign-applied.log
blockers: []
output_files:
  - docs/devdocs/.realign-plan.md
  - docs/devdocs/.realign-applied.log
new_ids: {}
next_recommended:
  skill: ms-verify
  args: "--schema-drift && --ssot-lint"
```

状态语义：

| status | 含义 |
|--------|------|
| `success` | Phase 1-6 全部完成且 validation 无 P0/block |
| `partial` | 至少一个 Phase 已 commit，但 validation 或人工决策阻塞 |
| `failed` | 执行错误导致停止，并已给出 checkpoint 回滚方式 |
| `interrupted` | 用户未完成 AskUserQuestion 或主动暂停 |
