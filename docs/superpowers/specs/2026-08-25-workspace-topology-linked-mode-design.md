# workspace-topology：探测重写 + 第三种拓扑 `linked`

## 0. 问题（用户原话）

1. 「『都没有』时不能粗暴的判断为 inline，你可以先思考判断，如果拿不准问用户」
2. 「频繁出现『按规则"都没有 → 判 inline"』，这个有点粗暴了，而且在我已经做成 shell 结构的事实下」
3. 「维护微服务场景，inline 和 shell 都不合适」
4. 「微服务场景下使用子模块太重，并行时会有多分代码仓库副本」
5. 「你不要假定为 mic，我只是举例场景，skill 不要与具体场景案例关联」
6. 「我不明白引用路径为什么不能是绝对而是相对路径，有些轻量场景路径反而比 worktree 轻量」

## 1. 两个缺陷的真因

### 1.1 「频繁判 inline」不是判据不准，是判据算错

`git ls-files` 会把子模块的 **gitlink 条目当普通文件列出**。一个标准外壳仓的跟踪清单形如：

```
.gitignore  .gitmodules  AGENTS.md  CLAUDE.md   ← 元文件
web  api  worker  gateway  ...                  ← gitlink，mode 160000
```

把后半截算成「本仓自有代码」，任何外壳仓都会被判成 `inline`。

**修正**：判据取 `git ls-files -s` 中 **mode ≠ 160000** 的条目。

### 1.2 `inline` 不该坐在兜底位置

兜底默认必然在「有事实但没声明」时给出错误答案。

**但正确的替代不是「换一套更准的自动判据」，是不自动判定** —— 见 §3。

## 2. 拓扑模型：三种

| mode | 代码根在哪 | 归本仓所有吗 |
|---|---|---|
| `inline` | 仓库根 | 是 |
| `shell` | 本仓的 git 子模块 | 是（gitlink 锁 commit） |
| `linked`（新） | **本机的目录引用**，仓内仓外皆可 | **否**，本仓只持有引用 |

`inline` / `shell` 的共同前提是「本仓拥有代码」。`linked` 打破的正是这一条 —— 这是它独立成第三种、而非给 `shell` 加 flag 的原因：所有权变了，校验规则跟着变。

**与具体场景无关**。多仓联调、按需组合的临时工作区、只想让文档仓记住相关代码在哪，都落在这一种。

**文档根仍恒为 `<仓库根>/docs/`**，三种拓扑通用，不设字段。

### 2.0 迁移边界：`linked` 不参与

`migrate` 只在 **`inline` ↔ `shell`** 之间发生，双向皆可（`shell → inline` 仍只给手动规划，不承诺自动化）。

**`linked` 任何方向都不参与迁移。**

判据就是上表最后一列 —— `inline` 与 `shell` 同在「本仓拥有代码」的前提内，迁移只改挂法，不改归属；而 `linked` 跨的是所有权边界：

| 方向 | 实际要做的事 | 为什么不做 |
|---|---|---|
| → `linked` | 把本仓资产变成外部引用：clone / 建 worktree / 移动目录 / 决定放哪 | 这是「造」，属独立的 provisioning 决策（§8） |
| `linked` → | 把外部引用变成本仓资产：吞并一个不属于本仓的仓库 | 本 skill 无权处置它不拥有的东西 |

要在 `linked` 与其它形态间转换，由用户自行完成物理改造，再跑 `reconcile` 重新声明。

### 2.1 `path` 语义

相对路径（相对仓根解析）、`~/` 展开、**绝对路径**，三种都合法。

唯一拒绝的是**解析不出目录**的路径 —— 那报缺失，不是报格式错。

绝对路径的代价如实记录、不禁止：声明文件进版本控制后，在另一台机器上必然失效。`linked` 工作区本来就不可跨机复现（git 不为目录引用提供任何重建能力），路径形式不改变这一点。

### 2.1.1 路径声明不是写权限授权

`AGENTS.md` 是版本控制里的普通文件，**可能来自不可信来源**（clone 别人的仓、合并他人的分支）。而 `code_roots` 现在同时允许绝对路径、`..` 和符号链接，下游流程又会 `cd` 进去改文件。

⛔ **解析出的路径不得自动扩大 agent 的可写范围。**

| 规则 | 说明 |
|---|---|
| 解析后的路径逃逸出用户已授权的工作范围 | ⛔ 拒绝并报告，不静默接受 |
| 符号链接 | 按**解析后的真实目标**判定，不按链接自身位置 |
| 绝对路径 | 是本机绑定的事实，报告时如实标注，⛔ 不得呈现为「可移植的仓库事实」 |

