---
title: 实现 realign --scope=layout——填补悬空的布局健康维度
status: 📐 设计稿 v2（推翻 v1 的「新建命名规范」骨架），待实施
date: 2026-09-20
supersedes: 本文件 v1（同日 commit 0722126）——骨架已废，结论仅部分留用
scope: layout scope 实现、布局清单 SSOT、字节尺寸规则、SessionStart 触发点
inputs:
  - 用户原话 4 条 + 5 次裁定
  - 17 个真实项目 devdocs 实测
  - Codex 独立评审（禁读 v1 稿，逐条已复核）
related:
  - docs/superpowers/specs/2026-09-11-devdocs-object-model-convergence-v2-design.md（已封存，不 reactivate）
---

# 实现 `realign --scope=layout`

## 0. 诉求与裁定

用户原话（逐字）：

> 1.「我有个发现，devdocs 目录下文档有点乱，第一命名格式不统一，第二没有全局的索引控制，第三部分文档可能过大」
> 2.「应当由 keel 做检测，然后进行迁移，而且在当前会话进行」
> 3.「我在思考hook机制，以及rule 能为优化带来什么？或者整个keel 流」
> 4.「我的原本意思是keel可以做一次文档健康检查，决定下一步要干什么」

⛔ **第 4 条是诉求的权威表述，前三条是它的症状面。** v1 稿把症状当成了诉求，据此新建了一套命名法规——方向错了。

裁定：

| # | 问题 | 裁定 |
|---|---|---|
| 1 | 痛点来源 | 四项全中：存量读不动 · 新项目一开头就歪 · Agent 定位错文件 · 人找不到文件 |
| 2 | 迁移触发 | 开工时自动检测，**当场问**，同一会话跑完 |
| 3 | 自动迁移权限 | **只改名 + 归档移位**，⛔ 不自动拆分内容 |
| 4 | hook 范围 | **只进 `SessionStart`** |
| 5 | v1 推翻后 | **重写**，不做局部修补 |

## 1. 关键发现：槽位已经存在，且是空的

用户要的「做一次文档健康检查，决定下一步干什么」——`realign --scope=health` 就是它，且设计相当完整：

| 能力 | 位置 |
|---|---|
| 三大维度 + 评分（0-100）+ 阈值提示（<60 建议立即处理 / <40 不达标）| [realign-scope-health.md:179](../../../skills/pipeline/references/realign-scope-health.md) |
| `.health-report.md` 产出 + schema + 防 stale（`report_hash` / `source_git_commit`）| 同文件 :108 / :203 |
| **`next_recommended`**——按违规分布动态生成的「下一步干什么」| 同文件 :245 |
| `AskUserQuestion` 触发点表 | 同文件 :191 |
| `--apply` 四 Phase 修复路径 | 同文件 :217 |

而 `layout` 这个 scope **在同一文件里被引用了三次**：

1. `next_recommended` 拓扑顺序：`spec → layout → prd-mapping → health`（:245 区）
2. 边界：「维度 c 中单文件 ≥ 1500 行 → 仅报告，**不拆分**」（:294）
3. 报告字段：`route_note: "current.md >1500 拆分由 layout scope 处理"`（:146）

⛔ **全仓搜不到 `layout` scope 的任何定义。** 它是悬空引用。

> **这就是 v1 跑偏的根因**：在重造一个已经有名字的空槽。本稿改为把槽填上。

## 2. v1 为什么被推翻

Codex 独立评审（禁读 v1 稿），六条，**逐条已由本方复核属实**：

