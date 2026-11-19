# keel 门禁机制化：规则由工具保证，spec 退为指引

> 2026-11-19。状态：设计稿，待用户批准。触发：ai-code（EMSPR，SIDM-71103）M-003 第 1 批反馈（emspr-pm 会话转达）与本仓对该项目的三次复盘。

## 1. 意图

用户原话：

> 规则能否靠 hook 和 rule 机制，也就是 agent 本身机制，而不是 spec，spec 遵守是最差的
>
> 我想的不只是台账而是整体 keel 工作流，按严格的机制保证，而不是 spec
>
> spec 要进一步简化，规则、门禁和护栏由工具和机制保证而不是大模型，spec 是指引的作用，否则就会出现规矩立了但是始终有遗漏点或被绕过等情况

keel 现有 756 处 ⛔ 规则，全部靠模型读了 spec 后自觉遵守；机器执行的只有 1 个脚本（`health-lint.py`）和 3 个 hook，且 3 个 hook 都是「提示、不拦」。同一个项目（ai-code）三次复盘的规律一致：规则写进 spec → 写进项目 AGENTS.md → 写进常驻约束，问题照样复发。

本设计把 keel 改成：**能机器判定的规则由工具执行，模型绕不过；spec 只讲为什么、往哪走、被拦后怎么办。**

### 1.1 现状证据（ai-code，2026-11-19 实读）

| 现象 | 数据 | 说明 |
|---|---|---|
| 台账当执行日志 | `04-dev-tasks.md` 11-19 涨到 334KB，PM 当天手工瘦身到 184KB（`30667e6`），超长行移到 `audit/T-xxx/ledger-record.md` | T-248 一行含 patch_id、注错次数、20 检查点结论、PM 复核、真库待补 |
| 台账当会话交接 | §2.12 引用块写着「排期」「现场」「VM 待验清单」 | 同 09-28 复盘「当前状态有 5 个载体」 |
| 警报被无视 | `layout/size-cap` 96KiB 警报一直在，SessionStart 提示原文「本提示不拦任何操作」 | 只提示不拦 = 无约束 |
| 规则在上下文里也被违反 | ai-code AGENTS.md 有「范围外发现只登记一行」「台账只经 skill 更新」，仍复发 | 常驻 ≠ 遵守 |
| 格式各写各的 | 一份台账里四种表头；`process-guards.md` 实测一张表的分隔符有五种写法 | 靠解析 markdown 做门禁会很脆 |
| backlog 已自发结构化 | `backlog/T-26-1.md` 一条一文件 + 索引 | 方案 B 的形态项目里已经长出来了 |

## 2. 目标、非目标、反目标

**目标**

- 规则、门禁、护栏由工具执行：违反时当场拦下，模型看到原因并改正。
- 每次门禁命中（拦下、警告、放行）都留记录，供用户在实际使用中判断哪些门该紧、哪些该松。
- 每接管一类规则，spec 里对应条文删除，只留一行「由某检查保证，被拦时这样处理」。
- 存量项目能经 keel 现有 realign 路径升级过来（用户会在 ai-code 升级插件后反馈）。

**非目标**

- 不把判断类规则伪装成机器检查（「算不算范围外」「结论核没核实」「设计好不好」）。它们留在 spec 里当指引，第 1 段只为它们留记录（见 5.6）。
- 不改 ai-code 等下游项目的文档；只改插件和它的升级路径。
- 不做通用规则引擎、不做插件化门禁框架。门就是 `keel.py` 里的函数加一张默认档位表。

**反目标**（能跑但算失败）

- 门把正常流程频繁拦下，用户为了干活整体关门。命中记录必须能看出误报率。
- 工具变成第二份 spec：`--help` 和错误信息长到要模型去「理解规则」。被拦信息只说哪里违反、怎么改，一两行。
- 有漏口却假装没有。三端 hook 的漏口（见 6）写在文档里，并用工具自检和 git hook 兜底。

## 3. 约束

