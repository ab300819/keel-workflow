---
title: devdocs 文档健康检查——检测器修复、死规格清理、双形态存储裁定、布局清单
status: 📐 设计稿 v4（v1/v2/v3 三个骨架均已推翻），P0 已实施，P1~P4 待实施
date: 2026-09-20
supersedes: 本文件 v1（0722126）、v2（cf4749e）、v3（20cd84f）
scope: health-lint 误报修复、health 规格死引用清理、存储模型裁定、布局清单 SSOT、三条检测规则、SessionStart 触发点
inputs:
  - 用户原话 4 条 + 6 次裁定
  - 17 个真实项目 devdocs 实测
  - Codex 三轮独立调查/评审（均禁读本稿），结论全部逐条复核
related:
  - docs/superpowers/specs/2026-08-31-layout-v2-goal-attainment-design.md（layout.v2 删除决策，⛔ 不推翻）
  - docs/superpowers/specs/2026-09-11-devdocs-object-model-convergence-v2-design.md（已封存，⛔ 不 reactivate）
---

# devdocs 文档健康检查

## 0. 诉求

用户原话（逐字）：

> 1.「我有个发现，devdocs 目录下文档有点乱，第一命名格式不统一，第二没有全局的索引控制，第三部分文档可能过大」
> 2.「应当由 keel 做检测，然后进行迁移，而且在当前会话进行」
> 3.「我在思考hook机制，以及rule 能为优化带来什么？或者整个keel 流」
> 4.「我的原本意思是keel可以做一次文档健康检查，决定下一步要干什么」

⛔ **第 4 条是权威表述**，前三条是症状面。

| # | 裁定 |
|---|---|
| 1 | 痛点四项全中：存量读不动 · 新项目一开头就歪 · Agent 定位错文件 · 人找不到文件 |
| 2 | 开工时自动检测，**当场问**，同一会话跑完 |
| 3 | 自动动作**只改名 + 归档移位**，⛔ 不自动拆分内容 |
| 4 | hook **只进 `SessionStart`** |
| 5 | 骨架错了就重写，⛔ 不局部修补 |
| 6 | 闭环做到**检查 → 决策 → 执行 → 复查** |
| 7 | 存储模型：**两套都合法，按规模转**（见 §3）|

## 1. 三次骨架错误的复盘

| 版本 | 骨架 | 被什么推翻 |
|---|---|---|
| v1 | 新建命名法规 + retrofit 迁移 | `ordinal-key` 会把现役契约 `04-dev-tasks-pNN.md` 判违规；主从关系不能靠连字符反推 |
| v2 | 实现 `realign --scope=layout` | `layout` 是 `e7c6771` 删除后的残留引用，不是预留空槽 |
| v3 | 三条检测挂现役 health 维度 | 方向对，但**前提塌了**：现役检测器在一个样本上 98% 误报；减量出口 `/sync --archive` 零项目验证过；四组权威源冲突未处理 |

⛔ **共因**：先设计，后查现状；三次都由外部证据纠正，无一次自查发现。

⇒ v4 的组织方式改变：**按依赖排序的工作项**，每项都先有实测事实再有动作。

## 2. 实测基线

全部可复现，命令与样本在 §8。

| 事实 | 数据 |
|---|---|
| 现役检测器**在大规模误报** | dji-4g 422 blocker 中 **416 条**同一误报；缩进定义漏认率 dji 70% · mic-en 27% · tm-reborn 0% |
| `/sync --archive` **从未执行过** | 17 个项目里 `archive/` 目录数 = **0** |
| health apply **真跑过** | mic-en `47252f3`：state 214 KB → 43.7 KB，修 30 条路径；但报告写的是「post-apply **估算**总分」，非完整重扫；当前 state 又涨回 58 KB |
| 推的探针**对正文失明** | 只 `stat` `devdocs-state.md`，不碰 devdocs 正文 |
| 命名 / 目录登记 / 正文体积 **零现役 rule** | project scope 实现 6 条，无一涉及 |
| 维度 a **对普通 inline 项目零可执行检测** | 未实现的两条 `design/adr-only-revision`（语义）、`submodule/pointer-drift`（仅 shell）正好都在维度 a |
| 索引**并非没有** | mic-en 有 6 个 `index.md` + `00-context.md §8`；缺的是**登记与实际文件集合一致**的约束 |

