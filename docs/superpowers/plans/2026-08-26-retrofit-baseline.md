# ms-retrofit 建立项目基线 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 删除 `ms-retrofit` 的代码逆向推导，改为建立 `docs/devdocs/00-baseline.md`，并修复因此产生的 6 处下游断点。

**Architecture:** 本仓是 Markdown 规格库，无代码、无 build/test/lint 命令。「实现」= 改写 SKILL.md 与 references/templates；「测试」= 可执行的 grep 断言 + markdownlint 类型集不退化 + SKILL.md ≤ 500 行。每个任务先写断言（此时必然失败），再改文件，再跑断言。

**Tech Stack:** Markdown + YAML frontmatter；`markdownlint-cli2`（经 `npx --no-install`）；`grep` / `wc` 做断言。

**Spec:** [docs/superpowers/specs/2026-08-25-retrofit-baseline-design.md](../specs/2026-08-25-retrofit-baseline-design.md)

## Global Constraints

以下为全局要求，每个任务的验收隐含包含本节。

- **lint 判据是「错误类型集不新增」，不是零错误。** 本仓无 markdownlint 配置，存量文件均有错误。判据：改动后该文件的 `MD` 类型集 ⊆ 改动前的类型集。各文件改动前基线（已实测）：

  | 文件 | 改动前类型集 |
  |---|---|
  | `skills/retrofit/SKILL.md` | MD013 MD022 MD024 MD032 MD040 MD060 |
  | `skills/feature/SKILL.md` | MD013 MD024 MD032 MD040 MD060 |
  | `skills/bugfix/SKILL.md` | MD013 MD040 MD060 |
  | `skills/onboard/SKILL.md` | MD013 MD022 MD031 MD032 MD040 MD060 |
  | `skills/pipeline/SKILL.md` | MD013 MD029 MD032 MD040 MD060 |
  | `skills/dev-workflow/SKILL.md` | MD007 MD013 MD022 MD024 MD028 MD032 MD060 |
  | `skills/verify/SKILL.md` | MD013 MD028 MD032 MD040 MD056 MD060 |
  | `skills/requirements/references/context-mode.md` | MD001 MD034 MD060 |

- ⛔ **绝不为压低 MD060 而改表格分隔符风格**（Goodhart：指标好看了，可读性坏了）。
- **`SKILL.md` ≤ 500 行是硬约束。** 现状：retrofit 291 / feature 332 / bugfix 483 / onboard 452 / pipeline 414 / dev-workflow 422 / verify 441。**`bugfix` 只剩 17 行余量**，改动必须是等量替换。
- **提交规范**：Conventional Commits，中文描述。每个 commit 末尾附
  `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`
- **语言**：文档用中文。
- **不动版本迁移路径**：`ms-retrofit` 的「旧 DevDocs → 新规范」那条腿整体不改，含它的 `00-retrofit-report.md`。
- **不迁移存量逆向产物**：已生成的 F/US/AC 留在原地。
- **`git mv` 保留历史**：本计划无文件重命名，此条不触发。

---

## 文件结构

| 文件 | 责任 | 任务 |
|---|---|---|
| `skills/retrofit/templates/baseline-template.md` | 🆕 基线产物的形状（六节 + 来源标注） | 1 |
| `skills/retrofit/references/realign.md` | 🆕 `baseline.v1` 常量 + 禁止自动覆盖 | 1 |
| `skills/retrofit/SKILL.md` | 主改：description / allowed-tools / 检测 / 流程 / 约束 / 摘要 / 输出 | 2 |
| `skills/retrofit/references/new-project-retrofit.md` | 重写为建立基线流程 | 2 |
| `skills/retrofit/templates/retrofit-report-template.md` | 瘦身，只服务版本迁移 | 2 |
| `skills/feature/SKILL.md` | 前置条件加 `00-baseline.md`（解死循环） | 3 |
| `skills/bugfix/SKILL.md` | 「关联功能」允许 `baseline` | 3 |
| `skills/pipeline/SKILL.md` | 路由表加「仅基线」行 | 3 |
| `skills/onboard/SKILL.md` | 提取源加基线 + 文案去逆向 | 4 |
| `skills/dev-workflow/SKILL.md` | 探索模式承诺改写 | 4 |
| `skills/requirements/references/context-mode.md` | SSOT 边界 + 基线增量补全入口 | 5 |
| `skills/verify/SKILL.md` | `coverage_scope: post-baseline` | 5 |
| `skills/verify/templates/verify-report.md` | `coverage_scope` 字段 | 5 |
| `skills/sync/SKILL.md` | `coverage_scope` 标注 | 5 |
| `skills/verify/references/schema-drift.md` | 登记 `00-baseline.md` | 6 |
| `AGENTS.md` | 记录本次改动 | 6 |

---

### Task 1: 基线产物定义

产出基线的「形状」。后续所有任务都引用它，所以它必须先落地。

**Files:**
- Create: `skills/retrofit/templates/baseline-template.md`
- Create: `skills/retrofit/references/realign.md`

**Interfaces:**
- Consumes: 无（首个任务）
- Produces: 文件路径常量 `docs/devdocs/00-baseline.md`；frontmatter 字段 `generated_by: ms-retrofit` / `spec_version: baseline.v1` / `generated_at` / `adoption_commit`；六个章节标题（`## 1. 建立记录` / `## 2. 项目目的与边界` / `## 3. 代码外部的硬约束` / `## 4. 仍在约束未来改动的护栏` / `## 5. 已知未知 + 证据冲突` / `## 6. 权威来源地图`）；四档来源标注枚举 `用户确认` / `已有文档` / `推导待确认` / `未知`；三档校验标记 `已佐证` / `未可验` / `与代码矛盾`。Task 2 的 SKILL.md 与 Task 6 的 schema-drift 登记均按这些字面量匹配。

- [ ] **Step 1: 写断言脚本，先跑一次确认失败**

创建 `/tmp/t1-check.sh`：

```bash
#!/bin/bash
cd /Users/mason/Projects/skills
fail=0
chk(){ if eval "$2" >/dev/null 2>&1; then echo "PASS  $1"; else echo "FAIL  $1"; fail=1; fi; }

T=skills/retrofit/templates/baseline-template.md
R=skills/retrofit/references/realign.md

chk "模板文件存在"        "test -f $T"
chk "realign 文件存在"    "test -f $R"
chk "spec_version 常量"   "grep -q 'baseline.v1' $R"
chk "禁自动覆盖"          "grep -q '不得被自动覆盖' $R"
chk "frontmatter generated_by" "grep -q 'generated_by: ms-retrofit' $T"
chk "frontmatter spec_version" "grep -q 'spec_version: baseline.v1' $T"
chk "frontmatter adoption_commit" "grep -q 'adoption_commit' $T"
for s in '## 1. 建立记录' '## 2. 项目目的与边界' '## 3. 代码外部的硬约束' \
         '## 4. 仍在约束未来改动的护栏' '## 5. 已知未知 + 证据冲突' '## 6. 权威来源地图'; do
  chk "章节 $s" "grep -qF '$s' $T"
done
for a in 用户确认 已有文档 推导待确认 未知 已佐证 未可验 与代码矛盾; do
  chk "标注枚举 $a" "grep -q '$a' $T"
done
chk "禁清单条款"          "grep -q '不得出现' $T"
chk "安全默认动作"        "grep -q '安全默认动作' $T"
chk "护栏三要素-决定"     "grep -q '\*\*决定\*\*' $T"
chk "护栏三要素-约束"     "grep -q '\*\*约束\*\*' $T"
chk "护栏三要素-依据"     "grep -q '\*\*依据\*\*' $T"
# 反向断言：基线模板不得出现被禁的清单类章节
chk "无模块表标题"        "! grep -qE '^\|.*模块.*\|.*路径.*\|' $T"
exit $fail

```

- [ ] **Step 2: 跑断言，确认失败**

Run: `bash /tmp/t1-check.sh`
Expected: 大量 `FAIL`，退出码 1（文件都还不存在）

- [ ] **Step 3: 创建 `skills/retrofit/templates/baseline-template.md`**

写入以下**完整内容**（这是给用户项目复制用的模板，内联具体值是允许的——模板复制进项目后 skill 不在场）：

````markdown
# 项目基线模板

> 使用此模板生成 `docs/devdocs/00-baseline.md`。
>
> 判据见 [spec §3](../../../docs/superpowers/specs/2026-08-25-retrofit-baseline-design.md)：基线只装**重扫代码无法重建**的信息。

---

