---
title: DevDocs 拆分为 keel 独立插件仓 + 零散 skill 仓
status: ✅ 可实施 —— Codex 三轮审查 PASS（6→6→0）；V1 已验；D1~D3 全部结清
date: 2026-09-16
scope: 仓库拓扑、三端分发、命名空间、历史重写
supersedes: 架构决策「目录名 ≡ frontmatter name，单仓 npx 分发」（AGENTS.md）
inputs:
  - 用户原话 6 条 + 3 轮对齐
  - Codex 独立方案（未读本稿，136k token 自行调研）
---

# DevDocs → `keel`

## 0. 诉求与已拍板决定

用户原话（逐字）：

> 1. 把 devodcs 流程拆出来，独立仓库
> 2. devdocs 将以插件形式安装，可以放弃 npx，支持 codex/claude code/opencode，已便更好的支持 hook 和 SOTT
> 3. devdocs 将修改历史 commit 和作者，并强推远程仓库
> 4. 剩余 skill 作为工作用 skill，支持 npx，不支持插件，也没有远程
> 5. 当前目录将变成一个"组"，放 devdocs 和 工作用 skill
> 6. devdocs 插件名称需要重新设计，以及命名空间，去掉 `ms-` 前缀

更正与决定：

| # | 决定 |
|---|---|
| a | "SOTT" = **SSOT** |
| b | 原话 4 措辞更正：**"零散的纯 skill"**，不是"工作用 skill 集" |
| c | 被 DevDocs 依赖的共享 skill 与共享约束 → **一并归插件** |
| d | 历史重写 = **去工作邮箱身份、全历史改写作者**（不筛子集、不丢历史）|
| e | "组" = **壳目录装两个独立 repo** |
| f | 现有远程 `ab300819/skills` → **改名承接插件仓** |
| g | **三端必须都支持**（Claude Code / Codex / OpenCode）—— 覆盖了"先做一端"的建议 |
| h | **工作流名 = `keel`**（龙骨：贯穿全船的主承重结构）。调用形如 `/keel:pipeline`，⛔ skill 名不带前缀 |
| i | 零散仓**接受无远程/无异地备份**（D2）|
| j | `AGENTS.md` / `CLAUDE.md` **两边各留精简版**（D3，拆法见 §8）|

## 1. 实测事实

| 项 | 值 | 来源 |
|---|---|---|
| skill 总数 | 40（`ms-*` 21）| `ls -d skills/*/` |
| `ms-` 字面 | 2372 处 / 166 文件 | `grep -ro` |
| 模板内 `/ms-xxx` | 42 处（⚠️ 复制进用户项目）| `grep skills/*/templates/` |
| git 历史 | 366 commit；工作邮箱 **16** 个 | `git log --format='%an <%ae>'` |
| 文档内活 commit SHA | **21 个 / 13 份文档** | 逐个 `git cat-file -e` 验活 |
| 三端版本 | codex 0.154.0 · claude 2.1.273 · opencode 1.18.15 | `--version` |

### 1.1 安装态：三棵树，相对链接不跨树

```
npx skills add        →  ~/.agents/skills/<name>/         （真身，81 个）
Claude Code           →  ~/.claude/skills/<name>  →  符号链接到 ~/.agents/skills/
Claude Code 插件      →  ~/.claude/plugins/marketplaces/<plugin>/skills/<name>/
OpenCode              →  扫 ~/.agents/skills · ~/.claude/skills · ~/.config/opencode/skills
```

⛔ **插件树与 `~/.agents/skills` 树之间没有可用的相对路径。** 这条决定 §4 的全部取舍。

⚠️ **旧安装会继续被发现**：`~/.claude/skills/` 下 81 个符号链接指向 `~/.agents/skills/`，
拆分后旧 `ms-*` 名仍在列表里。**必须有清理步骤**（Codex 抓到，本稿原漏）。

### 1.2 OpenCode 实测（`opencode debug skill`，83 条）

- **完全扁平，零个含冒号的名字** ⇒ `/keel:pipeline` 形式在 OpenCode **不可用**，那边只能裸名。
- 它**已经在读 `~/.agents/skills/`**，现有 40 个 skill 全部可见 ⇒ 安装 = 放进被扫描目录即可。
- `_shared` **正常加载** ⇒ 台账 §4.6（下划线不符 OpenCode 正则）**证伪，可关闭**。

### 1.3 三端插件形态

