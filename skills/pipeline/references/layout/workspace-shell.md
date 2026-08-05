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
5. 写入外壳仓根 `AGENTS.md` 的 `devdocs:` frontmatter：`workspace_mode: shell` + `code_roots: [<选中的 name>]`
6. 写入后立即跑一次校验（`workspace/fail-closed` 全表），任一 ⛔ 则回滚本次写入并报告

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
