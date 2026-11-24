# 并行工作区：worktree 整体设计（设计稿）

> 状态：待用户审阅。由 claude、codex、agy 三方独立设计后对齐（2026-11-24），整合稿经 codex、agy 复审两轮并修订（第二轮发现一处由修订引入的问题，已撤回该项检查而不是继续加固）；分歧由用户裁定（§8）。本稿取代 [2026-11-23 worktree 支持设计稿](2026-11-23-worktree-support-design.md) 的整体定位，该稿已实施的两项改动按 §7 处理。

## 1. 为什么做

用户原话（逐字）：

1. 「linked 我想改成 worktree 模式，在项目根目录下建`.worktree`目录，其中检出「应用+分支名」的worktree……」
2. 「……如果我在工作区加入 worktree 支持，有哪些方案」
3. 「……你要回答我 worktree 算什么目录模式」
4. 「这块我感觉有点乱不系统，不能基于局部优化或设计，这块你整体全面帮我设计下，worktree 的目的是应对多agent或并行任务场景，或者临时处理问题等」

此前的改动都是局部补丁：拒绝在 worktree 写台账、约定 `.worktree/` 目录、完成门「已知限制」。实测还暴露了两个硬伤：linked 项目代码根在项目外时完成门卡死；linked 项目在 worktree 里干活时，Commit 1 会按声明路径提交到源仓而不是 worktree。

## 2. worktree 和三种拓扑的关系

**正交，不是第四种模式。**

- 拓扑（inline / shell / linked）回答「文档和代码是什么关系、代码归谁」，是仓库级事实，写在声明里。
- worktree 回答「同一个仓同时检出几份、各在哪个分支」，是运行期事实，git 自己记着（`git worktree list`）。一个 worktree 继承它来源仓的拓扑。

按来源分两种，后面的规则都按这两种分：

| 种类 | 来源仓 | 里面有什么 |
|---|---|---|
| 项目 worktree | inline 的项目仓 | 代码 + `AGENTS.md` + `docs/devdocs/`（含台账）的分支副本 |
| 代码 worktree | linked 引用的代码仓、shell 的子模块仓 | 只有代码 |

shell 不开外壳仓的 worktree（每份都要重新初始化子模块，指针与清理都变复杂），只开受影响子模块仓的。

用词：拓扑模式 `linked` 与 git 的 linked worktree 同名不同义。规格文字里 git 的一律写「git worktree（非主工作树）」。

## 3. 根因与角色

根因：台账（`state/`、04 生成区、`backlog.md`）语义上只有一份，物理上随分支走。并行时各分支各写一份 → 合并冲突、编号撞车（实测）。

所以统一成两个角色，三个场景都套这一个模型：

| 角色 | 在哪 | 做什么 |
|---|---|---|
| 台账会话 | 主工作树（文档仓） | 唯一写台账与 `docs/devdocs/`：建卡、派单、登记提交、合并工作分支、改状态、清理 worktree |
| 工作会话 | 某个 worktree | 只写代码和测试，交回提交 sha 与验证结果 |

- **多 agent 并行**：PM = 台账会话；每个执行者一个工作会话、每个涉及的仓一个 worktree、一个分支。
- **一个人多任务**：主会话兼任台账会话；另开的会话各占 worktree。只有一个任务时不开 worktree，现状不变。
- **临时修问题**：手上活脏着又要插一个修复 → 另开一个 worktree 修（基点按 §4.1），不动原现场（不 stash、不切分支）。不脏或很快能收尾的，不必开 worktree。

**主工作树停在集成分支上，不在上面开发**（有并行时）。台账写在哪个分支就落在哪个分支，主工作树在集成分支上，台账才不会困在某个功能分支里。这是约定，keel 不直接检查；违反时会在标完成时被 §4.4 的兜底检查拦下。

「只有台账会话写」是流程责任。工具能拦住「在 git worktree 里写台账」，但分辨不出某个会话是不是 PM。