| # | 发现 | 证据 | 对 v1 的杀伤 |
|---|---|---|---|
| 1 | `04-dev-tasks-pNN.md` 是**现役契约声明的权威位置**；mic-en 的 pN 分册全部在主文件登记且带语义（「P1 后端基础 + 买家端」T-01~T-22）| [devdocs-state-template.md:71](../../../skills/agent-memory/templates/devdocs-state-template.md) · mic-en `04-dev-tasks.md:373` | v1 的 `layout/ordinal-key` 会把一份现役契约判违规。⇒ **删除该规则** |
| 2 | 主从关系不能靠连字符反推：`03-test-unit.md` 的主文件是 `03-test-cases.md`（词干不同）；`05-refactor-{audit,plan,report,rewrite}.md` 是四个独立产物，反推会去找不存在的 `05-refactor.md` | [test-cases/SKILL.md:156](../../../skills/test-cases/SKILL.md) · [refactor/SKILL.md:365](../../../skills/refactor/SKILL.md) | v1 的「文件名语法」不成立 ⇒ 改为**显式映射表** |
| 3 | 行数阈值有第三处消费方，且**拆分阈值 ≠ 归档阈值** | [archive-rules.md:16](../../../skills/dev-tasks/templates/archive-rules.md) · [requirements/SKILL.md:244](../../../skills/requirements/SKILL.md) · [system-design/SKILL.md:264](../../../skills/system-design/SKILL.md) | v1 的「删掉行数阈值列」会误伤拆分规则 ⇒ **限定范围** |
| 4 | 「只做 `git mv`」闭不了环：tm-reborn 的 `06-ui-hig-swiftui-checklist.md` 在 `04-dev-tasks.md:19` 被链接，改名即制造死链 | tm-reborn 实盘 | ⇒ 改名必须连带改引用，或列为「仅移动无法闭合」交用户 |
| 5 | `SessionStart` 在 OpenCode **没有接入点**——适配器只实现 `tool.execute.after` | [opencode-plugin.js:50](../../../hooks/opencode-plugin.js) | ⇒ ⛔ 不得宣称三端覆盖 |
| 6 | retrofit M1 **不是表驱动**（只有示例检测结果，无规则表读取 / 路径匹配 / 主从解析契约）；M2/M4 含拆分、加编号、补追溯矩阵，接布局检查会顺带触发内容迁移；基线项目进 M1 前短路 | [version-migration.md:7](../../../skills/retrofit/references/version-migration.md) · [retrofit/SKILL.md:131](../../../skills/retrofit/SKILL.md) | ⇒ **整个绕开 retrofit**，迁移的家是 layout scope 自己 |

> ⚠️ **提案方在 v1 中两次用同一个错误样本（mic-en 的 `-pN` 分册）论证 `ordinal-key` 规则。** 按本仓熔断判据（连续自引入即复盘、塌缩维度而非继续加固），v1 重写而非修补。

此外 codex 指出 v1 的载体分类装不下：`audit/<T-XX>-external-review.yaml`（门禁唯一权威输入）、`audit/<T-XX>-external-review-raw/<round-N>.txt`（嵌套目录）、`archive/releases/v1.0.0/01-requirements.md`（版本快照）。而 [health-lint.py:64](../../../skills/pipeline/scripts/health-lint.py) 的 `collect_files()` **只收 `.md`** ⇒ 非 md 产物永不受检。

⇒ 清单必须描述**相对路径模式 + owner + 主从关系**，⛔ 不能只列文件名语法。

## 3. 设计：`--scope=layout`

### 3.1 定位与边界

**layout = 布局健康维度**：devdocs 目录里「有什么文件、归谁、谁是谁的分册、多大」。

与既有三个 scope 正交：

| scope | 管 |
|---|---|
| `spec` | `spec_version` 差距补齐（产物**内容**是否跟上规范） |
| `prd-mapping` | PRD ↔ keel 编号映射 |
| `health` | 当前规范下产物是否健康（结构 / 链接 / state 卫生） |
| **`layout`** | **文件本身的位置、归属、主从、体积** |

⛔ **layout 不改文件内容**，只改文件名与位置（裁定 3）。内容减量仍走 `/sync --archive`。

### 3.2 数据源：布局清单

落点 `skills/shared/devdocs-layout.md`。理由：消费方全在 `skills/` 里，`shared/` 是跨 skill 共享资源的既定家（`constraints.md` / `runlog.md` 同处）。⛔ 不放 `constraints.md`（已 559 行，且它装规则、清单是结构事实）。

**三列结构**，⛔ 不是文件名语法：