## 3. 存储模型裁定（裁定 7）

### 3.1 四组「冲突」的真相

`agent-memory/templates/devdocs-state-template.md:61` 声明资源目录为权威源，而生产方 skill 写集中文件：

| 对象 | 生产方 | state 模板 |
|---|---|---|
| ADR | 设计文档的 ADR 节 | `adr/ADR-NNN.md` + `adr/index.md` |
| INS | `05-insights.md` | `insights/INS-NNN.md` + 索引 |
| BUG | `05-bugfix-log.md`（追加）| `bugs/BUG-NNN.md` + 索引 |
| Backlog | `backlog.md`（声明唯一 SSOT）| `backlog/NN-<slug>.md` |

⛔ **这不是新旧残留**。资源目录模型引入于 `0054e99`（2026-05-25），比 layout.v2 删除（2026-08-31）早三个月，动机是「治本 100k+ 膨胀」——独立理由。

### 3.2 实测：两套各自在其规模区间都对

| | mic-en（360 md）| tm-reborn（活跃，22 md）|
|---|---|---|
| BUG | `bugs/` **122 文件** | `05-bugfix-log.md` 2.3 KB |
| INS | `insights/` 33 文件 | — |
| ADR | `adr/` 30 文件 | — |
| Backlog | `backlog/` 16 文件 | `backlog.md` 5.4 KB |
| 集中文件 | 全部缩成 1~2 KB 指针 | 完全够用 |

mic-en 的 `04-backlog.md` 原文：「**本文件已采用一文件一资源结构**」。

⇒ **mic-en 不是没守规范，是撞到规模上限后自己迁移了**，方向正是 state 模板所指。缺的从来不是「哪套对」，是**没人说过什么时候该转、谁来转**。

### 3.3 裁定

**两套形态都合法。** 清单为这四类资源各登记两行；超尺寸阈值时报「建议转资源目录」。

⛔ **转换动作不自动执行**——它是内容迁移，违反裁定 3。由用户触发。

⛔ **本稿不建「两形态并存」检测**。mic-en 当前正是并存（集中文件退化为指针），合法；区分「合法指针」与「半迁移残局」需要启发式，等它真咬人再说。

## 4. 工作项（按依赖排序）

### P0 · 修检测器误报 ✅ 已实施（`35a4da8`）

`health-lint.py:30` 的 `DEF_LIST` 正则 `^[-*]` 要求列表符号顶格，而 `- **US-001**` 下嵌套的 `  - **AC-001**` 是写验收标准的常规形状，缩进一层即判「无定义」。

改为 `^\s*[-*]`。红绿验证：先加夹具复现（缩进的 `AC-010` 被误报成第 4 条 dead-link）→ 改正则 → 三样本实测。

| 样本 | 修前 blocker | 修后 |
|---|---|---|
| **tm-reborn（对照组）** | 9 | **9**（不变，证明改动是外科式的）|
| dji-4g | 422 | **6** |
| mic-en-legacy | 529 | 485 |

⚠️ **代价明说**：放宽定义识别，会让「列表里提到但其实没定义」的编号不再报——用假阴换掉 70% 的假阳。

**为什么排第一**：P3 要往这个检测器加三条规则。在 70% 漏认的底座上加规则，新信号会淹进噪音，且无法分辨新规则是真报还是又一个误报。

### P1 · 清死规格（6 处）

⛔ 纯清理，不加功能。这些是历次删除的残留，与本诉求无关但挡路——不清，P3 会照着矛盾的规格写。

| 死规格 | 位置 |
|---|---|
| 维度 d 已废弃，`--apply` Phase 2 仍执行它 | `realign-scope-health.md:51` ↔ `:226` |
| `layout` 残留 4 处 | `pipeline/SKILL.md:81` · health scope `:144` `:146` `:279` |
| 声明三维，正文仍写「完整四维扫描」 | health scope `:25` ↔ `:43` |
| 扫描范围列 `docs/prd/**`，脚本只收 devdocs | health scope `:92` ↔ `health-lint.py:451` |
| `--changed-only` 规格写「变更行」，实现按变更文件 | health scope `:68` ↔ `health-lint.py:719` |
| sync health-scoring 引用已移交的 `--schema-drift` | `health-scoring.md:9` |

### P2 · 存储模型裁定 ✅ 已裁定

