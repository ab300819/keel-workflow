---
name: workspace-topology
description: 维护仓库的工作区拓扑声明——代码与文档同仓（inline）、代码作 git 子模块（shell）、还是代码根在本仓之外只持有引用（linked）。三个入口：inspect 返回稳定的拓扑上下文供其他流程消费，reconcile 交互式维护声明（幂等、可重入、支持增删代码根与新增子模块），migrate 把单仓改造成外壳布局（手动/自动双模式）。独立于 DevDocs，非 DevDocs 项目也可单跑。Triggers on "/workspace-topology", "工作区模式", "外壳仓", "shell 模式", "inline 模式", "linked 模式", "代码根", "代码根在仓外", "引用外部代码", "code_roots", "把项目转成子模块", "文档和代码分仓", "workspace mode", "submodule 布局". NOT for 记忆文件维护（用 agent-memory）、代码盘点（用 ms-codebase-insight）。
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion
metadata:
  spec_version: workspace-topology.v2
  interaction: multi-turn
user-invocable: true
---

# Workspace Topology

**管仓库的形状：代码在哪、文档在哪。不管代码内容，不管文档内容。**

三种形状：

| 形状 | 代码 | 文档 | 代码归本仓所有 |
|---|---|---|---|
| `inline`（缺省） | 仓库根 | `<仓库根>/docs/` | 是 |
| `shell` | 各 git 子模块下 | `<仓库根>/docs/` | 是 |
| `linked` | 本机目录引用，仓内仓外皆可 | `<仓库根>/docs/` | **否** |

**文档根三种形状下都是 `docs/`**，这是固定不变量，不设配置字段。变的只有代码在哪、归谁。

`shell` 服务两类零污染场景：维护开源项目（自己的文档不能进上游仓）、自有项目待公开。
`linked` 服务「代码根不属于本仓」的场景：多仓联调、按需组合的临时工作区、只想让文档仓记住相关代码在哪。用什么手段组织（worktree / clone / symlink / 就是个目录）由用户决定，本 skill **只认不造**。

## 三个入口

| 入口 | 做什么 | 写文件吗 |
|---|---|---|
| `inspect` | 返回拓扑上下文，供其他流程消费 | **仅在声明缺失且判不出时**：问一次并落声明；已有声明时不写 |
| `reconcile` | 交互式维护声明（幂等，可重入） | 是 |
| `migrate --to shell --mode manual\|auto` | 单仓 → 外壳布局的仓库改造 | 是 |

无参数调用等同 `reconcile`。

## 无声明时：问，不猜

有 `workspace:` 声明就直接用。**没有声明就问用户**，答案写进 `AGENTS.md`，此后不再问。

```text
1. 问 mode：inline / shell / linked 三选一
2. 按 mode 问代码根：
     inline → 不用问，代码根就是仓库根
     shell  → 列出 .gitmodules 的条目，多选哪些是代码根
     linked → 问路径，可多个（相对 / ~/ / 绝对都行）
3. 写进 AGENTS.md 的 workspace: 块
```

⛔ **不做自动判定。** 仓库形状是产品决策，不是能从文件布局推出来的事实 —— 尤其 `linked` 的代码根可以在仓外，任何仓内扫描都发现不了。

**扫描只用来给选项排预设，猜错无所谓**：

| 扫到 | 预设 |
|---|---|
| `.gitmodules` 有条目 | `shell` 排前面，子模块列为代码根候选 |
| 仓根有自己的文件 | `inline` 排前面 |
| 都没有 | 三个选项平铺 |

判断「仓根有自己的文件」要用 `git ls-files -s` 并排掉 **mode 为 160000** 的条目 —— 那是子模块记录，不是本仓的文件。不排掉的话每个外壳仓都会被预设成 `inline`。

⚠️ 子模块也可能是 vendor / 素材，所以 `shell` 下**哪些**子模块算代码根必须问，不能把 `.gitmodules` 的条目照单全收。

## inspect

读声明并返回 `yaml-summary-v1`，拓扑上下文落 `summary.details`。**已有声明时纯只读**；没有声明时按上一节问一次并落声明，之后就一直是只读了。

```yaml
schema: workspace-context.v2
mode: inline | shell | linked
workspace_root: /abs/path
docs_dir: docs
code_roots:
  - name: api
    path: /abs/resolved/path      # 解析后的绝对路径，消费方唯一要用的
    declared_path: ../pool/api    # 声明原文，供报告与诊断
missing_code_roots:               # 声明了但解析不到实体
  - name: web
    declared_path: ../pool/web
```