| 相对路径模式 | owner | 主文件 |
|---|---|---|
| `01-requirements.md` | requirements | — |
| `02-system-design.md` | system-design | — |
| `02-system-design-api.md` | system-design | `02-system-design.md` |
| `02-system-design-data.md` | system-design | `02-system-design.md` |
| `03-test-cases.md` | test-cases | — |
| `03-test-{unit,integration,e2e}.md` | test-cases | `03-test-cases.md` |
| `04-dev-tasks.md` | dev-tasks | — |
| `04-dev-tasks-p<NN>.md` | dev-tasks | `04-dev-tasks.md` |
| `05-refactor-{audit,plan,report,rewrite}.md` | refactor | —（四个独立产物，⛔ 非分册）|
| `audit/<T-XX>-external-review.yaml` | dev-workflow | — |
| `audit/<T-XX>-external-review-raw/<round-N>.txt` | dev-workflow | — |
| `.health-report.md` · `.batch-checkpoint.json` | pipeline | —（机器态，排除扫描）|

（完整表在实施时从各 skill 的输出声明逐一提取，⛔ 不凭记忆填。）

**防复发**：⛔ 任何 skill 新增一种 devdocs 产出，必须先进清单。v1 暴露的问题正是 `verify-report.md` / `schema-drift-report.md` 等是各 skill 自己长出来的，`docs/architecture.md` 的文件结构块只列 10 项而实际 ≥18 种。

**连带改动**：`docs/architecture.md` 文件结构块改成指向清单的一行——留着就是第二处真源，而它已证明会过期。

### 3.3 三条检测规则

全部 ⚠️，⛔ 无 blocker。

| rule_id | 检测 | 为什么不是 blocker |
|---|---|---|
| `layout/unknown-path` | 实际文件不匹配清单任何模式 → 报「待分类」 | 新产物先于清单出现是正常时序，判非法会误伤 |
| `layout/unregistered-split` | 清单中**已声明主文件**的分册，其文件名未在主文件正文出现 | 登记缺失不影响正确性，只影响可发现性 |
| `layout/size-cap` | devdocs 正文 `.md` > 96 KiB | 拆分键未解（见 §7），设 blocker 即造无解之门 |

⛔ **v1 的 `layout/ordinal-key` 与 `layout/illegal-name` 删除**（理由见 §2 之 1、2）。

`unknown-path` 的措辞是「待分类」而非「非法」——这是 codex 建议的准确命名，⛔ 不把「字符串命中」宣传成全局索引完整性。

**扫描面须扩**：`collect_files()` 现只收 `.md`（[health-lint.py:64](../../../skills/pipeline/scripts/health-lint.py)），`layout/unknown-path` 必须看见 `.yaml` / `.txt` / 嵌套目录，否则三类已知产物永不受检。

### 3.4 尺寸：单位换字节

**依据**：行数与字节严重脱钩——tm-reborn `01-requirements.md` = 620 行 / 28 KB；mic-en `01-requirements.md` = 556 行 / 160 KB（平均每行 46 B vs 288 B，后者全是宽表格）。痛点是「读一个文件把上下文预算吃光」，预算按 token 算不按行算。隔壁 `state/total-size-cap` 用的正是字节。

阈值 **96 KiB** 单档警告。校准：tm-reborn 全部通过（最大 61 KB）；mic-en 命中 `02`(400KB) `03-test-unit`(215KB) `01`(160KB) `04`(135KB)。

⛔ **不删 `sync/references/archive.md` 的行数阈值列**（v1 的连带改动撤回）。理由见 §2 之 3：那些是**归档触发器**与**拆分建议**，与**尺寸警报**是三件事。本稿只新增尺寸警报，三者分工在清单里写清。

### 3.5 出口：复用已有的决策机制

⛔ 不新建任何决策通道：

- **`next_recommended`**——layout 违规时生成 `"realign --scope=layout --apply"`；已有的拓扑顺序 `spec → layout → prd-mapping → health` 本就给 layout 留了位
- **`AskUserQuestion` 触发点**——新增一行：判不出归属的文件（如 tm-reborn 的 `T-31-a11y-interactive-checklist.md`），展示候选归属交用户

⛔ **机械判不出归属的，只列清单问用户，不猜。** 猜一个改过去等于静默丢信息。

### 3.6 apply：改名 + 归档移位

