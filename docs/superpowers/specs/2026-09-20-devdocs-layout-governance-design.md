---
title: devdocs 布局健康检查——清单 SSOT + 三条 health 维度规则 + 闭环
status: 📐 设计稿 v3（v1「新建命名规范」、v2「填 layout 空槽」两个骨架均已推翻），待实施
date: 2026-09-20
supersedes: 本文件 v1（commit 0722126）、v2（commit cf4749e）
scope: 布局清单 SSOT、health 维度扩面、字节尺寸判据、闭环四步、SessionStart 触发点
inputs:
  - 用户原话 4 条 + 6 次裁定
  - 17 个真实项目 devdocs 实测
  - Codex 两轮独立评审（均禁读本稿，全部结论已逐条复核）
related:
  - docs/superpowers/specs/2026-08-31-layout-v2-goal-attainment-design.md（layout.v2 删除决策，本稿 ⛔ 不推翻它）
  - docs/superpowers/specs/2026-09-11-devdocs-object-model-convergence-v2-design.md（已封存，⛔ 不 reactivate）
---

# devdocs 布局健康检查

## 0. 诉求与裁定

用户原话（逐字）：

> 1.「我有个发现，devdocs 目录下文档有点乱，第一命名格式不统一，第二没有全局的索引控制，第三部分文档可能过大」
> 2.「应当由 keel 做检测，然后进行迁移，而且在当前会话进行」
> 3.「我在思考hook机制，以及rule 能为优化带来什么？或者整个keel 流」
> 4.「我的原本意思是keel可以做一次文档健康检查，决定下一步要干什么」

⛔ **第 4 条是诉求的权威表述**，前三条是它的症状面。

| # | 裁定 |
|---|---|
| 1 | 痛点四项全中：存量读不动 · 新项目一开头就歪 · Agent 定位错文件 · 人找不到文件 |
| 2 | 开工时自动检测，**当场问**，同一会话跑完 |
| 3 | 自动动作**只改名 + 归档移位**，⛔ 不自动拆分内容 |
| 4 | hook **只进 `SessionStart`** |
| 5 | v1 推翻后重写 |
| 6 | 闭环做到**检查 → 决策 → 执行 → 复查**四步；执行限于 `git mv` 与分流，减量本身不由本设计做 |

## 1. 复盘：两次骨架错误的共因

| 版本 | 骨架 | 为什么错 |
|---|---|---|
| v1 | 新建一套命名法规（四类载体语法 + 4 条 rule + retrofit 迁移）| 把症状当诉求。`ordinal-key` 规则会把现役契约 `04-dev-tasks-pNN.md` 判违规；主从关系不能靠连字符反推 |
| v2 | 实现 `realign --scope=layout`（认定它是预留空槽）| **`layout` 是被裁定删除后的残留引用**，不是空槽。见 §2 |

⛔ **共因**：两次都先造新东西（新规范 / 新 scope），而不是先查清现役已有什么；两次都由外部证据（Codex、git 历史）纠正，而非自查发现。

> 本仓熔断判据：连续自引入即复盘、塌缩维度而非继续加固。v3 据此约束自己——**唯一新增物是一份清单与三条 rule**，其余一律挂现役机制。

## 2. 关键事实：`layout` 是墓碑，不是空槽

```
9d7f870  feat(realign-scope-layout): 落地 --scope=layout 执行接口   ← 建（334 行）
e7c6771  refactor(layout): 删除 layout.v2 —— 目标已由现役更便宜的手段达成  ← 删（336 行）
1ff8115  fix(layout): 补清 layout.v2 产物名残留 —— 前次清扫的 grep 有盲区
```

`skills/pipeline/references/realign-scope-layout.md` 曾存在，随 layout.v2 一并删除。删除决策见 [layout-v2-goal-attainment-design.md](2026-08-31-layout-v2-goal-attainment-design.md)，交叉确认见 [repo-governance-backlog.md:59](../../audits/2026-08-31-repo-governance-backlog.md)。

⇒ **⛔ 不复活该 scope。** 残留引用是 `1ff8115` 所述「grep 有盲区」的续漏，属待清理缺陷。

