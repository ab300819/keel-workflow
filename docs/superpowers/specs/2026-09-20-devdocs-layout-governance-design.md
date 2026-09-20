---
title: devdocs 布局治理——命名语法、权威清单、尺寸规则
status: 📐 设计稿，待实施
date: 2026-09-20
scope: devdocs 文件命名、权威清单 SSOT、尺寸阈值、存量迁移、SessionStart hook
inputs:
  - 用户原话 4 条 + 4 次 AskUserQuestion 裁定
  - 17 个真实项目 devdocs 目录实测
related:
  - docs/superpowers/specs/2026-09-11-devdocs-object-model-convergence-v2-design.md（已封存，§6 文档结构与本稿相邻但不重叠）
  - docs/superpowers/specs/2026-08-31-layout-v2-goal-attainment-design.md（原则 2「主文件只记索引」）
---

# devdocs 布局治理

## 0. 诉求与已拍板决定

用户原话（逐字）：

> 1. 我有个发现，devdocs 目录下文档有点乱，第一命名格式不统一，第二没有全局的索引控制，第三部分文档可能过大
> 2. 应当由 keel 做检测，然后进行迁移，而且在当前会话进行
> 3. 我在思考 hook 机制，以及 rule 能为优化带来什么？或者整个 keel 流

四次裁定：

| # | 问题 | 裁定 |
|---|---|---|
| 1 | 哪个场景在咬人 | **四个全中**：存量大项目读不动 · 新项目一开头就歪 · Agent 定位错文件 · 人找不到文件 |
| 2 | 迁移触发时机 | 开工时自动检测，**当场问**要不要迁，同一会话跑完 |
| 3 | 自动迁移的权限边界 | **只改名 + 归档移位**（`git mv` 级），⛔ 不自动拆分内容 |
| 4 | hook 范围 | **只进 `SessionStart`**，`PostToolUse` 防漂移本轮不做 |

## 1. 现状与根因

### 1.1 三个症状是一个根因

没有「多大该拆、拆完叫什么」的规则 → 文档涨到读不动时临时拆 → 每次拆各起各的名 → 文件多到找不着 → 才冒出索引需求。

**症状 ① 和 ③ 是因果两端，② 是后果。**

### 1.2 命名混乱在规范层，不只是项目漂移

`docs/devdocs/` 里现在并存四套命名，全部由 skills 正式写出：

| 形态 | 实例 | 产出方 |
|---|---|---|
| 编号型 | `01-requirements.md` … `05-insights.md` | requirements / system-design / … |
| 裸名型 | `backlog.md` · `verify-report.md` · `readiness-report.md` · `schema-drift-report.md` | backlog / verify |
| 隐藏型 | `.health-report.md` · `.batch-checkpoint.json` | pipeline |
| 目录型 | `adr/` · `audit/` · `bugs/` · `insights/` · `patterns/` · `archive/` | 多个 |

`docs/architecture.md` 的「文件结构」块**列了 10 项，skills 实际写出 ≥18 种路径**。缺的那份权威清单本该是它，它已经过期。后果：每个 skill 自己发明路径，没人对账。

⚠️ **`05` 段同时挂 test-report / insights / bugfix-log 不是缺陷**——三者同属收尾段。但规则从没写清「`NN` 是段不是文件序号」，于是 codex-mcp 自行顺延发明了 `06-test-report.md`。

### 1.3 尺寸不是「零机制」，是「测错了东西 + 没人跑」

`sync/references/archive.md` 已有归档阈值，但按**行数**：

| 文件 | 行数 | 字节 | 平均每行 |
|---|---|---|---|
| tm-reborn `01-requirements.md` | 620 行 | 28 KB | 46 B |
| mic-en `01-requirements.md` | 556 行 | **160 KB** | 288 B |

