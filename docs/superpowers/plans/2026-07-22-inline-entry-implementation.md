# inline 轻量入口实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 落地 `/ms-dev-workflow --inline` 轻量入口:内联任务定义 + AC 物化为 stub(AC 落 `01-requirements.md` 唯一编号源),下游显式受限分支,追溯/SSOT 不减。

**Architecture:** 纯 Markdown 规格变更,4 个正文文件 + 2 个一致性文件。协议私有于 dev-workflow(`references/inline-entry.md`),共享层 `constraints.md` 零改动。权威规格:[specs/2026-07-22-inline-input-satisfaction-design.md](../specs/2026-07-22-inline-input-satisfaction-design.md)(已过 codex 2 轮对抗审查)。

**Tech Stack:** Markdown 规格库,无 build/test;验证 = grep 锚点 + `wc -l` 行数约束 + 链接有效性。

## Global Constraints

- SKILL.md ≤ 500 行(硬约束;`skills/dev-workflow/SKILL.md` 当前 423 行)
- 门控标记只用 `⛔/⚠️/ℹ️` 三类;规范文件短门控可用 `恢复方式:<动作>` 行内简写(constraints.md §7)
- 不改 `skills/_shared/constraints.md`、`ms-requirements`、`ms-verify`(设计 §4)
- `trace-mode.md` 仅 +1 行规则,不重构
- review_profile 下限 guarded 措辞必须保留"命中 audit 信号升 audit"
- 层级按实际类别填写(🔴🟡🟢⚪ 皆合法),不写"默认 🔴"
- 提交规范:Conventional Commits,中文 description

---

### Task 1: 新增 inline-entry.md 私有协议文件

**Files:**
- Create: `skills/dev-workflow/references/inline-entry.md`

**Interfaces:**
- Produces: 协议规则 ID `inline/satisfy-not-exist`、`inline/explicit-entry`、`inline/materialize-two-files`、`inline/provenance-marker`、`inline/upstream-optional`、`inline/backfill-manual`;stub 模板两份;回填协议。Task 2~4 的正文以相对链接 `references/inline-entry.md` / `../../dev-workflow/references/inline-entry.md` 引用本文件。

- [ ] **Step 1: 创建文件**,内容 = 设计稿 §3.1 + §3.4 + §3.5 的完整展开(以下为必须包含的骨架,措辞可微调但规则 ID、模板字段、门控不得省略):

```markdown
# inline 轻量入口(--inline)

> 私有协议:仅 ms-dev-workflow 消费。出现第二个消费者时按 constraints.md 宪章流程上升共享层,本文不得被其他 skill 直接引用为规范源。
> 设计来源:docs/superpowers/specs/2026-07-22-inline-input-satisfaction-design.md(codex 2 轮审查)。

## 协议规则

- `inline/satisfy-not-exist`:前置条件的语义是"所需上下文可满足";具名文件存在只是**默认**满足方式,不是唯一方式。
- `inline/explicit-entry`:inline 分支仅由显式参数触发:`/ms-dev-workflow --inline "<任务定义>" --ac "<验收标准>"`;自由文本不进指定符解析,避免与 T/F/US 语法歧义。缺 `--ac` ⚠️ 必须确认:让用户补验收标准或确认转 /dev-flow(零追溯)。
- `inline/materialize-two-files`:入口物化**两处** stub:`01-requirements.md`(AC 条目,唯一编号源)+ `04-dev-tasks.md`(任务条目);文件不存在则按下方模板创建最小骨架。
- `inline/provenance-marker`:stub 条目必须标注 `来源: inline`;追溯矩阵照常引用该编号;`grep "来源: inline"` 即未回填台账。
- `inline/upstream-optional`:inline 条目允许上游链不完整(AC 无所属 US/F、无 02/03 文档),缺口显式标记 `—(inline)`,不静默断链。
- `inline/backfill-manual`:回填仅手动执行(无任何 skill 自动识别);编号回填中**不变**,操作是**移动而非复制**。

## 编号分配

- AC:扫描 `01-requirements.md` 全文件最大 AC 号续编;文件不存在从 AC-001 起。
- T:按 `04-dev-tasks.md` 现行规则续编;文件不存在从 T-01 起。
- F/US:不要求;关联需求列写 `—(inline)`。

## stub 模板

(此处放设计稿 §3.4 两份模板完整原文:01 最小骨架含 frontmatter/`## 4. 验收标准`/`### Inline stubs(待回填)` 追加区 + AC 条目;04 最小骨架含 frontmatter/`# 开发任务`/`## 任务列表`/层级分组 + 任务条目全字段表。关键约束原文保留:"已有 01 时在 ## 4 下创建或复用追加区";"层级按实际任务类别填写(分类输入,如实填写)";"review_profile: guarded(inline 强制下限,禁 fast;命中 audit 信号升 audit)";"TDD 模式随实际层级填写"。)