**v2 的事实错误一并订正**：残留只有三处——`realign-scope-health.md` 的 `:144` 枚举、`:146` `route_note` 示例、`:279` 拓扑排序。`:294` **不是**残留，它已正确写成「归档减量走 `/sync --archive`」。

> ⚠️ layout.v2 的删除理由是**成本与已有替代路径**，⛔ 不是永久禁止布局治理。本稿不以「填空槽」为授权，而是重新论证必要性（§3）。

### 2.1 本稿的清单与 layout.v2 方向相反

被删的 layout.v2 是**另一套目录树**：`index.md` / `aliases.yml` / `traceability.yml` + 7 类编号目录 + 一文件一编号（`FEAT-001.md`）+ 编号前缀双轨（`F→FEAT`）+ 12 个命令 + ssot-lint。它要把现状**改造成理想态**。

本稿的清单只**描述现状**：不动文件位置、不引入目录树、不改编号、不加命令。⇒ 不构成复活。

## 3. 根因修正：生产方自己就说了两套

v1/v2 都把命名漂移当成项目侧问题。实测推翻：

```
skills/dev-tasks/SKILL.md:117                   → `04-dev-tasks-archive.md`（根目录）
skills/dev-tasks/templates/archive-rules.md:25  → `docs/devdocs/archive/04-dev-tasks-archive.md`（子目录）
```

⇒ **只检测、不收口生产方，问题会再生。** 清单必须同时是生产方的落盘权威，这是 v1/v2 漏掉的一半。

### 3.1 现存三份互相不一致的清单

| 清单 | 覆盖 | 问题 |
|---|---|---|
| `docs/architecture.md` 文件结构块 | 10 项 | 实际 ≥18 种路径 |
| `skills/onboard/SKILL.md` §8「keel 文档索引」 | **4 行硬编码表**（01/02/03/04 主文件）| 分册、裸名产物、目录全缺 |
| 各 skill 正文散落的路径声明 | ≥18 种 | 互相矛盾（见上） |

⇒ 症状②「没有全局的索引控制」的现役承载者（onboard §8）本身就是第三份过期清单。

## 4. 设计

### 4.1 挂载点：已有的 health scope

⛔ 不新建 scope。三条规则挂 `realign --scope=health` 的既有维度：

| 维度 | 新增检测 |
|---|---|
| a 结构正确性 | `layout/unknown-path` |
| b 索引/链接正确性 | `layout/unregistered-split` |
| c 过大文档识别 | `layout/size-cap` |

health scope 已具备本诉求所需的全部机制：评分（0-100）+ 阈值提示、`.health-report.md` + 防 stale、`next_recommended`、`AskUserQuestion` 触发点、`--apply` 分 Phase 修复、幂等契约。

### 4.2 数据源：布局清单

落点 `skills/shared/devdocs-layout.md`（`shared/` 是跨 skill 共享资源既定家；⛔ 不放已 559 行的 `constraints.md`——它装规则，清单是结构事实）。

三列：**相对路径模式 / owner / 主文件**。

⛔ **主文件列允许为空，且只有生产方明确声明过分册关系的才填。**

| 有声明（可填主文件） | 证据 |
|---|---|
| `02-system-design-{api,data}.md` → `02-system-design.md` | [system-design/SKILL.md:269](../../../skills/system-design/SKILL.md) |
| `03-test-{unit,integration,e2e}.md` → `03-test-cases.md` | [test-cases/SKILL.md:162](../../../skills/test-cases/SKILL.md) |
| `04-dev-tasks-*.md` → `04-dev-tasks.md` | [dev-tasks/SKILL.md:104](../../../skills/dev-tasks/SKILL.md) |
| `01-requirements-*.md` → `01-requirements.md` | [requirements/SKILL.md:242](../../../skills/requirements/SKILL.md) |

| ⛔ 无声明（主文件留空，不跑分册检查） | 为什么 |
|---|---|
| `patterns/<name>.md` | 是独立经验文件；compound 明确只更新 patterns 不改其他文档 |
| `audit/<T-XX>-external-review.yaml` / `-raw/<round-N>.txt` | 声明的是**证据层级**（YAML 权威、任务状态派生、原始输出可选），⛔ 不是主从 |
| `adr/ADR-NNN.md` | 主文件不能靠前缀猜 |
| `05-refactor-{audit,plan,report,rewrite}.md` | 四个独立产物，⛔ 非分册 |