⛔ **行数阈值测错了东西。** 按「需求 > 400 行」这把尺子，28 KB 的文件比 160 KB 的更超标，差 5.7 倍的原因是后者全是宽表格。而痛点是「读一个文件把上下文预算吃光」——预算按 token 算，不按行算。隔壁 `state/total-size-cap` 用的正是字节。

第二个断层：`realign --scope=health` 维度 c 名为「过大文档识别」，但挂的三条规则（`state/total-size-cap` / `state/line-length-cap` / `state/forbidden-content`）**全部只作用于 `.claude/rules/devdocs-state.md`**，devdocs 正文一条都不管。这就是 400 KB 的 `02-system-design.md` 从没被报过的原因。

### 1.4 存量分布

17 个 devdocs 目录，**近两周还在动的只有 3 个**：tm-reborn（21 文件/340 KB）· dji-4g（9 文件）· file-server-dev（7 文件）。最大的 mic-en-legacy（59 文件/7.8 MB）名字就带 legacy，最后改动 6 月 25。

这个分布是本设计敢做迁移的前提：迁移面小。

## 2. 方案选型

| 方案 | 内容 | 裁定 |
|---|---|---|
| **1 清单驱动** | 一份 SSOT 清单，retrofit / health-lint / 各 skill 三方消费 | ✅ **采用** |
| 2 规则驱动 | 不做清单，health-lint 里硬编合法名正则，skill 路径维持各写各的 | ❌ 清单仍散着，正则与 skill 正文是两处真源，下次加新产物照样漏——现状的加固版，不是修复 |
| 3 换布局 | `changes/<ID>.md` + `verification/` + `tasks/` + `evidence/` | ❌ 封存稿已判「迁移成本过高暂缓」，且需重切全部内容，超出裁定 3 的授权 |

## 3. 命名语法

**不发明新体系**——现有四套命名其实有一套潜规则，只是从没写下来。本节把它命名下来并补掉缺口。

| 载体 | 语法 | 含义 | 合规实例 |
|---|---|---|---|
| 阶段主文件 | `NN-<name>.md` | `NN` 是**流程段**，⛔ 不是文件序号 | `01-requirements.md` |
| 分册 | `NN-<name>-<key>.md` | `<key>` 须表意，且须在主文件登记 | `03-test-unit.md` |
| 跨阶段 / 一次性产物 | `<name>.md` | 不属任何单段，不带号 | `backlog.md` · `verify-report.md` |
| 机器状态 | `.<name>.<ext>` | 不给人读，排除扫描 | `.health-report.md` |
| 归档 | `archive/<原名>-archive.md` | sync 已这么定，存量在根目录需迁 | — |

### 3.1 `NN` 是段，不是序号

同段可挂多个文件（`05` 段的 test-report / insights / bugfix-log 均合法）。**自造段号即违规**，可检测。

### 3.2 分册键：表意 + 登记

原设计写的是「键须来自受控键集」，**已撤回**。受控键集要预先枚举，而 `02-system-design` 的键封存稿也没枚举出来；硬编一个现在编得出来、但会编错。

改为两条，都机器可查：

- `layout/unregistered-split`：分册文件名没在主文件正文里出现过 → 报
- `layout/ordinal-key`：键匹配 `^[a-z]?\d+$` 或单字母（`p1` / `a` / `b`）→ 报

**依据是现实而非发明**：`04-dev-tasks.md` 与 `03-test-cases.md` 已自发在主文件列出分册目录（带编号区间 / 数量）；`02-system-design.md` 有 `-api` / `-data` 两个分册却零登记——正是「拆了找不到」的具体形态。规则只是把已有的好做法固化。

mic-en 那 19 个 `-p1`~`-p19` 分册正是 `ordinal-key` 形态：没人知道哪册装什么。

> ⚠️ **本节比原方案弱**：不保证键正交（对象模型那套才保证）。这是用便宜一个数量级换来的，明示为已知代价。

## 4. 权威清单与消费契约

### 4.1 落点

`skills/shared/devdocs-layout.md`。