这条独立于「path 允许哪些形式」：允许写下某个路径，不等于允许往那里写文件。

### 2.2 skill 对每个引用只做一件事

解析它实际是什么，如实报告，**不评判**：

| 探测到 | 报告 |
|---|---|
| git worktree（`git-dir ≠ git-common-dir`） | 上游 URL、当前分支、该仓全部并行工作树 |
| 普通 git 仓 | 上游 URL、当前分支 |
| symlink | 解析目标后按上面判定，标注是链接 |
| 非 git 的普通目录 | 就报是个目录，不猜 |
| 路径不存在 | 报缺失 + 声明里的重建线索（若有） |

用什么手段组织代码根（worktree / clone / symlink / 就是个目录）由用户按有没有并行需求决定，**skill 不替他选，也不替他造**。

## 3. 无声明时：问，不猜

有 `workspace:` 声明就直接用。**没有声明就问用户**，答案写进 `AGENTS.md`，此后不再问。

```text
1. 问 mode：inline / shell / linked 三选一
2. 按 mode 问代码根：
     inline → 不用问，代码根就是仓库根
     shell  → 列出 .gitmodules 的条目，多选哪些是代码根
     linked → 问路径，可多个（相对 / ~/ / 绝对都行）
3. 写进 AGENTS.md 的 workspace: 块
```

### 3.1 为什么不做自动判定

**仓库形状是产品决策，不是能从文件布局推出来的事实。**

本方案的前几稿设计过一套三信号自动判据（本仓自有代码 / 挂着子模块 / 仓内有被忽略的嵌套 git 仓），恰好命中一个才给结论，信号冲突或零信号才问。它被推翻，原因有二：

**一、`linked` 在结构上就探测不到。** `linked` 的定义是「代码根不归本仓所有，仓内仓外皆可」，而识别它的信号只能扫仓内被 `.gitignore` 忽略的目录 —— **仓外的路径 `.gitignore` 管不着**。217 仓调查里该信号零命中（§3.2），当时被解释为「新形态还没人这么组织」，真实原因是它覆盖不到 `linked` 的主要场景。于是真实 `linked` 项目只能走「零信号 → 判不出 → 问」这条路，而整套 follow-through 都是按「判定为某种拓扑之后」写的，那条路是死的。

**二、把「问」当兜底会持续渗漏。** 主路径是自动判定时，每加一种拓扑就要给它配一条探测信号、一套 follow-through、一组信号冲突处置。三轮独立审查每轮都在这套机器里发现新的 Critical，而每次修复只补「正在看的那一层」：改了判定表漏执行程序，改了执行程序漏 follow-through，改了 follow-through 漏 ask 分支。

**主次调回来即可**：问是主路径，扫描只用于给选项排预设。

| 扫到 | 预设 |
|---|---|
| `.gitmodules` 有条目 | `shell` 排前面，子模块列为代码根候选 |
| 仓根有自己的文件 | `inline` 排前面 |
| 都没有 | 三个选项平铺 |

**预设猜错无所谓，用户会选。** 这把 §1.1 的 gitlink 缺陷从「判定正确性」降级为「预设准确性」—— 算错只是把外壳仓的默认选项设成 `inline`，用户一眼能改回来，不再是静默给错答案。

判断「仓根有自己的文件」仍须用 `git ls-files -s` 排掉 mode 为 160000 的条目（§1.1）。

⚠️ 子模块也可能是 vendor / 素材，所以 `shell` 下**哪些**子模块算代码根必须问，不能把 `.gitmodules` 的条目照单全收。

### 3.2 gitlink 缺陷的现实规模（n=217）

在 217 个真实仓库上验证 §1.1 的判据修正（排除 mode 160000 前后对比）：

| 类别 | 数量 | 说明 |
|---|---|---|
| 仓根有自有文件、无子模块 | 201 | 预设 `inline`，正确 |
| 无自有文件、有子模块 | 4 | 修正前**全部被误判成 `inline`**；修正后预设 `shell`，逐个人工核对正确 |
| 既有自有文件又有子模块 | 8 | 无法自动区分，见下 |
| 两者皆无 | 4 | 纯文档仓 1、空仓 2、单文件仓 1 |

**那 8 个「既有自有文件又有子模块」的仓，正是不能自动判的实证**。逐个查根目录的自有文件后，它们分成两类：

