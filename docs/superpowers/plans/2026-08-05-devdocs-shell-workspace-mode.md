# DevDocs 外壳工作区模式（workspace_mode: shell）实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 DevDocs 支持「文档在外壳仓、代码在 git 子模块」的隔离布局，使维护开源项目 / 待公开项目时私有文档不污染代码仓。

**Architecture:** 新增一个与 layout/id/trace 正交的维度 `workspace_mode`（`inline` 默认 / `shell`）。协议正文落 `skills/_shared/workspace-mode.md`（跨 skill SSOT），操作手册落 `skills/pipeline/references/layout/workspace-shell.md`，9 个碰代码的 skill 加指针。无 `workspace_mode` 字段 = `inline` = 现状，现存项目零影响。

**Tech Stack:** Markdown + YAML skill 定义。**本仓无 build / test / lint 命令**，验证靠 `grep` / `rg` 静态核对 + 真实仓端到端实测。

---

## 前置：执行者必读

**动手前先完整读一遍设计文档**：`docs/superpowers/specs/2026-08-05-devdocs-shell-workspace-mode-design.md`

本计划**不复制** spec 中已定稿的表格（校验规则表、零污染写入范围表、Recovery 三类表等）——那些表已是最终形态，转写时原样搬运即可。计划只逐字给出 **spec 中没有的新内容**（指针文本、rule 算法、各 skill 的插入片段）。

## Global Constraints

以下约束适用于**每一个** task，值从 spec 原样抄录：

- **`SKILL.md` ≤ 500 行**（本仓硬约束，见 AGENTS.md）。修改 SKILL.md 后必须 `wc -l` 复核
- **所有新增规则的触发条件必须是 `workspace_mode: shell`**。落地后 grep 核对无裸露的无条件门（Task 10 强制验收）
- **`code_roots` 元素是 `.gitmodules` 的 submodule name，不是路径**。路径一律经 `git config -f .gitmodules submodule.<name>.path` 解析
- **零污染红线**：LLM 不主动往 `code_roots` 写任何非代码文件；已存在的 `AGENTS.md` / `CLAUDE.md` 照读照尊重
- **不新增 realign scope**（复用 `layout` + `health`，守 `scope-enum-authority`）
- **不 bump 任何 skill 的 `spec_version`**（本方案不改产物模板结构）；唯一 bump 是 `constraints.md` 自身 `shared-constraints.v1` → `v2`
- 提交遵循 Conventional Commits，文档用中文
- **每个 task 结束时提交**，一个 task 一个 commit

---

### Task 1: 协议 SSOT

**Files:**
- Create: `skills/_shared/workspace-mode.md`
- Modify: `skills/_shared/constraints.md`（frontmatter + 文件末尾 §9 之后、`## 差异点与跳过项` 之前插入 §10）

**Interfaces:**
- Produces: 后续所有 task 引用的锚点 —— 条款 id `workspace/mode-enum`、`workspace/code-roots-source`、`workspace/fail-closed`、`workspace/no-pollution`、`workspace/commit-protocol`、`workspace/recovery`；文件路径 `skills/_shared/workspace-mode.md`
- Consumes: 无

- [ ] **Step 1: 写验证命令，确认当前为「红」**

```bash
cd /Users/mason/Projects/Personal/skills
test -f skills/_shared/workspace-mode.md && echo "EXISTS" || echo "MISSING"
grep -c "workspace/mode-enum" skills/_shared/constraints.md
```

Expected: `MISSING` 且 `0`

- [ ] **Step 2: 创建 `skills/_shared/workspace-mode.md`**

frontmatter 仿 `constraints.md` 形态，但 `status` 明确本文**引入新规则**（这是它不能放 constraints.md 的原因）：

```markdown
---
title: 工作区模式协议 SSOT（inline / shell）
status: 引入新协议，跨 skill 强制
scope: 文档仓与代码仓的拓扑关系
related:
  - skills/_shared/constraints.md（§10 指针）
  - skills/pipeline/references/layout/layout-metadata-schema.md（frontmatter schema）
  - skills/pipeline/references/layout/workspace-shell.md（操作手册）
generated_at: 2026-08-05
spec_version: workspace-mode.v1
---
```

正文六节，内容从 spec 对应节**原样转写**：

| 本文节 | 来源 | 条款 id |
|--------|------|---------|
| 1. 模式枚举与缺省 | spec §1「关键事实」+ §2.1 | `workspace/mode-enum` |
| 2. `code_roots` 与真源 | spec §2.1 后半（记 name 不记路径的三条理由） | `workspace/code-roots-source` |
| 3. 校验规则（fail-closed） | spec §2.2 整张表 | `workspace/fail-closed` |
| 4. 归属判定 | spec §2.4 | `workspace/root-attribution` |
| 5. 零污染写入范围 | spec §3 整张表 + 违约检测段 | `workspace/no-pollution` |
| 6. N+1 仓提交协议 | spec §4.1–4.4（含 detached HEAD 前置门、commit message 契约、Recovery 三类表） | `workspace/commit-protocol`、`workspace/recovery` |

每节末尾以 `- \`条款 id\`：一句话规则` 形式给出可被引用的条款行，形式对齐 `constraints.md` 现有条款（如 `realign/single-entry`）。

**不写进本文**：探测步骤、迁移流程、故障修复手册 —— 那些是操作细节，归 Task 3 / Task 8 的 `workspace-shell.md`。

- [ ] **Step 3: 在 `constraints.md` 插入 §10（仅指针）**

插入位置：§9 末尾之后、`## 差异点与跳过项` 之前。逐字内容：

```markdown
## 10. 工作区模式（inline / shell）

> 本节**仅声明协议层共性与指针**（遵 `doc/reference-over-copy`）。完整协议正文见 [workspace-mode.md](workspace-mode.md)——该文件引入新执行语义，故独立成文，不并入本文。

- `workspace/mode-enum`：`workspace_mode` 二值枚举 `inline` | `shell`，声明在项目根 `AGENTS.md` 的 `devdocs:` frontmatter。**缺省 `inline`**——无此字段的存量项目行为完全不变。
- `workspace/code-roots-source`：`shell` 模式下 `code_roots` 必填，元素为 `.gitmodules` 的 submodule **name**；路径与 URL 的唯一真源是 `.gitmodules`，不在 frontmatter 复制。
- `workspace/orthogonal-to-layout`：本维度与 `docs_layout_version` / `id_scheme` / `traceability_version` **正交**——docs 内部结构不因模式而变，不进 layout 版本矩阵。
- `workspace/pointer`：字段 schema 见 [layout/layout-metadata-schema.md](../pipeline/references/layout/layout-metadata-schema.md) §1；探测、迁移与故障处置见 [layout/workspace-shell.md](../pipeline/references/layout/workspace-shell.md)。
```