```markdown
---
generated_by: ms-retrofit
spec_version: baseline.v1
generated_at: <ISO8601，如 2026-08-26T10:00:00+08:00>
adoption_commit: "<git rev-parse HEAD 输出>"
---

# 项目基线：<项目名>

> 本文只记录**重扫代码无法重建**的信息。
> 模块 / 接口 / 数据对象 / 技术栈 → `docs/codebase-insight.md`；当前进度 / 待办 → `docs/devdocs/00-context.md`。
>
> 每条非生成内容都带来源标注：`用户确认` / `已有文档` / `推导待确认` / `未知`。
> ⛔ `推导待确认` **不因无人反对而升格**为 `用户确认`。

## 1. 建立记录

| 项 | 值 |
|---|---|
| adoption_commit | `<hash>` —— DevDocs 接管的分界线，固定不变 |
| 建立日期 | YYYY-MM-DD |
| 工作区状态 | 干净 / dirty（`<n>` 个未提交改动） |
| 构建 | `<命令>` → ✅ 通过 / ❌ 失败：`<摘要>` / ⏭️ 无构建 |
| 测试 | `<命令>` → ✅ `<n>` 通过 / ❌ `<n>` 失败 / ⏭️ 无测试 |

构建与测试是**实跑结果**，不是推测。跑不起来就如实记跑不起来——它标定的是基线时点的可信度，让后来的会话知道红了不是自己弄坏的。

**本基线的局限**（`推导待确认` 与 `未知` 汇总）：

- [ ] `<条目>` —— 未知
- [ ] `<条目>` —— 推导待确认，依据 `<file:line>`

## 2. 项目目的与边界

**做什么**：`<...>` `[用户确认]`

**明确不做什么**：`<...>` `[已有文档 README.md:12 · 已佐证]`

「不做什么」和「做什么」同等重要——不知道边界，接手者会接受任何需求。

> 整节推不出来时，如实写：
> ⚠️ **未知** —— 调查过 README / CHANGELOG / 早期提交 / issue，未找到关于项目目的的陈述；接手时亦无交接。

## 3. 代码外部的硬约束

判据：**不读生产环境、外部系统或历史协议，单看本仓代码无法可靠知道**的事实。

| 约束 | 内容 | 来源 |
|---|---|---|
| 真实消费者 | `<谁在调这个系统>` | `用户确认` |
| 数据归属 | `<哪些数据不归本系统管>` | `未知` |
| 兼容范围 | `<必须兼容的版本 / 协议>` | `已有文档 <path:line> · 未可验` |
| 部署边界 | `<部署在哪、受什么限制>` | `未知` |
| 不可逆操作 | `<哪些操作做了收不回来>` | `推导待确认，依据 <file:line>` |
| 安全 / 合规 | `<合规要求>` | `未知` |

这一类最实用：「这个接口有外部消费者，改了炸别人」——单读代码绝对不知道，改了就出事。

## 4. 仍在约束未来改动的护栏

⛔ **三要素缺一不写。** 写不出「它约束哪些改动」的，是变更历史不是护栏——不要写进来。

### G-1: `<护栏一句话>`

- **决定**：`<当前决定是什么>`
- **约束**：`<它禁止 / 要求哪些改动>`
- **依据**：`<来源；完整推理若存在 → ADR 指针>`
- **来源**：`用户确认` / `已有文档 <path:line>` / `推导待确认`

> 正例：「不要重新引入多需求并行——已实践证伪，整套机器已删除」（写得出「约束哪些改动」）
> 反例：「某年某月试过多需求并行，后来删了」（流水账，写不出约束，出局）

## 5. 已知未知 + 证据冲突

> 对接手者（尤其是 LLM）而言，「不要把这个推断当事实」往往比一段架构介绍有价值得多。

### 5.1 已知未知

| # | 不确定的是 | 确认前的安全默认动作 |
|---|---|---|
| U-1 | `<...>` | `<在确认前该怎么做>` |

⛔ **每条必须有「安全默认动作」。** 只说「不确定」不说「那怎么办」，等于把判断又扔回给最容易猜错的一方。

### 5.2 证据冲突

| # | 文档声称 | 代码实际 | 裁定 |
|---|---|---|---|
| C-1 | `README.md:8` 说用 Redis 做分布式锁 | `src/lock/` 是数据库行锁 | 以代码为准；文档已过期或从未实现 |

文档陈述**不删除**——「曾经打算做 X」本身是关于项目历史的信息。

## 6. 权威来源地图

| 想知道 | 信谁 |
|---|---|
| 代码现在是什么 | 当前代码；`docs/codebase-insight.md`（其 `commit_hash` 与 HEAD 一致时） |
| 当前在做什么、下一步 | `docs/devdocs/00-context.md` |
| 项目边界、外部约束、护栏、未知项 | **本文** |
| 新需求该怎么做 | `docs/devdocs/01-requirements.md` 等 DevDocs 正式产物 |

⛔ 代码是「**在做什么**」的权威，**不是**「还在被用吗 / 做对了吗」的权威。死代码和活代码长得一模一样；关掉的 feature flag、没人调的端点、固化了 Bug 的逻辑，代码都不会告诉你。这类判断走本文 §5。

```

---

## ⛔ 本模板不得出现的内容

| 禁项 | 去哪儿 |
|---|---|
| 模块表 / 接口表 / 数据对象表 / 依赖图 / 技术栈清单 / 目录结构树 | `docs/codebase-insight.md` |
| 当前分支 / 未提交改动 / 完成率 / 待办 | `docs/devdocs/00-context.md` |
| 逆向推出的 F / US / AC / 用户故事 | 不产出（spec §1） |
| 泛化的编码规范、提交规范、工具使用说明 | `/code-quality`、`AGENTS.md` |
| 旧文档全文摘录、完整变更历史、流水账式决策过程 | 不产出 |
| 从实现细节推导出的「必须保持此行为」 | 不产出 |
| 没有来源、没有适用范围、没有可信状态的自信陈述 | 不产出 |

**最大的危害不是过时，是把实现偶然性写成设计意图。** 后续读者（尤其是 LLM）会把它当约束**主动保护**——保护的可能只是一个 bug、一笔技术债，或一段早已失效的行为。过期的信息读者还会怀疑，被写成「设计意图」的偶然性没人会去质疑。

````

- [ ] **Step 4: 创建 `skills/retrofit/references/realign.md`**

写入以下完整内容：

```markdown
# retrofit Realign 实例化

> 共享契约见 [../../pipeline/references/realign.md](../../pipeline/references/realign.md)。

## 当前 spec_version

**`baseline.v1`**（MVP 起点）

适用产物：`docs/devdocs/00-baseline.md`（`ms-retrofit` 基线路径产出）。

版本迁移路径的 `00-retrofit-report.md` 是一次性报告、非持久 A/B 类产物，不纳入 `spec_version` 体系。

## Migration Matrix（保留字段）

### v1 → v2（未来启用）

| 分级 | 变更项 | 修复动作 | 判据 |
|---|---|---|---|
| additive | （示例）新增章节 | 追加章节占位，标注待人工填写 | §章节缺失 |
| restructuring | （示例）来源标注枚举扩展 | AskUserQuestion 呈现 before/after | 标注值不在枚举内 |

## Realign 子流程

入口：`/ms-pipeline realign --scope=spec` 编排调度。

⛔ **基线不得被自动覆盖重生成。** realign 只做**结构性**查漏补缺（缺失章节追加占位、frontmatter 字段补齐），**不得改写任何带 `用户确认` / `已有文档` / `推导待确认` 标注的正文内容**——那些是问人和挖证据得来的，重生成产不出来。

判据见 [spec §2 派生 vs 原生](../../../docs/superpowers/specs/2026-08-25-retrofit-baseline-design.md)：`codebase-insight.md` 与 `00-context.md` 可被扫描重建，基线不可。把基线当可重生成产物处理，等于把它降级成前两者的副本。

```

- [ ] **Step 5: 跑断言，确认全部通过**

Run: `bash /tmp/t1-check.sh`
Expected: 全部 `PASS`，退出码 0

- [ ] **Step 6: lint 类型集检查（新文件，判据是不引入基线之外的类型）**

Run:

```bash
cd /Users/mason/Projects/skills
for f in skills/retrofit/templates/baseline-template.md skills/retrofit/references/realign.md; do
  echo "$f: $(npx --no-install markdownlint-cli2 "$f" 2>&1 | grep -oE 'MD[0-9]+' | sort -u | tr '\n' ' ')"
done

```

Expected: 类型集 ⊆ `MD013 MD022 MD024 MD031 MD032 MD040 MD046 MD060`（本仓 skills 目录常见类型全集）。若出现该集合外的类型，修掉再继续。

- [ ] **Step 7: 提交**

```bash
cd /Users/mason/Projects/skills
git add skills/retrofit/templates/baseline-template.md skills/retrofit/references/realign.md
git commit -m "$(cat <<'EOF'
feat(retrofit): 新增基线模板与 baseline.v1 治理身份

00-baseline.md 六节：建立记录 / 项目目的与边界 / 代码外部的硬约束 /
仍在约束未来改动的护栏 / 已知未知+证据冲突 / 权威来源地图。

四档来源标注（用户确认 / 已有文档 / 推导待确认 / 未知）+ 三档校验标记
（已佐证 / 未可验 / 与代码矛盾）。护栏节要求三要素缺一不写，该要求同时
是流水账过滤器。realign.md 锁死「基线不得被自动覆盖重生成」。

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"

```

---

### Task 2: retrofit 主体改造

删除逆向推导，接上基线流程，并修「重入死循环」与 `allowed-tools` 缺 `Task` 两个缺陷。

**Files:**
- Modify: `skills/retrofit/SKILL.md`（frontmatter / 工作流程 / 项目状态检测 / 新项目改造流程 / 改造报告 / 约束 / 子 Agent 摘要 / 输出文件）
- Modify: `skills/retrofit/references/new-project-retrofit.md`（整体重写）
- Modify: `skills/retrofit/templates/retrofit-report-template.md`（瘦身）

**Interfaces:**
- Consumes: Task 1 的 `docs/devdocs/00-baseline.md` 路径、六个章节标题、`baseline.v1`
- Produces: 检测终态第三值「基线已建」（Task 3 的 pipeline 路由与 Task 6 的一致性扫描依赖它）；摘要契约字段 `baseline_established: true` 与 `adoption_commit`；`next_recommended.skill: ms-feature`

- [ ] **Step 1: 写断言脚本，先跑一次确认失败**

创建 `/tmp/t2-check.sh`：