- 消费方全在 `skills/` 里，`shared/` 是跨 skill 共享资源的既定家（`constraints.md` / `runlog.md` 同处）
- ⛔ 不放 `constraints.md`：该文件已 559 行，且装的是**规则**；文件清单是**结构事实**，混入会稀释

### 4.2 内容

四块：四类载体语法（§3）· 合法文件全表（文件 × 产出方）· 分册登记规则 · 尺寸阈值（§5）。

### 4.3 三个消费方

| 消费方 | 用法 | 现状 |
|---|---|---|
| `retrofit` M1 规范检查 | 当检测表，比对实际文件 → 出迁移清单 | 硬编了几个例子，没有表 |
| `health-lint.py` | 当 rule 的数据源（合法名 / 阈值） | 完全不管 devdocs 正文 |
| 各产出 skill | 当落盘路径的权威 | 18 处各写各的 |

### 4.4 防复发

⛔ **任何 skill 新增一种 devdocs 产出，必须先进清单。**

今天这个缺陷的成因就是 `verify-report.md` / `.health-report.md` / `schema-drift-report.md` 是各 skill 自己长出来的，从没人汇总——所以架构文档的文件结构块才会只列 10 项而实际有 18 种。

### 4.5 连带改动

`docs/architecture.md` 的文件结构块改成指向清单的一行。留着它就是第二处真源，而它**已经证明会过期**。

## 5. 尺寸规则

- **单位换字节**（依据见 §1.3）
- **一档警告，⛔ 不设阻断**，阈值 **96 KiB**
- 警告出口接到已有动作：超阈值 → 报警 + 建议跑 `/sync --archive`（它有真实的自动减量动作）；分不分册、怎么分当场问用户

按 96 KiB 校准的实测结果：

| 项目 | 命中 |
|---|---|
| tm-reborn（活跃） | 0 个（最大 61 KB，且已按 `-ui`/`-core`/`-infra` 表意分册，正面样本） |
| mic-en-legacy | `02`(400 KB) · `03-test-unit`(215 KB) · `01`(160 KB) · `04`(135 KB) |

⛔ **不设阻断的理由**：裁定 3 只授权改名 + 归档移位，未授权自动拆分；而 `02` / `00-context` / `backlog` 的分册键封存稿明说未解。设一个 ⛔ 就是造一个**用户被卡住却没有解法**的门。

### 5.1 连带改动：消掉第二处尺寸真源

`sync/references/archive.md` 的「行数阈值」列**删除**，改为引用清单的字节阈值。不删则尺寸标准有两处真源——正是本设计在治的病。

该表的「数量阈值」与「状态条件」两列**保留**：它们是**归档的语义触发器**，与尺寸警报是两件事，分工在清单里写清。

## 6. 迁移执行

复用 `retrofit` 的 M1-M4（规范检查 → 差异清单 → 执行 → 报告），⛔ 不新建工具。该路径本就定义为「检测到已有 keel 文档但不符合当前规范时执行」，`git mv 03-test-plan.md → 03-test-cases.md` 是它现成的例子。

**动作只有两种**，都是 `git mv`：改名、移进 `archive/`。

触发链：`SessionStart` hook 扫描 → 命中则一行提示 → 用户点头 → retrofit M1-M4 → 单独 commit。

安全约束沿用现成的，⛔ 不新造：

- `confirm/destructive-change`（constraints §5）——重命名 / 移动前必须用户确认
- realign 安全不变量——工作区洁净才能跑、每阶段单独 commit 便于回滚

### 6.1 一条纪律

⛔ **机械判不出归属的，只列清单问用户，不猜。**

例：`T-31-a11y-interactive-checklist.md`，keel 不知道它该叫什么。猜一个改过去等于静默丢失信息。

### 6.2 对 tm-reborn 的实测预测（可验证）