- 三端（Claude Code / Codex / OpenCode v2）共用一份 `skills/`；hook 适配层沿用现有两份文件（`hooks/hooks.json`、`hooks/opencode-plugin.js`）。
- 工具用 Python，只用标准库，兼容 3.9（macOS 自带）。与 `health-lint.py` 同一路子，不引入依赖。
- **运行时契约**：需要 `python3`（≥3.9）和 `bash`，与现有 hook 的依赖相同（`hooks/hooks.json` 已用 bash 调 Python）。不依赖 jq。缺运行时时垫片报「keel 工具未就绪」并说明缺什么，⛔ 不退回手写状态。原生 Windows（无 bash）第 1 段不支持，在 README 写明；WSL / Git Bash 视同 Linux，能测则测。
- 本仓「一条规则只写一处」：规则真源从 spec 正文移到检查代码；spec 只留名字和处理办法。
- SKILL.md ≤ 500 行。
- 分发按版本键控：这是破坏性改动，插件版本升到 3.0.0，各 manifest 同步。
- **推翻的既有决策**（用户已同意方向，实施时在原处改写并注明本稿）：
  - `hooks/README.md`「hook 只能是加速器，规则本身必须仍写在 skill 正文里，⛔ 不得把门挪进 hook」。原理由是 hook 只在插件安装路径下生效；现在三端都按插件分发，理由不再成立。
  - `docs/audits/2026-09-28-ai-code-process-audit.md`「hook 拦截直接编辑台账——不做」。原理由是 hook 分不清 skill 在改还是绕过流程；本设计改为「状态文件只有工具能写」，不需要区分是谁在改。

## 4. 方案对比（用户已选 B）

| 方案 | 做法 | 代价 | 结论 |
|---|---|---|---|
| A. 事后检查 | 台账仍是模型手写 markdown，hook 在编辑后检查结果并拦回 | 状态流转只能靠解析 markdown 推断，脆；shell 改文件的路径要逐个补 | 否：模型仍在手写被检查的东西 |
| **B. 状态只由工具写** | 状态存结构化文件，只能经 `keel` 命令写；人看的台账由工具生成；hook 拒绝直接编辑；命令当场校验 | 改造量最大；存量项目要迁移；三端 hook 能力不一 | **选定**。分段上线 |
| C. 折中 | markdown 台账定死格式，命令改写 markdown，hook 拒绝破坏格式 | 仍要解析 markdown | 否：A 的脆弱点只是缩小 |

## 5. 整体框架

### 5.1 四层防线

规则由哪层执行，按「能不能被绕过」从强到弱：

1. **工具自身**：`keel` 命令写状态前校验字段、取值、条件必填；每次运行先核对状态文件的完整性，对不上就拒绝继续（只允许查看和 `keel state accept`）。这一层不依赖任何客户端能力。
2. **客户端 hook**：PreToolUse 按路径拒绝直接编辑状态文件；PostToolUse 检查本次编辑后的文件（行长、体积）和完整性，违规时拦回。
3. **git hook（可选安装）**：`pre-commit` 跑 `keel check --staged`。不分客户端、不分人和模型，是最后一道自动检查（可被跳过，见 `hooks/README.md` 已知漏口）。
4. **spec 指引**：说明为什么、怎么用命令、被拦后怎么办。不再承担「必须」。

第 1 层和第 3 层兜住第 2 层的漏口（Codex 出错放行、插件 hook 未信任、shell 绕过）。

### 5.2 命令行工具与调用入口