```bash
#!/bin/bash
cd /Users/mason/Projects/skills
fail=0
chk(){ if eval "$2" >/dev/null 2>&1; then echo "PASS  $1"; else echo "FAIL  $1"; fail=1; fi; }

S=skills/retrofit/SKILL.md
N=skills/retrofit/references/new-project-retrofit.md
P=skills/retrofit/templates/retrofit-report-template.md

# --- 删除类断言 ---
chk "description 去掉 逆向"        "! grep -n 'description:' $S | grep -q '逆向'"
chk "description 去掉 从代码生成文档" "! grep -n 'description:' $S | grep -q '从代码生成文档'"
chk "description 去掉 Reverse-engineer" "! grep -n 'description:' $S | grep -qi 'Reverse-engineer'"
chk "SKILL 无 US-XXX 逆向"          "! grep -q '测试描述.*US-XXX' $N"
chk "SKILL 无 AC-XXX 逆向"          "! grep -q '测试断言.*AC-XXX' $N"
chk "new-project 无逆向推导表"      "! grep -q '路由/页面.*F-XXX' $N"
chk "无 UT/IT/E2E 逆向登记"         "! grep -q '单元测试文件.*UT-XXX' $N"
chk "编号约束已删"                  "! grep -q '必须为所有用户故事分配 US-XXX 编号' $S"
chk "摘要无 new_ids features"       "! grep -q 'features: \[F-001' $S"
chk "报告模板无编号分配表"          "! grep -q '功能点 (F)' $P"

# --- 新增类断言 ---
chk "allowed-tools 含 Task"         "grep -n 'allowed-tools' $S | grep -q 'Task'"
chk "description 含 基线"           "grep -n 'description:' $S | grep -q '基线'"
chk "SKILL 提及 00-baseline.md"     "grep -q '00-baseline.md' $S"
chk "检测有第三终态 基线已建"       "grep -q '基线已建' $S"
chk "检测排除 01~04 判据"           "grep -q '只有 00-baseline.md' $S"
chk "委托 codebase-insight"         "grep -q 'ms-codebase-insight' $S"
chk "摘要含 baseline_established"   "grep -q 'baseline_established' $S"
chk "摘要含 adoption_commit"        "grep -q 'adoption_commit' $S"
chk "next_recommended 指向 feature" "grep -q 'ms-feature' $S"
chk "约束含基线禁清单"              "grep -q '不得出现模块表' $S"
chk "约束含 我也不清楚 出口"        "grep -q '我也不清楚' $S"
chk "约束含 推导待确认 不升格"      "grep -q '不得因用户沉默' $S"
chk "new-project 有调查步骤"        "grep -q '调查' $N"
chk "new-project 有校验步骤"        "grep -q '与代码矛盾' $N"
chk "new-project 引用模板"          "grep -q 'baseline-template.md' $N"
chk "报告模板仅服务版本迁移"        "grep -q '仅版本迁移路径' $P"

# --- 硬约束 ---
chk "SKILL.md ≤ 500 行"            "[ \$(wc -l < $S) -le 500 ]"
exit $fail

```

- [ ] **Step 2: 跑断言，确认失败**

Run: `bash /tmp/t2-check.sh`
Expected: 多条 `FAIL`（新增类全 FAIL，删除类部分 FAIL），退出码 1

- [ ] **Step 3: 改 `skills/retrofit/SKILL.md` frontmatter**

把第 2–4 行整体替换为：

```yaml
name: ms-retrofit
description: Retrofit existing projects to DevDocs workflow, or migrate old DevDocs to new standards. For projects without docs, establish a project baseline recording what code cannot answer. Use when users want to adapt existing projects, take over legacy code, migrate documentation, standardize documents, or upgrade DevDocs version. Triggers on "retrofit", "改造", "适配", "迁移", "标准化", "基线", "摸底", "接手项目", "升级文档", "existing project", "已有项目". NOT for initializing new projects (use ms-pipeline), adding features to existing DevDocs (use ms-feature), or code inventory (use ms-codebase-insight).
allowed-tools: Read, Write, Glob, Grep, AskUserQuestion, Bash, Task

```

`Task` 是新增的——正文两处早已写着 `Task: /workspace-topology reconcile` 与 `Task: /agent-memory --update`，但 `allowed-tools` 一直没有它，属既存缺陷；本次委托 `ms-codebase-insight` 也需要它。

- [ ] **Step 4: 替换「工作流程」整节**

把 `## 工作流程` 到下一个 `---` 之间的 ASCII 流程图替换为：

```text
1. 扫描项目结构
   │
   ▼
2. 检测项目状态
   │
   ├── 无 docs/devdocs/ ──────────────────► 建立项目基线
   │
   ├── 只有 00-baseline.md（无 01~04）───► 基线已建，终态，无需改造
   │
   ├── 有 DevDocs（符合规范）────────────► 无需改造
   │
   └── 有 DevDocs（旧版）────────────────► 版本迁移
   │
   ▼
3. 呈现方案 + AskUserQuestion 确认
   │
   ▼
4. 执行
   │
   ├── 建立基线：调查 → 校验 → 推导 → 提问 → 落盘 00-baseline.md
   └── 版本迁移：更新迁移文档 → 生成/更新 docs/devdocs/
   │
   ▼
5. 收尾
   │
   ├── 基线路径：不产报告（建立记录已在基线内）
   └── 版本迁移：生成 00-retrofit-report.md

```

- [ ] **Step 5: 替换「项目状态检测」的检测逻辑**

把 `### 检测逻辑` 下的代码块替换为：

````markdown
```text
1. docs/devdocs/ 是否存在？
   │
   ├── 不存在 → 建立项目基线
   │
   └── 存在 → 目录内是否只有 00-baseline.md（无 01~04）？
       │
       ├── 是 → 基线已建（第三终态）→ 无需改造，提示下一步 /ms-feature
       │
       └── 否 → 规范符合性检查
           │
           ├── 符合当前规范 → 无需改造
           │
           └── 不符合 → 版本迁移流程

```

⛔ **「基线已建」是与「符合规范」并列的第三种终态，不是「旧版待迁移」。**

基线项目一项编号都没有，若直接进规范符合性检查，会被判成「缺少 F/US/AC 编号 ⚠️ 需迁移」，
于是版本迁移流程**试图把刚建好的基线项目迁回旧的编号形态**——用户第二次跑 `/ms-retrofit`
就会撞上这个死循环。判据必须在规范检查**之前**短路。

````

- [ ] **Step 6: 替换「新项目改造流程」整节**

把 `## 新项目改造流程（无 DevDocs）` 整节（到下一个 `---`）替换为：

```markdown
## 建立项目基线（无 DevDocs）

当项目没有 DevDocs 文档时执行。完整流程（调查范围 / 校验规则 / 来源标注 / 提问纪律 / 落盘）见 [references/new-project-retrofit.md](references/new-project-retrofit.md)，产物形状见 [templates/baseline-template.md](templates/baseline-template.md)。

**基线只记录重扫代码无法重建的信息。** 模块 / 接口 / 数据对象 / 技术栈归 `docs/codebase-insight.md`；当前进度 / 待办归 `docs/devdocs/00-context.md`。

要点：

- Step 1 调查：委托 `ms-codebase-insight` 摸排 + README / CHANGELOG / git 提交信息 / issue·PR / 实跑构建测试
- Step 2 校验：拿代码检验文档里每条可验证陈述 → `已佐证` / `未可验` / `与代码矛盾`
- Step 3 推导：起草带依据标注的草案，每条写清「据什么」
- Step 4 提问：只问推不出、依据薄弱、或校验出矛盾的项；⛔ 每题必须有「我也不清楚」出口
- Step 5 落盘：`docs/devdocs/00-baseline.md`，不产 `01`~`04`

**存量代码不编号。** `01-requirements.md` 由首次 `/ms-feature` 创建，`F-001` 从新需求起。
改造完成到首个需求之间，`/ms-board`、`/ms-test-cases`、`/ms-verify` 会拒绝运行——**这是正确行为**，还没有需求，当然不能评审需求。

```

- [ ] **Step 7: 替换「改造报告」节的首段**

把这两行：

```markdown
改造完成后必须生成 `00-retrofit-report.md`，包含改造概览、文档状态、编号分配、待完善项、下一步建议。

详细模板参见 [templates/retrofit-report-template.md](templates/retrofit-report-template.md)。

```

替换为：

```markdown
**仅版本迁移路径生成** `00-retrofit-report.md`，包含迁移动作清单（改了哪些编号、重命名了哪些文件）。详细模板参见 [templates/retrofit-report-template.md](templates/retrofit-report-template.md)。

**基线路径不产报告**：原报告的「编号分配」表整张作废（不再产编号）、「文档状态」表塌成一行（只产一份基线），剩下的「待完善项」与「下一步建议」已并入基线的「建立记录」节——它跟着基线走，下次读基线的人才看得到这份基线的局限。

```

同节的「**关键规则**」一行替换为：

```markdown
**关键规则**：基线不是终点。有新需求 → `/ms-feature`；补充项目背景或把 `推导待确认` 升为 `用户确认` → `/ms-requirements --context`（写入 `00-baseline.md`）。

```

- [ ] **Step 8: 改「约束」节**

删除 `### 编号约束` 整节（5 个 checkbox），替换为：

```markdown
### 基线内容约束

- [ ] **⛔ `00-baseline.md` 不得出现模块表 / 接口表 / 数据对象表 / 依赖图 / 技术栈清单 / 目录结构树**（→ `codebase-insight.md`）
- [ ] **⛔ 不得出现当前分支 / 未提交改动 / 完成率 / 待办**（→ `00-context.md`）
- [ ] **⛔ 不得从实现细节推导出「必须保持此行为」**——最大的危害不是过时，是把实现偶然性写成设计意图
- [ ] **⛔ 不得出现没有来源标注的断言**；推不出就标 `未知`
- [ ] **⛔ `推导待确认` 不得因用户沉默而升格为 `用户确认`**
- [ ] **⛔ 每次提问必须提供「我也不清楚」出口**，且选它不算失败——不给出口，用户被迫瞎选产生的假信息比标 `未知` 更糟
- [ ] 护栏节三要素（决定 / 约束哪些改动 / 依据）**缺一不写**
- [ ] 「已知未知」每条必须写出「确认前的安全默认动作」

```

同时把「输出约束」里这两条：

```markdown
- [ ] 输出目录统一为 `docs/devdocs/`
- [ ] 逆向推导内容必须标注 `[从代码推导]`

```