- [ ] **Step 4: bump `constraints.md` frontmatter**

`spec_version: shared-constraints.v1` → `shared-constraints.v2`；`related:` 列表追加一行 `- skills/_shared/workspace-mode.md（工作区模式协议正文）`。

- [ ] **Step 5: 跑验证命令，确认转「绿」**

```bash
cd /Users/mason/Projects/Personal/skills
test -f skills/_shared/workspace-mode.md && echo OK
grep -c "workspace/mode-enum" skills/_shared/constraints.md          # 期望 ≥1
grep -n "shared-constraints.v2" skills/_shared/constraints.md         # 期望有命中
# 反向：确认 constraints.md 没有塞进正文（§10 应短）
awk '/^## 10\./,/^## 差异点/' skills/_shared/constraints.md | wc -l   # 期望 < 20
```

- [ ] **Step 6: 提交**

```bash
git add skills/_shared/workspace-mode.md skills/_shared/constraints.md
git commit -m "feat(shared): 新增工作区模式协议 SSOT(inline/shell)

正文落 _shared/workspace-mode.md,constraints.md §10 仅留指针
(constraints.md 宪章 doc/status-extraction 禁止引入新执行语义)。
bump shared-constraints.v1 → v2。"
```

---

### Task 2: frontmatter schema

**Files:**
- Modify: `skills/pipeline/references/layout/layout-metadata-schema.md`（§1「AGENTS.md devdocs frontmatter」）

**Interfaces:**
- Consumes: Task 1 的 `workspace/fail-closed` 条款
- Produces: 字段名 `workspace_mode` / `code_roots` 的权威 schema 定义；Task 4 的探测写入以此为准

- [ ] **Step 1: 验证「红」**

```bash
grep -c "workspace_mode" skills/pipeline/references/layout/layout-metadata-schema.md
```

Expected: `0`

- [ ] **Step 2: 扩 §1 的 Schema 代码块**

在现有 yaml 示例的 `upgraded_from:` 之后、`legacy_annotation_grace_period:` 之前插入：

```yaml
  workspace_mode: shell                   # 可选，枚举 inline / shell，缺省 inline
  code_roots: [web, api]                  # workspace_mode=shell 时必填，≥1 项
                                          # 元素为 .gitmodules 的 submodule name（非路径）
                                          # 路径解析：git config -f .gitmodules submodule.<name>.path
```

- [ ] **Step 3: 扩 §1 的「校验规则」列表**

在现有 bullet 之后追加：

```markdown
- `workspace_mode` ∈ [`inline`, `shell`]，缺省 `inline`
- `workspace_mode: shell` 时 `code_roots` 必填且非空；每个元素必须在 `.gitmodules` 中存在同名 submodule
- `code_roots` 各元素解析出的 path 两两不得互为前缀（禁嵌套子模块）
- `workspace_mode` 与 `docs_layout_version` / `id_scheme` / `traceability_version` **正交**，无版本依赖
```

- [ ] **Step 4: 扩 §1 的「缺失时的行为」表**

追加四行（内容从 spec §2.2 校验表原样搬 `shell` 相关四种情形 + `inline` 却出现 `code_roots` 一行）。

- [ ] **Step 5: 验证「绿」**

```bash
grep -c "workspace_mode" skills/pipeline/references/layout/layout-metadata-schema.md   # 期望 ≥4
grep -c "code_roots" skills/pipeline/references/layout/layout-metadata-schema.md        # 期望 ≥3
```

- [ ] **Step 6: 提交**

```bash
git add skills/pipeline/references/layout/layout-metadata-schema.md
git commit -m "feat(layout): frontmatter schema 增 workspace_mode / code_roots"
```

---

### Task 3: 操作手册（探测 + 故障处置）

**Files:**
- Create: `skills/pipeline/references/layout/workspace-shell.md`

**Interfaces:**
- Consumes: Task 1 条款、Task 2 schema
- Produces: 章节锚点 `## 探测`、`## detached HEAD 处置`、`## 指针漂移修复`；Task 8 会往同一文件追加 `## inline → shell 迁移`

- [ ] **Step 1: 验证「红」**

```bash
test -f skills/pipeline/references/layout/workspace-shell.md && echo EXISTS || echo MISSING
```

Expected: `MISSING`

- [ ] **Step 2: 创建文件，写「定位」+「探测」两节**

「定位」节：一句话说明本文是 workspace_mode 的**操作手册**，协议正文在 `_shared/workspace-mode.md`，二者不重复。

「探测」节逐字内容：

```markdown
## 探测

**执行时机**：仅 `init` / `retrofit` / `realign --scope=layout`。**运行时只认 frontmatter，不重新探测**（fail-closed）。

**步骤**：

1. `test -f .gitmodules` —— 不存在则判定 `inline`，**不追问用户**，结束
2. 列出全部 submodule name：
   `git config -f .gitmodules --name-only --get-regexp '^submodule\..*\.path$' | sed 's/^submodule\.//; s/\.path$//'`
3. 无条目 → 判定 `inline`，结束
4. 有条目 → AskUserQuestion **多选**：哪些是代码根？
   - 选项逐个列出 `<name>（路径：<path>）`
   - 提示语必须说明「子模块也可能是素材 / vendor，不都算代码根」
   - 允许全不选 → 判定 `inline`
5. 写入外壳仓根 `AGENTS.md` 的 `devdocs:` frontmatter：`workspace_mode: shell` + `code_roots: [<选中的 name>]`
6. 写入后立即跑一次校验（`workspace/fail-closed` 全表），任一 ⛔ 则回滚本次写入并报告
```

- [ ] **Step 3: 写「detached HEAD 处置」节**

逐字内容：