- 代码：`skills/shared/scripts/keel.py`（单文件起步；超过约 1500 行再拆包）。带 `--self-test`，沿用 `health-lint.py` 的自测夹具写法。
- **调用入口问题**：skill 正文拿不到插件根路径（`external-reviewer-integration.md` 已记录 `CLAUDE_PLUGIN_ROOT` 在 skill 上下文不可用；`agent-memory` 现在写的是 `<keel>/skills/...` 占位，靠模型自己找）。
- **解决**：SessionStart hook 在项目里写一个垫片 `.keel/bin/keel`（`exec python3 <插件根>/skills/shared/scripts/keel.py "$@"`），并把 `.keel/` 写进 `.git/info/exclude`（不改用户的 `.gitignore`）。skill 一律调用 `.keel/bin/keel`。OpenCode 在插件 `setup` 里做同样的事。垫片每次会话开始重写，插件升级后自动指向新路径。
- **入口只做 CLI**（用户 2026-11-19 定）：hook、git pre-commit、人和模型共用同一个命令。不做 MCP：它唯一的好处是参数结构化，而 keel 的写命令参数很短；强制力也不来自 MCP（模型仍可绕开它直接改文件，兜底靠 hook 和校验和）。只有实际使用中出现 CLI 调用的具体问题时再评估。
- **查询入口**：模型查状态用 `keel task get <id>` / `keel task list --status … --fields …` / `keel backlog list --status …`，输出 JSON 或一行一条的文本，只返回请求的字段。结果必须附带覆盖情况（扫描了多少文件、有多少条目无法识别），⛔ 不静默漏计。正文检索仍用 grep / rg。
- 垫片不存在时（hook 未运行、Codex 未信任）：skill 指引让模型告诉用户「keel 工具未就绪」并给出原因清单，⛔ 不退回手写状态文件。

### 5.3 状态文件与生成视图

**状态与定义分开**：任务的「定义」（描述、验收标准、测试方法、执行步骤）是 dev-tasks 写的规格，仍是可编辑的 markdown；任务的「状态」（状态值、提交、审查字段）由工具独占。

```
docs/devdocs/
├── 04-dev-tasks*.md            # 定义：人和模型可编辑；主文件里有一段工具生成区
├── backlog.md                  # 整份由工具生成（索引 + 每条一行摘要）
├── backlog/<id>.md             # 每条的 Context / Reactivation Criteria，可编辑
├── audit/T-xxx/                # 执行记录、裁定、复核，可编辑（不变）
└── state/                      # 工具独占，提交入库
    ├── tasks/T-248.json
    ├── backlog/T-26-1.json
    └── gates.json              # 项目对默认门档位的覆盖
.keel/                          # 本地，git 忽略
├── bin/keel                    # 垫片
├── manifest.json               # 工具最近一次写入的各状态文件与生成区的 git blob sha1（可直接与 HEAD 比较）
└── gate-log.jsonl              # 命中记录
```

- 格式用 JSON（标准库可读写；键排序、缩进 2，git diff 可读）。
- 一条一个文件：多会话并行时减少冲突。编号由 `keel task add` / `keel backlog park` 分配（文件锁），解决 ai-code「编号靠人工避让撞号」。
- `04-dev-tasks.md` 的生成区用 `<!-- keel:begin ledger -->` / `<!-- keel:end ledger -->` 包住，每卡一行：编号、标题、状态、档位、依赖、里程碑、记录链接。生成区外的内容照旧由人和模型编辑。
- **合法内容的判据**：一个状态文件（或生成区）的内容，要么等于 git HEAD 中的版本，要么等于工具最近一次写入时登记在本地 `.keel/manifest.json` 的校验和；两者都不是，即判为非工具改动。
  - 经 git 进来的改动（pull、merge、rebase、checkout）会同时更新 HEAD，自动合法，不需要 git hook，也不需要确认。合并、cherry-pick、rebase 停在冲突上时，`MERGE_HEAD` / `CHERRY_PICK_HEAD` / `REBASE_HEAD` 里的版本同样合法；manifest 登记过、HEAD 与工作区都没有的文件（切分支带走的）不算违规，下次写入时清出 manifest。
  - 只有生成内容（K2）对不上时，`keel render` 从状态重新生成即可，不需要确认。
  - manifest 只在本地，不入库，所以不会产生合并冲突。
  - 任何不经工具的工作区改动（编辑器、shell、别的客户端）都会在下次 hook 或命令运行时被发现。不必逐个去堵 shell 的写法。
  - 剩下的合法例外只有手工解决合并冲突，需要 `keel state accept`。**只能人执行**（用户 2026-11-19 定）：命令要求在交互终端里输入确认，没有交互终端（模型的 shell 调用）时拒绝执行，并提示「这一步只能由人在交互终端执行：另开一个终端，在项目根目录运行 `.keel/bin/keel state accept`」。2026-11-19 实测：Claude Code 的 `!` 命令没有控制终端，故改为另开终端执行。每次认可都写入命中记录。