改为：

```markdown
- [ ] 输出目录统一为 `docs/devdocs/`
- [ ] 基线路径只产 `00-baseline.md`，不产 `01`~`04`

```

- [ ] **Step 9: 替换「子 Agent 摘要格式」的 yaml**

```yaml
skill: ms-retrofit
status: success | failed | partial
summary:
  headline: "项目基线已建立，5 项未知待补"
  details:
    path: baseline | version-migration
    baseline_established: true
    adoption_commit: "a1b2c3d"
    counts:
      用户确认: X
      已有文档: X
      推导待确认: X
      未知: X
    evidence_conflicts: X
    build: "pass | fail | none"
    tests: "pass | fail | none"
blockers: []
output_files:
  - docs/devdocs/00-baseline.md
new_ids: {}
next_recommended:
  skill: ms-feature
  args: ""

```

`new_ids` 恒为空——改造不再产编号。

- [ ] **Step 10: 替换「输出文件」节**

````markdown
## 输出文件

**基线路径**：

```text
docs/devdocs/
└── 00-baseline.md          # 项目基线（唯一产物）

```

附带（由委托的 skill 各自产出，不由本 skill 写）：`docs/codebase-insight.md`（`ms-codebase-insight`）、`AGENTS.md` 的领域术语与架构决策节（`agent-memory`）。

**版本迁移路径**：

```text
docs/devdocs/
├── 00-retrofit-report.md    # 迁移报告
└── <按迁移范围更新的既有 01~04 文档>

```
````

- [ ] **Step 11: 重写 `skills/retrofit/references/new-project-retrofit.md`**

整个文件替换为：

````markdown
# ms-retrofit 建立项目基线流程详解

> 当项目没有 DevDocs 文档时执行。产物形状见 [../templates/baseline-template.md](../templates/baseline-template.md)。
>
> SKILL.md 仅保留触发判定 + 总览；本文件提供执行细节。

## 判据：接手难在建立「认知权威」

基线的主要消费者是**大模型**——在后续的全新会话里读它接手项目；人也看，但不是主要读者。

接手一个已有项目，最难的不是理解代码，而是区分四件事：

| # | 问题 | LLM 的表现 |
|---|---|---|
| 1 | 代码**实际**做了什么 | 极擅长——读一遍就知道 |
| 2 | 系统**本该**做什么 | 读不出来 |
| 3 | 外部世界**要求**它必须做什么 | 读不出来 |
| 4 | 目前**根本不知道**什么 | 读不出来，且会用推测填空 |

**LLM 极易把第 1 项误当成后三项。** 基线的全部职责就是承载 2、3、4 并标出 1 的边界。
凡是第 1 项能回答的，基线一律不装——那是代码和 `codebase-insight.md` 的地盘，重扫成本很低，写进基线只是从「读真实代码」那里抢 token。

## 流程

```text
1. 调查：把别人留下的陈述挖干净
   │   ├── 委托 ms-codebase-insight 摸排  → docs/codebase-insight.md（清单层）
   │   ├── README / CHANGELOG / docs/ / 包描述字段
   │   ├── git log 提交信息（尤其早期提交和大改动的说明）
   │   ├── issue / PR 讨论（如可访问）
   │   └── 实跑构建 / 测试 / 启动，记录真实结果
   │
   ▼
2. 校验：拿代码检验文档里的每一条可验证陈述
   │   ├── 与代码一致          → 已佐证
   │   ├── 与代码矛盾          → 与代码矛盾，冲突进「已知未知」§5.2
   │   └── 纯意图，代码验不了  → 未可验
   │
   ▼
3. 推导：起草带依据标注的基线草案
   │   每条都写清「据什么」——路径行号 + 校验标记，或推导依据
   │
   ▼
4. 提问：只问推不出、依据薄弱、或校验出矛盾的项
   │   ├── 形式为「确认 / 修正」，不是开放式空白页
   │   ├── ⛔ 每题必须有「我也不清楚」出口
   │   └── 现状：拿模块清单 × 提交时间分布 × TODO/FIXME 密度 × 测试覆盖
   │            出候选，让用户判「完成 / 半成品 / 废弃 / 不清楚」
   │
   ▼
5. 落盘 docs/devdocs/00-baseline.md
       用户确认的 → 用户确认   用户没表态的 → 保持推导待确认
       推不出也问不到的 → 未知，汇总进「建立记录」

```

## Step 1: 调查——为什么必须在提问之前

README 里写着的东西还去问用户，是浪费用户时间。

更要紧的是**接手场景**：项目中途接手时，用户对「为什么做、解决什么问题、哪儿有坑」的了解**未必比 agent 多**。此时别人留下的陈述（commit message、issue、PR 讨论、旧文档）往往是 why 的**唯一**来源——用户自己也是从这些材料里知道的。

调查范围：

| 来源 | 挖什么 |
|---|---|
| `ms-codebase-insight` 产物 | 模块 / 接口 / 数据对象清单（作为提问的候选底稿，**不抄进基线**） |
| README / CHANGELOG / `docs/` | 项目目的、约束、历史决策的**人写陈述** |
| 包描述字段（`package.json` 的 `description` 等） | 一句话定位 |
| `git log` 提交信息 | 早期提交常含项目缘起；大改动的说明常含决策理由 |
| issue / PR 讨论 | 被否决的方案、外部约束、真实消费者 |
| 实跑构建 / 测试 / 启动 | 基线时点的可信度——跑不起来就如实记 |

## Step 2: 校验——文档不是权威，代码是

接手项目的文档**不必然可信**。README 可能描述的是两年前被重构掉的系统，而它**带着确信地错**，比空白更危险。

⛔ **凡文档陈述可被代码检验的，必须检验。** 不检验就采信 = 把过期信息当证据。

| 校验标记 | 含义 |
|---|---|
| `已佐证` | 文档说 X，代码确实如此 |
| `未可验` | 纯意图类陈述（为什么做 / 给谁用），代码检验不了 |
| `与代码矛盾` | 文档说 X，代码实际是 Y |

⛔ **冲突时以代码为准。** 文档陈述**不删除**，改记为「文档声称 X（`README.md:3`），代码实际 Y——已过期或从未实现」。两边都留着，因为「曾经打算做 X」本身是关于项目历史的信息。

**`未可验` 不得与 `已佐证` 同等呈现。** 纯意图陈述仍是接手场景下最好的线索，但没有任何东西为它背书——可能是过期的项目定位，也可能是从没实现过的愿景。

**冲突本身是最有价值的产出。**「文档说 A，代码是 B」正是接手者最容易踩的坑——它进基线 §5.2，并写明确认前的安全默认动作，不能只当脚注。

**但别把代码的权威用过头。** 代码是「在做什么」的权威，**不是**「还在被用吗 / 做对了吗」的权威：死代码和活代码长得一模一样，关掉的 feature flag、没人调用的端点、固化了 Bug 的逻辑，代码都不会告诉你。这些归基线 §5「已知未知」，给出安全默认动作。

## Step 3: 推导——四档来源标注

基线里非纯生成的每一项，须标注四者之一：

| 标注 | 含义 | 硬要求 |
|---|---|---|
| `用户确认` | 用户明确说过，或确认了草案 | — |
| `已有文档` | 来自 README / CHANGELOG / 旧业务文档 | **必附路径行号 + 校验标记** |
| `推导待确认` | 从代码、结构、提交历史推出，用户尚未表态 | **必附推导依据** |
| `未知` | 调查过，推不出，问了也没答 | — |

⛔ **不得出现无标注、无依据的断言。** 推不出就标 `未知`，不许用「大概是做 XX 的」填满页面。

⛔ **`推导待确认` 不得因用户沉默而升格为 `用户确认`。** 用户没表态就一直是待确认——这是它和已废弃的逆向推导的根本区别：逆向把推导直接当结论落库，这里推导始终带着「未经确认」的标记活着。

三种来源、三种待遇：

| 材料 | 标注 |
|---|---|
| README 写着「本服务解决订单超卖」 | `已有文档` + `README.md:3` + `未可验`——纯意图，代码证不了也伪不了 |
| README 写着「用 Redis 做分布式锁」，代码里确实是 | `已有文档` + 路径行号 + `已佐证` |
| README 写着「用 Redis 做分布式锁」，代码已换成数据库行锁 | `已有文档` + `与代码矛盾`，以代码为准，冲突进 §5.2 |
| 从类名 `StockLockService` 推「大概与库存并发有关」 | `推导待确认` + 推导依据 |

## Step 4: 提问——「未知」是正确结论，不是失败

最常见的场景是**中途接手项目**，此时用户未必比 agent 知道得多。设计不能假设人是 why 的权威。

1. ⛔ **每一次提问都必须提供「我也不清楚」出口，且选它不算失败。**
   不给出口，用户会被迫在几个选项里挑一个——产生的假信息**比标「未知」更糟**，因为它带着「用户确认」的权威。
2. **大面积 `未知` 是接手场景的正常形态。** 一份诚实标出十几处「未知」的基线，价值高于一份看起来完整但有一半是猜的。它告诉接手者**自己不知道什么**——这本身就是接手时最需要的信息。
3. **基线可增量补全，不是一次性冻结。** 接手者三个月后摸清了某块，跑 `/ms-requirements --context` 填回去，并把该条从 `推导待确认` / `未知` 升为 `用户确认`。

「现状」一问采用**代码信号出候选、判断权在人**。两个极端都被否决：

- **纯问人**：面对空白页答不出来；接手场景下更是根本不知道
- **纯代码推断**（TODO 密度 / 提交时间 / 覆盖率自动判成熟度）：这是「推导出没人决定过的结论」的老毛病换个马甲

## Step 5: 落盘

按 [../templates/baseline-template.md](../templates/baseline-template.md) 写 `docs/devdocs/00-baseline.md`。