```markdown
## detached HEAD 处置

**为什么必须有这道门**：`git submodule update` 默认把子模块置于 detached HEAD。在此状态下提交会产生**游离 commit** —— 外壳仓 bump 指针后代码看似都在，但子模块里无任何分支引用它，`git gc` 后可能被回收，且 `git push` 推不上去。这是本布局最容易踩、最难察觉的坑。

**检测**（提交前对每个**有变更的** code_root 执行）：

```bash
git -C <path> symbolic-ref -q HEAD
```

- 退出码 0 且输出形如 `refs/heads/<branch>` → 通过
- 退出码非 0（无输出）→ detached，⛔ **阻塞提交**

**⛔ 阻塞文案**（恢复方式按共享约束 §7 格式）：

> ⛔ 子模块 `<name>` 处于 detached HEAD，此状态下提交会产生游离 commit。
> 恢复方式：`git -C <path> checkout <branch>`（若变更已在工作区，checkout 会带过去；若已误提交，先 `git -C <path> branch <tmp> <sha>` 保住 commit 再切）

**不自动修复** —— 该切哪个分支是用户决策（可能要新建 feature 分支，也可能要切回主干）。
```

- [ ] **Step 4: 写「指针漂移修复」节**

逐字内容：

```markdown
## 指针漂移修复

**症状**：外壳仓记录的子模块 SHA ≠ 子模块实际 HEAD。

**检测**：`git submodule status` —— 前缀 `+` 表示已检出的 commit 与外壳仓记录不一致。

**三种成因与处置**：

| 成因 | 判据 | 处置 |
|------|------|------|
| 漏 bump（子模块已提交，外壳仓没跟） | 子模块 HEAD 比记录**新**，且在同一分支上 | 补一次外壳仓提交：`git add <path> && git commit` |
| 未 update（外壳仓记录较新，本地子模块滞后） | 记录的 SHA 在子模块中存在但非 HEAD | `git submodule update <path>` |
| 分叉（互不包含） | 记录的 SHA 与 HEAD 无祖先关系 | ⛔ 阻塞，AskUserQuestion 让用户决定以哪边为准，**不自动选** |
```

- [ ] **Step 5: 验证「绿」**

```bash
cd /Users/mason/Projects/Personal/skills
grep -c "^## " skills/pipeline/references/layout/workspace-shell.md   # 期望 ≥4（定位/探测/detached/漂移）
grep -q "symbolic-ref" skills/pipeline/references/layout/workspace-shell.md && echo OK
```

- [ ] **Step 6: 提交**

```bash
git add skills/pipeline/references/layout/workspace-shell.md
git commit -m "docs(layout): 新增 workspace-shell 操作手册(探测/detached HEAD/指针漂移)"
```

---

### Task 4: 探测接入编排层

**Files:**
- Modify: `skills/pipeline/SKILL.md`（`### 入口私有约束` 节）
- Modify: `skills/pipeline/references/realign-scope-layout.md`（`### 执行步骤` + `### Phase 5：frontmatter 升级`）

**Interfaces:**
- Consumes: Task 3 的 `## 探测` 节锚点
- Produces: init / retrofit / realign 三条路径上的探测调用点

- [ ] **Step 1: 验证「红」**

```bash
grep -c "workspace-shell" skills/pipeline/SKILL.md skills/pipeline/references/realign-scope-layout.md
```

Expected: 两个 `0`

- [ ] **Step 2: `pipeline/SKILL.md` 入口私有约束加一条**

逐字内容（放该节末尾）：

```markdown
- **工作区模式探测（`init` / `retrofit`）**：`ms-requirements` 完成后（首次产生 `docs/devdocs/`）、`agent-memory --update` 之前，执行一次工作区模式探测，见 [layout/workspace-shell.md § 探测](references/layout/workspace-shell.md#探测)。探测结果写入 `AGENTS.md` 的 `devdocs:` frontmatter。无 `.gitmodules` 时静默判定 `inline`，不打扰用户。
```

改完 `wc -l skills/pipeline/SKILL.md` 确认 ≤ 500。

- [ ] **Step 3: `realign-scope-layout.md` 执行步骤加一步**

在 `### 执行步骤` 列表末尾追加：

```markdown
N. **工作区模式核对**：读 `AGENTS.md` 的 `workspace_mode`。
   - 无字段且仓内存在 `.gitmodules` → 在 plan 中列为「可选项：未声明工作区模式」，dry-run 展示，**不自动改**
   - 有 `workspace_mode: shell` → 跑 `workspace/fail-closed` 全表校验，失配项进 plan 的修复清单
   - 有 `workspace_mode: inline` → 无操作
```

（`N.` 替换为实际的下一个序号。）

- [ ] **Step 4: `realign-scope-layout.md` Phase 5 加 frontmatter 升级项**

在 `### Phase 5：frontmatter 升级` 中补：修复 `workspace_mode` / `code_roots` 失配（如 name 已从 `.gitmodules` 移除）时，按 `workspace/fail-closed` 提示的方向修正，**每项 AskUserQuestion 确认**。

- [ ] **Step 5: 验证「绿」**

```bash
cd /Users/mason/Projects/Personal/skills
grep -c "workspace-shell\|workspace_mode" skills/pipeline/SKILL.md                          # ≥1
grep -c "workspace_mode" skills/pipeline/references/realign-scope-layout.md                 # ≥3
wc -l skills/pipeline/SKILL.md                                                              # ≤500
```

- [ ] **Step 6: 提交**

```bash
git add skills/pipeline/SKILL.md skills/pipeline/references/realign-scope-layout.md
git commit -m "feat(pipeline): init/retrofit/realign 接入工作区模式探测"
```

---

### Task 5: health rule `submodule-pointer-drift`

**Files:**
- Modify: `skills/pipeline/references/health-lint-implementation.md`（rule 表 5 条 → 6 条 + 新增 `### submodule/pointer-drift` 详情节 + Finding schema 的 rule_id 枚举）
- Modify: `skills/pipeline/references/realign-scope-health.md`（`### 执行步骤` 第 4 步的 rule → 维度映射）

**Interfaces:**
- Consumes: Task 3 的 `## 指针漂移修复` 节（修复路径指向它，不重复算法）
- Produces: rule_id `submodule/pointer-drift`

- [ ] **Step 1: 验证「红」**

```bash
grep -c "pointer-drift" skills/pipeline/references/health-lint-implementation.md
```

Expected: `0`

- [ ] **Step 2: rule 表加一行**

标题 `## Rule 集（[新增] 5 条）` → `## Rule 集（[新增] 6 条）`，表内追加：

