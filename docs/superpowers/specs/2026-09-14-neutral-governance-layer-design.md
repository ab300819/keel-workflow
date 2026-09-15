---
title: 中立治理层（双模式 SSOT 第 3 步）
status: 📦 已封存 —— ⛔ 不实施，保留作调研底稿
date: 2026-09-14
step: C（共三步：B 共享边界 ✅ → A CHG 对象与模式 B ✅ → **C 中立治理层**）
depends_on:
  - docs/superpowers/specs/2026-09-12-shared-boundary-redraw-design.md
  - docs/superpowers/specs/2026-09-14-mode-b-chg-design.md
scope: 治理层归属迁移 + 3 条 realign 规则改写
shelved: 2026-09-15
shelved_reason: |
  ROI 判定：模式 B 全套需改 50+ 文件、跨 21 个 skill（新对象 + 新 skill + 验收契约
  + 11 个消费点改写 + 红绿协议变体 + 治理层迁移 35 处/31 文件）；而实证样本 ai-code
  已用自建 00-id-registry.md、自写等价迁移方法论适应了现状，摩擦真实但不阻塞出活。
  触发条件（第二个项目撞同一堵墙）未出现。
  ⇒ 已提交的是第 1 轮成果（4 文件 +119/−11）：id/prefix-consumption-contract
  + health-lint id/unknown-prefix，直接治「治理工具看不见自造前缀」这一报告症状。
shelved_value: |
  本稿不作废——它把「重构工作在 DevDocs 里为什么别扭」查到了 文件:行 级别，
  将来真要做时省掉全部调研。最关键的一条：task-orchestration.md:595
  「新测试意外通过 ⇒ 测试无效」与行为保持根本冲突——保持性回归测试在改动前
  就该通过，照现协议会被判无效。
reactivate_when: 第二个项目在技术升级/重构/治理上撞同一堵墙
---

# 中立治理层

## 0. 要解决的一件事

治理扫描（`realign` / `health-lint`）现在归模式 A 的编排器 `ms-pipeline` 所有。

模式 B 并行后，治理层要**按产物把校验分发给 A 或 B 的私有 validator**。这个分发逻辑住在 A 的 skill 里就是结构错。

⇒ **把逻辑搬到中立归属，用户命令不变。**

⚠️ **v1 称这是「纯搬运」，错了。** §1 实测：至少 3 处是真调度/动作，另有命名撞车与报告协议冲突。**这是协议迁移，⛔ 不是 `git mv`。**

## 1. ⛔ 「逻辑已经中立」是错的（v1 的核心断言被证伪）

v1 称「1258 行里 23 处提及，⛔ 无一处是真逻辑耦合」。外部审查逐条打开后，**至少 3 处是真调度/动作**：

| 位置 | 内容 | 性质 |
|---|---|---|
| `realign.md:57` | 「**分组：按 A 类（DevDocs 主链路产物）与 B 类（PRD 流程 / insights / onboard）分别分组差距项**」 | 🔴 **真调度规则**，硬绑 A 的产物分类 |
| `realign-scope-health.md:220` | 「明细落到 `04-dev-tasks-pNN.md` 或 ADR 对应文件」 | 🔴 **修复动作**，写 A 的产物 |
| `health-lint-implementation.md:253-268` | 定义与引用扫描**硬编码前缀 + Markdown 形状**（heading / 表格首列 / 列表项）| 🔴 `CHG` 的定义在 YAML `id:` 里，**补前缀也匹配不上** |

### 1.1 一个必须先解决的命名撞车

`realign.md:57` 的 **「A 类 / B 类」和本设计的「模式 A / 模式 B」是两回事**：

- 那里的 A 类 = DevDocs 主链路产物（01~04），B 类 = PRD / insights / onboard 旁路
- 本设计的 A = 需求功能模式，B = 技术变更模式

⛔ **同一份文件里两套 A/B 含义，落地时必然被混淆。** 迁移前必须先给其中一套改名。

### 1.2 报告协议也冲突

本稿 §4.3 要求四分节、⛔ 不合并总分；而拟原样搬迁的 `realign-scope-health.md` 强制旧维度 + `total_score` + 总分门（`:118-145` `:165-186` `:205` `:253-254`）。

⇒ **这不是"搬一个已经中立的东西"，是协议迁移。**

## 2. 迁移

### 2.1 新建 `ms-govern`

```
skills/ms-govern/
├── SKILL.md                              # 新建：入口 + 模式分发
└── references/
    ├── realign.md                        # ← ms-pipeline/references/
    ├── realign-scope-health.md           # ← 同上
    └── health-lint-implementation.md     # ← 同上
```