`adoption_commit` 取落盘时的 `git rev-parse HEAD`，**固定不变**——它是 DevDocs 接管的分界线，让「基线前 / 基线后」成为可判定的，追溯覆盖率语义（`coverage_scope: post-baseline`）锚在它上面。

⛔ **不产 `01`~`04`。** 存量代码不编号。

````

- [ ] **Step 12: 瘦身 `skills/retrofit/templates/retrofit-report-template.md`**

整个文件替换为：

````markdown
# DevDocs 改造报告模板

> **仅版本迁移路径使用**（旧 DevDocs → 新规范）。
>
> 基线路径不产报告——「待完善项」与「下一步建议」已并入 `00-baseline.md` 的「建立记录」节，
> 跟着基线走，下次读基线的人才看得到这份基线的局限。

使用此模板生成 `docs/devdocs/00-retrofit-report.md`。

---

```markdown
# DevDocs 迁移报告

## 迁移概览

- **项目名称**：<project>
- **迁移时间**：<timestamp>
- **迁移方式**：完整迁移 / 选择性迁移

## 迁移动作

### 文件变更

| 文档 | 迁移前 | 迁移后 | 动作 |
|------|--------|--------|------|
| 需求文档 | docs/req.md | docs/devdocs/01-requirements.md | 转换 + 编号 |
| 测试用例 | tests/README.md | docs/devdocs/03-test-cases.md | 转换 + 编号 |
| 开发任务 | TODO.md | docs/devdocs/04-dev-tasks.md | 标准化 |

### 编号补齐

| 类型 | 数量 | 范围 |
|------|------|------|
| 功能点 (F) | 5 | F-001 ~ F-005 |
| 用户故事 (US) | 12 | US-001 ~ US-012 |
| 验收标准 (AC) | 28 | AC-001 ~ AC-028 |

> 这些编号来自**已有文档的既有内容**，不是从代码推导的。
> 从代码逆向推导 F/US/AC 已废弃（构成循环论证：测试断言→AC→同一测试证明覆盖）。

### 待完善项

- [ ] <迁移后仍标记 [待补充] 的章节>

## 下一步

| 场景 | 执行 |
|------|------|
| 检查追溯健康度 | `/ms-sync` |
| 完善需求文档 | `/ms-requirements` |
| 开始开发 | `/ms-dev-tasks` → `/ms-dev-workflow` |
| 添加功能 | `/ms-feature` |

```
````

- [ ] **Step 13: 跑断言，确认全部通过**

Run: `bash /tmp/t2-check.sh`
Expected: 全部 `PASS`，退出码 0

- [ ] **Step 14: lint 类型集不退化**

Run:

```bash
cd /Users/mason/Projects/skills
npx --no-install markdownlint-cli2 skills/retrofit/SKILL.md skills/retrofit/references/new-project-retrofit.md skills/retrofit/templates/retrofit-report-template.md 2>&1 | grep -oE 'MD[0-9]+' | sort -u | tr '\n' ' '

```

Expected: 结果 ⊆ `MD013 MD022 MD024 MD032 MD040 MD046 MD060`（`skills/retrofit/SKILL.md` 改前为 `MD013 MD022 MD024 MD032 MD040 MD060`）。超出即修。

- [ ] **Step 15: 内部链接可达**

Run:

```bash
cd /Users/mason/Projects/skills/skills/retrofit
for l in templates/baseline-template.md references/new-project-retrofit.md \
         templates/retrofit-report-template.md references/realign.md \
         references/version-migration.md references/error-handling.md; do
  test -f "$l" && echo "OK   $l" || echo "MISS $l"
done

```

Expected: 全部 `OK`

- [ ] **Step 16: 提交**

```bash
cd /Users/mason/Projects/skills
git add skills/retrofit/
git commit -m "$(cat <<'EOF'
feat(retrofit): 逆向推导改为建立项目基线

删除 F/US/AC 与 UT/IT/E2E 全链逆向推导。它构成循环论证——测试断言逆向成
AC、再由同一条测试证明该 AC 已覆盖，产出必然 100% 的假追溯率，且会把已有
Bug 的现状行为固化成验收标准。改为建立 docs/devdocs/00-baseline.md。

同批修两个既存缺陷：
- allowed-tools 补 Task。正文两处早已写着 Task: /workspace-topology
  reconcile 与 Task: /agent-memory --update，但 allowed-tools 一直没有它，
  委托指令实际跑不了。
- 检测逻辑新增第三终态「基线已建」。基线项目一项编号都没有，原逻辑会判成
  「缺少 F/US/AC 编号 ⚠️ 需迁移」，于是版本迁移试图把刚建好的基线迁回旧编号
  形态——第二次跑 /ms-retrofit 就会撞上。

报告瘦身为仅服务版本迁移；基线路径不产报告，待完善项并入基线的建立记录节。

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"

```

---

### Task 3: 结构性断点修复

这三处决定「基线建完之后还能不能往下走」。**`ms-feature` 那条是死循环，最严重。**

**Files:**
- Modify: `skills/feature/SKILL.md:26-33`（前置条件）
- Modify: `skills/bugfix/SKILL.md:138`、`:240`、`:281`（关联功能三处）
- Modify: `skills/pipeline/SKILL.md:104-115`（路由表）

**Interfaces:**
- Consumes: Task 2 的「基线已建」终态、`00-baseline.md` 路径
- Produces: `关联功能` 字段的新合法值 `baseline`（Task 6 的一致性扫描会检查它没被别处否定）

- [ ] **Step 1: 写断言脚本，先跑一次确认失败**

创建 `/tmp/t3-check.sh`：

```bash
#!/bin/bash
cd /Users/mason/Projects/skills
fail=0
chk(){ if eval "$2" >/dev/null 2>&1; then echo "PASS  $1"; else echo "FAIL  $1"; fail=1; fi; }

F=skills/feature/SKILL.md
B=skills/bugfix/SKILL.md
P=skills/pipeline/SKILL.md

chk "feature 前置接受基线"      "grep -q '00-baseline.md' $F"
chk "feature 不再无条件要求 01" "! grep -q '^- 至少存在 \`01-requirements.md\`$' $F"
chk "feature 说明 F-001 起编"   "grep -q 'F-001' $F"
chk "bugfix 关联功能允许 baseline" "grep -c 'baseline' $B | grep -qv '^0$'"
chk "bugfix 三处都改了"         "[ \$(grep -c 'baseline' $B) -ge 3 ]"
chk "pipeline 路由有仅基线行"   "grep -q '仅 \`00-baseline.md\`' $P"
chk "pipeline 路由指向 feature" "grep -A0 '仅 \`00-baseline.md\`' $P | grep -q 'ms-feature'"

chk "feature ≤ 500 行"          "[ \$(wc -l < $F) -le 500 ]"
chk "bugfix ≤ 500 行"           "[ \$(wc -l < $B) -le 500 ]"
chk "pipeline ≤ 500 行"         "[ \$(wc -l < $P) -le 500 ]"
exit $fail

```

- [ ] **Step 2: 跑断言，确认失败**

Run: `bash /tmp/t3-check.sh`
Expected: 前 7 条 `FAIL`，退出码 1

- [ ] **Step 3: 修 `skills/feature/SKILL.md` 死循环**

把这一段：

```markdown
## 前置条件

- 已存在 DevDocs 文档目录：`docs/devdocs/`
- 至少存在 `01-requirements.md`

如不存在，建议：
- 新项目 → `/ms-requirements`
- 已有代码无文档 → `/ms-retrofit`

```

替换为：

```markdown
## 前置条件

- 已存在 DevDocs 文档目录：`docs/devdocs/`
- 存在 `01-requirements.md` **或** `00-baseline.md`

**只有 `00-baseline.md`（基线项目）时**：本 skill 创建 `01-requirements.md`，`F-001` 从这个新需求起。
存量代码不编号——基线项目的历史实现不进编号体系，只有基线之后的真实变更才有 F/US/AC。

如两者都不存在，建议：

- 新项目 → `/ms-requirements`
- 已有代码无文档 → `/ms-retrofit`（建立项目基线）

> ⛔ 这条前置条件曾写死「至少存在 `01-requirements.md`」，与 `/ms-retrofit` 的「基线已建，无需改造」
> 终态构成死循环：想加新功能 → feature 说去跑 retrofit → retrofit 说基线已建 → 回到 feature。
> 基线项目必须能从这里进入。

```

- [ ] **Step 4: 修 `skills/bugfix/SKILL.md` 三处「关联功能」**

第 138 行附近，把：

```markdown
| 关联功能 | F-XXX / AC-XXX | **必须** |

```

改为：

```markdown
| 关联功能 | F-XXX / AC-XXX，或 `baseline` | **必须** |

```

第 240 行附近，把：

```markdown
| **关联功能** | F-XXX, AC-XXX |

```

改为：

```markdown
| **关联功能** | F-XXX, AC-XXX（或 `baseline`：涉及基线前代码） |

```

第 281 行附近，把：

```markdown
| 关联功能 | 涉及哪个功能点（F-XXX / AC-XXX） | **必须** |

```

改为：

```markdown
| 关联功能 | 涉及哪个功能点（F-XXX / AC-XXX）；基线前的存量代码填 `baseline` | **必须** |

```

并在「Step 1: 理解 Bug」的信息表**下方**（`如信息不足，使用 AskUserQuestion 询问。` 那一行之后）补一段：

```markdown
**基线项目的第一个 Bug**：基线项目（只有 `00-baseline.md`，无 `01`~`04`）修的是基线前的存量代码，
它没有 F 编号，也**不该临时编一个**——临时编号是「推导出没人决定过的结论」的老毛病。
此时「关联功能」填 `baseline`，回归测试仍必须写，`@verifies` 标注对象从 `AC-XXX` 换成 `BUG-XXX`。

`bugfix/SKILL.md` 已近 500 行硬限，本段为等量替换，勿再扩写。

```