**写入的并发与落盘**：

- 写命令都是字段级操作（改状态、加提交、挂起原因等），⛔ 不提供整条记录覆盖写。
- 每次写入在项目级锁（`.keel/lock`）内完成「读取 → 校验 → 写临时文件 → `os.replace` 原子替换 → 更新 manifest」，两个会话同时写同一条不会互相覆盖；拿不到锁时等待数秒后报错，不静默跳过。
- 校验失败时原文件不动；中途崩溃留下的临时文件下次运行时清理。替换状态文件与更新 manifest 之间崩溃时，manifest 落后于状态文件，之后会被判为 K1，须人执行 `keel state accept` 恢复（已知漏口）。

**任务状态字段**（第 1 段；具体键名由实施者定）：编号、标题（≤80 字）、状态（待开发 / 进行中 / review_pending / 已完成 / 已归档）、review_profile、依赖、里程碑、层级、来源（`derived_from`：由哪张卡在执行中派生，可空）、commits（`<repo>@<sha>` + 一句描述）、batch / due / pending_reason、ext_review_state、skip_trace_reason（≤200 字）、exploration_mode、profile_downgrade_reason（≤200 字）、record（`audit/T-xxx/` 链接）。

**backlog 字段**：沿用 `backlog.v2` 的 schema（source_id、entry_no、status、created_at、created_by_skill，及按状态的条件必填），新增 note ≤200 字的上限。

**长文本一律不进状态**：任何超过上限的说明写到 `audit/T-xxx/` 或 `backlog/<id>.md`，状态里只存链接。

### 5.4 门禁清单（第 1 段）

| 门 | 判定 | 执行层 | 默认档位 |
|---|---|---|---|
| K1 状态完整性 | `state/` 下文件被非工具改动（校验和不符），或有 Edit/Write 指向 `state/` | Pre 按路径拒绝；Post（含 Bash）和每次命令运行核对校验和；pre-commit | 拦 |
| K2 生成区完整性 | 生成区或 `backlog.md` 被非工具改动 | 同 K1 | 拦 |
| K3 行长棘轮 | 状态载体文件中**相对 git HEAD 新增或改动**的行超过 500 字符（表格行同样计） | Post 检查磁盘文件对比 HEAD；pre-commit | 拦 |
| K4 体积棘轮 | 状态载体文件已超过 96KiB 且本次比 HEAD 更大 | Post；pre-commit | 拦 |
| K5 字段校验 | 取值不在枚举内、条件必填缺失、文本超上限、依赖指向不存在的编号 | 工具内 | 拦（不可调） |

- **状态载体文件**：会被每个会话读来判断现状的文件，即 `04-dev-tasks*.md`、`backlog.md`、`00-context.md`、`.claude/rules/devdocs-state.md`。长文本的去处（`audit/**`、`backlog/<id>.md`）和规格文档（01–03）不在范围内：它们按需读，长段落是正常的，否则迁移搬过去的长行会自己触发 K3。
- **与 health-lint 的关系**：阈值和判定函数只在 `keel.py` 里写一处；`health-lint.py` 的 `state/line-length-cap`、`state/total-size-cap`、`layout/size-cap` 改为调用它们出报告，不再自带阈值。
- **棘轮**：K3、K4 只拦新增和变大，已有超长行、已超体积的文件可以照常改小。存量项目升级后不会一上来全红，又不会继续长。
- K3、K4 放在 Post 而不是 Pre：Pre 要从 Edit / apply_patch / patch 三种输入模拟出结果文件，三端各不相同；Post 直接读磁盘，三端一致。代价是文件已写入，模型须当场改回；没改回的由 pre-commit 和下次 Post 继续拦。
- 档位：`拦` / `警告` / `关`。插件默认值写在 `keel.py`；项目覆盖在 `state/gates.json`，只能用 `keel gate set <门> <档位> --reason "<原因>"` 改，改动本身记一条命中记录且进 git diff。第 1 段不提供「单次放行」。

### 5.5 命中记录