⚠️ **「分册名必须出现在主文件正文」是本稿新增规则**，⛔ 不是既有约束，明示承认。

**防复发**：⛔ 任何 skill 新增 devdocs 产出必须先进清单。

### 4.3 三条规则（全部 ⚠️，⛔ 无 blocker）

| rule_id | 检测 | 边界 |
|---|---|---|
| `layout/unknown-path` | 实际文件不匹配清单任何模式 → 报「**待分类**」 | ⛔ 不判非法。新产物先于清单出现是正常时序 |
| `layout/unregistered-split` | 清单中**已声明主文件**的分册，文件名未在主文件正文出现 | 只保证**可发现性下限**，⛔ 不宣称索引完整性 |
| `layout/size-cap` | devdocs 正文 `.md` > 96 KiB | 见 §4.5 |

⛔ v1 的 `layout/ordinal-key`、`layout/illegal-name` 已删（理由见 §1）。

**扫描面**：`collect_files()` 需扩**文件类型**（现只收 `.md`，`.yaml`/`.txt` 产物永不受检）。

⚠️ **事实订正**：该函数用 `os.walk`，**本来就递归嵌套目录**；v2 称「须扩到嵌套目录」有误。

⚠️ **排除 `archive/` 有风险**：`collect_files()` 的结果同时参与**编号定义索引**（[health-lint.py:445](../../../skills/pipeline/scripts/health-lint.py)）。直接排除会让指向历史编号的合法引用变死链。⇒ 须区分「归档**不报**活跃文档问题」与「归档定义**仍可**被引用」，⛔ 不做整目录排除。

### 4.4 闭环四步（裁定 6）

⛔ 全部复用现役机制，⛔ 不新建决策通道：

| 步 | 机制 | 现状 |
|---|---|---|
| 检查 | health dry-run → `.health-report.md` | 已有 |
| 决策 | `next_recommended` + `AskUserQuestion` 触发点新增一行（判不出归属的文件展示候选交用户）| 已有，加一行 |
| 执行 | health `--apply` 新增 Phase：改名 + 归档移位 | 已有框架 |
| **复查** | health 幂等契约（二次 dry-run `total_score` 一致、已修复项跳过）| 已有，须在本 Phase 显式引用 |

⛔ **机械判不出归属的只列清单问用户，不猜**——猜一个改过去等于静默丢信息。

⚠️ **改名必须同批更新所有指向它的引用**。实证：tm-reborn 的 `06-ui-hig-swiftui-checklist.md` 在 `04-dev-tasks.md:19` 被链接，只 `git mv` 即制造死链。⛔ 补登记需编辑正文，超出裁定 3 的授权 ⇒ 单列为「仅移动无法闭合」，逐项问。

### 4.5 尺寸：新判据 + 两条分流出口

⚠️ **96 KiB 是本稿的新功能设计，⛔ 不是修 bug。** 与之相关但性质不同的是：`realign-scope-health.md` 的 `1500 行` 只有散文承诺、无实现（[health-lint-implementation.md](../../../skills/pipeline/references/health-lint-implementation.md) 的 Rule 集表无对应规则），**清理该悬空承诺**才是修复。两者分开记账。

**单位换字节的依据**：tm-reborn `01-requirements.md` = 620 行 / 28 KB；mic-en `01-requirements.md` = 556 行 / 160 KB（46 B/行 vs 288 B/行，后者全是宽表格）。痛点是上下文预算被吃光，预算按 token 算不按行算。现役 `state/total-size-cap` 用的正是字节。

**校准**：tm-reborn 全通过（最大 61 KB）；mic-en 命中 `02`(400KB) `03-test-unit`(215KB) `01`(160KB) `04`(135KB)。

⛔ **不设 blocker**：裁定 3 未授权自动拆分，且 `02` / `00-context` / `backlog` 的分册键仍未解，设 blocker 即造无解之门。

**⛔ 不能全部路由到 apply——apply 不能减量。** 按内容性质分流到两条现役出口：

| 情形 | 出口 |
|---|---|
| 历史内容可归档 | `/sync --archive`（有真实减量动作）|
| 活跃内容需拆分 | 各 skill 已有的拆分规则（[system-design:262](../../../skills/system-design/SKILL.md) 等）|

