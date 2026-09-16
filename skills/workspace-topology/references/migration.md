# Workspace Shell 操作手册

## 目录

- 定位
- 确认拓扑
- detached HEAD 处置
- 指针漂移修复
- inline → shell 迁移

## 定位

本文是 工作区拓扑的**操作手册**，回答"具体怎么操作"；协议正文（模式枚举、`code_roots` 真源、fail-closed 校验表、归属判定、零污染范围、N+1 仓提交协议、Recovery 格式等"规则是什么"）的唯一权威源是 [protocol.md](protocol.md)，本文不重复其规则表格，引用规则时以指针链接代替。

> **本手册仅覆盖 `inline` ↔ `shell`。** `linked` 任何方向都不参与 `migrate`——判据是所有权：`inline` 与 `shell` 同在「本仓拥有代码」的前提内，迁移只改挂法不改归属；`linked` 跨的是所有权边界。
>
> | 方向 | 实际要做的事 | 为什么不做 |
> |---|---|---|
> | `→ linked` | clone / 建 worktree / 移动目录 / 决定放哪 | 这是「造」，属独立的 provisioning 决策 |
> | `linked →` | 吞并一个不属于本仓的仓库 | 本 skill 无权处置它不拥有的东西 |
>
> 需要转换时由用户自行完成物理改造，再跑 `reconcile` 重新声明。

## 确认拓扑

**执行时机**：`reconcile`（用户直接跑，或由 `pipeline init` / `retrofit` 委托），以及 `inspect` 遇到无声明时。**已有声明的场景直接读声明，不再问。**

⛔ **不做自动判定** —— 仓库形状是产品决策，不是能从文件布局推出来的事实。扫描只用于给选项排预设（见 [../SKILL.md § 无声明时：问，不猜](../SKILL.md)）。

**步骤**：

1. AskUserQuestion 问 `mode`：`inline` / `shell` / `linked` 三选一。
   - 扫到 `.gitmodules` 有条目 → `shell` 排前面
   - 仓根有自己的文件（`git ls-files -s` 排掉 mode 为 160000 的子模块记录后仍有剩余，且不只是 `docs/` 与 `README*` / `AGENTS.md` / `CLAUDE.md` / `LICENSE*` / `CONTRIBUTING*` / `CHANGELOG*` / `.gitignore` / `.gitmodules` / `.gitattributes` 这类元文件）→ `inline` 排前面
   - 都没扫到 → 三个平铺
   - **预设猜错无所谓，用户会选**

2. 按 `mode` 问代码根：

   **`inline`** —— 不用问，代码根就是仓库根。

   **`shell`** —— 先列出全部 submodule name：
   `git config -f .gitmodules --name-only --get-regexp '^submodule\..*\.path$' | sed 's/^submodule\.//; s/\.path$//'`
   再 AskUserQuestion **多选**：哪些子模块是代码根？
   - 选项逐个列出 `<name>（路径：<path>）`
   - 提示语必须说明「子模块也可能是素材 / vendor，不都算代码根」

   **`linked`** —— AskUserQuestion 问路径，可多个，相对 / `~/` / 绝对都接受。每个路径记 `name` + `path`。
   - ⛔ 不建 worktree、不 clone、不动被引用的目录——只登记声明
   - 路径解析不到目录 → 当场告知并让用户改，不静默接受

3. 写入仓库根 `AGENTS.md` frontmatter 的**独立 `workspace:` 块**：**仅** `mode` + `code_roots` 两个字段。

   ```yaml
   ---
   workspace:
     mode: shell
     code_roots: [chiaki-ng]
   ---
   ```

   `linked` 形状（元素为对象，`path` 必填）：

   ```yaml
   ---
   workspace:
     mode: linked
     code_roots:
       - name: api
         path: ../pool/api
   ---
   ```

   **`devdocs:` 块不碰**——三层版本号、`initialized_at` 都不在本 skill 的写入范围内，它们归 `agent-memory` 与 layout 元数据机制。⛔ 不代写、不伪造：三层版本号没有可靠来源，伪造比缺失更糟。

   `AGENTS.md` 已有 frontmatter → 在其中新增/更新 `workspace:` 块，其余 key 原样保留（含键序）。无 frontmatter（首行是 HTML 注释等正文）→ 在**文件最前面**插入，原有内容整体下移，不改写原内容一个字符。`AGENTS.md` 不存在 → 只创建含该块的 frontmatter，不生成正文（正文归 `agent-memory`）。

   **非 DevDocs 项目只有 `workspace:` 块，没有 `devdocs:` 块**——这是合法的正常状态，消费方不得当异常处理。