见 §3。⛔ 不改四个生产方 skill 的落盘行为，⛔ 也不删 state 模板那套——两者都进清单。

### P3 · 布局清单 + 三条检测

#### 清单落点

`skills/shared/devdocs-layout.md`（`shared/` 是跨 skill 共享资源既定家；⛔ 不放已 559 行的 `constraints.md`——它装规则，清单是结构事实）。

三列：**相对路径模式 / owner / 主文件**。

⛔ **主文件列允许为空**，只有生产方明确声明过分册的才填：

| 有声明 | 证据 |
|---|---|
| `01-requirements-{stories,nfr}.md` → `01-requirements.md` | `requirements/SKILL.md:242` |
| `02-system-design-{api,data}.md` → `02-system-design.md` | `system-design/SKILL.md:260` |
| `03-test-{unit,integration,e2e}.md` → `03-test-cases.md` | `test-cases/SKILL.md:156` |
| `04-dev-tasks-*.md` → `04-dev-tasks.md` | `dev-tasks/SKILL.md:95` |

⛔ **无声明的不推导主从**：`patterns/<name>.md`（compound 独立经验文件）· `audit/<T-XX>-external-review.yaml`（声明的是**证据层级**：L2 权威、L1 派生、L3 可选，不是主从）· `adr/ADR-NNN.md`（主文件不能靠前缀猜）· `05-refactor-{audit,plan,report,rewrite}.md`（四个独立产物，按连字符反推会去找不存在的 `05-refactor.md`）。

四类双形态资源各登记两行（§3.3）。

⚠️ **「分册名必须出现在主文件正文」是本稿新增规则**，⛔ 不是既有约束。

**防复发**：⛔ 任何 skill 新增 devdocs 产出必须先进清单。现存三份互不一致的清单——`docs/architecture.md` 文件结构块（10 项）、`onboard/SKILL.md §8`（4 行硬编码）、各 skill 散落声明（≥18 种）——前两份改为指向清单。

#### 三条规则（全部 ⚠️，⛔ 无 blocker）

| rule_id | 检测 | 边界 |
|---|---|---|
| `layout/unknown-path` | 不匹配清单任何模式 → 报「**待分类**」 | ⛔ 不判非法：新产物先于清单出现是正常时序 |
| `layout/unregistered-split` | 清单中**已声明主文件**的分册，文件名未在主文件正文出现 | 只保证**可发现性下限**，⛔ 不宣称索引完整性 |
| `layout/size-cap` | devdocs 正文 `.md` > 96 KiB | 修复建议**按类型分流**，见下 |

**扫描面**：`collect_files()` 需扩**文件类型**（现只收 `.md`，`.yaml`/`.txt` 永不受检）。

⚠️ 该函数用 `os.walk`，**本就递归嵌套目录**——v2/v3 称「须扩到嵌套目录」有误。

⚠️ **⛔ 不整目录排除 `archive/`**：`collect_files()` 结果同时参与**编号定义索引**（`health-lint.py:445`），排除会让指向历史编号的合法引用变死链。须区分「归档**不报**活跃文档问题」与「归档定义**仍可**被引用」。

#### 尺寸：新判据 + 三条分流出口

⚠️ **96 KiB 是本稿的新功能设计，⛔ 不是修 bug。** 与之相关但性质不同：health scope `:294` 的 `1500 行` 只有散文承诺、Rule 集表无对应规则，**清理该悬空承诺**才是修复。两者分开记账。

**单位换字节的依据**：tm-reborn `01-requirements.md` = 620 行 / 28 KB；mic-en 同名文件 = 556 行 / 160 KB（46 B/行 vs 288 B/行，后者全是宽表格）。痛点是上下文预算被吃光，预算按 token 算。

**校准**：tm-reborn 全通过（最大 61 KB）；mic-en 命中 `02`(400KB) `03-test-unit`(215KB) `01`(160KB) `04`(135KB)。

⛔ **不设 blocker**：裁定 3 未授权自动拆分，`02`/`00-context`/`backlog` 的分册键仍未解，设 blocker 即造无解之门。

⛔ **apply 不能减量**，按内容性质分流：

| 情形 | 出口 |
|---|---|
| ADR/INS/BUG/Backlog 四类资源超阈值 | 建议**转资源目录**（§3.3）|
| 历史内容可归档 | `/sync --archive` |
| 活跃内容需拆分 | 各 skill 已有拆分规则 |