> ⚠️ `bugfix/SKILL.md` 改前 483 行，硬限 500。上述补充约 5 行，改后应 ≤ 490。Step 1 的断言会兜住。

- [ ] **Step 5: 修 `skills/pipeline/SKILL.md` 路由表**

在「已有 DevDocs 文件时」表格里，`| verify-report（...）|` 那一行**之前**插入一行：

```markdown
| 仅 `00-baseline.md`（基线已建，尚无需求） | 有新需求 → `/ms-feature`；补充背景 → `/ms-requirements --context` |

```

并在表格下方（`报告类文件（readiness-report、verify-report）应比其源文件更新，过期时建议重新验证。` 之前）补一行：

```markdown
⛔ 「仅基线」必须排在表首。基线项目 `docs/devdocs/` 存在会进入这张表，但除这一行外**匹配不到任何行**——原表最短的一行是「仅 `01-requirements.md`」，基线项目会直接落空。

```

- [ ] **Step 6: 跑断言，确认全部通过**

Run: `bash /tmp/t3-check.sh`
Expected: 全部 `PASS`，退出码 0

- [ ] **Step 7: lint 类型集不退化**

Run:

```bash
cd /Users/mason/Projects/skills
for f in skills/feature/SKILL.md skills/bugfix/SKILL.md skills/pipeline/SKILL.md; do
  echo "$f: $(npx --no-install markdownlint-cli2 "$f" 2>&1 | grep -oE 'MD[0-9]+' | sort -u | tr '\n' ' ')"
done

```

Expected:

- `feature` ⊆ `MD013 MD024 MD032 MD040 MD060`
- `bugfix` ⊆ `MD013 MD040 MD060`
- `pipeline` ⊆ `MD013 MD029 MD032 MD040 MD060`

超出即修（常见新增是 MD028：相邻引用块之间有空行 → 用 `>` 连起来）。

- [ ] **Step 8: 提交**

```bash
cd /Users/mason/Projects/skills
git add skills/feature/SKILL.md skills/bugfix/SKILL.md skills/pipeline/SKILL.md
git commit -m "$(cat <<'EOF'
fix(devdocs): 修基线项目的三处结构性断点

ms-feature 前置条件写死「至少存在 01-requirements.md」，与 retrofit 的
「基线已建，无需改造」终态构成死循环——想加新功能被指去跑 retrofit，
retrofit 说无需改造，转回 feature。基线建完就进不去后续流程，直接打断
「后续用 devdocs 维护」。前置改为「01 或 00-baseline.md」。

ms-bugfix 三处要求「关联功能 F-XXX/AC-XXX 必须」，基线项目修存量代码时
无编号可填，也不该临时编一个。新增合法值 baseline。

ms-pipeline 路由表最短的一行是「仅 01-requirements.md」，基线项目会进表
却匹配不到任何行、直接落空。表首加「仅基线」行。

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"

```

---

### Task 4: 文案过期修复

两处文案描述的行为（逆向）已不存在。不修的话，用户按提示走会扑空。

**Files:**
- Modify: `skills/onboard/SKILL.md:161`（提取源）、`:394`（协作表）
- Modify: `skills/dev-workflow/SKILL.md:58`、`:60`（探索模式）

**Interfaces:**
- Consumes: Task 2 的基线路径
- Produces: 无

- [ ] **Step 1: 写断言脚本，先跑一次确认失败**

创建 `/tmp/t4-check.sh`：

```bash
#!/bin/bash
cd /Users/mason/Projects/skills
fail=0
chk(){ if eval "$2" >/dev/null 2>&1; then echo "PASS  $1"; else echo "FAIL  $1"; fail=1; fi; }

O=skills/onboard/SKILL.md
D=skills/dev-workflow/SKILL.md

chk "onboard 协作表无 逆向生成"   "! grep -q '先从代码逆向生成文档' $O"
chk "onboard 协作表提基线"        "grep -q '建立项目基线' $O"
chk "onboard 1.1 提取源含基线"    "grep -q '00-baseline.md' $O"
chk "dev-workflow 无 retrofit 补AC" "! grep -q 'ms-retrofit\` 补 AC' $D"
chk "dev-workflow 无 retrofit 补文档" "! grep -q 'ms-retrofit\` 补文档' $D"
chk "dev-workflow 改为用户确认补AC" "grep -q '用户确认目标行为后补建真实 AC' $D"
chk "Exploration-Mode 尾注保留"   "grep -q 'Exploration-Mode: true' $D"

chk "onboard ≤ 500 行"           "[ \$(wc -l < $O) -le 500 ]"
chk "dev-workflow ≤ 500 行"      "[ \$(wc -l < $D) -le 500 ]"
exit $fail

```

- [ ] **Step 2: 跑断言，确认失败**

Run: `bash /tmp/t4-check.sh`
Expected: 前 6 条中多条 `FAIL`，退出码 1

- [ ] **Step 3: 修 `skills/onboard/SKILL.md` 提取源**

第 160–161 行，把：

```markdown
### 1.1 项目目标
<从 01-requirements.md 提取>

```

改为：

```markdown
### 1.1 项目目标
<从 01-requirements.md 提取；不存在时从 00-baseline.md 的「项目目的与边界」提取，并保留其来源标注>

```

> 这是**既存缺陷**，与本次改动无关：`01-requirements.md` 不存在时（改造后、首个需求前）此节本来就取不到值。

- [ ] **Step 4: 修 `skills/onboard/SKILL.md` 协作表**

第 394 行，把：

```markdown
| DevDocs 不存在 | `/ms-retrofit` | 先从代码逆向生成文档 |

```

改为：

```markdown
| DevDocs 不存在 | `/ms-retrofit` | 先建立项目基线（`00-baseline.md`） |

```

- [ ] **Step 5: 修 `skills/dev-workflow/SKILL.md` 探索模式**

第 58 行，把：

```markdown
| **探索** | 原型、技术调研 | → 允许跳过部分验证，事后 `/ms-retrofit` 补文档 |

```

改为：

```markdown
| **探索** | 原型、技术调研 | → 允许跳过部分验证，事后由用户确认目标行为后补建 AC |

```

第 60 行，把结尾：

```markdown
写入 Commit 1 `Exploration-Mode: true` 尾注便于 `/ms-retrofit` 补 AC。无证据 ⛔ 阻止提交。

```

改为：

```markdown
写入 Commit 1 `Exploration-Mode: true` 尾注，便于事后由用户确认目标行为后补建真实 AC。无证据 ⛔ 阻止提交。

```

> 尾注本身**保留**——它记录的是「这次提交跳过了文档强制」，这个事实仍然有效。
> 变的只是补 AC 的途径：`/ms-retrofit` 不再从代码推导 AC（那正是被废弃的循环论证）。

- [ ] **Step 6: 跑断言，确认全部通过**

Run: `bash /tmp/t4-check.sh`
Expected: 全部 `PASS`，退出码 0

- [ ] **Step 7: lint 类型集不退化**

Run:

```bash
cd /Users/mason/Projects/skills
for f in skills/onboard/SKILL.md skills/dev-workflow/SKILL.md; do
  echo "$f: $(npx --no-install markdownlint-cli2 "$f" 2>&1 | grep -oE 'MD[0-9]+' | sort -u | tr '\n' ' ')"
done

```

Expected:

- `onboard` ⊆ `MD013 MD022 MD031 MD032 MD040 MD060`
- `dev-workflow` ⊆ `MD007 MD013 MD022 MD024 MD028 MD032 MD060`

- [ ] **Step 8: 提交**

```bash
cd /Users/mason/Projects/skills
git add skills/onboard/SKILL.md skills/dev-workflow/SKILL.md
git commit -m "$(cat <<'EOF'
fix(devdocs): 修两处指向已废弃逆向流程的文案

ms-onboard 协作表写「/ms-retrofit 先从代码逆向生成文档」，逆向已删除。
顺带修其既存缺陷：00-context.md 的「1.1 项目目标」写死从 01-requirements.md
提取，而改造后到首个需求之间 01 并不存在，此节本来就取不到值。

ms-dev-workflow 探索模式承诺「事后 /ms-retrofit 补 AC」，retrofit 不再
补 AC。改为「由用户确认目标行为后补建真实 AC」。Exploration-Mode 尾注
保留——它记录的是这次提交跳过了文档强制，该事实仍然有效。

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"

```

---

### Task 5: SSOT 边界与 `coverage_scope`

两件事：把 `--context` 的边界划清并接上基线的增量补全入口；给追溯覆盖率加范围标注，防止「100% 覆盖」被误读成全系统覆盖。

**Files:**
- Modify: `skills/requirements/references/context-mode.md`（开头「典型场景」+ 新增边界节）
- Modify: `skills/verify/SKILL.md`（B1 AC 满足度审查）
- Modify: `skills/verify/templates/verify-report.md`（报告头）
- Modify: `skills/sync/SKILL.md`（核心理念 · 文档与代码的关系）

**Interfaces:**
- Consumes: Task 1 的四档来源标注、Task 2 的 `adoption_commit`
- Produces: 字段名 `coverage_scope`，取值 `post-baseline` / `full`（Task 6 一致性扫描按此字面量检查）

- [ ] **Step 1: 写断言脚本，先跑一次确认失败**

创建 `/tmp/t5-check.sh`：