## 回填协议(仅手动;预检-写入-恢复)

(此处放设计稿 §3.5 完整原文:预检 3 项全过才写入(定 F/US、查重 ⛔、记录原始片段)→ 写入 3 步(移动 AC/补矩阵行、无 03 跳过并提示/04 改真实引用+已回填标记)→ 失败按原始片段恢复并报告 → 收尾联合扫描恰一处定义。)

## 下游受限分支速查

(此处放设计稿 §5 表格:指定符解析/ms-verify --impl/ms-requirements/Test Agent/ms-sync --trace/health-lint 六行,标注"正常工作/受限"及承载位置。)
```

- [ ] **Step 2: 验证**

Run: `grep -c "inline/" skills/dev-workflow/references/inline-entry.md`
Expected: ≥ 6(6 条规则 ID 全在)

Run: `grep -n "Inline stubs(待回填)\|guarded(inline 强制下限\|移动而非复制" skills/dev-workflow/references/inline-entry.md`
Expected: 三个锚点各至少 1 处

- [ ] **Step 3: Commit**

```bash
git add skills/dev-workflow/references/inline-entry.md
git commit -m "feat(dev-workflow): 新增 inline 轻量入口私有协议(规则/stub 模板/回填协议)"
```

---

### Task 2: SKILL.md 接入 --inline(前置条件 + 语法表)

**Files:**
- Modify: `skills/dev-workflow/SKILL.md`(语法表约 :64-80;前置条件 :91-94)

**Interfaces:**
- Consumes: Task 1 的 `references/inline-entry.md`
- Produces: 用户面入口声明,Task 3 的解析器分支与此处语法一致(`--inline "<任务定义>" --ac "<验收标准>"`)

- [ ] **Step 1: 语法表追加一行**(插在"无人值守 `--headless`"行之前):

```markdown
| 轻量入口 | `--inline "<任务定义>" --ac "<验收标准>"` | 无 04 文档也可进入:按 [inline-entry.md](references/inline-entry.md) 物化 stub(01 AC 条目 + 04 任务条目)后转单任务路径;review_profile 下限 guarded |
```

- [ ] **Step 2: 前置条件改为"或"分支**:

```markdown
## 前置条件

- 任务文档:`docs/devdocs/04-dev-tasks.md`,且任务已定义并包含:关联需求、验收标准、测试方法
- **或** `--inline "<任务定义>" --ac "<验收标准>"`:按 [inline-entry.md](references/inline-entry.md) 物化 stub 后进入 S1;Test Agent 输入中 02/03 字段标 `—(inline)`,以 S1.5 Sprint Contract 为测试输入约束
```

- [ ] **Step 3: 验证**

Run: `wc -l skills/dev-workflow/SKILL.md`
Expected: ≤ 500

Run: `grep -c "inline-entry.md" skills/dev-workflow/SKILL.md`
Expected: 2(语法表 + 前置条件各一处)

- [ ] **Step 4: Commit**

```bash
git add skills/dev-workflow/SKILL.md
git commit -m "feat(dev-workflow): SKILL.md 接入 --inline 轻量入口(语法表 + 前置条件或分支)"
```

---

### Task 3: task-orchestration.md 解析分支 + Test Agent 输入表 inline 行

**Files:**
- Modify: `skills/dev-workflow/references/task-orchestration.md`(§1 指定符语法/解析流程 :5-30;Test Agent 输入表 :373-390)

**Interfaces:**
- Consumes: Task 1 协议(物化规则)、Task 2 语法声明
- Produces: `ms-sync` 受限行为的上游语境(Task 4)

- [ ] **Step 1: §1 语法块追加**(在 `--all` 行后):

```
/ms-dev-workflow --inline "<任务定义>" --ac "<验收标准>"   # 轻量入口:物化 stub 后转单任务
```

- [ ] **Step 2: 解析流程追加分支**(在 `--all` 分支后、"3. 返回去重后的任务 ID 列表"之前):

```
   └── --inline      → 不读 04 指定符;按 references/inline-entry.md 物化
                        01 AC 条目 + 04 任务条目(缺 --ac ⚠️ 必须确认:补验收标准或转 /dev-flow),
                        物化得到 T-XX 后转单任务路径(与现有 T-XX 行为一致)