| 类别 | 自有文件数 | 实际是什么 |
|---|---|---|
| 自有代码 + vendor 依赖 | 1273 / 333 / 177 | `inline` |
| **外壳仓 + 粘合文件** | 1 / 6 / 7 / 22 | `shell` |

第二类的「自有文件」全是 `.claude`、`.dockerignore`、`.env.example`、`deploy.sh`、`docker-compose.yml`、`agents/`、`scripts/` 这类编排与工具配置，不是业务代码。**没有任何文件级判据能把它们和第一类分开** —— `vendor/` `third-party/` `3rd/` 这类路径名启发式会把 `frontend`、`backend`、`DJOneHub` 全判错。

这批数据同时证否了一个更弱的方案：「按信号命中数分流，恰好一个才给结论」。这 8 个仓在那套规则下会被判为「信号冲突」，问一次即可；但它们本质上属于某一种单一形态，不是混合拓扑 —— 也就是说，那套规则做的事和「直接问」完全一样，只是绕了一大圈。

## 4. `inspect` 契约

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

三条约束：

- **三种 mode 下 `code_roots` 元素形状完全一致**，保住原有的「调用方不分支」原则。`inline` 下仍是单项，`path` = 仓根绝对路径。
- **解析不到的代码根不进 `code_roots`**，进 `missing_code_roots`。消费方拿到的每一项都能直接 `cd`，不用先探活。
- **`missing_code_roots` 非空不阻塞流程**，⚠️ 报告即可。真正的失败留到消费方确实要用它的时候。恢复线索（`git submodule update --init <path>` 之类）属于报告内容，**不进契约** —— 同 §4.1。

### 4.1 契约之外的信息

`kind` / `branch` / `upstream` **不进契约**，只在 `reconcile` 问用户时作为选项的辅助说明、以及报告里展示给人看。

理由：消费方只需要 `cd` 进去干活。进了契约就得永远维护，而没有消费方。

## 5. 声明格式

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

`code_roots` 同时接受字符串项与对象项，字符串 `foo` 等价于 `{name: foo}`：

- `shell` 下 name 足够（路径真源是 `.gitmodules`），**现有声明零改动**
- `linked` 下必须给 `path`（没有 `.gitmodules` 兜底）

`upstream` / `branch` 是可选的重建线索，不强制 —— skill 只认不造，记它们只为了让缺失报告能说清「这个引用原本指向哪」。

## 6. 校验全表分家

现行表按 `shell` 一种形态写成，须按 mode 拆开。

### 6.1 两处变化

| 情形 | 现行 | 改后 |
|---|---|---|
| 声明的代码根解析不到（`shell` 下即子模块未 init） | ⛔ 运行时阻塞 | ⚠️ 归 `missing_code_roots`，报告里给恢复线索 |
| `path` 含 `..` / 为绝对路径 | ⛔ 路径非法 | `shell` 下仍 ⛔（子模块不可能在仓外）；`linked` 下**合法** |

第一处是**既存缺陷**：一条流程根本不碰的代码根没 init，不该把整条流程挡死；而且那是一条命令可恢复的状态，不是损坏。

### 6.2 保持不变

重复 name ⛔、`path` 为 `.` 或等于 `docs` ⛔、`inline` 却有 `code_roots` ⚠️。

「两个 path 互为前缀」在 `shell` 下仍 ⛔（嵌套子模块属依赖项、不该进 `code_roots`），`linked` 下**不检查** —— §8 明确「多个引用指向同一目标可能是有意的，只认不评判」。

### 6.3 新增

| 新增 | 级别 | 理由 |
|---|---|---|
| 裸 gitlink（跟踪了 mode 160000 但 `.gitmodules` 无对应条目） | ⛔ **全 mode** | 客观损坏：clone 下来是空目录且无法 `submodule update` 恢复，git 自己只 hint 不拦（实测见 §9） |
| 解析后的路径逃逸出已授权工作范围 | ⛔ **全 mode** | §2.1.1。声明文件可能来自不可信来源，路径声明不是写权限授权 |

## 7. `reconcile` 在 `linked` 下

- 问用户要路径（可多个），每个记 `name` + `path`
- 路径解析不到目录 → 当场告知并让用户改，不静默接受
- 增删引用是**纯声明变更**
- ⛔ 不建 worktree、不 clone、不动被引用的目录

与 `shell` 下「退出 `code_roots` ≠ 删子模块」同一条纪律：改声明 ≠ 改真实拓扑。

### 7.1 消费方判据：看 `mode`，不看代码根数量

流程要区分的只有一件事：**代码和文档在不在同一个仓**。`inline` 在，`shell` 与 `linked` 不在。这就是 `mode` 本身。