- 每次门禁判定（拦、警告、档位为关时的跳过）追加一行到 `.keel/gate-log.jsonl`：时间、门、档位、结果、客户端、触发的工具、路径、一句细节。
- `keel gate report [--since <日期>]`：按门汇总命中次数、涉及文件，供用户校准档位并反馈给本仓。
- 日志放本地不入库：多会话写同一入库文件会冲突，且它是校准用的观测数据，不是项目事实。

### 5.6 判断类问题：只记录，不拦

第 3 条（发现差异就立卡）和第 6 条（先下结论后订正）无法机器判定。第 1 段只做两件事：

- `keel task add` 必须写来源；执行中派生的卡记 `derived_from`。`keel gate report` 附带「每卡派生数」统计。是否设收敛上限，等有了数据再定。
- `keel backlog park` 是一行命令（note ≤200 字），让「登记一行」比「开一张卡」省事。

### 5.7 迁移（存量项目升级）

- **未迁移项目先迁移再继续**（用户 2026-11-19 定）：插件升到 3.0.0 后，项目还是 `tasks.v2` / `backlog.v2` 时，所有写状态的命令都拒绝执行，并提示先跑 `/pipeline realign`；只读命令照常可用。skill 只写一套「走命令」的路径，不保留手写过渡路径。K3、K4 从第一个会话起就生效（棘轮，不会让存量一上来全红）；K1、K2 在 `state/` 存在后生效。
- `keel migrate --dry-run`（默认）/ `--apply`。由 `/pipeline realign` 在检测到 `tasks.v2` / `backlog.v2` 时调度；restructuring 级别，按现有规则逐项确认。
- 任务：识别 keel 模板的 `#### T-XX` 属性表，以及首列为编号的汇总表（表头列名按别名表映射：状态 / profile / review_profile / 依赖 / 来源 / 层 / commits…）。状态值归一化；项目自定义值（如 ai-code 的 `🔍 待审查`）无法映射时列入报告，用 `--map-status "🔍 待审查=review_pending"` 显式指定，⛔ 不猜。
- 超过上限的文本搬到 `audit/T-xxx/ledger-record.md`（追加，不覆盖），状态里留链接。ai-code 已手工搬过的，识别出已有文件就不重复搬。
- backlog：识别 `### <id>` + yaml 块的集中形态，以及 `backlog/<file>.md` + yaml 的目录形态。
- 输出 `.keel/migration-report.md`：迁了什么、没认出什么、搬了哪些长文本。有未认出的任务时 `--apply` 拒绝执行，除非 `--allow-partial`（未认出的原样保留在生成区外）。
- 原文件里的定义内容不删；只把原状态表替换为生成区。
- 样本：ai-code 位于 `~/Projects/Workspace/ai-code/docs/devdocs/`，可读。主文件汇总表 245 行，表头 `ID | 描述 | 状态 | profile | 执行 | 依赖 | 来源 | 层`；另有 `任务 | 档 | 已提交？ | ext_review_state | 备注` 等三种表头；分册（`-core/-infra/-api/-ui`）是 `## T-xx · 标题` 节；backlog 已是 `backlog/<id>.md` 目录形态加 `backlog.md` 索引。只读，不改。

### 5.8 归档与分册

- 归档时，定义块照旧由 `/sync --archive` 搬到 `archive/04-dev-tasks-archive.md`（定义是可编辑 markdown）；状态文件保留，状态改为「已归档」（经 `keel task archive`）。
- 生成区只列未归档任务，末尾一行给出已归档数和归档文件链接。
- 分册里的任务统一汇总到主文件的那一个生成区，分册里不设生成区。
- 生成区不受 dev-tasks 的 300 行拆分建议约束：每行约 150 字符，250 卡约 37KB，在 K4 以内。
- 迁移完成后提示是否安装 git pre-commit hook（`keel git-hook install`），已有 hook 或 `core.hooksPath` 时串接，⛔ 不覆盖。

## 6. 三端差异与已知漏口

依据：子代理 2026-11-19 核对官方文档（code.claude.com/docs/en/hooks、learn.chatgpt.com/docs/hooks、opencode.ai/v2/docs/build/plugins），未在真实客户端上跑。