## 4. 规则

### 4.1 建与删（agent 按统一流程用 git，keel 不提供命令）

用户只说自然语言（「并行做这几张卡」「另外修一下这个」），由台账会话按下面的流程执行 git。流程只写在 `constraints.md` 一处。

- **何时开**：有并行，或需要保留当前脏现场时。⛔ 不为每张卡强制开。
- **位置**：默认 `<项目根>/.worktree/<应用>-<分支安全名>`。安全名把 `/` 换成 `-`、去掉文件名非法字符，撞名时加短标识。项目 worktree 的「应用」取项目目录名，代码 worktree 取声明里代码根的 `name`。真实分支名另行记录（任务的 `branch` 字段），⛔ 不从目录名反推。已有的仓外 worktree 照常可用，不为迁就默认位置而挪动它。
- **来源**：inline → 项目仓；shell → 子模块仓；linked → 代码根声明的源仓。一张卡涉及几个仓就开几个 worktree，不造跨仓的 worktree。
- **基点**：派单 → 集成分支当前头；临时修问题 → 默认建议先 `fetch` 再基于远端默认分支，但维护分支、未推送的集成分支、远端不叫 `origin` 等情况都存在，实际基点与集成目标在 brief 里写明，拿不准就问。⛔ 不改来源仓的工作文件与当前分支。
- **建之前**：目标在项目内时，`.worktree/` 必须已被 git 忽略：未忽略 → 先补 `.gitignore`；已被索引跟踪（如误提交成 gitlink）→ 停下报告，加忽略并不会让它退出索引，修索引要用户确认。目录未被占用；分支未在别处检出。
- **认领已有 worktree**：核对其 `git rev-parse --git-common-dir` 与来源仓一致，路径和分支对得上不能证明是同一个仓。
- **建之后**：用 `git worktree list --porcelain` 核对路径、分支、HEAD。git 是 worktree 清单的唯一真源，⛔ 不在台账或声明里另记路径。
- **删**：卡已交付或明确放弃、分支已合入（用 `git merge-base --is-ancestor` 自己查，`worktree remove` 不拦未合入）或用户明确放弃、worktree 干净（含未跟踪文件）、没人还在用 → `git -C <来源仓> worktree remove <路径>`。交付状态或使用者不明时保留。⛔ 不加 `--force`，⛔ 不 `rm -rf`。分支默认保留，删分支另行决定。`git worktree prune` 只清已确认失效的记录。执行者下线不等于可删。

### 4.2 台账与 docs

- 台账与 `docs/devdocs/` 只在主工作树写。git worktree 里写台账的命令一律拒绝（保留现有实现），提示里给出主工作树路径，并说明查最新台账可用 `<主工作树>/.keel/bin/keel --root <主工作树> task get …`。⛔ 不把写操作自动转到主工作树。
- 项目 worktree 里的台账可读，但只是分支快照。工作会话需要的卡片信息、设计版本由派单 brief 给出。
- 执行者交卡后，台账会话检查其分支相对基点的改动：碰了 `docs/devdocs/` 或 `state/` → 退回。
- inline 项目在 worktree 里修缺陷：开工前先由台账会话在主工作树给这次修复建一张卡；worktree 里只提交修复代码；合回主工作树后补记缺陷日志，再关卡（避免缺陷编号撞车与日志末尾冲突；忘了补时卡会一直挂在台账里）。shell / linked 下文档仓就是主工作树，原地记。

### 4.3 工作会话拿到的上下文

- 编排层下发的 `workspace_context` 保持原形状，但在工作会话里 `code_roots[].path` 换成本任务对应的 worktree 路径；`workspace_root` 与 docs 根仍指向主工作树；`capabilities` 不变。下游（含 dev-workflow 的 Commit 1）按它干活，就会提交到 worktree 的分支，而不是源仓。
- 派单 brief 必须带：主项目根路径、各仓的 worktree 路径与分支、基点、集成目标分支、已知共享资源（端口、数据库、外部服务、构建缓存）及项目自己的避让方式。worktree 不隔离这些。
- 代码 worktree 里没有 keel 垫片：要跑 `move-check` 时用 `<主项目根>/.keel/bin/keel --root <当前 worktree> move-check …`。