```markdown
| `submodule/pointer-drift` | ⛔ / ⚠️ | a 结构正确性 | v1+v2（仅 shell）| ❌（manual_decision）|
```

同时更新表下方那句「5 条全部 [新增]」为 6 条，并补一句：`submodule/pointer-drift` 仅在 `workspace_mode: shell` 下生效，`inline` 项目报 `not_applicable`。

- [ ] **Step 3: 写 rule 详情节**

仿 `state/total-size-cap` 的结构（目的 / 检测对象 / 算法 / 修复路径 / 误报与边界），逐字内容：

```markdown
### `submodule/pointer-drift`

**目的**：检测外壳仓记录的子模块指针与子模块实际状态不一致，防止「代码已提交但追溯链断裂」静默累积。

**检测对象**：`AGENTS.md` 的 `code_roots` 解析出的每个子模块路径。

**适用性门**：读 `AGENTS.md` 的 `workspace_mode`；非 `shell`（含字段缺失）→ 输出 finding `{ status: not_applicable }`，return。

**算法**（Agent 执行步骤）：

```text
1. 适用性门
   mode = AGENTS.md devdocs.workspace_mode
   if mode != "shell": 输出 not_applicable，return

2. 解析各代码根路径
   for name in code_roots:
     path = Bash: git config -f .gitmodules submodule.$name.path
     if 解析失败: severity = blocker
                  verdict_msg = "code_roots 中的 $name 不存在于 .gitmodules"
                  继续下一个

3. 读指针状态
   status = Bash: git submodule status -- "$path"
   首字符判定：
     ' ' (空格) → 一致，pass
     '+'        → 漂移，进第 4 步定性
     '-'        → 未初始化
                  severity = warning
                  verdict_msg = "$name 未初始化，跑 git submodule update --init $path"
                  继续下一个

4. 漂移定性（区分三种成因，见 workspace-shell.md § 指针漂移修复）
   recorded = Bash: git ls-tree HEAD "$path" | awk '{print $3}'
   actual   = Bash: git -C "$path" rev-parse HEAD
   if Bash: git -C "$path" merge-base --is-ancestor "$recorded" "$actual" 成功:
     severity = warning   # 漏 bump：子模块领先
     verdict_msg = "$name 已领先记录 N 个 commit，外壳仓漏 bump 指针"
   elif Bash: git -C "$path" merge-base --is-ancestor "$actual" "$recorded" 成功:
     severity = warning   # 未 update：本地滞后
     verdict_msg = "$name 落后外壳仓记录，跑 git submodule update $path"
   else:
     severity = blocker   # 分叉
     verdict_msg = "$name 与外壳仓记录已分叉（互无祖先关系），需人工裁定"

5. 输出 finding（见"Finding 输出 schema"）
```

**修复路径**：**不可自动修复**。三种成因的处置见 [layout/workspace-shell.md § 指针漂移修复](layout/workspace-shell.md#指针漂移修复)（本文不重复）。分叉情形必须 AskUserQuestion。

**误报与边界**：

- 子模块目录为空（未 `submodule update --init`）→ 报 ⚠️ 而非 ⛔，因为这是本地环境问题不是仓库问题
- `.gitmodules` 中存在但不在 `code_roots` 里的子模块（素材 / vendor）**不扫**
```

- [ ] **Step 4: 更新 Finding schema 的 rule_id 枚举**

`## Finding 输出 schema` 里那行 `rule_id: state/total-size-cap | ... | health/dead-link` 追加 `| submodule/pointer-drift`。同时检查 `design/adr-only-revision` 是否也漏在该枚举里——若漏，一并补上（属顺手修既有遗漏，在 commit message 中说明）。

- [ ] **Step 5: `realign-scope-health.md` 映射**

`### 执行步骤` 第 4 步的 rule → 维度映射列表追加：

```markdown
   - `submodule/pointer-drift` → 维度 a（仅 `workspace_mode: shell`；`inline` 报 not_applicable）
```

- [ ] **Step 6: 验证「绿」**

```bash
cd /Users/mason/Projects/Personal/skills
grep -c "submodule/pointer-drift" skills/pipeline/references/health-lint-implementation.md   # ≥4
grep -c "submodule/pointer-drift" skills/pipeline/references/realign-scope-health.md         # ≥1
grep -q "6 条" skills/pipeline/references/health-lint-implementation.md && echo COUNT_OK
# 适用性门必须存在
grep -q "not_applicable" skills/pipeline/references/health-lint-implementation.md && echo GATE_OK
```

- [ ] **Step 7: 提交**

```bash
git add skills/pipeline/references/health-lint-implementation.md skills/pipeline/references/realign-scope-health.md
git commit -m "feat(health): 新增 submodule/pointer-drift rule(仅 shell 模式生效)"
```

---

### Task 6: 消费侧 A —— 提交与工作区

**Files:**
- Modify: `skills/dev-workflow/SKILL.md`（`### 原子提交约束`、`### 断点续做约束`、Phase 流程里的「自描述更新」）
- Modify: `skills/dev-workflow/references/task-orchestration.md`（状态检测四重验证）
- Modify: `skills/bugfix/SKILL.md`（提交节）
- Modify: `skills/dev-flow/SKILL.md`（原子提交节）

**Interfaces:**
- Consumes: `workspace/commit-protocol`、`workspace/recovery`、`workspace/no-pollution`（Task 1）
- Produces: 无（叶子消费点）

- [ ] **Step 1: 验证「红」**

```bash
grep -c "workspace-mode\|workspace_mode" skills/dev-workflow/SKILL.md skills/bugfix/SKILL.md skills/dev-flow/SKILL.md skills/dev-workflow/references/task-orchestration.md
```

Expected: 全 `0`

- [ ] **Step 2: `dev-workflow/SKILL.md` 原子提交约束加三条**

在 `### 原子提交约束` 现有 checkbox 之后追加：

```markdown
- [ ] **`workspace_mode: shell` 时展开为 N+1 仓提交**：Commit 1 拆成每个有变更的 code_root 一个 commit，Commit 2 是外壳仓一次 commit（文档 + 所有变更子模块的指针 bump）。协议见 [_shared/workspace-mode.md § N+1 仓提交协议](../_shared/workspace-mode.md)
- [ ] **shell 模式提交前必过 detached HEAD 门**：每个变更子模块 `git -C <path> symbolic-ref -q HEAD` 失败即 ⛔ 阻塞，处置见 [workspace-shell.md § detached HEAD 处置](../pipeline/references/layout/workspace-shell.md#detached-head-处置)
- [ ] **shell 模式下 `--single-commit` 不可用**：跨仓无法合并为单 commit，⚠️ 忽略该 flag 并提示
```