| 项 | Claude Code | Codex | OpenCode v2 |
|---|---|---|---|
| Pre 拒绝 | `permissionDecision: deny` + 原因，模型可见 | 同形；**出错、超时、输出不合规时放行** | `execute.before` 里 throw，仅迁移示例里有；文档化的路径是 `permission.hook("evaluate")` |
| Post 拦回 | `decision: block` 原因附在结果旁 | 同形，但**替换**工具结果 | 无契约，只能改写 `event.result` |
| 编辑输入 | `file_path` + 内容 | `apply_patch` 的补丁文本，**无 file_path** | `path` / `patchText` |
| 插件 hook 生效 | 启用即生效 | **须用户在 `/hooks` 信任，插件每次改动 hook 脚本后须重新信任** | 无信任步骤 |

对设计的影响：

- 第 2 层（hook）在 Codex 上不能当硬边界，靠第 1 层（工具自检）和第 3 层（pre-commit）兜底。
- Codex 的路径要从补丁文本里解析 `*** Update File:` 等行；`opencode-plugin.js` 已有同类解析，抽成共用逻辑。现有 `skill-flag-lint` 在 Codex 上同样拿不到路径，顺手修。
- `hooks.json` 里的 `"shell": "bash"` 不是 Codex 文档化字段，实施时实测其行为。
- Codex 是否支持 SessionStart（垫片依赖它）须实测；不支持时由 skill 首次调用前用 `keel` 绝对路径兜底的方案由实施者定。
- README 增加「Codex 用户升级插件后须在 `/hooks` 重新信任」。

## 7. 分段与边界

| 段 | 内容 | 本稿细度 |
|---|---|---|
| 1 | 工具骨架、垫片、状态文件与生成区、K1–K5、命中记录、迁移、git hook、相关 skill 改走命令、spec 瘦身（台账与 backlog 部分） | 可直接写计划 |
| 2 | 状态流转核证据：转 review_pending 须有冻结哈希一致、绿验记录（skipped/todo=0）；转已完成须有 drain 裁定文件。需要先把这些证据定成固定格式落盘 | 只定边界 |
| 3 | 提交与代码：提交信息不带 keel 编号、改产品代码须有「进行中」的任务（`keel task start` 认领）、代码注释不带 T-xx。走 git `commit-msg` / `pre-commit` 与 Pre Bash `git commit` 检查 | 只定边界 |
| 随行 | spec 瘦身：每段接管的规则在 spec 中删除条文，留一行指引 | 随各段 |

第 2、3 段开工前各自再出设计稿，以第 1 段的命中记录和用户在 ai-code 的反馈为输入。

## 8. 第 1 段要改的 skill

（读写方清单来自子代理 2026-11-19 对本仓的全量检索。）

| skill / 文件 | 改动 |
|---|---|
| `shared/constraints.md` §任务台账协议、§review_pending 字段 | 字段表删除，改为「字段与取值由 `keel schema task` 输出，违规由 K5 拦」 |
| `dev-tasks` 模板与 SKILL | 新建任务走 `keel task add`；定义块属性表删除状态、commits、审查状态行；`spec_version` → `tasks.v3`；归档规则改走工具 |
| `dev-workflow`（SKILL、execution-flow、task-orchestration、verification-flow、auto-mode、inline-entry） | 所有状态与字段写入改为 `keel task …`；读状态用 `keel task show/list` 或读生成区 |
| `verify --review-drain` | 放行与字段写入走 `keel task` |
| `sync`（archive、absorb-mode） | 状态推进与归档走 `keel task` |
| `feature`、`retrofit` | 新增任务走 `keel task add` |
| `backlog` | 全部动作改为 `keel backlog …`；门控（source_id 白名单、条件必填、重复入池确认）进 K5 或命令交互；`spec_version` → `backlog.v3` |
| `pipeline` realign | 调度 `keel migrate` |
| `agent-memory` 模板 | 「台账只经 skill 更新」改为「台账状态由 keel 工具维护，直接编辑会被拦」；取最大 T 改用工具 |
| `hooks/` | 新增 keel 门禁 hook（Pre + Post + SessionStart 垫片）；README 改写「门不进 hook」决策；Codex 补丁路径解析 |
| `docs/architecture.md`、`README.md`、各 manifest | 记录架构变化；版本 3.0.0 |
| 只读方：`onboard`、`compound`、`test-run`、`dev-flow`、`verify`（readiness、schema-drift）、`retrofit`（version-migration）、`agent-memory`（devdocs-state 模板） | 读状态改为读生成区或 `keel task show/list`；schema-drift 认 `tasks.v3` / `backlog.v3` |