现有 8 处消费方（N+1 提交展开、drain 侧逐 code_root 定位、工作区遍历、`--single-commit` 不可用、断点续做状态检测）用的判据是「`code_roots` 多于一项」。**该判据在单代码根的外壳仓下恒假** —— 维护一个 fork 就只有一项，与 `inline` 的一项分不开。后果最重的是外审：drain 时去外壳仓找代码提交，而提交在子模块里，找不到就记「无代码变更」并静默跳过。

这是 v1 就有的缺陷，本次引入 `linked` 后必须一并改对：**判据统一为 `mode` 不是 `inline`**。

例外两处：`codebase-insight` 与 `test-run` 的「逐项跑一遍」是循环，三种 mode 行为一致，用数量是对的。

`protocol.md` §6 的分层按依赖划分，不按 mode 一刀切：

| 组 | 内容 | 判据 |
|---|---|---|
| `shell` 与 `linked` 共用 | Commit 1 按代码根拆分、drain 侧逐 code_root 定位、工作区遍历、`--single-commit` 不可用 | `mode` 不是 `inline` |
| 仅 `shell` | 指针 bump、追溯枢纽、指针漂移 Recovery、断点续做的「Git 历史」维收紧与第五维「指针一致性」 | 依赖 gitlink |
| 全适用（除 `inline`） | detached HEAD 前置门 | 游离 commit 被 gc 回收、push 不上去，与 gitlink 无关；`linked` 的代码根若 detached checkout 同样中招 |

## 8. 明确不做

| 不做 | 理由 |
|---|---|
| **自动判定拓扑** | §3.1。仓库形状是产品决策，不是能从文件布局推出来的事实；`linked` 的代码根可以在仓外，任何仓内扫描都发现不了。扫描只用于给选项排预设 |
| `linked` 参与 `migrate`（任何方向） | §2.0。`migrate` 只在所有权不变的 `inline` ↔ `shell` 间发生；跨所有权边界的转换要么是「造」，要么是处置本仓不拥有的东西 |
| worktree 生命周期编排（建、清理、需求↔应用映射持久化） | 同上。封存为 FUTURE，触发条件 = 真实痛点出现 |
| 从路径名推断子模块是 vendor 还是代码根 | §3.2 数据证否：`frontend` `backend` `DJOneHub` 会被全判错 |
| 禁止绝对路径 | §2.1。`linked` 本来就不可跨机复现，路径形式不改变这一点。**但路径形式自由 ≠ 写入范围自由**，见 §2.1.1 |
| 多个引用指向同一目标时告警 | 轻量场景下共享同一目录可能是有意的。skill 只认不评判 |

## 9. 实测记录

全部在真实仓库或合成仓库上实跑，非推断。

### 9.1 worktree 的语义与代价

| 项 | 实测值 |
|---|---|
| 完整 clone 一份（样本仓） | `.git` 227M + 源码 26.6M ≈ 254M/份 |
| worktree 派生一份 | `.git` 共享（0）+ 源码 26.6M ≈ 27M/份 |
| 构建产物 | 805M，两种方式都得各自一份，无差别 |
| 分支独占 | git 硬拒：``fatal: '<branch>' is already used by worktree at '<path>'`` |
| 身份判定 | worktree 目录中 `git rev-parse --git-dir` ≠ `--git-common-dir` |
| 并行副本枚举 | `git worktree list` 从任一副本即可列出全部工作树及各自分支 |

### 9.2 嵌套 git 仓的风险边界

| 操作 | 实测结果 |
|---|---|
| `git clean -xfd`（单 `f`） | ✅ 安全，dry-run 输出为空 —— git 拒绝递归进入嵌套仓库 |
| `git clean -xffd`（双 `f`） | ⚠️ `Would remove A/` 并真删。**只丢未提交内容**，已提交的仍在被引用仓的分支上；被引用仓留下 `prunable` 记录，`git worktree prune` 清除 |
| 误 `git add <嵌套仓目录>` | ⚠️ 生成裸 gitlink（mode 160000，无 `.gitmodules` 条目），git 只输出 hint 不拦截 |
| 移动外层仓目录 | ⚠️ 被引用仓侧反向指针失效，`git worktree repair <path>` 一条命令修复（实测有效） |

这些是「代码根恰好是仓内嵌套 git 仓」时的已知坑，写进 references 供参考，**不写成强制门** —— 除裸 gitlink 外（§6.3），其余都不是拓扑声明问题。

### 9.3 未实测