| 客户端 | skill 来源 | hook |
|---|---|---|
| Claude Code | `.claude-plugin/plugin.json` + `skills/` | 插件 `hooks/hooks.json`，`PostToolUse` |
| Codex | `.codex-plugin/plugin.json` + `skills/`（`"skills": "./skills/"`）| Codex hooks，**需信任确认** |
| OpenCode | 软链进 `~/.config/opencode/skills/` 或 `~/.agents/skills/` | `plugins/*.js`，`tool.execute.after` |

依据：`~/.codex/skills/.system/plugin-creator/scripts/create_basic_plugin.py:316,323`。

⇒ **Claude Code 与 Codex 的插件布局同形**。三端共用**同一份 `skills/`**，
⛔ **不需要 `dist/` 构建产物**（Codex 方案提了生成器，因其假设需按端改名；目录名统一后不必）。

## 2. 拆分边界

**判据（采纳 Codex）**：DevDocs 正常执行路径中**实际 slash 调用**或**读取文件**的 → 进插件；
仅作任务分流、后续推荐、历史出处的提及 → 不算依赖。

⛔ 不按相对链接计数划界——那会漏掉 slash 调用（本稿第一版即因此少算 6 个）。

### 2.1 进 `keel` 插件：21 + 12 = **33 个 skill** + `shared/`

```
21 个 ms-*（去前缀）
+ code-quality 42 · testing-guide 33 · workspace-topology 19 · adversarial-review 15
  · agent-memory 14 · ui-orchestrator 6 · commit-convention 4 · code-self-describe 4
  · git-safety 3 · doc-organization 1          ← 数字为 ms-* 侧 slash 调用次数
+ dev-flow · refactor                          ← 反向依赖，见 2.3
+ _shared  →  改为 shared/ 普通资源目录
```

**`_shared` 取消 skill 身份**（采纳 Codex）：它成为 skill 的唯一理由是 npx 一次只搬一个目录
（`_shared/SKILL.md:15` 自陈）；插件整包分发后这层包装多余。顺带消除 `_shared` 这个非常规名。

### 2.2 留零散仓：**6 个**

`e2e-test-flow` · `idea-mcp-workflow` · `markdown-style` · `prior-art-scan` ·
`python-spec` · `work-report`

它们对插件侧共 **21 处 slash 提及，全部是分流表 / 后续推荐**，零硬依赖。样本：

```
prior-art-scan:153  | 自建 | `/prd` 或 `/pipeline init`（重型）；`/dev-flow`（轻量）|
e2e-test-flow:34    不适合? 设计用例 → `/test-cases`;跑测试套件 → `/test-run`
```

⇒ **§4 原计划的"内联 2 处规则"不再需要**——需要规则正文的 skill 全部进了插件。

### 2.3 ⚠️ `dev-flow` 与 `refactor` 改判进插件（R2 修正）

本稿第一版把这两个留在零散仓，依据是 **ms-\* 侧对它们的调用**（各 2 处，属分流推荐）。
但**反方向没查** —— 同一判据应用到 `它们 → 插件侧` 后：

| skill | slash 调用 | 硬依赖原文 |
|---|---:|---|
| `refactor` | **45** | `refactor:402` 「UI 重构**必须**应用 `/ui-orchestrator` 约束」· `:403` 「**必须**应用 `/code-quality` MTE 原则」· `:404` 「重写前**必须**用 `/ms-retrofit` 建立基线」· `:242` 「编写测试时**必须**遵循 `/testing-guide`」 |
| `dev-flow` | **22** | 调 `/ms-dev-workflow` `/ms-retrofit` `/ms-dev-tasks` `/agent-memory` `/adversarial-review` `/workspace-topology` |

⇒ 它们不是"零散的纯 skill"，是 **DevDocs 生态的外围成员**。
`refactor` 用 retrofit/test-cases/system-design 做重构；`dev-flow` 是 DevDocs 的零追溯轻量版。

⚠️ **这是同一个方法论错误犯第二次**：R1 已把 `ms-* → 非 ms-` 的划界从"数相对链接"改为
"数 slash 调用"，但反方向仍在数相对链接（14 处），实际 slash 调用 **83 处**。
留作纪律：**判据一旦改了，两个方向都要重算。**

## 3. 命名

| 对象 | 名称 |
|---|---|
| 壳目录 | `/Users/mason/Projects/skills/`（无 `.git`）|
| 插件仓 | `keel`（GitHub `ab300819/skills` 改名而来）|
| 零散仓 | `skills-local`（本地，⛔ 无远程——D2 已确认接受）|
| 插件 / 命名空间 | `keel` |
| marketplace | `ab300819-keel` |
| skill 名 | **去 `ms-` 直取后缀，⛔ 不加新前缀** |