三种 mode 下 `code_roots` 元素形状**完全一致**——**调用方不分支**，`inline` 也是一个代码根（单项，`path` = 仓根绝对路径）。

`inline` 时的单项取 `{name: ".", path: <仓根绝对路径>, declared_path: "."}` —— `name` 与 `declared_path` 保留 `.` 作为哨兵，消费方可据此判别，不必读 `mode`。

- `path` 给解析后的绝对路径，消费方零解析；`declared_path` 只用于给人看
- **解析不到的代码根不进 `code_roots`**，进 `missing_code_roots`。消费方拿到的每一项都能直接 `cd`，不用先探活
- **`missing_code_roots` 非空不阻塞流程**，⚠️ 报告即可。真正的失败留到消费方确实要用它的时候
- 探测到的 `kind` / `branch` / `upstream` **不进契约**，只在 `reconcile` 与报告里展示给人看——消费方只需要 `cd` 进去干活

### 消费方怎么拿到它

⛔ **不要求消费方自己调本 skill**。多数原子 skill 的 `allowed-tools` 没有 `Task`，无法派发子 Agent；让它们自己读声明文件又会把实现细节泄漏出去。

走 [constraints.md §3](../_shared/constraints.md) 的最小握手协议：

- **编排层**（`ms-pipeline` / `ms-feature` / `ms-bugfix` / `ms-dev-workflow`）在流程开头调一次 `inspect`，把 `workspace_context` 随握手的 `inputs` 下传
- **原子 skill** 从 `inputs.workspace_context` 读，不需要 `Task`
- **单跑**（用户直接调某个原子 skill，无编排层）：无 `workspace_context` → 按 `inline` 缺省 + ℹ️ 提示「`shell` / `linked` 项目请经编排层调用」

消费方依赖的是**入参形状**，不是声明文件、不是 `.gitmodules`。

## reconcile

交互式维护声明。**幂等：状态一致则 no-op，不产生空提交。**

| 动作 | 语义 |
|---|---|
| 重新确认 | 按「## 无声明时：问，不猜」问一遍 mode 与代码根，覆盖已有声明。⛔ 不自动判定 |
| 调整 `code_roots` | 纯声明变更 |
| 已存在子模块加入管理范围 | 纯声明变更 |
| 新增子模块 | 用户给 URL 与路径 → `git submodule add` → 追加 `code_roots` |
| 退出 `code_roots` | **仅退声明**，表示「不再作为工作代码根」。⛔ 不动 `.gitmodules`、不动本地目录 |
| legacy 字段迁移 | 见下方「元数据」，一次性 |
| 中断续做 | 从**实际 git 状态**继续，不依赖「执行到第几步」的记录 |
| `linked` 路径维护 | 问用户要路径（可多个）。增删是**纯声明变更**，⛔ 不建 worktree、不 clone、不动被引用的目录 |

**两个必须区分的界限**：

1. **改声明 ≠ 改真实拓扑**。`mode` 字段可以随便改，但 `inline → shell` 的真实拓扑变更是仓库改造，走 `migrate`。
2. **退出 `code_roots` ≠ 删子模块**。后者会改 `.gitmodules`、gitlink 和本地目录，是破坏性操作，本 skill **不做**，交用户自行执行。

**写入后自校验**：立即重跑校验全表，任一 ⛔ → 回滚本次写入并报告。⛔ 不得以「命令退出码为 0」代表完成。

**`shell → inline`**：只给手动规划，不承诺自动化——多代码根时「合并进哪个仓 / 是否保留外壳历史 / 多远端怎么处理」没有安全默认答案。

## migrate

**`migrate` 只在 `inline` ↔ `shell` 之间发生，双向皆可。`linked` 任何方向都不参与**——判据是所有权，完整理由见 [references/migration.md](references/migration.md)。需要在 `linked` 与其它形态间转换时，由用户自行完成物理改造，再跑 `reconcile` 重新声明。

要点：

