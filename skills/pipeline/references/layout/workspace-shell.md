# Workspace Shell 操作手册

## 定位

本文是 `workspace_mode` 维度的**操作手册**，回答"具体怎么操作"；协议正文（模式枚举、`code_roots` 真源、fail-closed 校验表、归属判定、零污染范围、N+1 仓提交协议、Recovery 格式等"规则是什么"）的唯一权威源是 [../../../_shared/workspace-mode.md](../../../_shared/workspace-mode.md)，本文不重复其规则表格，引用规则时以指针链接代替。

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
5. 写入外壳仓根 `AGENTS.md` 的 `devdocs:` frontmatter：**仅** `workspace_mode: shell` + `code_roots: [<选中的 name>]` 这两个字段——探测的写入范围到此为止，不涉及其余字段。

   **若 `devdocs:` 段此前完全不存在**（项目从未跑过 `init`/`retrofit`，`AGENTS.md` 里没有任何 `devdocs:` frontmatter）：探测会就地创建一个**只含这两字段的部分块**，例如：

   ```yaml
   ---
   devdocs:
     workspace_mode: shell
     code_roots: [chiaki-ng]
   ---
   ```

   `docs_layout_version` / `id_scheme` / `traceability_version` 三层版本号与 `initialized_at` **不在探测的写入范围内**——它们由 layout 元数据机制负责，该机制的执行接口在本仓标 FUTURE（见 [layout-metadata-schema.md](layout-metadata-schema.md)）。探测**不代写、不伪造**这几个字段：三层版本号没有可靠来源，伪造比缺失更糟；`initialized_at` 的语义是「DevDocs 首次初始化时间」，探测无权代为声称这件事。

   此时按 [layout-metadata-schema.md §1「缺失时的行为」](layout-metadata-schema.md#缺失时的行为)：devdocs 段不完整（缺字段）→ skill surface **⚠️ 警告 + 建议补全**，**不阻塞**。消费方不得把这条部分块当 ⛔ 处理——探测产出的部分块是合法的既知状态，不是意外。
6. 写入后立即跑一次校验（`workspace/fail-closed` 全表），任一 ⛔ 则回滚本次写入并报告。该表只校验 `workspace_mode`/`code_roots` 相关规则，不涉及第 5 步说明的三层版本号/`initialized_at`（那些字段的缺失走上方 ⚠️ 不阻塞路径，不在本表判定范围内）

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

## 指针漂移修复

**症状**：外壳仓记录的子模块 SHA ≠ 子模块实际 HEAD。

**检测**：`git submodule status` —— 前缀 `+` 表示已检出的 commit 与外壳仓记录不一致。

**三种成因与处置**：

| 成因 | 判据 | 处置 |
|------|------|------|
| 漏 bump（子模块已提交，外壳仓没跟） | 子模块 HEAD 比记录**新**，且在同一分支上 | 补一次外壳仓提交：`git add <path> && git commit` |
| 未 update（外壳仓记录较新，本地子模块滞后） | 记录的 SHA 在子模块中存在但非 HEAD | `git submodule update <path>` |
| 分叉（互不包含） | 记录的 SHA 与 HEAD 无祖先关系 | ⛔ 阻塞，AskUserQuestion 让用户决定以哪边为准，**不自动选** |

## inline → shell 迁移

**触发**：**仅由用户显式意图触发**（如「把这个项目转成外壳模式」），经 `/ms-pipeline realign --scope=layout` 路由至此。realign 自身**永不主动提议**做仓库手术——那是产品决策，不是规范差距。

要做的是一次**仓库手术**：单仓 R（code + docs 混在一起）→ 外壳仓 W + R 作为 W 的子模块。R 保留全部历史并继续当代码仓，W 是新建的空仓。

以下命令示例中，`$R` 表示 R 的绝对路径（迁移前的单仓工作目录），`$W` 表示外壳仓目标路径（默认 `../<R名>-dev`，Step 3 可覆盖）。

### 七步，dry-run 优先

| 步 | 动作 | 门 |
|----|------|-----|
| 1 | 前置检查：R 工作区干净、有 remote、无未推送提交 | 任一不满足 ⛔ 阻塞 —— 手术前必须有远端兜底 |
| 2 | 输出完整计划（建哪个仓、移哪些文件、产生哪几个 commit），AskUserQuestion 确认 | 未确认不动任何文件 |
| 3 | 在 `../<R名>-dev` 建 W（`git init` + 初始 commit），路径可覆盖 | 目标已存在 ⛔ |
| 4 | `git submodule add <R 的 url> <name>` | |
| 5 | 迁移 DevDocs 产物到 `W/docs/`；R 根 `AGENTS.md` 的 `devdocs:` 治理段迁到 `W/AGENTS.md`；委托 `agent-memory --update` 补工作流路由节 | 见下方「迁移范围」小节 |
| 6 | R 内 `git rm -r` 已迁走的路径 + 清掉 `devdocs:` frontmatter → commit `chore: 迁出 DevDocs 产物` | **不自动 push**，提示用户自行推送 |
| 7 | W 写 `workspace_mode: shell` / `code_roots: [<name>]`，bump 子模块指针，commit | |

每步失败都给 Recovery（见下方「失败恢复」）。步序刻意设计成**前 5 步全部可逆**（只新增不删除）；唯一不可逆的删除集中在第 6 步，且此时 W 已完整。

#### 逐步命令

**Step 1 —— 前置检查**

```bash
git -C "$R" status --porcelain
# 非空输出 ⛔ 阻塞：工作区不干净

R_REMOTE=$(git -C "$R" remote | grep -qx origin && echo origin || git -C "$R" remote | head -1)
[ -z "$R_REMOTE" ] && echo "⛔ 阻塞：无 remote，手术前必须有远端兜底"
# R_REMOTE 记录探测到的实际 remote 名（优先 origin，否则取第一个）；Step 4 复用，不假设一定叫 origin

git -C "$R" rev-list --count '@{u}..HEAD' 2>/dev/null
# 非 0（或命令报错说明无上游）⛔ 阻塞：存在未推送提交
```

**Step 2 —— dry-run 计划**

```bash
R_NAME=$(basename "$(git -C "$R" rev-parse --show-toplevel)")
W="${W:-$(dirname "$R")/${R_NAME}-dev}"

# 无条件迁移清单
ls -d "$R"/docs/devdocs "$R"/docs/prd "$R"/docs/codebase-insight.md 2>/dev/null

# docs/ 下未分类条目 —— 逐项 AskUserQuestion
ls "$R"/docs 2>/dev/null | grep -vE '^(devdocs|prd|codebase-insight\.md)$'
```

dry-run 计划必须列出并经 AskUserQuestion 确认：

- **将创建的仓路径**：`$W`
- **将迁移的文件清单**：`docs/devdocs/`、`docs/prd/`、`docs/codebase-insight.md`（无条件）+ 用户对未分类条目逐项确认后的清单
- **将产生的 commit 及其 message**：
  - `$W` 初始 commit：`chore: init shell workspace`（Step 3）
  - `$W` 迁入 commit：`chore: 迁入 DevDocs 产物`（Step 5）
  - `$R` 迁出 commit：`chore: 迁出 DevDocs 产物`（Step 6）
  - `$W` 收尾 commit：`chore: 声明 workspace_mode: shell 并初始化子模块指针`（Step 7）

未确认（用户未回复 AskUserQuestion，或选择放弃）**不动任何文件**。

**Step 3 —— 建 W**

```bash
test -e "$W" && { echo "⛔ 目标已存在：$W"; exit 1; }   # 真阻断：命中即退出，不继续往下执行

mkdir -p "$W"
cd "$W" && git init
git commit --allow-empty -m "chore: init shell workspace"
```

**Step 4 —— 加子模块**

```bash
R_URL=$(git -C "$R" remote get-url "$R_REMOTE")   # 复用 Step 1 探测到的 remote 名，不硬编码 origin
cd "$W"
git submodule add "$R_URL" "<name>"   # <name> 默认取 R_NAME，用户可在计划确认时改
```

**Step 5 —— 迁移产物**

```bash
mkdir -p "$W/docs"

# 无条件迁移（拷贝而非 git mv：R/W 是两个独立仓，跨仓无法保留同一次移动记录，见「明确不做」第 2 条）
cp -r "$R/docs/devdocs" "$W/docs/devdocs"
[ -d "$R/docs/prd" ] && cp -r "$R/docs/prd" "$W/docs/prd"
[ -f "$R/docs/codebase-insight.md" ] && cp "$R/docs/codebase-insight.md" "$W/docs/codebase-insight.md"
# Step 2 确认要迁移的未分类条目，同样逐个 cp -r 到 "$W/docs/<条目>"

# 将 R 根 AGENTS.md 的 devdocs: frontmatter 段整体剪切到 W/AGENTS.md
# （文本编辑操作，非 shell 命令；R 侧原文件此时保持不动，删除留到 Step 6）

cd "$W"
git add docs/ AGENTS.md
git commit -m "chore: 迁入 DevDocs 产物"
```

委托 `agent-memory --update` 为 `$W/AGENTS.md` 补工作流路由节。

**Step 6 —— R 内清理（唯一不可逆删除）**

```bash
cd "$R"
git rm -r docs/devdocs docs/prd docs/codebase-insight.md   # 只删已确认迁走的路径，不是 git rm -r docs/
# Step 2 确认要迁移的未分类条目，同样逐个 git rm -r "docs/<条目>"（与 Step 5 的 cp 对称，两侧都要处理，否则两边都留着）
# 手工清掉 AGENTS.md 里的 devdocs: frontmatter 段（内容已在 Step 5 剪切进 W）
git add AGENTS.md
git commit -m "chore: 迁出 DevDocs 产物"
# 不自动 push —— 提示用户自行 git push
```

**Step 6 与 Step 7 之间 —— push + 把子模块具名分支快进到最新（必需，否则 Step 7 指针不含迁出变更）**

Step 4 的 `git submodule add` 是从远端 URL **独立 clone**，工作树内容取自当时的远端 HEAD，并不指向本地 `$R` 目录；Step 6 的迁出 commit 只落在 `$R` 本地（「不自动 push」）。若跳过同步直接执行 Step 7，`git -C "<name>" rev-parse HEAD` 读到的还是 Step 4 clone 时的旧 SHA —— 子模块工作树里 `docs/devdocs` 等本该迁出的内容**依然存在**，迁移在代码根一侧根本没有完成。

```bash
# 1. 用户需先在 R 本地把 Step 6 的迁出 commit 推到远端
git -C "$R" push

# 2. 子模块目录里把具名分支指针快进到最新
#    —— 不能用 `checkout <branch>`：子模块本就在该分支上，checkout 同分支是空操作，
#       它只更新 origin/<branch>（远程追踪分支），不移动本地分支指针本身（已实测验证，见失败恢复后的实测记录）
git -C "$W/<name>" fetch origin
git -C "$W/<name>" merge --ff-only origin/<branch>

# 3. 断言同步到位且仍在具名分支上，再进入 Step 7
[ "$(git -C "$W/<name>" rev-parse HEAD)" = "$(git -C "$R" rev-parse HEAD)" ] || echo "⛔ 未同步到位，见下方「若用户未 push」"
git -C "$W/<name>" symbolic-ref -q HEAD || echo "⛔ 已脱离具名分支，不得继续"
```

**为什么不用 `git submodule update --remote`**：该命令会把子模块置于 **detached HEAD**——正是 `## detached HEAD 处置` 小节警告的危险态（游离 commit、`git gc` 可能回收），且违反"Step 7 之后一切都依赖仍在具名分支上"的前提，因此不作为备选，只保留 `merge --ff-only` 这一条路径。

**若用户未 push 就跑了同步**：`merge --ff-only` 不会报错，只会输出"已经是最新的"（因为 `origin/<branch>` 本身没有新内容可合并）——子模块 HEAD 悄悄停留在旧内容上，比报错更隐蔽。这正是第 3 步要显式断言 `rev-parse HEAD` 与 `$R` 本地 HEAD 是否一致的原因：只看 `merge` 命令退出码（恒为 0）不足以判断同步是否到位。断言失败 → ⛔ 提示用户先确认 `git -C "$R" push` 已成功，再重跑第 2、3 步；不得直接进入 Step 7。若已经带着错误指针跑完 Step 7，按下方「指针漂移修复」的「未 update」情形处置，不在此重复算法。

**Step 7 —— W 声明模式 + 指针**

```bash
cd "$W"
# 编辑 AGENTS.md 写入 workspace_mode: shell / code_roots: [<name>]
SUBMODULE_SHA=$(git -C "<name>" rev-parse HEAD)
git add AGENTS.md "<name>"
git commit -m "chore: 声明 workspace_mode: shell 并初始化子模块指针"
```

### 迁移范围：只搬 DevDocs 产物，不搬整个 docs/

`docs/` 里未必只有 DevDocs 产物 —— 用户面文档、API 文档、架构图等属于代码仓，搬走反而是错的。

- **无条件迁移**：`docs/devdocs/`、`docs/prd/`、`docs/codebase-insight.md`
- **留在 R**：`docs/` 下其余内容
- **逐项确认**：第 2 步的 dry-run 计划里列出 `docs/` 下所有未分类条目，AskUserQuestion 让用户决定去留

第 6 步的 `git rm` 只删已确认迁走的路径，不是 `git rm -r docs/`。

### 明确不做

1. **不重写 R 的历史。** docs 仍留在 R 的历史里。若 R 已公开且历史含私有内容，泄露已发生，迁移救不回来 —— 只提示 `git filter-repo` 这条路存在，**绝不代执行**。
2. **不搬 docs 的 git 历史到 W。** W 的 `docs/` 从一个干净 commit 起步。要考古去 R 的历史查，成本远低于 subtree split 的复杂度与风险。
3. **不自动 push、不删 R 本地目录、不动 R 里除 `docs/` 和 `AGENTS.md` 外的任何文件。**

### 反向迁移（shell → inline）不提供

无真实动机，YAGNI。

### 失败恢复

前 5 步只新增不删除，故全部可逆；唯一不可逆的删除在第 6 步，且此时 W 已完整（Step 5 已把全部产物 commit 进 W）。

| 步 | 失败点 | 残留状态 | 恢复命令 |
|----|--------|---------|---------|
| 1 | 前置检查未过（工作区不干净 / 无 remote / 有未推送提交） | 未做任何操作，R 未被触碰 | 按提示 `git stash` 或 commit 清理工作区、`git remote add origin <url>`、`git push` 推送未推送提交后重跑 Step 1 |
| 2 | 用户未确认或拒绝 dry-run 计划 | 只生成了计划文本，未创建任何文件 | 修改计划后重新发起 AskUserQuestion 确认；用户放弃则无需清理，直接结束 |
| 3 | 建 W 失败（目标路径已存在 / `git init` 失败） | 可能已 `mkdir` 出空目录，R 未变 | 确认是本次新建的空目录后 `rm -rf "$W"`，或换路径重跑 Step 3；R 侧无需操作 |
| 4 | `git submodule add` 失败（URL 不可达 / 网络中断） | W 已有初始 commit，`.gitmodules` 可能被部分写入，无有效子模块内容 | `git submodule deinit -f "<name>"; rm -rf "$W/.git/modules/<name>"` 清理残留后重跑 Step 4；R 未变 |
| 5 | 迁移拷贝 / 迁入 commit 失败 | R 的 `docs/`、`AGENTS.md` 原封不动（尚未删除、未编辑）；W 可能已 `cp` 部分文件但未 commit | 清理 `$W/docs` 下已复制的半成品文件后重新执行拷贝 + commit；R 侧无需任何操作 |
| 6 | R 内 `git rm` / commit 失败（**唯一不可逆删除点**） | 若尚未 commit：工作区已 `git rm` 但可用 `git checkout -- docs/ AGENTS.md` 完整还原；若已 commit：删除已写入 R 历史 | 未 commit：`git checkout -- docs/ AGENTS.md` 还原后重试；已 commit 需撤销：`git revert <sha>`（不用 `reset --hard`，遵守不改写已提交历史）——此时 W 已持有完整副本，内容零丢失 |
| 6→7 之间 | 用户未 push R 的迁出 commit 就跑了同步（`merge --ff-only` 静默 no-op，退出码仍是 0，不会报错）；或压根跳过同步直接执行 Step 7 | W 记录的子模块指针停留在旧 SHA（跳过同步前的状态，或 Step 4 clone 时的状态），`docs/devdocs` 等本该迁出的内容依然存在 | 先跑「Step 6 与 Step 7 之间」第 3 步的两条断言确认是否真的同步到位；断言失败则确认/补跑 `git -C "$R" push` 后重跑第 2、3 步；若已经带着错误指针跑完 Step 7，按「指针漂移修复」的「未 update」情形处置（不在此重复） |
| 7 | W 写 frontmatter / 指针 commit 失败 | W 已有 `docs/` 内容，但缺 `workspace_mode` 声明，子模块指针未确认一致 | 修正 `AGENTS.md` frontmatter 后重新 `git add AGENTS.md "<name>" && git commit`；不影响 R（R 侧 Step 6 已独立完成） |