21 个：`backlog` `board` `bugfix` `codebase-insight` `compound` `dev-tasks` `dev-workflow`
`feature` `insights` `onboard` `pipeline` `prd` `prd-brainstorm` `prd-parser` `requirements`
`retrofit` `sync` `system-design` `test-cases` `test-run` `verify`

10 个共享 skill 保留原名（`dev-workflow` 与零散仓的 `dev-flow` 不同名，无冲突）。

**调用形式按端不同，⛔ 不强求统一**：

| 端 | 形式 |
|---|---|
| Claude Code | `/keel:pipeline` ✅ 目标形态 |
| Codex | `/keel:pipeline` ✅ V2b 已验：注册名就是 `keel:<name>` |
| OpenCode | `/pipeline` 裸名 —— 该端无命名空间（§1.2）|

### 3.1 V1 实测结论（2026-09-16）：**裸名可解析**

```
Skill(ponytail-help)            ← ⛔ 不带 ponytail: 前缀
→ ~/.claude/plugins/cache/ponytail/ponytail/4.9.0/skills/ponytail-help
```

该 skill 在列表里注册为 `ponytail:ponytail-help`，裸名仍解析成功。
旁证：ponytail 自己的帮助卡片把 Claude Code 的调用形式写作裸名 `/ponytail-help`。

**撞名实测**：全部安装位置（`~/.agents/skills` · `~/.claude/skills` ·
`~/.config/opencode/skills` · 全部插件 marketplace）共 **112 个 skill 名**，
与去前缀后的 21 个 **零撞车**。

⇒ **调用形式按"这个字符串会不会被当作调用执行"分两种**：

| 用途 | 形式 | 判据 |
|---|---|---|
| **给人看**：README · 安装说明 · "怎么调用 keel" | `/keel:pipeline` | 显式标归属；用户明确要求这个形态 |
| **给模型执行**：SKILL.md 里的委托与协作表 · 42 处模板 | **裸名 `/pipeline`** | ⛔ OpenCode 无命名空间（§1.2），带 `keel:` 的调用在该端直接失效 |

⚠️ **R3 修正**：本稿原按「文档 vs 模板」分轴，**错了**。SKILL.md 正文里同样有可执行委托 ——
`ms-pipeline/SKILL.md:215`「`ms-requirements` 完成后即 `Task: /agent-memory --update`」，
全仓 14 处 `Task: /xxx` 形式，外加 `ms-dev-workflow:195` 那张阶段协作表。
照原分轴改写会把 `/keel:agent-memory` 写进执行路径，**在 OpenCode 上直接断**，
与「三端必须都支持」冲突。

⇒ 正确判据是**给人看 vs 给模型执行**，⛔ 不是文档 vs 模板。

⚠️ **裸名是便利不是契约**：`spec/claude-skill-spec.md:86` 写「Plugin skills use a
`plugin-name:skill-name` namespace, so they cannot conflict with other levels」——
暗示撞名时带命名空间的形式才可靠。⇒ 一旦某个名字真撞了，**给那一个改名**
（⛔ 不预先给 21 个都加前缀，那等于把 `ms-` 换成 `keel-`，与决定 h 冲突）。

## 4. 22 处跨界残留的处置

按 §2.3 改判后，零散仓 6 个 skill 对插件侧共 **21 处 slash 提及 + 1 处相对链接**，
**全部是分流推荐或可选集成，零硬依赖**：

| 类别 | 处 | 处置 |
|---|---:|---|
| 分流表 / 后续推荐（`prior-art-scan` 12 · `e2e-test-flow` 6 · `markdown-style` 3）| 21 | 改为文字说明："若已装 keel 可用 `/keel:xxx`" |
| `workspace_context` 契约（`e2e-test-flow:48`）| 1 | 删链接，**保留 fallback**——原文已写「未传入时按 inline 缺省」，依赖本就可选 |

**⛔ 零内联。** 本稿第一版要内联 2 处规则正文，是因为当时把 `dev-flow`/`refactor`
错留在零散仓；它们改判进插件后，规则与消费方同侧，不产生副本。

⇒ **"零散的纯 skill"这个定性现在真正成立**：6 个 skill，零硬依赖，装不装 keel 都能跑。

## 5. 执行顺序

> 不可逆的放最后，待验项挡在前面。

