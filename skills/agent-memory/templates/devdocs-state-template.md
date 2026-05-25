# DevDocs 工作流状态模板

使用此模板生成目标项目的 `.claude/rules/devdocs-state.md`（Claude 专属运行态）。

> ⚠️ **设计意图**：本文件是**编号状态快照**，不是 sprint 日志。明细一律去对应资源文件查；本文件只承担"单页 grep 速读 + 当前最大值"。
>
> 健康度审查由 `/ms-pipeline realign --scope=health` 主动检测（详见 [pipeline/references/health-lint-implementation.md](../../pipeline/references/health-lint-implementation.md)）。

## 边界约束（硬性）

| 约束 | 阈值 | 违反时 |
|------|------|--------|
| 文件总大小 | ⚠️ > 10 KiB / ⛔ > 40 KiB | health-lint `state/total-size-cap` 告警 / 阻断 |
| 单行字符数 | ⛔ > 500 字符 | health-lint `state/line-length-cap` 阻断 |
| 单条占位 prose | ≤ 200 字符 | 超出即应拆出明细 |

## Forbidden 内容（不得写入本文件）

以下信息**只能写在资源文件**（task / ADR / commit message / PR description），本文件占位 prose 中**禁止**出现：

| 类别 | 示例 | 应去 |
|------|------|------|
| git commit hash | `0c263bf4d4`、`trade@abc1234` | commit message / PR / `04-dev-tasks-pNN.md` |
| LOC 计数 | `+184/-5`、`732 LOC`、`净 -85 LOC` | task 文件 / PR description |
| 测试结果数 | `49/49 GREEN`、`94 cases`、`焦点 51/51 PASS` | task 文件 / CI 报告 |
| codex 分数 | `R1 88 → R2 92`、`health=92 PASS` | task 文件 review 章节 |
| 源码文件路径 | `OssFundTraceProviderImpl.java:L54` | task 文件 / ADR |
| submodule 引用 | `trade@`、`envo@`、`mstatic@` | commit / task |
| 工时统计 | `~45min vs 估 2-3h`、`75% 节省` | task 文件 retrospective |

> health-lint `state/forbidden-content` 会扫描以上 6 类模式并告警。文件头部"边界约束"段落本身豁免扫描（前 50 行）。

## 模板正文

```markdown
# DevDocs 工作流状态

## 单一事实源约定

| 资源类 | 权威源（single source） | 本文件角色 |
|---|---|---|
| ADR-NNN | `docs/devdocs/adr/ADR-NNN.md` + `adr/index.md` | 占位（≤200 字符）|
| INS-NNN | `docs/devdocs/insights/INS-NNN.md` + `insights/index.md` | 占位（≤200 字符）|
| BUG-NNN | `docs/devdocs/bugs/BUG-NNN.md` + `bugs/index.md` | 占位（≤200 字符）|
| F / US / AC | `docs/devdocs/01-requirements.md` + `requirements/F-NNN.md` | 占位（≤200 字符）|
| Backlog 候选 | `docs/devdocs/backlog/NN-<slug>.md` | 占位（≤200 字符）|
| T / T-RF | `docs/devdocs/04-dev-tasks.md` + `04-dev-tasks-pNN.md` | 占位（≤200 字符）|
| UT / IT / E2E | `docs/devdocs/03-test-*.md` | 占位（≤200 字符）|

**规则**：

1. 修改资源文件 = 真实落地；本文件占位 prose 是**事实快照**，不追踪 drift。
2. 编号语义 / AC 内容 / 决策依据 / 全文以**资源文件**为准。
3. 新增 ADR / INS / BUG / F / Backlog **直接在对应目录新建单文件 + 追加索引表行**，**不在本文件回填明细**。
4. 已完成 sprint 在本文件**仅保留状态行**，明细去 `04-dev-tasks-pNN.md` 查（避免 monolithic 倾倒）。

## 编号状态

| 类型 | 当前最大 | 下一个 |
|------|----------|--------|
| F | F-XXX | F-XXX+1 |
| US | US-XXX | US-XXX+1 |
| AC | AC-XXX | AC-XXX+1 |
| T | T-XXX | T-XXX+1 |
| ADR | ADR-XXX | ADR-XXX+1 |
| INS | INS-XXX | INS-XXX+1 |
| BUG | BUG-XXX | BUG-XXX+1 |

（按项目实际使用的编号类型增删行；不使用的类型不必列出。）

## 编号占位指针

> 编号语义/约束/AC 内容以资源文件为准；本节仅作占位 + 状态标记。
> **每条占位 prose ≤ 200 字符**；明细去资源文件查。

### F / US / AC

- F-XXX / US-XXX / AC-XXX~XXX — <sprint 名> ✅ shipped YYYY-MM-DD（→ 04-dev-tasks-pNN.md）
- F-XXX / US-XXX / AC-XXX~XXX — <sprint 名> 🟡 in-progress（→ 04-dev-tasks-pNN.md）
- F-XXX / US-XXX / AC-XXX~XXX — <sprint 名> ⚪ 候选（→ 资源文件）

### T / T-RF（可选；活跃 sprint 期间列出）

- T-RF-XX — <一句话角色> ✅ shipped YYYY-MM-DD
- T-RF-XX — <一句话角色> 🟡 in-progress

### ADR / INS / BUG（可选；按需列出活跃项）

- ADR-XXX — <一句话决策摘要>（→ `docs/devdocs/adr/ADR-XXX.md`）
- INS-XXX — <一句话洞察>（→ `docs/devdocs/insights/INS-XXX.md`）
- BUG-XXX — <一句话症状> 🟢 fixed / 🟡 open（→ `docs/devdocs/bugs/BUG-XXX.md`）

## 文档更新时间（可选）

> 信息源是 git log，本表只为不便查 git 时提供 grep 锚点。可省略。

| 文档 | 更新日期 |
|------|----------|
| 01-requirements.md | YYYY-MM-DD |
| 02-system-design.md | YYYY-MM-DD |
| 03-test-cases.md | YYYY-MM-DD |
| 04-dev-tasks.md | YYYY-MM-DD |
```

## 正反例对比

### ✅ 合规占位（≤200 字符）

```markdown
- F-019 / US-043 / AC-148~152 — V0.9.x P19 ✅ shipped 2026-05-21（→ 04-dev-tasks-p19.md；12 T-RF 全收口）
- F-022 / US-046 / AC-169~172 — V0.9.8 P12 ✅ 9/9（INS-015 + ADR-017）
```

### ❌ 反模式（health-lint 会拦截）

```markdown
- F-019 / US-043 — V0.9.x P19 W5 ✅ 全收口 2026-05-21（**T-RF-12 ✅ shipped 2026-05-21** trade@0c263bf4d4 — IT-041 sprint 反契约 grep 守门；2 files +184/-5（新建 IT_041_AntiContractGuardTest 207 LOC / 3 cases / 全 GREEN 0.476s + ...
```

违反三条 rule：
- `state/line-length-cap`：单行 6000+ 字符
- `state/forbidden-content`：commit hash `0c263bf4d4` + LOC `+184/-5` + 文件路径 + 测试用例数
- `state/total-size-cap`：累积导致文件总大小爆表

修复路径：把明细搬到 `04-dev-tasks-p19.md` 对应 T-RF-12 章节；本文件占位保留一句话状态行。

## 触发健康度审查

```bash
# dry-run：扫描违规，输出 .health-report.md
/ms-pipeline realign --scope=health --dry-run

# apply：经 AskUserQuestion 确认归档目标后，搬迁明细 + 简化占位
/ms-pipeline realign --scope=health --apply
```