```bash
#!/bin/bash
cd /Users/mason/Projects/skills
fail=0
chk(){ if eval "$2" >/dev/null 2>&1; then echo "PASS  $1"; else echo "FAIL  $1"; fail=1; fi; }

C=skills/requirements/references/context-mode.md
V=skills/verify/SKILL.md
R=skills/verify/templates/verify-report.md
Y=skills/sync/SKILL.md

chk "context-mode 场景1 去逆向"    "! grep -q '代码逆向推导完成后' $C"
chk "context-mode 提基线"          "grep -q '00-baseline.md' $C"
chk "context-mode 有 SSOT 边界节"  "grep -q '与项目基线的边界' $C"
chk "context-mode 是增量补全入口"  "grep -q '增量补全' $C"
chk "context-mode 提四档标注"      "grep -q '推导待确认' $C"
chk "verify 有 coverage_scope"     "grep -q 'coverage_scope' $V"
chk "verify 提 post-baseline"      "grep -q 'post-baseline' $V"
chk "report 模板有 coverage_scope" "grep -q 'coverage_scope' $R"
chk "sync 有 coverage_scope"       "grep -q 'coverage_scope' $Y"

chk "verify ≤ 500 行"              "[ \$(wc -l < $V) -le 500 ]"
chk "sync ≤ 500 行"                "[ \$(wc -l < $Y) -le 500 ]"
exit $fail

```

- [ ] **Step 2: 跑断言，确认失败**

Run: `bash /tmp/t5-check.sh`
Expected: 前 9 条 `FAIL`，退出码 1

- [ ] **Step 3: 修 `skills/requirements/references/context-mode.md` 开头**

把：

```markdown
### 典型场景

1. **Retrofit 后补充**：代码逆向推导完成后，补充代码中看不出的背景

```

改为：

```markdown
### 典型场景

1. **基线增量补全**：`/ms-retrofit` 建立 `00-baseline.md` 后，把当时标为 `未知` / `推导待确认` 的条目补齐

```

- [ ] **Step 4: 在 `context-mode.md` 的「典型场景」列表之后插入边界节**

```markdown
### 与项目基线的边界

`01-requirements.md §1 背景与目标` 五项里，**只有「项目背景」与 `00-baseline.md` 重叠**：

| §1 章节 | 归属 |
|---|---|
| 1.1 项目背景 | → `00-baseline.md`「项目目的与边界」。`§1.1` 在有基线时**只写指针**，不复制内容 |
| 1.2 领域知识 | 留 `§1` |
| 1.3 技术约束 | 留 `§1`（**业务性**约束；代码外部的硬约束如真实消费者 / 数据归属 / 合规，归基线） |
| 1.4 参考资料 | 留 `§1` |
| 1.5 决策记录 | 留 `§1`（**当前变更**的决策；仍在约束未来改动的项目级护栏，归基线） |

**本模式同时是基线的增量补全入口。** `--context` 的定位本就是「问人补代码里看不出的背景」，与基线同源，且本模式支持增量更新不覆盖原有内容。

写入基线时须遵守其标注制度：

- 用户这次明确说了 → 该条从 `未知` / `推导待确认` 升为 `用户确认`
- ⛔ **用户没提到的条目不得因此升格**——沉默不是确认
- ⛔ 不得往基线写模块表 / 接口表 / 技术栈清单等清单类内容（→ `docs/codebase-insight.md`）

不为基线补全新建 `/ms-retrofit --baseline-update` 一类的入口：补全基线是「补背景」，不是「改造项目」。

```

- [ ] **Step 5: 给 `skills/verify/SKILL.md` 的 B1 加 `coverage_scope`**

在 `### B1：AC 满足度审查` 的编号步骤 4 之后、`**辅助判断**` 之前，插入：

```markdown
5. **标注覆盖范围**：读 `docs/devdocs/00-baseline.md` 的 `adoption_commit`——
   - 基线存在 → 报告写 `coverage_scope: post-baseline`，并附 `adoption_commit`
   - 基线不存在 → 写 `coverage_scope: full`

⛔ 基线项目的「AC 覆盖率 100%」**只覆盖 `adoption_commit` 之后的变更**，不标注就会被读成全系统覆盖率。存量代码占比越大，这个误读越危险——它会让一个基本没有测试的老项目显得「测试覆盖完美」。

```

- [ ] **Step 6: 给 `skills/verify/templates/verify-report.md` 加字段**

在报告头里，把：

```markdown
**验证范围**：<T-XX / F-XXX / 全量>

```

改为：

```markdown
**验证范围**：<T-XX / F-XXX / 全量>
**coverage_scope**：<post-baseline（附 adoption_commit: <hash>）/ full>

```

并在该行下方补一行说明：

```markdown
> `post-baseline` 表示覆盖率**只统计 `adoption_commit` 之后的变更**，不含基线前的存量代码。

```

- [ ] **Step 7: 给 `skills/sync/SKILL.md` 加 `coverage_scope`**

在 `### 文档与代码的关系` 的 ASCII 图**之后**，插入：

```markdown
**基线项目的追溯范围**：项目存在 `docs/devdocs/00-baseline.md` 时，追溯矩阵与覆盖率必须标注
`coverage_scope: post-baseline` 并写明 `adoption_commit`——追溯从接管点之后开始，基线前的存量
代码不在 F→US→AC→测试 链路内。不标注会把局部覆盖率误报成全系统覆盖率。

```

- [ ] **Step 8: 跑断言，确认全部通过**

Run: `bash /tmp/t5-check.sh`
Expected: 全部 `PASS`，退出码 0

- [ ] **Step 9: lint 类型集不退化**

Run:

```bash
cd /Users/mason/Projects/skills
for f in skills/requirements/references/context-mode.md skills/verify/SKILL.md \
         skills/verify/templates/verify-report.md skills/sync/SKILL.md; do
  echo "$f: $(npx --no-install markdownlint-cli2 "$f" 2>&1 | grep -oE 'MD[0-9]+' | sort -u | tr '\n' ' ')"
done

```

Expected:

- `context-mode.md` ⊆ `MD001 MD034 MD060`
- `verify/SKILL.md` ⊆ `MD013 MD028 MD032 MD040 MD056 MD060`
- 另两个：类型集不得新增该文件改前没有的类型（改前先各跑一次记下来）

- [ ] **Step 10: 提交**

```bash
cd /Users/mason/Projects/skills
git add skills/requirements/references/context-mode.md skills/verify/SKILL.md \
        skills/verify/templates/verify-report.md skills/sync/SKILL.md
git commit -m "$(cat <<'EOF'
feat(devdocs): 划清 --context 与基线的边界，追溯覆盖率加范围标注

01-requirements.md §1 五项里只有「项目背景」与 00-baseline.md 重叠，改为
指针；其余四项留在 §1。--context 同时成为基线的增量补全入口——它的定位
本就是问人补代码里看不出的背景，与基线同源且支持增量不覆盖。写入时须守
基线的标注制度：用户没提到的条目不得因此升格，沉默不是确认。

新增 coverage_scope 字段。基线项目算出的「AC 覆盖率 100%」只覆盖
adoption_commit 之后的变更，不标注会被读成全系统覆盖率——存量越大误读
越危险，会让一个基本没测试的老项目显得覆盖完美。

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"

```

---

### Task 6: 治理登记、AGENTS.md 记录、全仓残留扫描

收尾。**全仓残留扫描是这个任务的重点**——前五个任务各改各的，只有在这里才能发现漏网的引用。

**Files:**
- Modify: `skills/verify/references/schema-drift.md`（扫描表）
- Modify: `AGENTS.md`（当前状态）

**Interfaces:**
- Consumes: 前五个任务的全部产出
- Produces: 无（终点）

- [ ] **Step 1: 写断言脚本，先跑一次确认失败**

创建 `/tmp/t6-check.sh`：

```bash
#!/bin/bash
cd /Users/mason/Projects/skills
fail=0
chk(){ if eval "$2" >/dev/null 2>&1; then echo "PASS  $1"; else echo "FAIL  $1"; fail=1; fi; }

D=skills/verify/references/schema-drift.md
A=AGENTS.md

chk "schema-drift 登记基线"       "grep -q '00-baseline.md' $D"
chk "schema-drift 指向 realign"   "grep -q 'skills/retrofit/references/realign.md' $D"
chk "AGENTS.md 记录基线改动"      "grep -q '00-baseline.md' $A"

echo "--- 全仓残留扫描 ---"
chk "无 从代码逆向生成文档"       "! grep -rlF '先从代码逆向生成文档' skills/"
chk "无 retrofit 补 AC 承诺"      "! grep -rlF 'ms-retrofit\` 补 AC' skills/"
chk "无 逆向推导 F-XXX 表"        "! grep -rlE '路由/页面.*F-XXX' skills/"
chk "retrofit description 无逆向" "! grep -n 'description:' skills/retrofit/SKILL.md | grep -q '逆向'"

echo "--- 全仓 SKILL.md 行数硬限 ---"
over=$(find skills -name SKILL.md -exec awk 'END{if(NR>500)print FILENAME" "NR}' {} \;)
if [ -z "$over" ]; then echo "PASS  所有 SKILL.md ≤ 500 行"; else echo "FAIL  超限：$over"; fail=1; fi

echo "--- 本计划触碰文件的内部链接 ---"
TOUCHED="skills/retrofit/SKILL.md skills/retrofit/references/new-project-retrofit.md
skills/retrofit/references/realign.md skills/retrofit/templates/baseline-template.md
skills/retrofit/templates/retrofit-report-template.md skills/feature/SKILL.md
skills/bugfix/SKILL.md skills/pipeline/SKILL.md skills/onboard/SKILL.md
skills/dev-workflow/SKILL.md skills/requirements/references/context-mode.md
skills/verify/SKILL.md skills/verify/templates/verify-report.md
skills/verify/references/schema-drift.md skills/sync/SKILL.md"
: > /tmp/t6-links.txt
for f in $TOUCHED; do
  [ -f "$f" ] || continue
  d=$(dirname "$f")
  grep -oE '\]\((\.\./|references/|templates/)[^)#[:space:]]*\.md\)' "$f" 2>/dev/null \
    | sed -E 's/^\]\(//; s/\)$//' \
    | while read -r l; do
        [ -f "$d/$l" ] || echo "  MISS $f -> $l" >> /tmp/t6-links.txt
      done
done
if [ ! -s /tmp/t6-links.txt ]; then echo "PASS  无断链"; else echo "FAIL  断链："; cat /tmp/t6-links.txt; fail=1; fi

exit $fail
```