## 9. 验证

- `keel.py --self-test`：字段校验、棘轮判定（新增行、改动行、改小）、校验和、迁移解析（keel 模板 + ai-code 四种表头 + 目录形态 backlog）。
- hook 夹具脚本（同 `test-devdocs-drift.sh`）：Claude Code 与 Codex 两种输入形状各一组，覆盖 Pre 拒绝、Post 拦回、Bash 改状态文件被发现。
- 迁移实测：把 ai-code 的 `docs/devdocs/` **复制到临时目录**跑 `--dry-run` 和 `--apply`，⛔ 不动原项目。
- 并发：两个进程同时对同一条状态做不同字段的修改，两处修改都保留；锁超时报错。
- 查询：`task list` 在 ai-code 迁移副本上返回的条目数与迁移报告一致，未识别条目计数非零时如实输出。
- 性能：Post hook 在 ai-code 规模（约 120 个 devdocs 文件）下 < 300ms。
- 真实客户端：Claude Code 实测 K1–K4；Codex、OpenCode 能测则测，测不了在交付说明里写明。

## 10. 留给实施者

- JSON 键名、命令参数语法、生成区每行的具体列与格式。
- `keel.py` 内部结构；Codex / OpenCode 补丁解析的共用方式。
- 垫片在 Codex 无 SessionStart 时的兜底方式。
- 迁移别名表的具体内容（以 keel 模板和 ai-code 实际表头为准）。

## 11. 决定记录

**用户定的**：方案 B，分段上线（4）；该拦的从一开始就拦，阈值可放松，记录必须有（5.4、5.5）；`keel state accept` 只能人执行（5.3）；未迁移项目先迁移再继续（5.7）；keel 只负责插件本身，ai-code 由用户升级并反馈；入口只做 CLI，不做 MCP（5.2）；第 1 段 backlog 和任务状态一起做（7）。

**评估后放弃的方向**：把全部文档改成 JSON、用 jq 查询（用户提出，2026-11-19 交 codex 独立调研后放弃）。原因：需求、设计、测试理由、任务验收标准是长篇正文，塞进 JSON 字符串既不好查也不好读；jq 不是各平台默认安装，不能作为发行依赖；按字段查询的收益由 `keel` 自带的查询命令提供（5.2）。工具独写的范围保持在状态字段。调研同时补出的三处缺口已写入：运行时契约（3）、查询入口（5.2）、并发与原子写（5.3）。

**Claude 替用户定的（请审阅）**：

1. 状态用 JSON、一条一文件，放 `docs/devdocs/state/` 并入库；完整性判据是「等于 HEAD 或等于工具最近一次写入」，校验和清单只在本地。
2. 任务「定义」仍是可编辑 markdown，只有「状态」归工具；`backlog.md` 整份生成。
3. 命中记录放本地 `.keel/gate-log.jsonl`，不入库。
4. 行长上限 500 字符、体积上限 96KiB 沿用现有阈值，均为棘轮（只拦新增和变大）。
5. K3、K4 在 Post 检查而非 Pre。
6. 第 1 段不提供单次放行，只能整门改档位（有记录）。
7. 判断类问题第 1 段只记录派生数，不设门。
8. 插件版本升 3.0.0。
9. K3、K4 只管状态载体文件（`04-dev-tasks*.md`、`backlog.md`、`00-context.md`、`devdocs-state.md`），不管 `audit/**`、`backlog/<id>.md` 和规格文档。
10. 阈值和判定只在 `keel.py` 写一处，`health-lint.py` 改为调用。
11. 归档：定义块照旧搬进归档文件，状态文件保留并标「已归档」；生成区只列未归档任务；分册不设生成区。