IDE（JetBrains 系）对嵌套 git 仓的识别行为。原理上靠 VCS 目录映射、通常需手动 Add root 并记入 `.idea/vcs.xml`，但**未实证**，不作为设计依据。

## 10. 评审结论

### 10.1 外部评审（设计阶段）

独立评审仅拿到用户原话与调查数据、未读设计稿。结论中被采纳的一条：

| 评审意见 | 处置 |
|---|---|
| 「路径声明不是写权限授权。版本库里的 `AGENTS.md` 可能不可信；绝对路径、`..` 和符号链接都不能自动扩大 Agent 的可写范围」 | **全盘采纳**，见 §2.1.1 与 §6.3。原设计完全缺失此项 |

不采纳的一条：把拓扑从「仓库级互斥枚举」降为「每个代码根分别标记」。理由是该形态在 217 仓中零样本，§3.2 逐个核查的 8 个歧义仓真实只有两类，互斥 `mode` 都能完整表达。

⚠️ **这次交审有个已知盲区**：为避免评审去审「自己加的戏」，交审材料刻意不含设计稿。代价是它审的是「该怎么设计」，没审「这个设计有没有洞」—— §3.1 那个「信号覆盖不到 `linked` 主要场景」的缺口正落在此。

### 10.2 实施阶段的三轮审查

实施后经三轮独立审查，共发现 6 个 Critical，全部核实属实。它们指向同一个结构性问题：**把自动判定当主路径**。

| 轮次 | 发现 |
|---|---|
| 1 | 探测的执行程序漏改（判定表改了，可执行步骤没改）；消费方按代码根数量判 `shell`，`linked` 会跑错提交协议；health-lint 适用性门用「单项 `.`」判 `inline`，`path` 改绝对路径后永不命中 |
| 2 | `linked` 的 follow-through 只覆盖信号命中分支，ask 分支是死路；谓词一刀切改 `mode == shell` 导致 `linked` 的 drain 静默跳过外审 |
| 3 | `inspect` 的「只读」表述与「无声明时会写」矛盾；仓外 `linked` 无采集路径；「多于一项」在单代码根下恒假 |

前两轮的修复都在同一套机器里补洞，每次只补「正在看的那一层」。第三轮之后熔断，改为 §3 的「问，不猜」—— 其中两个 Critical 随之消失（不存在「探测 `linked`」这回事了），第三个由 §7.1 的判据统一解决。

**教训**：验证时顺着自己的修改路径走，看不见用户的真实使用路径。真实 `linked` 项目走的是「零信号 → 问」，那条路在三轮修复中一次都没被走过。

## 11. 影响面

| 文件 | 改动 |
|---|---|
| `skills/workspace-topology/SKILL.md` | 拓扑表加 `linked`；「无声明时：问，不猜」节；迁移边界；`inspect` 语义；`workspace-context.v2` 契约；声明格式；校验摘要+指针 |
| `skills/workspace-topology/references/protocol.md` | 三种拓扑与所有权；校验全表分 mode；裸 gitlink 与路径写权；§6 按依赖分层；§6.5 `linked` 下无 N+1 无指针；§7 gitlink 排除仅 `shell` |
| `skills/workspace-topology/references/migration.md` | 确认拓扑的步骤（问 mode → 问代码根 → 写入 → 自校验）；迁移边界仅 `inline` ↔ `shell` |
| `skills/_shared/constraints.md` | `workspace-context.v1` → `v2`；`workspace/default-inline` 改写；小节标题补 `linked` |
| `skills/pipeline/references/health-lint-implementation.md` | 适用性门改读 `mode`；`not_applicable` 口径补 `linked` |
| `skills/dev-flow` / `bugfix` / `dev-workflow`（含 2 个 references） | 8 处判据改为「`mode` 不是 `inline`」；三处补指向 §6.5 |
| `skills/verify` / `e2e-test-flow` / `codebase-insight` / `test-run` | `inline` 单项的描述从 `.` 改为「`path` = 仓库根绝对路径」 |
| `skills/pipeline/SKILL.md` / `skills/retrofit/SKILL.md` / `docs/workflows.md` | 「静默判 `inline`」的表述改为「问一次并落声明」 |
| `README.md` / `docs/architecture.md` / `AGENTS.md` | 三拓扑枚举传播；`AGENTS.md` 旧条目里被本次推翻的表述改为当前状态 |

`spec_version`：`workspace-topology.v1` → `v2`。

**存量项目零影响**：已有 `workspace:` 声明的项目读取路径完全未变。变化只发生在无声明的项目上 —— 从「静默判 `inline`」改为「问一次并落声明」。