### 4.4 完成门：找到代码 + 确认已合入

**找到代码**：`<仓名>@<sha>` 的仓名按下面的顺序解析成目录，去掉现在「先在项目根碰运气」的猜法：

1. inline：项目根（仓名为项目自身时）。
2. shell：`git config -f .gitmodules submodule.<仓名>.path`，解析后须在项目根内。
3. linked：`AGENTS.md` frontmatter `workspace.code_roots` 里 `name` 等于仓名的 `path`（相对路径按项目根解析，展开 `~/`）。
4. 兼容：`<项目根>/<仓名>`，**只在没有 `workspace:` 声明时**使用。已声明、但声明的路径解析不到 → 报错并提示 `/workspace-topology reconcile`，⛔ 不退到同名目录（可能是另一个仓）。

inline 的仓名接受哨兵 `.` 与项目目录名两种写法。

worktree 与来源仓共用对象库，找到来源仓就能解析其任意 worktree 上的提交，与 worktree 放在哪无关。项目外的已声明路径只跑只读 git 命令：所有命令加 `-c core.fsmonitor=false`；`--no-ext-diff`、`--no-textconv` 只加给接受它们的 diff 类命令（`merge-base` 加了会报错，已实测）。keel 工具只解析 `workspace:` 块里的 `mode` 与 `code_roots` 的 `name` / `path`，不引入 YAML 库。这是 `constraints.md` 的 `workspace/context-over-declaration`（消费方不得自读声明）的明确例外：例外只给 keel 工具，因为它在命令行里跑，拿不到握手上下文；skill 仍从 `workspace_context` 读。

**确认已合入**（用户 2026-11-24 裁定：兜底检查 + 例外登记）：

- **兜底检查（不用登记）**：完成门触发时（有测试提交、move 卡转已完成，或卡上有 integration 条目），对每个仓检查本卡登记的每个测试 / 代码提交都是该仓当前 `HEAD` 的祖先。已实测三种情况：单会话直接在当前分支提交 → 通过，不多任何步骤；worktree 分支还没合并 → 拒绝，提示「代码还没合入」；合并后 → 通过。
- **例外登记**：代码合到了别的分支（主工作树或来源仓没停在集成分支上）时，兜底检查会拒绝，这时登记合入点：`task commit <id> <仓名>@<合入后的完整 sha> --kind integration --branch <集成目标分支> --note "…"`。某个仓登记了 integration，该仓就改按它检查：本卡在该仓的每个测试 / 代码提交都是 integration sha 的祖先；integration sha 是本地 `refs/heads/<branch>` 的祖先或就是它的头（按 `refs/heads/` 严格解析，分支不存在 → 拒绝并说明）。没登记的仓仍走兜底检查。
- `branch` 只允许出现在 integration 条目上且必填，按文本字段校验（长度上限、禁换行与 `<!--`）。同一个仓只保留一条：再登记即替换旧的。
- **integration 条目只是合入证据**：不计入代码提交，不参与「测试先于代码」、冻结、纯移动范围，也不进 `task get --diff-range`（否则 drain 的审查范围会卷进同期合入的其他卡）。
- 冻结检查的终点不变（仍到本卡最后一个登记的测试 / 代码提交）。⛔ 不延到合入点：集成分支上别的卡改过同一个测试文件时会被算到本卡头上（复核指出）。合并是否改坏了测试，靠合并后的验证保证，见 §5。
- **二次检查**：`review_pending → 已完成` 时完成门会再跑一遍。这期间分支被改写（rebase / reset）导致提交不再是祖先 → 拒绝；出路是重新登记 integration（替换旧条目），测试 / 代码 sha 也失效时按完成门现有的 sha 失效出路处理。
- 合并工作分支用 merge 或快进，⛔ 不 squash。必须 cherry-pick 时，交卡 sha 作废，按落地后的 sha 重新登记测试 / 代码提交。
- 「是否已推送到远端」不归完成门管。
- 多仓不是原子的：一个仓合入冲突时整卡不完成，已合入的仓保留记录，逐仓续做。