⛔ **不删** `sync/references/archive.md` 的行数阈值列（v1 的连带改动撤回）：那是**归档触发器**，与各 skill 的**拆分建议**、与本稿的**尺寸警报**是三件事。三者分工在清单里写清。

### 4.6 索引：接 onboard §8，不新建

症状②的现役承载者是 `onboard/SKILL.md` §8 的 4 行硬编码表（§3.1）。

⇒ 改为**从清单 + 实际文件生成**，覆盖分册与裸名产物。⛔ 不新建 `docs/devdocs/index.md`。

⚠️ 承认 Codex 的提醒：**插件内的路径类型清单 ≠ 项目当前文件索引**，两者不可互替。本稿的做法是让 onboard §8 承担后者、清单承担前者。

## 5. 触发：`SessionStart` hook

新增 `hooks/devdocs-layout`：开工时扫描 → 命中则一行非阻塞提示 → 接 §4.4 闭环。落裁定 2。

`SessionStart` 在 keel 现有 `hooks.json` 里是空槽（现只用 `PostToolUse`）。

### 5.1 rule 与 hook 的分工

**rule = 权威 + 覆盖 + 可测；hook = 送达。** 现状的病正是只有一半——维度 c 的规则装了，但要人主动敲命令才跑（`realign-scope-health.md` 原话：「解决"规则实装但没人跑"的断层」）。

⛔ hook 只治「该跑的没跑」，治不了别的。⚠️ 且 **hook 只扩大触达，⛔ 不能证明用户会处理**——闭环靠 §4.4 的四步，不靠 hook。

### 5.2 四条硬限制

1. ⛔ **OpenCode 不覆盖**：适配器只实现 `tool.execute.after`，`SessionStart` 无接入点（[opencode-plugin.js:50](../../../hooks/opencode-plugin.js)）。本轮明确只覆盖 Claude Code + Codex；清单 + rule 必须独立成立。
2. ⛔ **不挂在 `devdocs-drift` 上**——其文件头自述「试验件。验不过就删，⛔ 不要在它之上加功能」。
3. ⛔ **不做 `PostToolUse` 防漂移**（裁定 4）。
4. ⚠️ **hook 是常驻成本**：现役两个 `PostToolUse` 都被迫加冷却戳（5 / 2 分钟）；有实测教训——hook 常驻会让验收结果混叠。`SessionStart` 天然低频，⛔ 无需分钟级冷却；非 keel 项目静默退出。

## 6. 既存缺陷：修什么、不修什么

| # | 缺陷 | 属实 | 处置 |
|---|---|---|---|
| 1 | `--apply` Phase 2 仍执行「维度 d 引用替换」，而维度 d 已在同文件 `:51` 宣告废弃 | ✅ | **修**（最小一致性修复）|
| 2 | `layout` 三处残留引用（`:144` / `:146` / `:279`）指向已删 scope | ✅ | **修**（`1ff8115` 的续清）|
| 3 | `1500 行` 只有散文承诺、无实现 | ✅ | **修**（清理悬空承诺）；换 96 KiB 判据**单独记为新功能** |
| 4 | `collect_files()` 排除 `_archived/`，而归档约定是 `archive/` | ✅ | **修扫描政策**，但 ⛔ 不整目录排除（§4.3 死链风险）|
| 5 | `dev-tasks/SKILL.md:117` 与 `archive-rules.md:25` 归档路径写法不一 | ✅ | **修**（§3，收口生产方）|

## 7. 改动面