- [ ] **Step 3: `dev-workflow/SKILL.md` 断点续做约束加一条**

```markdown
- [ ] **`workspace_mode: shell` 时状态检测扩为五重**：「工作区」维遍历 N+1 个仓；「Git 历史」维收紧为「外壳仓存在带该 T-XX 的 commit **且** body 记录的子模块 SHA 与当前指针一致」；新增第五维「指针一致性」，不一致 → 进 Step 1.5 证据复核不直接跳过。**「证据复核」维（A/B/C/D1/D2/E）不变**——它复核 AC 表 / 测试 / trace / 对抗验证证据，与仓库拓扑无关
```

- [ ] **Step 4: `dev-workflow/SKILL.md` 自描述步骤加跳过条件**

找到 Phase 流程里「自描述更新」那一步（`grep -n "自描述" skills/dev-workflow/SKILL.md`），就地补：

```markdown
（`workspace_mode: shell` 时**默认跳过**——自描述产物写在代码目录内，违反零污染红线。跳过须在 yaml 摘要里以 ℹ️ 记录 `skipped: workspace_mode=shell`。用户显式 `--force-code-docs` 才执行）
```

- [ ] **Step 5: `task-orchestration.md` 状态检测扩写**

找到四重验证描述处，按 Step 3 同样的口径展开为五重，并给出具体命令：

```markdown
shell 模式下「工作区」维的遍历：

```bash
git status --porcelain                                    # 外壳仓
for p in <各 code_root path>; do git -C "$p" status --porcelain; done
```

任一仓有不相关变更 → 按现有 AskUserQuestion（stash / 忽略 / 终止）处理，**提示文案须标明是哪个仓**。
```

- [ ] **Step 6: `bugfix/SKILL.md` 提交节加指针**

```markdown
> `workspace_mode: shell` 时提交走 N+1 仓协议（含 detached HEAD 前置门与跨仓 Recovery），见 [_shared/workspace-mode.md § N+1 仓提交协议](../_shared/workspace-mode.md)。修复代码提交进对应子模块（commit message 沿用该仓风格、**不带 BUG-XX 编号**），bugfix 日志提交进外壳仓。
```

- [ ] **Step 7: `dev-flow/SKILL.md` 原子提交节加指针**

```markdown
> `workspace_mode: shell` 时「一项一 commit」展开为 N+1 仓，见 [_shared/workspace-mode.md § N+1 仓提交协议](../_shared/workspace-mode.md)。
```

- [ ] **Step 8: 验证「绿」**

```bash
cd /Users/mason/Projects/Personal/skills
for f in skills/dev-workflow/SKILL.md skills/bugfix/SKILL.md skills/dev-flow/SKILL.md skills/dev-workflow/references/task-orchestration.md; do
  echo "$f: $(grep -c 'workspace-mode\|workspace_mode' "$f")"
done
# SKILL.md 行数门
wc -l skills/dev-workflow/SKILL.md skills/bugfix/SKILL.md skills/dev-flow/SKILL.md
# 链接可达
grep -o '](\.\./_shared/workspace-mode\.md' skills/dev-workflow/SKILL.md | head -1
test -f skills/_shared/workspace-mode.md && echo LINK_TARGET_OK
```

四个文件均 ≥1 命中；三个 SKILL.md 均 ≤ 500 行。

- [ ] **Step 9: 提交**

```bash
git add skills/dev-workflow skills/bugfix/SKILL.md skills/dev-flow/SKILL.md
git commit -m "feat(dev): dev-workflow/bugfix/dev-flow 接入 N+1 仓提交协议"
```

---

### Task 7: 消费侧 B —— 只读与扫码

**Files:**
- Modify: `skills/codebase-insight/SKILL.md`
- Modify: `skills/test-run/SKILL.md`
- Modify: `skills/verify/SKILL.md`（`--impl` 维度）
- Modify: `skills/e2e-test-flow/SKILL.md`
- Modify: `skills/code-self-describe/SKILL.md`

**Interfaces:**
- Consumes: `workspace/code-roots-source`、`workspace/root-attribution`、`workspace/no-pollution`（Task 1）
- Produces: 无（叶子消费点）

- [ ] **Step 1: 验证「红」**

```bash
grep -c "workspace_mode" skills/codebase-insight/SKILL.md skills/test-run/SKILL.md skills/verify/SKILL.md skills/e2e-test-flow/SKILL.md skills/code-self-describe/SKILL.md
```

Expected: 全 `0`

- [ ] **Step 2: `codebase-insight/SKILL.md` —— 这是本 task 里最实质的一处**

多代码根时，仓间关系是核心产出。加一节：

```markdown
### 多代码根（workspace_mode: shell）

`workspace_mode: shell` 时代码不在仓库根，而在 `code_roots` 各子模块下（解析见 [_shared/workspace-mode.md](../_shared/workspace-mode.md)）。

- **逐个代码根盘点**，产出的模块 / 接口 / 数据对象一律带 `<root>/` 前缀限定，避免跨仓重名混淆
- **必须额外产出「仓间关系」小节**：依赖方向（谁调谁）、接口契约面（跨仓的 API / 消息 / 共享数据结构）、版本耦合点（改一边必须同改另一边的地方）。多代码根场景的价值主要在此——单仓时这节不存在
- 产物仍写外壳仓 `docs/codebase-insight.md`，**不往任何子模块写文件**
```

- [ ] **Step 3: `test-run/SKILL.md` 加指针**

```markdown
> `workspace_mode: shell` 时测试命令在各 `code_root` 目录下执行（`git -C <path>` 或 cd 进去），不在仓库根。多代码根时逐个执行并在报告中按 root 分组。测试报告写外壳仓 `docs/devdocs/05-test-report.md`。代码根解析见 [_shared/workspace-mode.md](../_shared/workspace-mode.md)。
```

- [ ] **Step 4: `verify/SKILL.md` 的 `--impl` 维度加指针**