| 阶段 | 动作 | 验收 |
|---|---|---|
| ~~**0 前置验证**~~ | ~~V1~~ | ✅ 已通过（§3.1），不再阻塞 |
| **1 冻结与备份** | `git bundle create --all`；记录远程全部 refs 与 `main` 的 oid；备份 `~/.agents/skills` 与三端配置 | `git bundle verify` 通过；能从备份恢复出全部 refs |
| **2 拆仓 + 改名**（可逆）| clone 两份；各删对侧 skill；`_shared` → `shared/`；21 目录去前缀 + frontmatter + 2372 处字面分类处理；建三端 manifest | `health-lint --skills-dir` 两侧 `skill/name-mismatch` + `skill/dead-link` 均 0 blocker |
| **3 接断链** | 按 §4 处置 22 处 | 两侧无跨仓可解析链接；6 个零散 skill 在**未装 keel** 时全部可独立运行 |
| **4 hook 三端适配** | 公共检查逻辑一份 + 三个薄适配层 | 各端真实会话触发一次（⚠️ 现有两个 hook 自陈未跑过，本次是首次实测）|
| ~~**4b 三端调度验收**~~ | ✅ 已通过（2026-09-16，见 §5.1）| —— |
| **5 历史重写**（⛔ 不可逆）| 在 `--mirror` 副本上 `git filter-repo --mailmap`；**再用 `commit-map` 回填 13 份文档里的 21 个 SHA** | 身份唯一；366 节点不变；tree 与父子关系逐提交相同；21 个 SHA 全部解析成功 |
| **6 远程切换**（⛔ 不可逆）| `gh api --method PATCH repos/ab300819/skills -f name=keel`；`git remote set-url`；`--force-with-lease` 按冻结时 oid 逐 ref 推 | 新 clone 的 refs 与发布清单一致；身份复查通过 |
| **7 本地换位** | 旧工作区移走并**禁用其 push**；建壳目录；放两个仓；**按迁移清单清理旧安装**（见下）；三端重装 | 壳内无 `.git`；零散仓 `git remote -v` 为空；**三端新会话里旧 `ms-*` 名全部消失**；三端各自能发现 33 个 skill；**42 个非本仓 skill 不受影响** |

#### 5.1 阶段 4b 实测结论（2026-09-16）

**裸名在三端都能解析**，但三端的机制各不相同：

| 端 | 注册名 | 裸名 `/requirements` 实测 |
|---|---|---|
| Claude Code | `keel:requirements` | ✅ V1（§3.1） |
| Codex CLI | `keel:requirements` | ✅ 加载到 `keel:requirements`（`codex exec` 真跑） |
| OpenCode | `requirements`（**零命名空间**）| ✅ `Skill "requirements"` 调用成功 |

⚠️ **一个反例值得记下**：同一个 Codex，如果 prompt 要求「把 `/requirements` 映射成清单里的
**精确标识符**」，它会答「解析不到」——清单里只有 `keel:requirements`。**自然委托语境下才解析得动。**
⇒ 裸名在 Codex 上靠的是语义匹配，不是字面查表；§3.1 的「裸名是便利不是契约」在这一端尤其成立。

同批验证：`skills/shared/` 随插件整包分发，`skills/pipeline/../shared/constraints.md`
在 Codex 插件缓存里解析成功 ⇒ §2.1 把 `shared/` 留在 `skills/` 下的取舍成立。

⚠️ 三端实测同时复现了 §1.1 的旧安装问题：OpenCode 注册表里 22 个旧 `ms-*` 仍在。

#### 阶段 7 的旧安装清理（R2 修正，原"清理 81 个符号链接"两头都错）

实测布局：

```
~/.agents/skills/ms-pipeline              drwxr-xr-x   ← 真身目录
~/.claude/skills/ms-pipeline  ->  ../../.agents/skills/ms-pipeline   ← 软链
```

- ⛔ **只删 Claude 侧软链不够**：OpenCode 直接扫 `~/.agents/skills/`（§1.2），
  真身还在就仍能发现旧 `ms-*`。Codex 同理需单独核。
- ⛔ **不许一把删 81 个软链**：实测其中 **42 个不属于本仓**（`baseline-ui` / `defuddle` /
  `lark-*` 等），误删会打掉无关能力。

⇒ **按原仓 40 个目录建迁移清单逐项处理**：删 `~/.agents/skills/` 下对应的 40 个真身，
再删三端指向它们的入口；⛔ 清单外一律不动。验收要同时确认「旧名消失」与「非迁移 skill 仍可发现」。