| 文件 | 判定 | 动作 |
|---|---|---|
| `06-ui-hig-swiftui-checklist.md` | 自造段号 | 问用户归哪段 |
| `T-31-a11y-interactive-checklist.md` | 不属任何载体 | 问用户 |
| `02-system-design.md` | 有 2 个分册但主文件未登记 | ⚠️ 只警告 |
| 其余 18 个 | 合规，尺寸全通过 | 不动 |

一个跑了几个月的活跃项目，迁移面是 **2 个要问 + 1 条警告**。该量级是设计未跑偏的证据。

## 7. hook

### 7.1 分工

**rule = 权威 + 覆盖 + 可测；hook = 送达。** 两者是一件事的两半，不是两个方案。

现状的病正是只有一半：维度 c 的规则装了，但要人主动敲 `/pipeline realign --scope=health` 才跑。`realign-scope-health.md` 自己写了这个断层——原话「解决"规则实装但没人跑"的断层」。

hook 治的是**一类特定病：该跑的没跑**。⛔ 它治不了别的。

### 7.2 本设计只用 `SessionStart`

新增 `hooks/devdocs-layout`：开工时扫描 → 命中则一行非阻塞提示 → 接 §6 触发链。keel 现在**完全没用过 `SessionStart`**，是空槽。

`PostToolUse` 防漂移（文件刚落盘就判名字）价值更高——它防止漂移而非事后清理，tm-reborn 那个自造段号会在出生那一秒被抓住——但**本轮不做**（裁定 4），理由是常驻成本需单独算账。

### 7.3 四条硬限制

1. ⛔ **OpenCode 没有 `additionalContext` 通道。** 三端里只有 Claude Code 与 Codex 能收 hook 提示。故 **hook 不能是唯一载体**，清单 + rule 必须独立成立，hook 只是加速器；否则 OpenCode 用户拿到的是不设防的规范。
2. ⛔ **`PostToolUse` 在写完之后才跑**，只能提示不能拦。要真拦需 `PreToolUse`，那是阻断级，超出授权，且会让 agent 卡在半路没有出口。
3. ⛔ **不挂在 `devdocs-drift` 上。** 该文件头明写：「试验件。验不过就删，⛔ 不要在它之上加功能。」布局检查另起一个 hook。
4. ⚠️ **hook 是常驻成本。** 现役两个 `PostToolUse` hook 都被迫加冷却戳（5 分钟 / 2 分钟）才没变噪声；且有实测教训：hook 常驻会让验收结果混叠。加 hook 按个算账，⛔ 不按批加。

### 7.4 冷却与静默

沿用现役形态：非 keel 项目（无 `docs/devdocs/`）静默退出；戳文件置于 `.git/`；`SessionStart` 天然低频，⛔ 无需 `PostToolUse` 那种分钟级冷却。

## 8. 改动面

| # | 文件 | 动作 |
|---|---|---|
| 1 | `skills/shared/devdocs-layout.md` | **新增**——清单 + 语法 + 阈值 |
| 2 | `docs/architecture.md` 文件结构块 | 改指针，消第二处真源 |
| 3 | `skills/pipeline/scripts/health-lint.py` | 加 4 条 rule + selftest 夹具 |
| 4 | `skills/pipeline/references/health-lint-implementation.md` | Rule 集表登记新 rule |
| 5 | `skills/pipeline/references/realign-scope-health.md` | 维度 c 扩到 devdocs 正文；命名归维度 a |
| 6 | `skills/sync/references/archive.md` | 删「行数阈值」列 → 引用清单 |
| 7 | `skills/retrofit/references/version-migration.md` | M1 检测表 → 引用清单 |
| 8 | `hooks/devdocs-layout` + `hooks/hooks.json` | **新增** `SessionStart` |
| 9 | 18 处 skill 落盘路径 | 只核对是否已在清单，发现矛盾才改 |
| 10 | `plugin.json` + `.claude-plugin/plugin.json` | version bump（不 bump 则分发空转） |