4. 写入后立即跑一次校验（`workspace/fail-closed` 全表，见 [protocol.md](protocol.md#3-校验规则fail-closed)），任一 ⛔ 则**回滚本次写入**并报告。

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

### 触发

**仅由用户显式意图触发**（如「把这个项目转成外壳模式」）。本 skill **永不主动提议**——那是产品决策，不是规范差距。

### 两个模式

分界在**谁把代码仓挪进根目录**这一个动作。它需要父目录写权限并会移动当前 cwd，Agent 未必能安全跨越这个边界。

| 步骤 | 手动模式 | 自动模式 |
|---|---|---|
| 状态盘点 | skill | skill |
| dry-run 计划 + 确认 | skill | skill |
| 建根目录、把代码仓 `mv` 进去 | **用户** | **skill** |
| `git init` 外壳仓 + 首次 commit | skill | skill |
| `submodule add` 登记 | skill | skill |
| 复制 DevDocs 产物到外壳仓 | skill | skill |
| **校验复制到位** | skill | skill |
| 删代码仓里的原件 | skill | skill |
| 写 `workspace:` 声明 | skill | skill |
| 子模块切具名分支 | skill | skill |
| 推送收尾 | skill（问过用户） | skill（问过用户） |

**手动模式不是让用户手工做全部事情**，只是让用户处理那一个跨工作区边界的动作。

**自动模式的前置**（全部满足才启动）：父目录在当前写入范围内 · 目标路径不存在或为空 · 完整 dry-run 已确认。

### 顺序是硬约束

```
建外壳仓 → 整仓 mv 进去 → submodule add 登记 → 复制文档到外壳仓
→ 逐项校验复制到位 → 才删代码仓里的原件 → 写声明 → 推送收尾
```

⛔ 校验未通过不得执行删除。

**为什么不需要备份**：整仓 `mv` 不销毁任何东西（未推送提交、staged、untracked 全部随目录带走）；`submodule add` 在目录已是有效 git 仓时是**登记**不是 clone，不碰工作区。全流程唯一的删除动作在复制校验**之后**，删的又是 git 已跟踪文件（历史里还在）。

> ℹ️ 跨文件系统 `mv` 非原子操作。目标目录与源仓不在同一文件系统时改用 copy → 校验 → 删源。

### 状态盘点取代前置门

旧版本有一道前置门：工作区不干净 ⛔、有未推送提交 ⛔。**这道门会把唯一真实场景挡在门外**——clone 开源项目并用 DevDocs 开发过，状态必然是二者之一。

```bash
git -C <R> status --porcelain              # DevDocs 产物在工作区？
git -C <R> log --oneline @{u}..HEAD        # 有未推送提交？
git -C <R> remote -v                       # remote 是上游还是自己的 fork？
```

盘点结果进 dry-run 计划，不阻塞。**但以下默认阻塞**（它们会在移动之后才失败，恢复变成手工仓库手术）：

- 未解决的 unmerged index
- 进行中的 merge / rebase / cherry-pick
- linked worktree / separate gitdir
- 目标路径已存在且非空

### 挂子模块

⛔ **不要用 `git submodule add <remote URL>` 直接挂一个还没移进来的仓** —— 那会从远端重新 clone，本地未推送的工作全丢。
⛔ **也不要传本地路径**（`./myproj`）—— 现代 git 默认禁 file 传输（`fatal: transport 'file' not allowed`，CVE-2022-39253 后），且那样会把本地路径写进 `.gitmodules`。

**先物理移进来，再传远程 URL 登记**：

```bash
mkdir W && cd W && git init && git commit --allow-empty -m "chore: init shell workspace"
mv ../myproj ./myproj
git submodule add https://github.com/you/myproj.git myproj
# → "Adding existing repo at 'myproj' to the index"，不 clone
git add .gitmodules myproj && git commit -m "chore: 挂载代码仓为子模块"
```

目录已是有效 git 仓时，`submodule add` 直接登记其当前 `HEAD`，`.gitmodules` 记的就是传入的远程 URL。实测（2026-08-24）：未推送提交、staged 文件、untracked 文件全部保留，子模块工作区状态原样。

### 迁移范围：只搬 DevDocs 产物，不搬整个 docs/

`docs/` 里未必只有 DevDocs 产物 —— 用户面文档、API 文档、架构图属于代码仓，搬走反而是错的。

- **无条件迁移**：`docs/devdocs/`、`docs/prd/`、`docs/codebase-insight.md`
- **留在代码仓**：`docs/` 下其余内容
- **逐项确认**：dry-run 计划里列出 `docs/` 下所有未分类条目，AskUserQuestion 让用户决定去留

删除步骤只删已确认迁走的路径，⛔ 不是 `git rm -r docs/`。

`AGENTS.md` 的 `workspace:` / `devdocs:` frontmatter 段整体剪切到外壳仓；代码仓侧的删除同样放在校验之后。

### 推送收尾

外壳仓记录的是代码仓当前所在的 commit。有提交没推送，别人 clone 外壳仓时 git 到远程找不到该 commit，直接报错退出：

```
fatal: remote error: upload-pack: not our ref <sha>
```

迁移末尾检查 `git -C <path> log @{u}..HEAD`，非空就问用户是否推送并推掉。clone 的开源仓没有推送权时先 fork 再推。

⛔ **不静默 push** —— 必须问过用户。

### 明确不做

| 不做 | 理由 |
|---|---|
| rebase / filter / squash / force-push 整理代码仓历史 | 对已公开的开源仓风险过高，且**不是布局迁移的必要步骤**。想整理让用户自己跑 |
| 自动删除原 checkout | 破坏性动作交用户 |
| 把 docs 的 git 历史搬到外壳仓 | 外壳仓的 `docs/` 从一个干净 commit 起步。要考古去代码仓历史查，成本远低于 subtree split 的复杂度与风险 |
| 反向迁移（`shell → inline`）自动化 | 多代码根时「合并进哪个仓 / 是否保留外壳历史 / 多远端怎么处理」没有安全默认答案。只给手动规划 |
| 保持原最外层路径不变的「原地换壳」 | 须先把当前 git 仓移成子目录再在原路径 init，会移动当前 cwd 且常需 workspace 根之外的父目录写权限 |
| 在 detached HEAD 上提交 | 见上方「detached HEAD 处置」 |
| 把已有脏改动混入迁移 commit | 迁移只提交迁移自身产生的变更 |

### 失败恢复

⛔ 不用 `reset --hard` 处理任何中间状态。

**从实际 git 状态恢复，不依赖「执行到第几步」的记录**——重跑 `migrate` 或 `reconcile`，让它重新盘点当前真实状态后继续。

| 失败点 | 残留状态 | 恢复 |
|---|---|---|
| 盘点 / dry-run 未确认 | 未触碰任何文件 | 直接结束，无需清理 |
| 建外壳仓失败 | 可能有一个新建的空目录，代码仓未变 | 确认是本次新建后 `rm -rf <W>`，或换路径重跑 |
| `mv` 中断（跨文件系统） | 源与目标各有部分内容 | ⛔ 手工核对，不自动处理。这是改用 copy → 校验 → 删源的理由 |
| `submodule add` 失败 | 外壳仓有初始 commit，`.gitmodules` 可能部分写入；代码仓目录已在 W 下且内容完整 | 清 `.gitmodules` 残留条目后重跑登记；代码仓内容未受影响 |
| 复制文档失败 | 代码仓原件**原封不动**（尚未删除）；外壳仓可能有半成品 | 清理外壳仓 `docs/` 下半成品后重跑复制 |
| 校验未通过 | 同上，原件仍在 | ⛔ 不得继续到删除步骤。修正后重跑复制 + 校验 |
| 删除原件失败 | 未 commit：`git checkout -- <路径>` 还原；已 commit：`git revert <sha>` | 此时外壳仓已持有完整副本，内容零丢失 |
| 写声明失败 | 外壳仓有文档但缺 `workspace:` 块 | 跑 `reconcile` 补声明 |
| 推送失败 | 一切就位，仅子模块 commit 未上远程 | 处理远程权限后 `git -C <path> push`；不影响本机使用 |

### 手动模式的恢复胶囊

手动模式在「用户去建目录」处暂停。skill 输出一份**恢复胶囊**（落在两个仓之外），记录：

源路径 realpath · 分支 · `HEAD` · remote 与其 ref OID · 目标结构 · 待迁移文档清单 · index 指纹 · 工作树清单 · 递归子模块状态

**恢复时必须重新盘点并比对**。任一项漂移（用户期间又提交了、改了工作区、换了 remote、移动了路径）→ 旧胶囊失效，重新生成计划并让用户确认受影响的步骤。⛔ 不得拿失效胶囊继续执行——那会处理用户从未确认过的状态。