⛔ **`--preserve-commit-hashes` 只改提交信息里的 SHA，改不到受控文件** ——
阶段 5 的"回填 21 个 SHA"是独立一步，两份方案原本都漏了。

## 6. ⚠️ 必须直说的代价

1. **全历史保留 ⇒ 零散 skill 的过去仍在 `keel` 远程历史里。** 只有最新树移出它们。
   要求"历史里也没有这些文件"就是筛历史，与决定 d 冲突。
2. **强推不能让工作邮箱从互联网彻底消失。** 已有 fork / clone / PR 引用 / 平台缓存不受控。
   能验收的只是"新发布 refs 可达提交里身份干净"。
3. **旧 URL 重定向是隐患不是保护。** 改名后旧地址 git 操作仍可能生效 ⇒ 旧工作区必须禁 push，
   且 ⛔ 不得重新创建 `ab300819/skills`。
4. **纯 skill 不等于零依赖。** `dev-flow` / `refactor` 的质量门规则来自插件侧；
   §4 选择内联那 2 处、其余降级说明，代价是它们在未装 keel 时功能略弱（明确提示，不静默降级）。
5. **OpenCode 端拿不到命名空间**，调用与另两端不同字符串（§3）。
6. **零散仓无远程 ⇒ 无异地备份**（D2 待你确认接受）。

## 7. 待验 / 待决

- ~~**V1**~~ —— **已验通过（2026-09-16）**，结论见 §3.1。阶段 2 解除阻塞。
- ~~**V2b**~~ —— **已验通过（2026-09-16）**：`codex debug prompt-input` 显示 33 个 skill
  全部注册为 `keel:<name>`，Codex **支持**冒号命名空间。
- ~~**D2**~~ —— **已定：接受**。零散仓无远程、无异地备份，误删不可恢复。
  ⚠️ 阶段 1 的 `git bundle` 备份因此是该仓**唯一**的历史保险，⛔ 不得省略。
- ~~**D3**~~ —— **已定：两边各留精简版**，拆法见 §6。

## 8. `AGENTS.md` / `CLAUDE.md` 拆法（D3）

现状 56 行 6 节。`CLAUDE.md` 为 7 行（`@AGENTS.md` 导入 + Claude Code 补充区），两边各留一份同形。

| 节（现行数）| keel 侧 | 零散仓侧 |
|---|---|---|
| 架构决策（5）| 留，改 `ms-*` 名与路径 | **精简**：只留「目录名 ≡ frontmatter `name`」「`templates/` `references/` 用途」。⛔ 删「编排层通过子代理调度原子 skill」——零散仓无编排层 |
| 修改 skill（9）| 全留 | **精简**：留 description 写法、正文保留目标与边界。⛔ 删 ROI 判据与跨 skill 协议条款——那是 DevDocs 规格治理 |
| 工作流路由（15）| 全留 | ⛔ **整节删**。原文是「⛔ 不在此启动 DevDocs 全流程」「本仓元开发没有 process owner skill」，零散仓没有 DevDocs |
| 验证（5）| 全留 | **精简**：留 `git diff --check` 与 `SKILL.md ≤ 500 行`。⛔ 删 health-lint 相关（见下） |
| 约定（4）| 全留 | 全留（Conventional Commits + 中文回复）|
| 按任务查阅（6）| 留，指向 keel 自己的 `docs/` | ⛔ **整节删**——零散仓无 `docs/`；如需索引改为一行指 README |

⇒ 零散仓 `AGENTS.md` 约 **15~20 行**。

⚠️ **连带损失**：`health-lint.py` 在 `ms-pipeline/scripts/` 下，随 keel 进插件 ⇒
零散仓失去 `skill/name-mismatch` · `skill/size-cap` · `skill/dead-link` 自检。
**判为可接受**：6 个 skill、彼此零耦合、无跨 skill 链接，人工核对成本低于维护脚本副本。
⛔ 不拷贝脚本。触发重评：零散仓 skill 数显著增长，或真出现名称/链接问题。

## 9. ⛔ 不做

- ⛔ 不建 `dist/` 构建产物（§1.3：三端共用一份 `skills/` 即可）
- ⛔ 不为跨仓引用造解析机制（§1.1 是结构约束）
- ⛔ 不预先给 skill 加防撞前缀（§3：真撞了再改那一个）
- ⛔ 不在本批做 `ms-verify` 拆分等未决项（台账 §4.3），一次只动拓扑