约 10 个文件。对比封存的对象模型方案（50+ 文件跨 21 个 skill，因此被封存）——规模差一个数量级，是两件事可以拆开做的证据。

### 8.1 新增 rule 清单

| rule_id | 严重度 | 检测 |
|---|---|---|
| `layout/illegal-name` | ⚠️ | 文件名不匹配四类载体任一语法（含自造段号） |
| `layout/unregistered-split` | ⚠️ | 分册文件名未在主文件正文出现 |
| `layout/ordinal-key` | ⚠️ | 分册键为纯序号 / 单字母 |
| `layout/size-cap` | ⚠️ | devdocs 正文 `.md` > 96 KiB |

四条全为 ⚠️，⛔ 无 blocker（理由见 §5）。

## 9. 非目标与诚实残留

### 9.1 非目标

⛔ 不改编号对象模型（封存稿范围）· ⛔ 不自动拆分大文件 · ⛔ 不做项目内 `index.md` · ⛔ 不定 `02` / `00-context` / `backlog` 的分册键 · ⛔ 不碰 version-bump 检测 · ⛔ 不设阻断级门 · ⛔ 不做 `PostToolUse` 防漂移

### 9.2 为什么不做项目内 `index.md`

命名语法一旦定死，`ls` 排出来的就是索引；再加一个文件反而多一个会漂的东西。`ls` 唯一解决不了的是「分册后哪册装什么」，该职责由主文件的分册目录承载（§3.2），主文件本就是入口。

这与 layout.v2 原则 2「主文件只记索引」一致——该原则的目标已被判定达成，手段不同。

### 9.3 诚实残留

- `02-system-design` / `00-context` / `backlog` 的分册键仍未解，与封存稿 §6.2 的结论一致。超阈值只报警，怎么拆当场问用户。
- 分册键不保证正交（§3.2）。
- `mic-en-legacy` 等 14 个不活跃目录不迁，⛔ 也不报错。回头再挖它们时仍然难用——这是裁定 1 的既定代价。

## 10. 验证方式

本仓无统一 build/test/lint，按 AGENTS.md 的验证要求逐项：

| 改动类型 | 验证 |
|---|---|
| `health-lint.py` 新 rule | selftest 夹具红绿各一（先构造违规文件证明会报，再修正证明不报）；⛔ 格式检查不算 |
| 新 rule 的 delta 行为 | 确认 `--since-baseline` 不吞掉新 rule 的首次报告 |
| `hooks/devdocs-layout` | `bash -n` 语法检查 + 三种输入实测：非 keel 项目（须静默）· 合规项目（须静默）· tm-reborn（须报 2 项） |
| 清单与消费方 | 生产方 / 消费方同时核对；18 处落盘路径逐一比对清单 |
| 分发配置 | version bump 后确认注入版本，⛔ 不改 version 则 push 与 update 全空转且零报错 |
| 文案改动 | `git diff --check` |

⚠️ **端到端行为须用代表性任务实测**：在 tm-reborn 上跑一次完整触发链（SessionStart 报告 → 确认 → retrofit 迁移 → 复扫归零）。未能实测的部分明确说明。

## 11. 与封存稿的关系

`2026-09-11-devdocs-object-model-convergence-v2-design.md` 已于 2026-09-15 封存，`reactivate_when: 第二个项目在技术升级/重构/治理上撞同一堵墙`。

**本稿不 reactivate 它。** 那份稿的主体是**编号对象模型**（`F` 的字段、`AC.kind`、`CHK.level`、追溯链），封存理由是该主体要改 50+ 文件跨 21 个 skill。它的 §6「文档结构」只是次要范围，且自陈「三个最大的文件本设计都没解」。

本稿只取文档结构这一维，且用「表意 + 登记」替掉「对象模型字段做键」，故与封存主体不冲突、不依赖、不解锁。封存稿的 `reactivate_when` 仍然有效，本稿不满足其触发条件。