按 health scope 的 apply 形态：工作区洁净前置、每项独立 commit、`report_hash` 防 stale、`pending` 决策未答不得继续。

两种动作：

1. **改名**（清单里有明确旧名→新名映射时）——`git mv` + **同批更新所有指向它的引用**
2. **归档移位**——把 `*-archive.md` 从根目录移进 `archive/`

⚠️ **仅移动无法闭合的项单列**（codex 发现 4）：改名会打断 `04-dev-tasks.md:19` 这类链接；补登记要编辑正文。这两类超出裁定 3 的 `git mv` 授权，⛔ 不隐含扩权——列清单，逐项问。

## 4. 触发：`SessionStart` hook

新增 `hooks/devdocs-layout`：开工时扫描 → 命中则一行非阻塞提示 → 接 §3.5 决策链。这落裁定 2 的「开工时自动检测，当场问」。

`SessionStart` 在 keel 现有 `hooks.json` 里是空槽（现只用 `PostToolUse`）。

### 4.1 rule 与 hook 的分工

**rule = 权威 + 覆盖 + 可测；hook = 送达。** 两者是一件事的两半。现状的病正是只有一半：维度 c 的规则装了，但要人主动敲命令才跑——`realign-scope-health.md` 自己写了这个断层（原话「解决"规则实装但没人跑"的断层」）。

⛔ hook 只治「该跑的没跑」这一类病，治不了别的。

### 4.2 四条硬限制

1. ⛔ **OpenCode 不覆盖**：适配器只实现 `tool.execute.after`，`SessionStart` 无接入点（[opencode-plugin.js:50](../../../hooks/opencode-plugin.js)）。本轮明确只覆盖 Claude Code + Codex。清单 + rule 必须独立成立，hook 只是加速器。
2. ⛔ **不挂在 `devdocs-drift` 上**——其文件头自述「试验件。验不过就删，⛔ 不要在它之上加功能」。
3. ⛔ **不做 `PostToolUse` 防漂移**（裁定 4）。它价值更高（漂移出生即被抓）但是常驻成本，单独算账。
4. ⚠️ **hook 是常驻成本**：现役两个 `PostToolUse` 都被迫加冷却戳（5 / 2 分钟）；且有实测教训——hook 常驻会让验收结果混叠。`SessionStart` 天然低频，⛔ 无需分钟级冷却；非 keel 项目（无 `docs/devdocs/`）静默退出。

## 5. 顺手修的既存缺陷

调查中发现，与本设计同源，⛔ 不另开任务：

| # | 缺陷 | 证据 |
|---|---|---|
| 1 | `--apply` Phase 2 写「维度 d 引用替换」，但**维度 d 已废弃**（同文件前文明写「原维度 d 与维度 e 均已废弃」）——死规格 | realign-scope-health.md :217 区 vs :43 区 |
| 2 | `1500 行` 阈值只在散文出现两次（:146 / :294），不在 Rule 集表，无实现 | 同文件 |
| 3 | `collect_files()` 排除 `_archived/`，但归档约定是 `archive/`（sync）——排除的是规格里不存在的目录名 | [health-lint.py:67](../../../skills/pipeline/scripts/health-lint.py) vs [sync/references/archive.md:147](../../../skills/sync/references/archive.md)。⚠️ 实盘 17 个项目均无 `_archived/`，故目前无实际漏扫，属规格层不一致 |

缺陷 2 的处理：`1500 行` 被 §3.4 的字节阈值取代，散文两处改写为指向 `layout/size-cap`。

## 6. 改动面

| # | 文件 | 动作 |
|---|---|---|
| 1 | `skills/shared/devdocs-layout.md` | **新增**——路径模式 / owner / 主从映射 / 尺寸阈值 |
| 2 | `skills/pipeline/references/realign-scope-layout.md` | **新增**——layout scope 执行接口（对标 `realign-scope-health.md`）|
| 3 | `skills/pipeline/references/realign.md` | scope 表加 `layout` 行 |
| 4 | `skills/pipeline/references/realign-scope-health.md` | 修缺陷 1、2；`next_recommended` 补 layout 路由 |
| 5 | `skills/pipeline/scripts/health-lint.py` | 加 3 条 rule；`collect_files()` 扩到非 `.md`；selftest 夹具 |
| 6 | `skills/pipeline/references/health-lint-implementation.md` | Rule 集表登记 3 条新 rule |
| 7 | `docs/architecture.md` | 文件结构块改指针 |
| 8 | `hooks/devdocs-layout` + `hooks/hooks.json` | **新增** `SessionStart` |
| 9 | `plugin.json` + `.claude-plugin/plugin.json` | version bump（⛔ 不 bump 则分发空转且零报错）|