⚠️ **`/sync --archive` 零项目验证过**（§2）。路由到它属于**未验证路径**，P3 实施时须在一个真实项目上先跑通，⛔ 不得只在规格里写它是出口。

⛔ **不删** `sync/references/archive.md` 的行数阈值列：那是**归档触发器**，与各 skill 的**拆分建议**、与本稿的**尺寸警报**是三件事。

#### 闭环四步（裁定 6）

⛔ 全部复用现役机制：

| 步 | 机制 | 现状 |
|---|---|---|
| 检查 | health dry-run → `.health-report.md` | 已有 |
| 决策 | `next_recommended` + `AskUserQuestion` 触发点加一行 | 已有，加一行 |
| 执行 | health `--apply` 新增 Phase：改名 + 归档移位 | 已有框架 |
| 复查 | health 幂等契约（二次 dry-run `total_score` 一致）| 已有，⚠️ 现役**未明确规定 apply 后必须全量重扫**，须补 |

⛔ **机械判不出归属的只列清单问用户，不猜。**

⚠️ **改名必须同批更新所有指向它的引用**。实证：tm-reborn 的 `06-ui-hig-swiftui-checklist.md` 在 `04-dev-tasks.md:19` 被链接，只 `git mv` 即制造死链。补登记需编辑正文，超出裁定 3 授权 ⇒ 单列为「仅移动无法闭合」，逐项问。

#### 索引

⛔ 不新建 `docs/devdocs/index.md`。`onboard/SKILL.md §8` 的 4 行硬编码表改为**从清单 + 实际文件生成**。

⚠️ 承认：**插件内的路径类型清单 ≠ 项目当前文件索引**，两者不可互替。清单承担前者，onboard §8 承担后者。

### P4 · `SessionStart` 触发点

新增 `hooks/devdocs-layout`：开工时扫描 → 命中则一行非阻塞提示 → 接闭环。落裁定 2。`SessionStart` 在现有 `hooks.json` 是空槽。

**rule 与 hook 的分工**：rule = 权威 + 覆盖 + 可测；hook = 送达。现状的病正是只有一半。⚠️ hook **只扩大触达，⛔ 不能证明用户会处理**——闭环靠四步，不靠 hook。

四条硬限制：

1. ⛔ **OpenCode 不覆盖**：适配器只实现 `tool.execute.after`，`SessionStart` 无接入点（`hooks/opencode-plugin.js:50`）。本轮只覆盖 Claude Code + Codex；清单 + rule 必须独立成立。
2. ⛔ **不挂在 `devdocs-drift` 上**——其文件头自述「试验件。验不过就删，⛔ 不要在它之上加功能」。
3. ⛔ **不做 `PostToolUse` 防漂移**（裁定 4）。
4. ⚠️ **hook 是常驻成本**：现役两个 `PostToolUse` 都被迫加冷却戳；有实测教训——hook 常驻会让验收结果混叠。`SessionStart` 天然低频，⛔ 无需分钟级冷却；非 keel 项目静默退出。

### 旁路 · 与主线无依赖

`test-run` 的发现 glob 是 `03-test-cases*.md`（`test-run/SKILL.md:65`），**匹配不到** test-cases 默认产出的 `03-test-{unit,integration,e2e}.md` ⇒ 测试详情扫不到。独立缺陷，可随时插。

## 5. 改动面

| # | 文件 | 工作项 |
|---|---|---|
| 1 | `skills/pipeline/scripts/health-lint.py` | P0 ✅ · P3（3 条 rule + `collect_files` 扩类型 + archive 扫描政策 + 夹具）|
| 2 | `skills/pipeline/references/realign-scope-health.md` | P1（4 处）· P3（维度接新 rule、AskUserQuestion 加行、apply 加 Phase、补复查）|
| 3 | `skills/pipeline/SKILL.md` | P1（`layout` 枚举残留）|
| 4 | `skills/sync/references/health-scoring.md` | P1（死引用）|
| 5 | `skills/shared/devdocs-layout.md` | P3 **新增** |
| 6 | `skills/pipeline/references/health-lint-implementation.md` | P3（Rule 集表登记）|
| 7 | `skills/onboard/SKILL.md` §8 | P3（改为生成）|
| 8 | `docs/architecture.md` | P3（文件结构块改指针）|
| 9 | `hooks/devdocs-layout` + `hooks/hooks.json` | P4 **新增** |
| 10 | `skills/test-run/SKILL.md` | 旁路（glob）|
| 11 | `plugin.json` ×2 | 每批 bump（⛔ 不 bump 则分发空转且零报错）|