- **仅由用户显式意图触发**，本 skill 永不主动提议——那是产品决策，不是规范差距
- 两个模式的分界在**谁把代码仓挪进根目录**：手动模式下用户处理这个跨工作区边界的动作（父目录写权限、cwd 迁移），其余仍由本 skill 完成
- 顺序是硬约束：建壳 → 整仓 `mv` 进去 → `submodule add` 登记 → 复制文档 → **校验复制到位** → 才删原件 → 写声明 → 推送收尾
- ⛔ 不做 rebase / filter / squash / force-push；⛔ 不静默 push；⛔ 不自动删除原 checkout；⛔ 不把代码仓自有文档（API 文档、README 资料）一并迁走

## 元数据

声明在项目根 `AGENTS.md` frontmatter 的**独立 `workspace:` 块**：

```yaml
---
workspace:
  mode: shell
  code_roots: [web, api]      # mode=shell / mode=linked 时必填。shell 下元素为 .gitmodules 的 submodule name；linked 下须给 path，见下方 linked 示例
devdocs:                      # DevDocs 项目才有；非 DevDocs 项目只有 workspace: 块
---
```

`linked` 形态与对象项写法：

```yaml
---
workspace:
  mode: linked
  code_roots:
    - name: api
      path: ../pool/api          # linked 下必填
      upstream: ssh://...        # 可选，重建线索
      branch: feature-x          # 可选，重建线索
---
```

`code_roots` 同时接受字符串项与对象项，字符串 `foo` 等价于 `{name: foo}`。`shell` 下 name 足够（路径真源是 `.gitmodules`），**现有声明零改动**；`linked` 下必须给 `path`。

**为什么独立成块**：这是仓库级事实，不是 DevDocs 事实。挂在 `devdocs:` 下会让「声明一个仓库设定」必须经过 DevDocs 流程。

**路径真源是 `.gitmodules`**（仅 `shell`），`code_roots` 只记 submodule name，运行时经 `git config -f .gitmodules submodule.<name>.path` 解析。子模块换路径只改 `.gitmodules`，声明不用跟。`linked` 下声明本身即真源。

### 所有权

| 谁 | 拥有什么 |
|---|---|
| `workspace-topology` | `workspace:` 块 |
| `agent-memory` | 正文 + `devdocs:` 块；⛔ 对 `workspace:` 块**原样保留**，不覆写不删除 |

### legacy 兼容

旧版本把字段放在 `devdocs.workspace_mode` / `devdocs.code_roots`。

| 情形 | 行为 |
|---|---|
| 只有 `workspace:` 块 | 正常读取 |
| 只有 legacy 字段 | **只读兼容**；`reconcile` 时迁移到 `workspace:` 并删除旧字段 |
| 两处并存且**一致** | 迁移并删除旧字段 |
| 两处并存且**冲突** | ⛔ 阻塞，由用户裁决以哪处为准 |
| 字段跨两处拆分（`mode` 在新、`code_roots` 在旧） | ⛔ 阻塞——拼接两处声明会让「以哪处为准」失去单一答案 |
| 都没有 | `inline`，零影响 |

`code_roots` 比较按**集合**语义，顺序无意义。

## 校验（fail-closed）

全表按 mode 分家，权威在 [references/protocol.md §3](references/protocol.md)。三条最容易踩的：

| 情形 | 行为 |
|---|---|
| 声明的代码根解析不到 | ⚠️ 归入 `missing_code_roots`，不阻塞流程 |
| 裸 gitlink（跟踪 mode 160000 但 `.gitmodules` 无条目） | ⛔ 全 mode——客观损坏，clone 下来是空目录且无法恢复 |
| 解析后路径逃逸出已授权工作范围 | ⛔ 全 mode——路径声明不是写权限授权 |

## 仓根残留文件

`shell` 下，仓库根不在 `docs/`、不属任何 `code_root` 的**已跟踪文件** → ℹ️ 列清单交用户判断。

⛔ **不猜哪个算源码**。上游仓目录约定各异，静态白名单会误伤。列出来，让人看。

## 提交

**谁干活谁提交**：本 skill 提交自己产生的东西（`.gitmodules`、`workspace:` 块、迁移中的文件搬运），不替别的 skill 提交，也不被别的 skill 用来代提交。

跨仓提交协议（`shell` 下 Commit 1 展开为 N+1 仓）见 [references/protocol.md](references/protocol.md)，由干活的 skill 按条文执行。

## 详细协议

- 校验全表、零污染写入范围、N+1 仓提交协议、gitlink 排除：[references/protocol.md](references/protocol.md)
- 迁移双模式、探测步骤、detached HEAD 处置、指针漂移修复：[references/migration.md](references/migration.md)