- [ ] **Step 2: 跑断言，确认失败**

Run: `bash /tmp/t6-check.sh`
Expected: 前 3 条 `FAIL`（本任务尚未做）；**残留扫描 4 条与行数、链接检查应全部 `PASS`**（Task 2–4 已修完）。若残留扫描出现 `FAIL`，说明前面任务有漏网，回去补完再继续。

- [ ] **Step 3: 登记 `00-baseline.md` 到 `skills/verify/references/schema-drift.md`**

在扫描范围表里，`| docs/devdocs/00-context.md | ms-onboard | ... |` 那一行**之前**插入：

```markdown
| `docs/devdocs/00-baseline.md` | ms-retrofit | `skills/retrofit/references/realign.md` |

```

并在表格下方（`**独立扫描...**` 之前）补一段：

```markdown
⛔ **`00-baseline.md` 只做结构性 drift 检测**（缺失章节 / frontmatter 字段），
realign **不得改写**其带 `用户确认` / `已有文档` / `推导待确认` 标注的正文——
那些内容问人和挖证据才得来，重生成产不出来。详见
[retrofit/references/realign.md](../../retrofit/references/realign.md)。

```

- [ ] **Step 4: 修 `skills/verify/references/schema-drift.md` 的 legacy 建议**

第 44 行附近，把：

```markdown
| **legacy** | 无 `spec_version` 字段 | 旧产物未迁移，建议 `/ms-retrofit` 首次化 |

```

保持不变（版本迁移路径仍然承担这个职责），但在第 73 行附近的示例表中，把：

```markdown
| docs/devdocs/01-requirements-legacy.md | /ms-retrofit |

```

保持不变。**本步骤不改动**——记录在此是为了让执行者确认这两处已核对过、无需修改。

- [ ] **Step 5: 更新 `AGENTS.md` 的「当前状态」**

在「当前状态」节的**第一条之前**插入一条（按该节既有的加粗标题 + 说明的写法）：

```markdown
- **retrofit 逆向推导 → 建立项目基线**：逆向出的 US/AC 是把端点和测试名换个说法重说一遍，且构成**循环论证**（测试断言→AC→同一测试证明覆盖），产出必然 100% 的假追溯率，还会把已有 Bug 的现状行为固化成验收标准。整条推导链（F/US/AC + UT/IT/E2E）**删除**，改为建立 `docs/devdocs/00-baseline.md`。判据是**认知权威四分法**——LLM 极擅长读出「代码实际做了什么」，也极易把它误当成「本该做什么 / 外部要求什么 / 根本不知道什么」；基线只承载后三者，凡重扫代码能重建的一律不装。六节：建立记录（含 `adoption_commit`）/ 项目目的与边界 / 代码外部的硬约束 / 仍在约束未来改动的护栏 / 已知未知+证据冲突 / 权威来源地图。四条纪律：调查先于提问、每条标来源（`用户确认`/`已有文档`/`推导待确认`/`未知`，沉默不升格）、文档不是权威代码是（可验证陈述必须拿代码校验，冲突以代码为准）、每次提问必有「我也不清楚」出口。存量代码不编号，`01` 由首次 `/ms-feature` 创建。同批修 6 处下游断点，其中 `ms-feature` 前置要求 `01` 存在会与「基线已建」形成**死循环**；另修两个既存缺陷（retrofit `allowed-tools` 缺 `Task` 导致其委托指令跑不了、onboard `1.1` 写死从 `01` 提取）。经 codex 两轮独立评审（禁读设计稿），第二轮推翻本方案「已证伪的路必装」的原结论——该结论依据 AGENTS.md 实测词频，但内容多也可能只是没人删（本文件 82 行/20KB 超 60 行硬限）；裁定改为「只装仍在约束未来改动的证伪结论，且须写成护栏形式」。方案见 [specs/2026-08-25-retrofit-baseline-design.md](docs/superpowers/specs/2026-08-25-retrofit-baseline-design.md)

```

同时更新「技术栈」节的 skill 计数行——本次未增删 skill，**计数不变**，确认无需改动即可。

- [ ] **Step 6: 跑断言，确认全部通过**

Run: `bash /tmp/t6-check.sh`
Expected: 全部 `PASS`，退出码 0

> 链接检查**只扫本计划触碰的 15 个文件**，不扫全仓。全仓扫会报出约 30 条 MISS，绝大多数是模板引用用户项目里的文件（如 `feature-log-template.md` → `01-requirements.md`）——那是正确行为，混进来只会训练执行者忽略这个检查。

- [ ] **Step 7: 全仓 lint 类型集回归**

Run:

```bash
cd /Users/mason/Projects/skills
npx --no-install markdownlint-cli2 'skills/**/*.md' AGENTS.md 2>&1 | grep -oE 'MD[0-9]+' | sort -u | tr '\n' ' '

```

对照本次改动前的全仓类型集（**执行者须在 Task 1 开始前先跑一次同样的命令并记下结果**）。判据：改后类型集 ⊆ 改前类型集。

> 若 Task 1 开始前忘了记录，用 `git stash` 或在 `git worktree` 里 checkout 本计划第一个 commit 的父提交重跑取基线。

- [ ] **Step 8: 提交**

```bash
cd /Users/mason/Projects/skills
git add skills/verify/references/schema-drift.md AGENTS.md
git commit -m "$(cat <<'EOF'
chore(devdocs): 登记基线治理身份并记录改动

00-baseline.md 进 schema-drift 扫描表，spec_version 常量在
skills/retrofit/references/realign.md。同时锁死：realign 只做结构性
drift 检测，不得改写带来源标注的正文——那些内容问人和挖证据才得来，
重生成产不出来。不登记的话基线会成为治理盲区（--schema-drift 扫不到、
realign --scope=spec 不知道怎么升），而同为 00-* 持久产物的 00-context.md
已在册。

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"

```

---

## 自审记录

### 1. Spec 覆盖检查

| Spec 章节 | 落点 |
|---|---|
| §1 逆向为什么没用 | Task 2 Step 11（写进 new-project-retrofit 判据节）；Task 2 commit message |
| §2 派生 vs 原生 | Task 1 Step 4（realign.md 禁自动覆盖） |
| §3.0 认知权威四分法 | Task 2 Step 11 |
| §3.1 六节结构 | Task 1 Step 3 |
| §3.2 硬约束 | Task 1 Step 3（模板禁项表）+ Task 2 Step 8（约束节） |
| §3.3 四档来源标注 | Task 1 Step 3 + Task 2 Step 11 |
| §3.4 未知不是失败 / 「我也不清楚」出口 | Task 2 Step 8、Step 11 |
| §3.5 文档不是权威代码是 | Task 2 Step 11 Step 2 校验 |
| §4 五步流程 | Task 2 Step 6、Step 11 |
| §5 删除清单 | Task 2 Step 3/6/8/9/10/11/12 |
| §6.1 四处重叠 | Task 5 Step 4 |
| §6.2 报告并入基线 | Task 2 Step 7、Step 12 |
| §6.3 --context 让出一项 + 增量补全入口 | Task 5 Step 3/4 |
| §6.4 术语表归 AGENTS.md | Task 2 Step 10（输出文件节注明由 agent-memory 产出） |
| §6.5 onboard 既存缺陷 | Task 4 Step 3 |
| §7 编号体系 | Task 2 Step 6、Task 3 Step 3 |
| §7.1 retrofit 重入死循环 | Task 2 Step 5 |
| §7.2 pipeline 路由 | Task 3 Step 5 |
| §7.3.1 feature 死循环 | Task 3 Step 3 |
| §7.3.2 bugfix 无编号 | Task 3 Step 4 |
| §7.3.3 onboard 文案 | Task 4 Step 4 |
| §7.3.4 dev-workflow 文案 | Task 4 Step 5 |
| §7.3.5 dev-tasks 非断点 | 不做（Task 6 Step 4 记录已核对） |
| §7.4 coverage_scope | Task 5 Step 5/6/7 |
| §9 改动面 15 文件 | Task 1–6 全覆盖 |
| §9.1 治理登记 | Task 1 Step 4 + Task 6 Step 3 |

**无遗漏。**

### 2. 占位符扫描

无 TBD / TODO / 「同 Task N」/ 「适当处理」。所有替换文本均为完整成品内容。

### 3. 一致性检查

- 文件路径 `docs/devdocs/00-baseline.md` 在 Task 1–6 中拼写一致
- `spec_version: baseline.v1` 在 Task 1 定义、Task 6 引用，一致
- 六个章节标题在 Task 1 模板与 Task 1 断言脚本中逐字一致
- 四档标注 `用户确认`/`已有文档`/`推导待确认`/`未知` 在 Task 1、2、5 中一致
- 三档校验标记 `已佐证`/`未可验`/`与代码矛盾` 在 Task 1、2 中一致
- `coverage_scope` 取值 `post-baseline`/`full` 在 Task 5 定义并在断言中检查，一致
- `关联功能` 新值 `baseline` 在 Task 3 三处一致

### 4. 已知风险

| 风险 | 缓解 |
|---|---|
| `bugfix/SKILL.md` 483 行，硬限 500 | Task 3 Step 1 断言含行数检查；补充段落约 5 行 |
| Task 6 全仓 lint 基线需在 Task 1 之前采集 | Task 6 Step 7 已写明补救方式（worktree 回到父提交重跑） |
| 断言脚本用 grep 匹配中文字面量，改写措辞会误判 | 断言与替换文本在同一 Step 内给出，逐字对应 |
| 基线流程无法在本仓实测（本仓不是被改造对象） | 已记入 spec §11 遗留；本计划只保证规格自洽，不保证真实项目效果 |