⛔ **不碰** `retrofit`（§2 之 6）、⛔ **不碰** `sync/references/archive.md`（§3.4）——v1 的这两项连带改动全部撤回。

## 7. 非目标与诚实残留

### 7.1 非目标

⛔ 不新建命名法规 · ⛔ 不做全局强制改名 · ⛔ 不自动拆分大文件 · ⛔ 不做项目内 `index.md` · ⛔ 不改编号对象模型 · ⛔ 不碰 version-bump 检测 · ⛔ 不设 blocker 级门 · ⛔ 不做 `PostToolUse` 防漂移 · ⛔ 不覆盖 OpenCode

### 7.2 为什么不做项目内 `index.md`

清单 + 主从映射到位后，「哪册装什么」由主文件的分册目录承载（`04-dev-tasks.md` 与 `03-test-cases.md` 已自发这么做）。独立 index 多一个会漂的文件。⚠️ 但须承认 codex 的提醒：**插件内的路径清单不能替代用户项目自己的导航索引**——若将来实证需要，另案。

### 7.3 诚实残留

- `02-system-design` / `00-context` / `backlog` 的**分册键仍未解**，与已封存的对象模型稿 §6.2 结论一致。超阈值只报警，怎么拆当场问用户。
- `unregistered-split` 只做「文件名在主文件正文出现过」的字面检查。codex 构造的反例成立：历史说明里写「已弃用 `02-system-design-api.md`」也会通过；链接文字对而目标错也会通过。⇒ 规则**只保证可发现性下限**，⛔ 不宣称索引完整性。
- 14 个不活跃项目不迁、⛔ 也不报错（裁定 1 的既定代价）。
- `layout/unknown-path` 对**文件放错目录**的检测依赖清单的路径模式写得够细；清单粗则漏检。

## 8. 验证方式

本仓无统一 build/test/lint，按 AGENTS.md 逐项：

| 改动 | 验证 |
|---|---|
| 3 条新 rule | selftest 夹具**红绿各一**（先构造违规证明会报，再修正证明不报）；⛔ 格式检查不算 |
| `collect_files()` 扩面 | 夹具含 `.yaml` / `.txt` / 嵌套目录，证明新路径进扫描且旧行为不变 |
| delta 行为 | 确认 `--since-baseline` 不吞掉新 rule 首次报告 |
| `hooks/devdocs-layout` | `bash -n` + 三种输入实测：非 keel 项目须静默 · 合规项目须静默 · tm-reborn 须命中 |
| 清单 | 生产方 / 消费方同时核对；各 skill 输出声明**逐一提取**，⛔ 不凭记忆 |
| scope 接入 | `next_recommended` 在 layout 违规时真的路由到 layout |
| 分发 | version bump 后确认注入版本 |
| 文案 | `git diff --check` |

⚠️ **端到端须实测**：在 tm-reborn 跑完整触发链（SessionStart 命中 → 报告 → 决策 → apply → 复扫归零）。未能实测的部分明确说明。

## 9. 与封存稿的关系

`2026-09-11-devdocs-object-model-convergence-v2-design.md` 于 2026-09-15 封存，`reactivate_when: 第二个项目在技术升级/重构/治理上撞同一堵墙`。

**本稿不 reactivate 它。** 那份稿的主体是编号对象模型（`F` 字段 / `AC.kind` / `CHK.level` / 追溯链），封存因其要改 50+ 文件跨 21 个 skill。本稿只填一个已被现役规格引用三次的空 scope，且用「显式映射表」替掉「对象模型字段做键」——不冲突、不依赖、不解锁。其 `reactivate_when` 仍有效，本稿不满足触发条件。