```markdown
> `workspace_mode: shell` 时实现代码扫描范围是各 `code_roots` 路径，不是仓库根。外壳仓根下（`docs/` 之外）出现源码文件 → ⚠️ 提示「外壳仓不该有代码」。代码根解析见 [_shared/workspace-mode.md](../_shared/workspace-mode.md)。
```

- [ ] **Step 5: `e2e-test-flow/SKILL.md` 加指针**

放在影响分析（读代码那一阶段）附近：

```markdown
> 若工作区是 DevDocs 外壳布局（外壳仓根 `AGENTS.md` 含 `workspace_mode: shell`），源码在 `code_roots` 各子模块下而非仓库根。本 skill 与 DevDocs 独立，仅借该字段定位源码，不读 `docs/devdocs/`。
```

- [ ] **Step 6: `code-self-describe/SKILL.md` 加默认跳过**

```markdown
### workspace_mode: shell 下默认跳过

本 skill 的产物（模块级 `CLAUDE.md` + 源文件头注释）写在代码目录内。`workspace_mode: shell` 的动机就是不让私有产物进代码仓，二者直接冲突。

- **默认跳过**，输出 ℹ️ 说明原因，不报错
- 仅 `--force-code-docs` 显式启用。启用前 AskUserQuestion 确认「这些文件会进入 <各 code_root>，若该仓将公开请确认可接受」
```

- [ ] **Step 7: 验证「绿」**

```bash
cd /Users/mason/Projects/Personal/skills
for f in skills/codebase-insight/SKILL.md skills/test-run/SKILL.md skills/verify/SKILL.md skills/e2e-test-flow/SKILL.md skills/code-self-describe/SKILL.md; do
  echo "$f: $(grep -c 'workspace_mode' "$f") lines=$(wc -l < "$f")"
done
grep -q "仓间关系" skills/codebase-insight/SKILL.md && echo INSIGHT_OK
grep -q "force-code-docs" skills/code-self-describe/SKILL.md && echo SELFDESC_OK
```

五个文件均 ≥1 命中且 ≤ 500 行。

- [ ] **Step 8: 提交**

```bash
git add skills/codebase-insight/SKILL.md skills/test-run/SKILL.md skills/verify/SKILL.md skills/e2e-test-flow/SKILL.md skills/code-self-describe/SKILL.md
git commit -m "feat(skills): 只读/扫码类 skill 接入 code_roots 定位与零污染约束"
```

---

### Task 8: inline → shell 迁移子流程

**Files:**
- Modify: `skills/pipeline/references/layout/workspace-shell.md`（追加 `## inline → shell 迁移` 节）
- Modify: `skills/pipeline/references/realign-scope-layout.md`（挂接入口）

**Interfaces:**
- Consumes: Task 3 建立的文件与章节结构
- Produces: 迁移七步流程

- [ ] **Step 1: 验证「红」**

```bash
grep -c "inline → shell 迁移" skills/pipeline/references/layout/workspace-shell.md
```

Expected: `0`

- [ ] **Step 2: 追加迁移节**

内容从 spec §6 原样转写（七步表 + 6.2.1 迁移范围 + 6.3 三条不做 + 6.4 反向不提供），并在节首补触发条件：

```markdown
## inline → shell 迁移

**触发**：**仅由用户显式意图触发**（如「把这个项目转成外壳模式」），经 `/ms-pipeline realign --scope=layout` 路由至此。realign 自身**永不主动提议**做仓库手术——那是产品决策，不是规范差距。
```

七步表中每一步都要写出实际命令（`git init` / `git submodule add` / `git rm` 等），第 2 步的 dry-run 计划要列出「将创建的仓路径 / 将迁移的文件清单 / 将产生的 commit 及其 message」。

- [ ] **Step 3: 每步补 Recovery**

七步表下方加「失败恢复」小节，逐步给出：失败点 → 残留状态 → 恢复命令。强调**前 5 步只新增不删除故全部可逆**，唯一不可逆删除在第 6 步且此时 W 已完整。

- [ ] **Step 4: `realign-scope-layout.md` 挂接**

在 `## AskUserQuestion 触发点` 表加一行：

```markdown
| 工作区模式迁移 | 用户显式要求 inline → shell | 走 [workspace-shell.md § inline → shell 迁移](layout/workspace-shell.md#inline--shell-迁移) 的七步流程，第 2 步 dry-run 计划必须确认后才动文件 |
```

- [ ] **Step 5: 验证「绿」**

```bash
cd /Users/mason/Projects/Personal/skills
grep -q "inline → shell 迁移" skills/pipeline/references/layout/workspace-shell.md && echo SECTION_OK
grep -c "git submodule add\|git rm\|git init" skills/pipeline/references/layout/workspace-shell.md   # ≥3
grep -q "workspace-shell.md#inline" skills/pipeline/references/realign-scope-layout.md && echo LINK_OK
# 三条不做必须在
grep -q "不重写 R 的历史" skills/pipeline/references/layout/workspace-shell.md && echo NODO_OK
```

- [ ] **Step 6: 提交**

```bash
git add skills/pipeline/references/layout/workspace-shell.md skills/pipeline/references/realign-scope-layout.md
git commit -m "feat(layout): inline → shell 迁移七步流程(dry-run 优先,前 5 步可逆)"
```

---

### Task 9: 文档层

**Files:**
- Modify: `AGENTS.md`（`## 当前状态`）
- Modify: `docs/architecture.md`（`## 文件结构`）
- Modify: `docs/workflows.md`（新增用户面小节）

**Interfaces:**
- Consumes: 前 8 个 task 的全部产出
- Produces: 无

- [ ] **Step 1: `AGENTS.md` 当前状态加一条**

```markdown
- **工作区模式（inline / shell）**：新增与 layout/id/trace **正交**的维度——`shell` 模式下文档在外壳仓 `docs/`，代码作 git 子模块挂在同级（服务「维护开源项目」「自有项目待公开」两类零污染场景）。`code_roots` 记 submodule name（`.gitmodules` 为路径唯一真源），多代码根为一等场景。核心：零污染红线（LLM 不主动往子模块写非代码文件）+ N+1 仓提交协议（detached HEAD 前置门 / 外壳仓 commit 为追溯枢纽 / 跨仓 Recovery 三类）+ inline→shell 迁移七步（dry-run 优先，前 5 步可逆）。协议 SSOT 在 [_shared/workspace-mode.md](skills/_shared/workspace-mode.md)，操作手册在 [layout/workspace-shell.md](skills/pipeline/references/layout/workspace-shell.md)，方案见 [specs/2026-08-05-devdocs-shell-workspace-mode-design.md](docs/superpowers/specs/2026-08-05-devdocs-shell-workspace-mode-design.md)。**无 `workspace_mode` 字段 = `inline` = 现状，存量项目零影响**
```