```

- [ ] **Step 3: Test Agent 输入表追加 inline 说明**(输入表下方紧接一段):

```markdown
> **inline 分支**(任务 `来源: inline`):`系统设计`/`测试用例` 两字段传 `—(inline)`;测试输入约束以 S1.5 Sprint Contract(AC + 当前代码上下文)为准——S1.5 本就是既有步骤,非新机制。`需求文档` 字段照常传 `01-requirements.md`(inline AC 定义于其 Inline stubs 区)。信息屏障不变。
```

- [ ] **Step 4: 验证**

Run: `grep -n -- "--inline" skills/dev-workflow/references/task-orchestration.md`
Expected: ≥ 2 处(语法块 + 解析流程);Test Agent 段 `grep -n "—(inline)"` ≥ 1 处

- [ ] **Step 5: Commit**

```bash
git add skills/dev-workflow/references/task-orchestration.md
git commit -m "feat(dev-workflow): 指定符解析与 Test Agent 输入表支持 inline 分支"
```

---

### Task 4: trace-mode.md +1 行 skip 规则

**Files:**
- Modify: `skills/sync/references/trace-mode.md`(扫描流程"1. 读取 03-test-cases.md 追溯矩阵"步骤处)

**Interfaces:**
- Consumes: Task 1 的 `来源: inline` 标记语义

- [ ] **Step 1: 在扫描流程步骤 1 下追加一行例外**:

```markdown
   ├── 03-test-cases.md 不存在且 AC 标 `来源: inline` → 跳过该 AC 的 trace 写入,提示"inline 条目待回填(见 dev-workflow references/inline-entry.md)"
```

- [ ] **Step 2: 验证**

Run: `grep -c "inline" skills/sync/references/trace-mode.md`
Expected: ≥ 1;`wc -l` 增量 ≤ 2 行

- [ ] **Step 3: Commit**

```bash
git add skills/sync/references/trace-mode.md
git commit -m "feat(sync): trace 扫描对 inline AC 无 03 时跳过并提示待回填"
```

---

### Task 5: spec_version bump + 一致性收尾(CLAUDE.md 业务域清单 / AGENTS.md 状态)

**Files:**
- Modify: `skills/dev-workflow/references/realign.md`(:7-9 当前 spec_version;Migration Matrix)
- Modify: `skills/dev-workflow/CLAUDE.md`(业务域清单表)
- Modify: `AGENTS.md`(## 当前状态)

**Interfaces:**
- Consumes: Task 1~4 全部落地后的最终形态

- [ ] **Step 1: realign.md bump** `devflow.v1` → `devflow.v2`,Migration Matrix 追加一行:

```markdown
| devflow.v1 → v2 | 新增 --inline 轻量入口(前置条件或分支/指定符/Test Agent inline 分支) | 已完成任务无结构差距,回扫 no-op;仅规范能力扩展 |
```

> 注:`realign/bump-sync-three-places` 要求同步"模板 frontmatter 示例"——dev-workflow 无自有产物模板(04 归 ms-dev-tasks),执行时 `grep -rn "spec_version" skills/dev-workflow/templates/ 2>/dev/null` 确认为空后,在 Migration Matrix 行内注明"无模板同步项"即可。

- [ ] **Step 2: dev-workflow/CLAUDE.md 业务域清单追加一行**:

```markdown
| `references/inline-entry.md` | inline 轻量入口(--inline):协议规则、stub 模板(01 AC 条目 + 04 任务条目)、手动回填协议、下游受限分支速查 |
```

- [ ] **Step 3: AGENTS.md「当前状态」追加一条**(置于列表末尾,一行):

```markdown
- **dev-workflow inline 轻量入口**:`--inline "<任务>" --ac "<AC>"` 无 04 也可进入,物化 stub(AC 落 01 唯一编号源、guarded 下限、`grep "来源: inline"` 即回填台账);协议私有于 dev-workflow references(constraints.md 零改动),方案见 [specs/2026-07-22-inline-input-satisfaction-design.md](docs/superpowers/specs/2026-07-22-inline-input-satisfaction-design.md)
```

- [ ] **Step 4: 全局验证**

Run: `grep -rn "devflow.v2" skills/dev-workflow/references/realign.md | head -3`
Expected: 常量 + Migration Matrix 两处

Run: `grep -c "inline-entry" skills/dev-workflow/CLAUDE.md AGENTS.md`
Expected: 各 ≥ 1

Run: 逐一确认 4 个正文文件中新增的相对链接目标存在(`references/inline-entry.md` 等)

- [ ] **Step 5: Commit**

```bash
git add skills/dev-workflow/references/realign.md skills/dev-workflow/CLAUDE.md AGENTS.md
git commit -m "docs(dev-workflow): spec_version bump devflow.v2 + inline 入口一致性收尾(CLAUDE.md/AGENTS.md)"
```

---

## 计划级验收(对照设计稿 §7)

1. 空 `docs/devdocs/`:语法/解析/物化规则齐备,`--inline` 路径从入口到 S1 无断链(规格层走查,无 runtime)。
2. 无 `--inline` 时所有原语法行为零变化(diff 只增不改原语义行)。
3. 已有 01:追加区规则明确(inline-entry.md 模板段)。
4. 回填:预检-写入-恢复协议完整落在 inline-entry.md。
5. `grep "来源: inline"` 台账语义在协议 + trace-mode 提示中一致。
