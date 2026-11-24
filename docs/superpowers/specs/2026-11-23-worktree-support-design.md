# 工作区 worktree 支持（设计稿）

> 状态：已实施；整体定位已被 [2026-11-24 并行工作区设计稿](2026-11-24-worktree-parallel-design.md) 取代。方案由用户 2026-11-23 选定（「按你建议来」= S3 + P2），取代搁置的 [linked-worktree 设计稿](2026-11-19-linked-worktree-design.md)（该稿只在分支 `feat/linked-worktree` 上，未合入）。

## 1. 为什么做

用户在 EMSPR 用 1 个 PM 会话 + 9 个执行 agent 并行开发，每个 agent 在自己的 worktree 和分支上干活（见 [多 agent 并行设计稿](2026-11-20-keel-parallel-agents-design.md)）。keel 目前对 worktree 只有一句「用户决定，只认不造」，有两处缺口：

1. **台账会分叉**。keel 用 `git rev-parse --show-toplevel` 找项目根，在 worktree 里找到的是 worktree 自己，所以每个 worktree 写的是自己分支上那份台账。实测（2026-11-23，临时仓）：主工作树和 worktree 各改同一张卡，合并时 `state/tasks/T-1.json` 和 04 的台账区都冲突。
2. **worktree 目录没约定**。放在项目里却没被 git 忽略时，`git add -A` 会把它记成一个 gitlink；事后能被「裸 gitlink」检查拦下，事前没有提醒。

## 2. 方案（用户已选）

| 问题 | 可选 | 选定 |
|---|---|---|
| worktree 里写哪份台账 | S1 维持现状 / S2 都写主工作树那份 / **S3 worktree 里拒绝写** | S3：改动小，把「只有 PM 写台账」从约定变成工具强制 |
| worktree 放哪、谁建 | P1 不管 / **P2 约定位置，只识别** / P3 keel 提供建删入口 / P4 派单时自动建 | P2：不新增「造」的职责，P3、P4 都和「只认不造」及并行设计稿的「keel 只记账」冲突 |

## 3. 设计

### 3.1 S3：worktree 里台账只读

- **判定**：`git rev-parse --git-dir` 与 `--git-common-dir` 解析后不同 → 当前在 linked worktree 里。子模块两者相同，不受影响。
- **位置**：`Project.lock()` 的排他分支。所有写台账的命令（`init`、`task` / `backlog` 的写命令、`render`、`migrate --apply`、`state accept`、`gate set`）都经过它，一处覆盖全部；只读检查用共享锁，不受影响。
- **行为**：拒绝，退出码 3（无法继续），文件不动。提示：「这里是 git worktree，台账只在主工作树写：<主工作树路径>。多 agent 并行时交给负责台账的会话；独自开发时到主工作树执行同一条命令。」主仓是 bare 时没有主工作树，提示改为说明这一点。
- **不变的**：`task list` / `task get` / `backlog list` 等读命令照常可用，读到的是该分支上的那份（可能比主工作树旧）；`check`、pre-commit、会话启动写垫片照常。
- **规则登记**：`skills/shared/constraints.md` § keel 工具 新增 `keel/worktree` 一条，各 skill 不复述。

### 3.2 P2：`.worktree/` 约定与检查

- **约定**：worktree 放在 `<项目根>/.worktree/<应用>-<分支>`，分支名里的 `/` 换成 `-`；`inline` 项目的「应用」取仓库目录名。由用户、PM 或用户自己的脚本建，keel 不建不删。`.worktree/` 必须写进项目根的 `.gitignore`。
- **检查**（`protocol.md` §3 新增一行，全 mode）：`.worktree/` 存在但没被 git 忽略 → ⚠️，提示加进 `.gitignore`。用 ⚠️ 不用 ⛔：此时还没损坏，真提交进去后已有的「裸 gitlink」⛔ 会兜底。
- **报告**：`inspect` 在给人看的报告里列出 `.worktree/` 下各目录及其当前分支（ℹ️），**不进 `workspace-context.v2` 契约**，下游不改。

## 4. 后果（用户须知）

- worktree 里的 agent 改不了台账：任务状态、领取、完成都得由主工作树里的会话写。独自用 worktree 开发的人也一样，要回主工作树执行。
- worktree 里读到的台账是开分支时的版本，要看最新状态去主工作树看或问 PM。
- 主仓是 bare 的项目（所有工作树都是 linked），台账无法写入。

## 5. 暂不做

| 需求 | 原因 |
|---|---|
| worktree 里的写自动转到主工作树（S2） | 改动 keel 找根逻辑，门禁、hook、提交都受影响；S3 先用起来再说 |
| keel 建删 worktree（P3 / P4） | 推翻「只认不造」；第二个项目也要再议 |
| `inspect` 契约里带 worktree 清单 | 没有消费方 |

## 6. 验收

- 在 linked worktree 里执行写命令（`task add`、`task set`、`init`）退出码 3，状态文件不变；主工作树里照常写入。
- worktree 里 `task list` / `task get` 正常。
- `bash scripts/check-python.sh` 全过；版本升到 3.1.0。