⛔ **不放 `_shared/`**——`_shared/SKILL.md` 自己声明「本目录**不提供流程**，只提供被其他 skill 引用的权威文件」。治理扫描是流程（有入口、有 Phase、有 apply），放进去就破坏 `_shared` 的定位。

### 2.2 用户命令不变

| 命令 | 状态 |
|---|---|
| `/ms-govern [--scope=…]` | **canonical**，新文档指向它 |
| `/ms-pipeline realign [--scope=…]` | **永久 alias**，行为完全相同 |

⛔ **不标 deprecated、⛔ 不设移除期。** 理由：`realign/deprecated-alias-one-version` 规定 alias 下一版本移除，而移除会打断用户已有的肌肉记忆——这与 [flow-backlog 第 1 条](../../audits/2026-09-11-devdocs-flow-backlog.md)「减少用户面子指令露出」同向：**减少的是需要记的东西，不是能用的东西。**

⇒ `ms-pipeline` 保留的是一行转发，⛔ 不保留治理逻辑。

### 2.3 引用改写：25 个文件

| 形态 | 文件数 | 改法 |
|---|---:|---|
| 样板行 `> 共享契约见 [../../ms-pipeline/references/realign.md](…)`<br>**11 个 `references/realign.md` + 1 个 `ms-verify/references/schema-drift.md`** | **12** | `sed` 批量替换路径 |
| `SKILL.md` 正文内引用 | **9** | 逐个改 |
| `_shared/constraints.md`（3 处指针规则）| 1 | 见 §3 |
| 其他（`agent-memory` 模板 · `workspace-topology/protocol.md` · `ms-prd` 治理）| **3** | 逐个改 |

> ✅ **路径深度不变**：`ms-govern/` 与 `ms-pipeline/` 是同级目录，`../../ms-pipeline/references/x.md` → `../../ms-govern/references/x.md`，`../` 层数不动。⇒ **纯目录名替换，⛔ 不需要重算相对路径。**
>
> ✅ **已实测 12 行写法一致**：11 行完全相同，1 行（`ms-system-design`）在句尾多一段说明，但**路径子串完全相同** ⇒ 按路径子串替换对 12 行全部安全。改完仍跑 §6 第 2 条的 `[ -f ]` 逐个验证。

## 3. 三条 `realign/*` 规则改写

第 1 步已标 `[pending:C]`，本步执行。

| 行 | rule_id | 现在 | 改为 |
|---:|---|---|---|
| 324 | `realign/single-entry` | 「统一通过 `/ms-pipeline realign [--scope=…]` 入口」 | 「统一通过治理层入口 `/ms-govern`（`/ms-pipeline realign` 为永久 alias）」 |
| 325 | `realign/scope-enum-authority` | scope 白名单位于 `skills/ms-pipeline/references/realign.md` | → `skills/ms-govern/references/realign.md` |
| 326 | `realign/no-direct-user-call` | 「用户面**只承认** `/ms-pipeline realign` 入口」 | 「用户面只承认 `/ms-govern` 及其 alias」 |

另需改的两条指针（第 1 步未标，本步一并）：

- `realign/shared-contract-pointer`（行 331）→ 指向 `ms-govern`
- `realign/health-execution-pointer`（行 333）→ 指向 `ms-govern`

## 4. 模式分发

### 4.1 B ⛔ 不需要新 scope

现有 scope（`spec` / `health` / `prd-mapping` / `layout`）对 `CHG` 产物同样成立：

- `spec` 查 `spec_version` drift —— `CHG` 有 `change.v1`，一样要查
- `health` 查文档健康度 —— `CHG` 一样会膨胀、死链

⇒ **需要扩的是扫描范围，⛔ 不是 scope 枚举。** 扫描范围从 `docs/devdocs/**/*.md` 自然覆盖 `changes/CHG-*.md`（现有 health scope 已递归扫 `docs/devdocs/**/*.md`）。

### 4.2 分发键：frontmatter，⛔ 不是路径

```
读产物 frontmatter 的 spec_version：
  req.v3 / design.v3 / test.v2 / tasks.v2 / …  → 模式 A validator（⚠️ 实测常量，⛔ 非 v3）
  change.v1                                     → 模式 B validator
  （无 spec_version）                            → 报 schema/spec-version-legacy，⛔ 不猜
```

⛔ **不按目录路径分发。** 路径是约定，frontmatter 是声明——这与 [模式 B §2.2](2026-09-14-mode-b-chg-design.md)「机器要解析的东西不得靠约定推断」同源。

### 4.3 报告分节，⛔ 不合并成单一总分

```yaml
dimensions:
  shared:      # 两模式共同适用的 rule
  mode_a:      # A 私有 validator
  mode_b:      # B 私有 validator
  cross_ref:   # 跨模式引用（F depends_on CHG 之类）的完整性
```