⛔ **不碰**：`retrofit`（M1 非表驱动、M2/M4 会触发内容迁移）· `sync/references/archive.md` 阈值列 · 四个生产方 skill 的落盘行为 · 任何新 scope。

## 6. 非目标

⛔ 不新建 scope · ⛔ 不新建命名法规 · ⛔ 不全局强制改名 · ⛔ 不自动拆分大文件 · ⛔ 不自动执行集中→资源目录转换 · ⛔ 不建「两形态并存」检测 · ⛔ 不新建项目内 `index.md` · ⛔ 不改编号对象模型 · ⛔ 不碰 version-bump 检测 · ⛔ 不设 blocker · ⛔ 不做 `PostToolUse` 防漂移 · ⛔ 不覆盖 OpenCode

## 7. 诚实残留

- **P0 用假阴换假阳**：列表里提到但未真正定义的编号不再报。
- **命名统一只做到「待分类 + 已声明映射改名」**。`unknown-path` ⛔ 不判定已匹配名称之间的冲突，也 ⛔ 不为任意文件生成唯一改名目标。
- `unregistered-split` 是字面检查：历史说明里写「已弃用 `02-system-design-api.md`」也会通过；链接文字对而目标错也会通过。⇒ 只保证可发现性下限。
- `02-system-design` / `00-context` / `backlog` 的**分册键仍未解**，与已封存的对象模型稿 §6.2 一致。
- **`/sync --archive` 是未验证路径**，P3 须先在真实项目跑通。
- 14 个不活跃项目不迁、⛔ 也不报错（裁定 1 的既定代价）。
- 集中→资源目录的**转换阈值复用 `layout/size-cap` 的 96 KiB**，⛔ 未按条目数单独定阈值——四类资源的条目粒度差异大，等实测再细分。

## 8. 验证方式

本仓无统一 build/test/lint，按 AGENTS.md 逐项：

| 改动 | 验证 |
|---|---|
| P0 | ✅ 已做：夹具红绿 + 三样本实测（tm-reborn 作对照组必须不变）|
| P1 死规格 | 清理后全仓 grep 该名字归零；`--scope=health` 规格自读一遍无矛盾 |
| P3 三条 rule | selftest 夹具**红绿各一**；⛔ 格式检查不算 |
| `collect_files` 改动 | 夹具含 `.yaml`/`.txt`；并验证 `archive/` 下编号定义**仍可被引用**（防引入死链误报）|
| delta 行为 | 确认 `--since-baseline` 不吞掉新 rule 首次报告 |
| 闭环四步 | tm-reborn 实测：命中 → 报告 → 决策 → apply → **复扫归零** |
| `/sync --archive` | ⚠️ 必须在一个真实项目跑通一次，⛔ 不接受只在规格里声明 |
| P4 hook | `bash -n` + 三输入：非 keel 项目须静默 · 合规项目须静默 · tm-reborn 须命中 |
| 清单 | 各 skill 输出声明**逐一提取**，⛔ 不凭记忆；生产方/消费方同时核对 |
| onboard §8 | 生成结果须覆盖分册与裸名产物，⛔ 不退回 4 行 |
| 分发 | version bump 后确认注入版本 |

复现命令：

```bash
python3 skills/pipeline/scripts/health-lint.py --selftest
cd <项目> && python3 <keel>/skills/pipeline/scripts/health-lint.py --target .
```

## 9. 与既有裁定的关系

| 既有裁定 | 本稿立场 |
|---|---|
| layout.v2 删除（`e7c6771`）| ⛔ **不推翻**。不复活 scope、不引入其目录树/编号双轨/12 命令 |
| 对象模型收敛 v2 封存 | ⛔ **不 reactivate**。不碰编号对象模型；触发条件未满足 |
| 维度 d / e 废弃 | ⛔ **不恢复**。P1 是删残留，⛔ 不是重建维度 d |
| state 模板的资源目录模型（`0054e99`）| ⛔ **不推翻**。裁定为合法形态之一（§3.3）|