| # | 文件 | 动作 |
|---|---|---|
| 1 | `skills/shared/devdocs-layout.md` | **新增**——路径模式 / owner / 主文件（可空）/ 尺寸阈值 / 三类阈值分工 |
| 2 | `skills/pipeline/scripts/health-lint.py` | 加 3 条 rule；`collect_files()` 扩文件类型；调整 archive 扫描政策；selftest 夹具 |
| 3 | `skills/pipeline/references/health-lint-implementation.md` | Rule 集表登记 3 条新 rule |
| 4 | `skills/pipeline/references/realign-scope-health.md` | 维度 a/b/c 接新 rule；`AskUserQuestion` 加一行；apply 加改名 Phase + 显式复查；修缺陷 1/2/3 |
| 5 | `skills/onboard/SKILL.md` §8 | 硬编码 4 行表 → 从清单 + 实际文件生成 |
| 6 | `skills/dev-tasks/SKILL.md` + `templates/archive-rules.md` | 统一归档路径写法 |
| 7 | `docs/architecture.md` | 文件结构块改指针 |
| 8 | `hooks/devdocs-layout` + `hooks/hooks.json` | **新增** `SessionStart` |
| 9 | `plugin.json` + `.claude-plugin/plugin.json` | version bump（⛔ 不 bump 则分发空转且零报错）|

⛔ **不碰**：`retrofit`（M1 非表驱动、M2/M4 会触发内容迁移）· `sync/references/archive.md` 的阈值列 · 任何新 scope。

## 8. 非目标与诚实残留

### 8.1 非目标

⛔ 不新建 scope · ⛔ 不新建命名法规 · ⛔ 不全局强制改名 · ⛔ 不自动拆分大文件 · ⛔ 不新建项目内 `index.md` · ⛔ 不改编号对象模型 · ⛔ 不碰 version-bump 检测 · ⛔ 不设 blocker · ⛔ 不做 `PostToolUse` 防漂移 · ⛔ 不覆盖 OpenCode

### 8.2 诚实残留

- **命名统一只做到「待分类 + 已声明映射改名」**。`unknown-path` ⛔ 不判定已匹配名称之间的冲突，也 ⛔ 不为任意文件生成唯一改名目标。彻底统一需生产方逐个收口，本稿只收口已实证矛盾的一处（`dev-tasks`）。
- `unregistered-split` 是字面检查。Codex 构造的反例成立：历史说明里写「已弃用 `02-system-design-api.md`」也会通过；链接文字对而目标错也会通过。⇒ 只保证可发现性下限。
- `02-system-design` / `00-context` / `backlog` 的**分册键仍未解**，与已封存的对象模型稿 §6.2 结论一致。
- 14 个不活跃项目不迁、⛔ 也不报错（裁定 1 的既定代价）。
- `layout/unknown-path` 对「文件放错目录」的检测依赖清单路径模式写得够细；清单粗则漏检。

## 9. 验证方式

本仓无统一 build/test/lint，按 AGENTS.md 逐项：

| 改动 | 验证 |
|---|---|
| 3 条新 rule | selftest 夹具**红绿各一**（先构造违规证明会报，再修正证明不报）；⛔ 格式检查不算 |
| `collect_files()` 改动 | 夹具含 `.yaml` / `.txt`；并验证 `archive/` 下的编号定义**仍可被引用**（防引入死链误报）|
| delta 行为 | 确认 `--since-baseline` 不吞掉新 rule 首次报告 |
| 闭环四步 | tm-reborn 实测：命中 → 报告 → 决策 → apply → **复扫归零**（`total_score` 幂等）|
| `hooks/devdocs-layout` | `bash -n` + 三种输入：非 keel 项目须静默 · 合规项目须静默 · tm-reborn 须命中 |
| 清单 | 各 skill 输出声明**逐一提取**，⛔ 不凭记忆；生产方 / 消费方同时核对 |
| onboard §8 | 生成结果须覆盖分册与裸名产物，⛔ 不退回 4 行 |
| 分发 | version bump 后确认注入版本 |
| 文案 | `git diff --check` |

## 10. 与既有裁定的关系

| 既有裁定 | 本稿立场 |
|---|---|
| layout.v2 删除（`e7c6771`，[设计稿](2026-08-31-layout-v2-goal-attainment-design.md)）| ⛔ **不推翻**。本稿不复活 scope、不引入其目录树/编号双轨/12 命令；清单方向相反（描述现状 vs 改造现状）|
| 对象模型收敛 v2 封存（`reactivate_when: 第二个项目撞同一堵墙`）| ⛔ **不 reactivate**。本稿不碰编号对象模型，用「显式映射表」替「对象模型字段做键」；其触发条件未满足 |
| 维度 d / e 废弃 | ⛔ **不恢复**。缺陷 1 是删残留，⛔ 不是重建维度 d |