### 4.5 workspace-topology

- § worktree 缩成指针，指向 `constraints.md` 的「并行工作区」一节。
- `inspect` 报告按各来源仓的 `git worktree list` 列出全部 worktree（含仓外的），只报 git 能证明的事实：分支、是否有未提交或未跟踪内容、分支是否已是集成分支的祖先（ℹ️，不进 `workspace-context.v2` 契约）。⛔ 不判「可删」：任务是否交付、还有没有人在用，git 不知道。
- 检查表保留「`.worktree/` 存在但未被忽略 → ⚠️」，这是只读检查。建 worktree 前的同一条件是硬前置，写在 §4.1，两者分别属于两个动作的边界。

## 5. 三种拓扑下的闭环

| 拓扑 | worktree 来源 | 交卡后 |
|---|---|---|
| inline | 项目仓 | 合回集成分支 → 登记测试 / 代码 / integration 提交 → 改状态 → Commit 2 |
| shell | 子模块仓 | 子模块仓合入 → 登记 → 外壳仓主工作树 bump 指针 + Commit 2 |
| linked | 代码根源仓 | 代码仓合入 → 登记 → 文档仓 Commit 2（无指针） |

合入后、改状态前，台账会话在集成分支上跑一次必要的验证（至少是本卡的测试）：合并解冲突可能改坏代码或测试，执行者分支上的测试结果不能代替。这一步靠流程，工具不查。

## 6. 要改的地方（规则只写一处）

| 文件 | 改什么 |
|---|---|
| `skills/shared/constraints.md` | `workspace/context-over-declaration` 写明 keel 工具例外。新增「并行工作区」一节作唯一真源：两种 worktree、两个角色、主工作树停在集成分支、§4.1 建删流程、§4.2 台账规则、§4.3 上下文与 brief 字段。`keel/worktree` 并入此节。§完成门：仓名解析顺序、integration 检查、删去对应的「已知限制」 |
| `keellib/donegate.py`、`schema.py`、`tasks.py`、`keel.py` + 测试 | 仓名解析；`kind=integration` 与 `--branch`（同仓替换）；兜底合入检查与 integration 检查（有 integration 条目时不走现有早退）；integration 单独分组；`diff_ranges` 排除 integration |
| `keellib/store.py` | 拒绝提示补 `--root` 读法 |
| `skills/workspace-topology/SKILL.md`、`references/protocol.md` | 正交关系与用词；§ worktree 缩成指针；`inspect` 报告列 worktree 状态 |
| `skills/dev-workflow/SKILL.md` | 开头「不做任务并行……手动用 worktree」改为链接；登记表加 integration 行（注明仅在合到别的分支时用） |
| `skills/dev-workflow/references/executor-mode.md` | 工作目录 = brief 给的 worktree；`move-check` 调法；交卡不碰 docs |
| `skills/dev-workflow/references/task-orchestration.md` | 派单 brief 字段指向 constraints |
| `skills/bugfix/SKILL.md` | inline worktree 里修缺陷：先建卡、合回后补日志再关卡（一行 + 链接） |
| `docs/workflows.md` | 三个场景的自然语言用法 |
| `docs/superpowers/specs/2026-11-20-keel-parallel-agents-design.md` | `branch` 字段与 §4.1 命名、§4.4 集成目标对齐（该稿待审，只加引用） |

## 7. 2026-11-23 两项改动