⛔ **不把 A 和 B 的分数平均。** 一个项目可能 A 健康 B 糟糕，合并后看不出来。

## 4.4 ⛔ 定义扫描必须先认 YAML `id:`

`health-lint-implementation.md:253-268` 的定义索引只认三种 Markdown 形状：heading / 表格首列 / 列表项。

`CHG` 的定义在 frontmatter 的 `id: CHG-007`。**给旧正则补一个 `CHG` 前缀也匹配不上**——形状就不对。

内存复算：

```text
输入：YAML id: CHG-007，正文标题不含编号
旧定义模式 + CHG 前缀 ⇒ 定义命中 = 0，引用命中 = 1
⇒ 每个 CHG 都会被报成「引用了未定义的编号」
```

⇒ **必须给定义索引加一种形状：frontmatter `id:` 字段。** 这是 B 能被治理的前提，⛔ 不是可选优化。

## 5. 改动清单

| # | 动作 | 处数 |
|---|---|---:|
| 1 | `git mv` 三个 reference 文件到 `skills/ms-govern/references/` | 3 |
| 2 | 新建 `skills/ms-govern/SKILL.md`（入口 + §4 分发 + 指向三个 reference）| 1 |
| 3 | `ms-pipeline/SKILL.md` 删治理正文，改为一行转发 | 1 |
| 4 | 12 个 skill 的 `references/realign.md` 样板行 `sed` 换路径 | 12 |
| 5 | 9 个 `SKILL.md` 正文引用逐个改 | 9 |
| 6 | 其他 3 个文件（`agent-memory` / `workspace-topology` / `ms-prd`）| 3 |
| 7 | `_shared/constraints.md` 5 条规则改写（§3）+ 去掉 `[pending:C]` 标记 | 1 |
| 8 | `docs/architecture.md` 治理章节的指向 | 1 |
| **9** | **解决 A/B 命名撞车**（§1.1）——给 `realign.md` 的旧 A 类/B 类改名 | 1 |
| **10** | **定义索引加 frontmatter `id:` 形状**（§4.4）| 1 |
| **11** | **统一报告协议**（§1.2）——旧 `total_score` 总分门 vs 新四分节 | 1 |
| **12** | `realign/deprecated-alias-one-version` 加永久 alias 例外（§2.2 需要它）| 1 |

**合计 35 处 / 31 个逻辑文件**（12 样板 + 9 SKILL + 3 其他 + `constraints.md` + `architecture.md` + 新建 `ms-govern/SKILL.md` + 改 `ms-pipeline/SKILL.md` + 3 个被搬文件）。

> ⚠️ **「处」⛔ 不等于文本替换次数**：25 个文件里完整旧路径出现 **45 次**。批量替换按次数算，人工核对按处算。

## 6. 验收

| 判据 | 怎么验 |
|---|---|
| ⛔ 无残留旧路径 | `grep -rn 'ms-pipeline/references/\(realign\|health-lint\)' skills/` 零命中。⚠️ **⛔ 不扫 `docs/`**——设计稿与历史审计文件**本来就要保留旧路径作取证**，按 v1 的判据永远归不了零 |
| 链接可达 | 逐个 `[ -f ]` 检查改后路径存在 |
| 用户命令不变 | `/ms-pipeline realign --scope=health` 仍走通（alias 转发）|
| `ms-pipeline` 不再含治理逻辑 | ⚠️ **⛔ 不用关键词计数当判据**——一段委托错误只出现一次也会通过。改为：逐条读剩余的 realign/health 段落，确认全部是转发说明 |
| 分发正确 | 造一个 `change.v1` frontmatter 的样例产物，确认走 B 分支 |

## 7. 代价与未决

### 代价

1. **35 处改动，其中 4 处是协议改写、⛔ 非机械搬运**（§5 的 9~12）。v1 把整件事称作「纯搬运」，低估了。
2. **`ms-govern` 是第 23 个 `ms-*`**（按 B→A→C，`ms-change` 先落地占第 22）、第 42 个 skill。 与"减少概念"方向相反——但它换掉的是"A 的编排器拥有 B 的治理"这个结构错，⛔ 不是净新增功能。
3. **B 的私有 validator 目前是空的。** `ms-govern` 先立分发骨架，B 的规则随模式 B 落地再填。⚠️ 骨架空转期间，分发逻辑没有第二个消费方验证它是否真中立。

### 未决

| # | 问题 |
|---|---|
| 1 | skill 名 `ms-govern`（本文暂用）|
| 2 | ~~执行顺序~~ —— ⛔ **已定为 B→A→C（用户决策 9），⛔ 不得重新打开**。v1 把它列为未决是错的 |
| 3 | `realign/deprecated-alias-one-version` 与 §2.2「永久 alias」冲突，需在 `constraints.md` 加一条例外说明 |