- [ ] **Step 2: `docs/architecture.md` 文件结构加 shell 布局图**

在现有 `docs/` 树之后追加：

```markdown
### workspace_mode: shell 布局

代码与文档分仓时（外壳仓私有、代码仓可公开）：

```
<project>-dev/                    # 外壳仓
├── AGENTS.md                     # devdocs.workspace_mode: shell + code_roots
├── .gitmodules                   # 路径与 URL 唯一真源
├── docs/                         # 结构与上方完全一致，一字节未变
├── web/                          # 子模块 = code_root
└── api/                          # 子模块 = code_root
```

docs 内部结构不因模式而变，故本维度与 layout 版本正交。详见 [_shared/workspace-mode.md](../skills/_shared/workspace-mode.md)。
```

- [ ] **Step 3: `docs/workflows.md` 加用户面小节**

```markdown
## 文档与代码分仓（workspace_mode: shell）

**什么时候用**：维护 fork 的开源项目，或自有项目计划公开——DevDocs 的需求 / 设计 / 任务 / 洞察都是私有产物，不该进代码仓。

**怎么开**：

- **新项目**：`/ms-pipeline init`。若仓内有 `.gitmodules`，会问你哪些子模块是代码根
- **已有外壳仓但没跑过 DevDocs**（如手工建好的 `xxx-dev`）：`/ms-pipeline retrofit`
- **现有单仓要拆开**：直接说「把这个项目转成外壳模式」，走 `realign --scope=layout` 的七步迁移，第 2 步会先给你完整 dry-run 计划

**开了之后有什么不同**：

| | 变了 | 没变 |
|---|------|------|
| 文档路径 | — | `docs/devdocs/` 等全部不变 |
| 提交 | 一个任务产生 N+1 个 commit（每个变更代码根一个 + 外壳仓一个）| 一任务一次提交的原则不变 |
| 代码仓 | 只收代码和测试，commit message 沿用该仓风格、不带 DevDocs 编号 | — |
| 自描述 / 代码注释类产物 | 默认跳过（`--force-code-docs` 才开） | — |

**追溯**：外壳仓的 commit 是枢纽——它带 T-XX，body 里记各子模块 SHA。代码仓自身干净得像没有 DevDocs 存在过。
```

- [ ] **Step 4: 验证「绿」**

```bash
cd /Users/mason/Projects/Personal/skills
grep -q "workspace_mode" AGENTS.md && echo AGENTS_OK
grep -q "workspace_mode: shell 布局" docs/architecture.md && echo ARCH_OK
grep -q "文档与代码分仓" docs/workflows.md && echo WF_OK
```

- [ ] **Step 5: 提交**

```bash
git add AGENTS.md docs/architecture.md docs/workflows.md
git commit -m "docs: 登记工作区模式(shell)——AGENTS 当前状态 + 布局图 + 用户面说明"
```

---

### Task 10: 静态一致性与零影响核验

**Files:**
- 无修改（纯验证；若发现问题则回到对应 task 的文件修）

**Interfaces:**
- Consumes: Task 1–9 全部产出
- Produces: 核验结论（写入本 task 的 commit message，不新增文件）

- [ ] **Step 1: 零影响核验 —— 无裸露无条件门**

逐条人工审查每一处新增规则，确认触发条件都带 `workspace_mode: shell` 限定：

```bash
cd /Users/mason/Projects/Personal/skills
# 列出所有提到 code_roots / N+1 提交 / detached HEAD 的行，逐行看是否在 shell 条件下
rg -n "code_roots|N\+1 仓|detached HEAD|pointer-drift" skills/ --type md
```

判据：每一处要么句中含 `shell`，要么所在小节标题 / 上文一句明确限定 `workspace_mode: shell`。**存在无限定的规则即为不合格**，必须回改。

- [ ] **Step 2: 字段名一致性**

```bash
cd /Users/mason/Projects/Personal/skills
rg -o "workspace_mode|code_roots|code_root\b" skills/ docs/ AGENTS.md --type md | \
  awk -F: '{print $NF}' | sort | uniq -c | sort -rn
```

判据：只应出现 `workspace_mode` / `code_roots` 两种（`code_root` 单数仅允许在「某个代码根」这类散文语境，不得作为字段名出现）。

- [ ] **Step 3: 条款 id 一致性**