- **git worktree 里拒绝写台账**：保留，只改提示。bare 仓（没有主工作树）暂不支持，有真实需求再引入「指定台账工作树」。
- **`.worktree/<应用>-<分支>` 约定与未忽略警告**：保留为默认位置（非强制）；约定本体移入 `constraints.md`；拓扑仍只认不造，建删由台账会话按 §4.1 执行。

## 8. 对齐记录

| 议题 | claude | codex | agy | 结论 |
|---|---|---|---|---|
| 与拓扑的关系、两种 worktree、shell 只开子模块仓 | 正交 | 正交 | 正交 | 一致 |
| 台账单写、保留拒写、不自动转写 | 同 | 同 | 同 | 一致 |
| 完成门按声明找代码根、不 squash | 同 | 同（传映射） | 同（读声明） | 一致；取 agy 的读声明 |
| 谁建删 worktree | keel 命令 | agent 用 git | agent 用 git | **用户裁定：agent 按统一流程用 git** |
| 完成门查合入 | — | 完整版 | — | **用户裁定：兜底检查（提交须在来源仓当前 HEAD 上，不用登记）+ 合到别的分支时登记 integration**。复审指出「所有卡都登记」在单会话下是自证；兜底检查是定稿后补的，未经两方复审 |
| 工作会话的代码根路径换成 worktree | — | 提出 | — | 采纳（已核实 dev-workflow:289） |
| brief 列共享资源 | — | 提出 | — | 采纳 |
| 主工作树停在集成分支 | 提出 | 风险里提到 | — | 采纳为约定 |
| inline worktree 修缺陷后补日志 | 不确定 | docs 只由 PM 写 | 提出 | 采纳 |
| `move-check` 用主项目垫片 + `--root` | 提出 | — | 提出 | 采纳 |

否掉的做法（三方合计）：第四种拓扑 / 改造 linked；台账自动转写；台账移出分支或软链共享；每分支一份台账再合并；在声明或 `code_roots` 里记每个 worktree；自动为所有应用建 worktree；keel 内置调度、锁、租约；自动解冲突、自动删分支、强删脏 worktree。

## 9. 风险与不确定

- 「主工作树停在集成分支」工具不直接查（哪个是集成分支没有声明），只在标完成时经兜底检查间接暴露。
- 兜底检查看的是来源仓当前 `HEAD`：主工作树或来源仓停在别的分支时会拒绝，需要登记 integration 才能过。这同时让「主工作树没停在集成分支」当场现形。
- 完成门读项目外的声明路径：`AGENTS.md` 可能来自不可信的仓。只读命令加三个保护开关之后，是否还需要额外的信任约束，未定。
- 声明漂移（新增代码仓没更新声明）时，完成门报解析不到，出路是 `/workspace-topology reconcile`。
- inline worktree 里修完缺陷、合回后要补缺陷日志，合完就忘的可能不小；真实使用中观察。
- 真实项目的目录形态没有现场核实；本稿不判定它属于哪种模式。

## 10. 验收

- 三种拓扑各一个临时仓：外部代码根、shell 子模块名 ≠ 路径、两个仓含相同 sha 前缀、分支未合入、单会话插入修复、删除脏 worktree 被拒、执行者改了 docs 被退回。
- 完成门兜底检查：单会话直接提交 → 过；worktree 分支未合并 → 拒；合并后 → 过；来源仓停在别的分支 → 拒，登记 integration 后过。integration：登记提交不是 integration sha 的祖先 → 拒；integration sha 不在目标分支上 → 拒；没有测试提交但登记了 integration 的卡同样检查；不触发完成门的卡行为与现在完全一样；另一张卡在集成分支上改过同一测试文件时不误拦；`--diff-range` 不含 integration；已声明路径失效时报错而不是退到同名目录。
- `bash scripts/check-python.sh` 全过；按落地顺序升 minor 版本（与多 agent 并行设计稿谁先落地谁用 3.3.0）。