```bash
cd /Users/mason/Projects/Personal/skills
# workspace-mode.md 定义了哪些条款
rg -o '`workspace/[a-z-]+`' skills/_shared/workspace-mode.md | sort -u
# 别处引用了哪些
rg -o '`workspace/[a-z-]+`' skills/ --type md | grep -v workspace-mode.md | awk -F'`' '{print $2}' | sort -u
```

判据：被引用的条款必须全部在定义集合内（引用了不存在的条款 = bug）。

- [ ] **Step 4: 死链核验**

```bash
cd /Users/mason/Projects/Personal/skills
# 抽出本次新增的相对链接并逐个 test -f
rg -o '\]\((\.\./)*[a-zA-Z0-9_/-]+\.md' skills/_shared/workspace-mode.md skills/pipeline/references/layout/workspace-shell.md
```

逐条 `test -f` 解析后的路径。任何不存在即为死链，必须修。

- [ ] **Step 5: SKILL.md 行数门**

```bash
cd /Users/mason/Projects/Personal/skills
for f in skills/*/SKILL.md; do n=$(wc -l < "$f"); [ "$n" -gt 500 ] && echo "OVER: $f=$n"; done
echo "行数检查完成"
```

判据：无输出（除最后那行）即通过。

- [ ] **Step 6: 存量项目回归自查**

确认 spec 声称的「无 `workspace_mode` = `inline` = 零影响」成立：随便挑一个现存的 `inline` 流程描述（如 `dev-workflow` 的原子提交约束），确认原有 checkbox **一条未删、一条未改语义**，新增的三条都带 shell 限定。

- [ ] **Step 7: 提交核验结论**

```bash
git commit --allow-empty -m "chore(verify): 工作区模式静态一致性核验通过

- 无裸露无条件门（所有新规则带 workspace_mode: shell 限定）
- 字段名统一 workspace_mode / code_roots
- workspace/* 条款引用全部有定义
- 新增相对链接无死链
- 全部 SKILL.md ≤ 500 行
- inline 路径原有约束一条未改"
```

若任一步不通过：**不要提交这个 commit**，回到对应 task 修完再跑。

---

### Task 11: 真实端到端 + 对抗审查

**Files:**
- 无本仓修改（端到端在 `~/Projects/Personal/chiaki-ng-dev` 进行）

**Interfaces:**
- Consumes: Task 1–10 全部产出

⚠️ **本 task 会改动本仓之外的仓库（`chiaki-ng-dev` 及其子模块），执行前必须向用户确认。**

- [ ] **Step 1: 端到端前置确认**

向用户确认：可以在 `~/Projects/Personal/chiaki-ng-dev` 上做实测吗？该仓已有子模块 `chiaki-ng` + `docs/devdocs/`（散文态），是 retrofit 的真实样本。确认包括：能否产生真实 commit、子模块能否切出临时分支。

- [ ] **Step 2: 探测实测**

在 `chiaki-ng-dev` 跑 `/ms-pipeline retrofit`（或直接触发探测），验证：

- 正确列出 `chiaki-ng` 并询问是否为代码根
- 选中后 `AGENTS.md` frontmatter 正确写入 `workspace_mode: shell` + `code_roots: [chiaki-ng]`
- 再跑一次为 no-op（幂等）

- [ ] **Step 3: 校验规则实测（fail-closed）**

人为制造三种失配，确认各自 ⛔ 且提示正确：

```bash
# a) name 不存在
# 临时把 code_roots 改成 [nonexistent]，跑任一 shell 感知的 skill，期望 ⛔ 提示修 frontmatter
# b) detached HEAD
git -C ~/Projects/Personal/chiaki-ng-dev/chiaki-ng checkout --detach
# 尝试走提交流程，期望 ⛔ 阻塞并给出 checkout 恢复命令
# c) 指针漂移
# 在子模块提交一个 commit 但不 bump 外壳仓，跑 /ms-pipeline realign --scope=health
# 期望 submodule/pointer-drift 报 ⚠️「漏 bump」
```

每种情形恢复现场后再测下一种。

- [ ] **Step 4: N+1 提交实测**

在 `chiaki-ng-dev` 造一个最小任务（改子模块里一个文件 + 改外壳仓一个文档），走提交流程，验证：

- 子模块产生 1 个 commit，message 沿用该仓风格，**不含 T-XX**
- 外壳仓产生 1 个 commit，含文档变更 + 子模块指针 bump，body 含 `chiaki-ng@<sha7>`
- 从外壳仓 commit 能反查到子模块 SHA（追溯枢纽成立）
- 子模块 `git status` 干净，无任何 DevDocs 文件

- [ ] **Step 5: 清理实测痕迹**

按 Step 1 与用户约定的方式处理实测 commit（保留 / reset / 切废弃分支）。

- [ ] **Step 6: 对抗审查**

```bash
/adversarial-review
```

审查范围为本次全部变更。重点交代给审查方三个靶子：

1. **detached HEAD 门是否足够** —— 有没有别的路径能绕过它产生游离 commit（如子模块内嵌套子模块、worktree）
2. **跨仓 Recovery 三类是否穷尽** —— 有没有第四种失败形态（如子模块 pre-commit hook 拒绝、外壳仓 commit 成功但 bump 了错误的 SHA）
3. **指针一致性维与 Step 1.5 六项证据复核是否冲突** —— 新增的第五维会不会让本该跳过的已完成任务反复进复核

- [ ] **Step 7: 处理审查结论并提交**

按 `/adversarial-review` 输出逐条判定采纳与否。采纳项改完后：

```bash
git add -A
git commit -m "fix(shell): 对抗审查反馈修正

<逐条列出采纳的反馈与改法>"
```

未采纳项在 commit message 或 spec 中记录理由。

---

## Self-Review 记录

**Spec 覆盖核对**（spec 章节 → 落地 task）：

| spec 章节 | 落地 |
|-----------|------|
| §1 问题与定位 / 正交性论证 | Task 1（workspace-mode.md 第 1 节）+ Task 9（architecture.md） |
| §2.1 frontmatter 字段 + name 而非路径 | Task 1 第 2 节 + Task 2 |
| §2.2 校验规则表 | Task 1 第 3 节 + Task 2 Step 3/4 |
| §2.3 探测 | Task 3 Step 2 + Task 4 |
| §2.4 归属判定 | Task 1 第 4 节 + Task 7 Step 4（verify 的外壳仓源码告警） |
| §2.5 多代码根一等场景（四条后果） | 后果 1 → Task 6 Step 2；后果 2 → Task 1 第 6 节；后果 3 → Task 7 Step 2；后果 4 → Task 6 Step 3/5 |
| §3 零污染写入范围 | Task 1 第 5 节 + Task 6 Step 4 + Task 7 Step 6 |
| §4.1–4.3 N+1 提交与追溯枢纽 | Task 1 第 6 节 + Task 6 Step 2 |
| §4.2 detached HEAD 前置门 | Task 3 Step 3 + Task 6 Step 2 |
| §4.4 跨仓 Recovery | Task 1 第 6 节 |
| §4.5 断点续做五重验证 | Task 6 Step 3 + Step 5 |
| §5 改动清单 | Task 1–9 逐项 |
| §5 版本号处置 | Task 1 Step 4（唯一 bump）+ Global Constraints |
| §6 迁移七步 + 6.2.1 范围 + 6.3 不做 | Task 8 |
| §7 不在范围 | 无需落地（negative scope） |
| §8 影响面与验证 | Task 10 + Task 11 |

无遗漏。

**已修正的内部不一致**：

- 初稿 Task 5 未给「适用性门」，会让 `inline` 项目跑到子模块解析步骤 → 已在算法第 1 步加 `not_applicable` 早退
- 初稿 Task 6 只说「扩为五重」未说「证据复核维不变」→ 已补，避免执行者误改 Step 1.5 的 A/B/C/D1/D2/E
- 初稿 Task 10 的零影响核验只做 grep 计数，无判据 → 已改为逐行审查 + 明确的合格判据
