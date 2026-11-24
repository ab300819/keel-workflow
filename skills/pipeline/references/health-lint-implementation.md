# Health Lint Implementation（health scope 可执行 lint rule 集）

> 把 [realign-scope-health.md](realign-scope-health.md) 维度 a/b/c 的检测要求落地为 lint rule。
>
> 本文件 16 条 rule：11 条 **project scope**（devdocs-state 膨胀 / 陈旧、死链、自造编号前缀、布局清单一致性），
> 5 条 **skill-library scope**（`flag/dangling-reference` + `skill/*`，⛔ 扫描对象不同，走 `--skills-dir`）。
>
> **14 条的判定以脚本 [`../scripts/health-lint.py`](../scripts/health-lint.py) 为准**，本文只写每条查什么、报了怎么办；阈值、正则、输出格式不在本文复述。余下 2 条脚本未实现，算法写在本文，由 Agent 执行。

## 定位

| 治理对象 | 文件 |
|---------|------|
| health scope 入口、`/pipeline realign --scope=health` 的命令与执行阶段 | [realign-scope-health.md](realign-scope-health.md) |
| **本文件**：rule 清单、怎么跑脚本、每条报了怎么办、2 条未实现 rule 的算法 | health-lint-implementation.md |
| 既有偏差评分 | `../../sync/references/health-scoring.md` |

## Rule 集（[新增] 16 条）

| rule_id | 严重度 | 维度 | 适用 | 自动修复 |
|---------|--------|------|------|---------|
| `state/total-size-cap` | ⛔ / ⚠️ | c 过大 | v1+v2 | ❌（manual_decision）|
| `state/line-length-cap` | ⛔ | c 过大 | v1+v2 | ❌（manual_decision）|
| `state/forbidden-content` | ⚠️ | c/state-hygiene（c 维度子项）| v1+v2 | ❌（manual_decision）|
| `health/dead-link` | ⛔ | b 索引/链接 | v1+v2 | ⚠️ 部分（删除引用可由 Agent 提议；补建定义需 manual）|
| `design/adr-only-revision` | ⚠️ | a 结构正确性 | v1+v2 | ❌（语义判断必须 manual）|
| `submodule/pointer-drift` | ⛔ / ⚠️ | a 结构正确性 | v1+v2（仅 shell）| ❌（manual_decision）|
| `state/max-id-stale` | ⚠️ | c/state-hygiene（c 维度子项）| v1+v2 | ❌（manual_decision：回填或删行）|
| `id/unknown-prefix` | ⚠️（永不升级 ⛔）| b 索引/链接 | v1+v2 | ❌（只报不判，manual_decision）|
| `flag/dangling-reference` | ⚠️ | b 索引/链接 | **skill 库**（非项目）| ❌（manual_decision）|
| `skill/size-cap` | ⛔ | a 结构正确性 | **skill 库** | ❌（manual_decision）|
| `skill/name-mismatch` | ⛔ | a 结构正确性 | **skill 库** | ❌（manual_decision）|
| `layout/unknown-path` | ⚠️ | a 结构正确性 | v1+v2 | ❌（manual_decision）|
| `layout/unregistered-split` | ⚠️ | b 索引/链接 | v1+v2 | ❌（manual_decision）|
| `layout/size-cap` | ⚠️ | c 过大 | v1+v2 | ❌（manual_decision）|
| `skill/dead-link` | ⚠️ | b 索引/链接 | **skill 库** | ❌（manual_decision）|
| `skill/retired-term` | ⚠️ | a 结构正确性 | **skill 库** | ❌（manual_decision）|

> `design/adr-only-revision` 与 `submodule/pointer-drift` 脚本输出 `not_implemented`，需 Agent 按本文算法补执行。⚠️ skill 库的 5 条走 `--skills-dir`，**不在** `--scope=health` 的 11 条之内。`submodule/pointer-drift` 仅在 shell 拓扑下生效，`inline` / `linked` 项目不适用。`layout/*` 三条按 [devdocs-layout.md](../../shared/devdocs-layout.md) 的清单判定，发现里自带处置建议，本文不另设详情节。

## 怎么跑

**⛔ 先跑脚本，不要逐条人肉扫。** 脚本零依赖，参数以 `--help` 为准。

```bash
python3 <skill_dir>/scripts/health-lint.py --target <项目根> [--changed-only] [--fix=<rule_id>]
python3 <skill_dir>/scripts/health-lint.py --skills-dir <skills/>
```

| 入口 | 用途 |
|---|---|
| `--target <根>` | project scope 中脚本已实现的 9 条 |
| `--skills-dir <skills/>` | skill 库的 5 条（`flag/dangling-reference` + 4 条 `skill/*`）；⛔ 与 `--target` 互斥 |
| `--baseline-init` / `--since-baseline` | 存量项目噪声抑制，见 [§ Baseline 与增量扫描](#baseline-与增量扫描) |
| `--changed-only` | 文件级：只报 `git diff HEAD` 变更文件（含未跟踪）里的 `health/dead-link` 与 `id/unknown-prefix`；⚠️ `state/*` 与 `layout/*` 始终全量 |
| `--fix=<rule_id>` | 只跑指定 rule |
| `--selftest` | 内置夹具自检；改脚本后必跑（`bash scripts/check-python.sh` 已包含）|

- 脚本每次都在 stderr 打印 `not_implemented(v1): design/adr-only-revision, submodule/pointer-drift`，⛔ **不得当作 pass**，这两条按下文算法补执行。
- 发现逐条输出到 stdout，字段固定为 `rule_id / severity / file / line / actual / threshold / message / context / fix_suggestion / auto_fixable`；规则专属的信息（子类型、命中的模式、拆分锚点）写在 `message` 与 `context` 里。
- `.claude/rules/devdocs-state.md` 不存在时 `state/*` 不产生发现，stderr 汇总行标 `not_applicable`；`docs/devdocs/` 不存在时直接退出 0。
- 不含 `--apply` / 自动修复；修复由 `/pipeline realign --scope=health --apply` 调度，见 [realign-scope-health.md](realign-scope-health.md)。

### 退出码

| 退出码 | 含义 |
|--------|------|
| 0 | 无违规（或全部在 baseline 内）|
| 1 | 只有 ⚠️ |
| 2 | 有 ⛔；⚠️ 命令行参数写错也是 2，看 stderr 区分 |
| 3 | lint 自身错误，stderr 给出下列之一 |

| stderr 错误码 | 触发 |
|------------|------|
| `health/baseline-missing` | `--since-baseline` 但 `.health-baseline.yml` 不存在 → 先 `--baseline-init` |
| `health/baseline-corrupt` | baseline 不是脚本写的固定结构 → 重新 `--baseline-init`，⛔ 不手改 |
| `health/git-unavailable` | `--changed-only` 时 git 不可用或不在仓内 → 去掉 `--changed-only` 全量扫 |
| `layout/clause-unavailable` | 读不到 [devdocs-layout.md](../../shared/devdocs-layout.md) 的清单 → 核对插件安装是否完整 |

Agent 执行的两条 rule 按各自的严重度并入结论：`submodule/pointer-drift` 的分叉是 ⛔，其余成因与 `design/adr-only-revision` 是 ⚠️。`--apply` 流程的 `health/report-stale`、`health/manual-pending` 见 [realign-scope-health.md](realign-scope-health.md)。

---

## Rule 详情

### skill 库的 5 条

扫 skill 库自身，不扫用户项目；本仓编辑 `skills/**/*.md` 后由 `hooks/skill-flag-lint` 自动跑。

| rule_id | 查什么 | 报了怎么办 |
|---|---|---|
| `skill/size-cap` | `SKILL.md` 超过 [AGENTS.md](../../../AGENTS.md) 的行数上限 | 把细节下沉到 `references/` |
| `skill/name-mismatch` | 目录名 ≠ frontmatter `name`，或目录缺 `SKILL.md` | 改成一致（安装按 `name` 复制整个目录，跨 skill 相对引用依赖它）|
| `skill/dead-link` | 仓内相对链接（`./` `../` 开头）目标不存在；`templates/` 不查（模板里的路径按产物落点算）| 修正路径；确为示例时行内加 `<!-- health-lint-disable-line skill/dead-link -->` |
| `skill/retired-term` | 出现已删除机制的说法（词表是脚本里的 `RETIRED_TERMS`）| 改掉说法。删机制时把它的专有词加进词表；确需保留的行加 `<!-- health-lint-disable-line skill/retired-term -->` |
| `flag/dangling-reference` | 某 skill 文档里写了 `/<别的 skill> --flag`，而目标 skill 目录里搜不到这个 flag | 改成现存的 flag 或删掉引用；否定句式的反例行内加 `<!-- health-lint-disable-line flag/dangling-reference: <理由> -->` |

`flag/dangling-reference` 为什么需要：子指令没有解析器，flag 打错、改名、删除都不会有任何东西报错。已知盲区：skill 引用自己的 flag 必然通过，只能查跨 skill 的引用。

### `state/total-size-cap`

**查什么**：`.claude/rules/devdocs-state.md` 整体膨胀（超过提醒线 ⚠️，超过阻断线 ⛔；数值见 [状态文件模板 § 边界约束](../../agent-memory/templates/devdocs-state-template.md)）。防止「占位 + sprint 锚点」退化成日志倾倒地。

**报了怎么办**：不可自动修复。每条明细归到哪个文件（任务分册 / ADR / archive）由用户决定，执行走 `--scope=health --apply` 的 [Phase 2](realign-scope-health.md#phase-2维度-c-自动归档state-size--size-cap)。

### `state/line-length-cap`

**查什么**：状态文件里的超长行（多个 sprint 报告用 `；` 拼进一行的反模式）。frontmatter 不查。发现里带建议的拆分锚点；表格行标 `table-row: yes`。

**报了怎么办**：不可自动修复。拆分边界与每段明细的去向由用户确认，执行同上 Phase 2。确为单行数据的表格行可在行内加 `<!-- health-lint-disable-line state/line-length-cap -->`。

### `state/forbidden-content`

**查什么**：状态文件「## 编号状态」之后的占位 prose 里嵌了实现明细：commit hash、LOC 或 diff 增减计数、codex 分数、源码文件路径、`<仓名>@<hash>` 引用。该标题之前的内容不查（没有该标题时从第 51 行查起）。

**报了怎么办**：不可自动修复。逐条决定去向（搬到任务文件 / ADR，或直接删），原行换成：

```
- <编号> — <一句话状态>（→ <资源文件路径>）
```

误报（例如形似 hash 的普通字符串）在行内加 `<!-- health-lint-disable-line state/forbidden-content -->`。

### `health/dead-link`

**查什么**：`docs/devdocs/**/*.md` 里引用的编号（F / US / AC / CON / T / T-RF / ADR / INS / BUG / UT / IT / E2E / Journey，含 `AC-148~152` 这类范围）找不到定义。发现分两类：`out-of-range`（超出该类型已定义的最大编号，多半是未来引用或笔误）、`missing-definition`（在范围内却没有定义，多半是笔误、未创建或已删除）。

- 代码块内的编号不算引用。
- `archive/` 下的文件只贡献定义（已归档的编号仍算已定义），自身的引用不查。
- 编号上界从资源文件推导，⛔ 不读 `devdocs-state.md` 的「当前最大」（它允许滞后，当上界会把合法新编号误报）。
- 同一文件多次引用同一个死链编号合并成一条。

**报了怎么办**：补建定义、换成正确编号，或标 `[FUTURE]`，三者由用户选。引用出现在删除线、「已取消」这类上下文里时，Agent 可提议删除该引用，仍须用户确认。

### `id/unknown-prefix`

**查什么**：`health/dead-link` 白名单之外的编号前缀候选，按前缀聚合报告（每个前缀一条，附出现次数与样本位置）。⚠️ **只报不判**：白名单外的编号没有任何检查管，打错或引用已删除的号不会被发现，本条只负责让这些前缀在报告里可见，⛔ 不主张它们不该存在，⛔ 不给归并建议。对应 [constraints.md](../../shared/constraints.md) 的 `id/prefix-consumption-contract`。

- 已登记但故意不入白名单的前缀（`M`、`FR`、`NFR`）不报；URL 与文件路径内的不算；行内代码里的照样算。
- 形态相同的非编号（`UTF-8`、审查发现编号、外部单号）必然命中，⛔ 不硬编码黑名单，由 baseline 消化。
- 本条的出现次数与 `health/dead-link` 的引用数是两套口径，⛔ 不得相加或互相校验。
- 严重度恒为 ⚠️：它报的是「这里工具看不见」，不是「这里错了」。

**报了怎么办**：按 `id/prefix-consumption-contract` 给该前缀补一份消费契约（作用域 / 消费方 / 检查归属）。三种合法结局：登记进白名单、明确「人工核对、不进机器检查」、确认无消费方后删除。

存量项目首扫会一次性报出全部历史前缀，先 `--baseline-init`。⛔ **baseline 不是语义审批**：它只是本机的噪声抑制，换机器会重新报一遍，前缀进了 baseline 之后它新增的编号也不再提示。想让团队持续接受某个局部前缀，落点是产物里受版本控制的消费契约。⛔ 不用状态文件的「## 编号状态」表当白名单。

### `state/max-id-stale`

**查什么**：状态文件「## 编号状态」表的「当前最大」与资源文件推导值不一致。子类型：`stale`（表滞后，最常见）、`phantom`（表里的编号在资源文件中找不到定义）、`missing-row`（资源文件有该类型而表里没有这一行）。模板占位行（`F-XXX`）不比对。

**为什么只是 ⚠️**：该表不是编号权威，分配新编号直接扫资源文件。它滞后只会让速读读到旧数字，是缓存过期，不是数据损坏。

**报了怎么办**（二选一，⛔ 不默认自动改写）：

| 选项 | 动作 |
|---|---|
| 回填 | 把「当前最大」改为推导值 |
| 删行 | 删掉该类型的行。项目从不看这张表时，删掉比维护它更诚实 |

`phantom` 先查是否有编号被误删（可能与 `health/dead-link` 同源）。

---

### `design/adr-only-revision`

**目的**：检测系统设计文档（`02-system-design*.md`）的增量修订中，**ADR 章节有新增/修改但正文相关章节无同期更新**的反模式，对应 system-design/SKILL.md 自检清单的硬约束 `⛔ 禁止继续（增量设计）：仅追加 ADR 而正文相关章节未更新`。

**背景**：用户实战反馈"每次修订只加增量修订记录、不改正文，正文偏差越来越大"。原硬约束依赖人工/Agent 自检，本 rule 把它落地为可自动扫描的检测。

**检测对象**：

- `docs/devdocs/02-system-design.md` 主文档
- `docs/devdocs/02-system-design-api.md` / `02-system-design-data.md`（v1 拆分文件）

**算法**（基于 line-range × heading-map，不依赖 git diff hunk header — 仓库无 markdown diff driver，hunk header 通常仅为 `@@ -x,y +x,y @@`）：

```text
1. 列出最近 N 个 commit
   commits = Bash: git log --format="%H" --since="<window>" -- <design_files>
   默认 --since="30 days ago"，可通过 --since=<date> 覆盖

2. 对每个 commit C 和每个 design_file F：
   a. 取 F 在 C 时刻的内容：
      content_at_C = Bash: git show "$C:$F"
   b. 构建该时刻的 heading map（line_number → section_name）：
      headings = grep -nP '^#{1,4}\s+' content_at_C
      sections = [(start_line, end_line, heading_text), ...]
        ├─ ADR section 判定：heading_text 匹配 /^##\s+(\d+\.\s+)?(设计变更记录|ADR)/i
        │                      或 /^###\s+ADR-\d+/
        └─ body section 判定：其他所有 heading（## 1.~## 15.，或 ## + 中文章节名）
   c. 取 C 对 F 的 changed line ranges：
      ranges = Bash: git diff "$C^..$C" --unified=0 -- "$F" | parse @@ headers
      （unified=0 拿到精确行号范围；hunk header 仅用于行号，**不用于章节判定**）
   d. 对每个 changed range (start, end)：
      映射到 sections，得到 changed_in_adr / changed_in_body 两个集合
   e. 判定：
      if changed_in_adr 非空 AND changed_in_body 为空:
        → 候选违规 (C, F)

3. 候选 commit 进一步过滤（降假阳性）：
   a. commit message 含关键词跳过：
      - "typo" / "format" / "措辞" / "排版" / "rename ADR" / "ADR 编号调整" / "[adr-only-ok]" / "[skip-revision-check]"
   b. ADR 内容含字段跳过：
      - "影响范围：无" / "仅记录原因" / "不涉及正文修改"
   c. ADR 字数 < 100（短笔记类 ADR）→ 跳过

4. 跨多 commit / 多文件聚合：
   - 同一 ADR 编号在多 commit 出现时，只要任一 commit 有正文同期更新 → 整条 ADR 视为已对齐
   - 一个 ADR 横跨 02-system-design.md + 02-system-design-api.md：任一文件有正文修改即视为有正文同期更新

5. 对剩余真违规候选：
   - 提取 ADR 编号
   - 提取 ADR 中声明的"影响范围"字段（如 `影响范围：§4 模块设计、§5 核心接口`）
   - 输出 finding（见下方 Finding 示例）
```

**严重度**：⚠️ warning（不阻断 health 评分 < 60 直接挂掉，但要求用户回看）。

> 不设为 ⛔ 的理由：纯文本启发式有一定假阳性可能性（如 ADR 描述本身复述了模块结构图 → 误判为"未改正文"）。warning 让用户复核而非强阻塞，比 ⛔ 更稳妥。已经在 system-design/SKILL.md 自检清单有 ⛔ 人工自检兜底。

**修复路径**：

- **不可自动修复**。每条违规 commit 必须用户判断：
  - 是真实遗漏 → 补充正文相关章节修改（独立 commit）
  - 是 ADR 不需要正文同步 → 在 ADR 内显式补 "影响范围：无（仅记录原因）" 字样，下次扫描跳过

**Finding 示例**：

```yaml
- rule_id: design/adr-only-revision
  severity: warning
  file: docs/devdocs/02-system-design.md
  line: null  # commit 级别，非行级别
  commit: abc1234
  commit_subject: "feat(design): 新增 ADR-023 v2 数据流极简化决策"
  commit_date: 2026-05-19T10:30:00+08:00
  adr_ids: [ADR-023]
  declared_impact: "§4 模块设计、§5 核心接口"
  message: "commit 仅修改 ADR 章节（行 480-520），正文 §4/§5 同期无更新"
  hint: "确认 ADR-023 是否需要同步修订 §4/§5；若不需要，在 ADR 内补 '影响范围：无（仅记录原因）'"
  auto_fixable: false
```

**误报与边界**：

- 文档拆分模式（02-system-design-api.md / -data.md）：跨多文件 commit 时聚合判定（任一文件含正文修改即视为"有正文同期更新"）。
- 初始设计模式（首次创建 02-system-design.md，整文件新建）→ 跳过（不区分 ADR vs 正文）。
- ADR 章节无编号（system-design 模板的「设计变更记录（ADR 格式）」节）；rule 通过 markdown heading 内"设计变更记录" / "ADR" 关键字识别。
- 用户主动豁免：在 commit message 加 `[adr-only-ok]` 或 `[skip-revision-check]` 标记 → 跳过该 commit。

**与 verify --docs 层 2 的关系**：

- verify --docs 层 2（需求文档 → 系统设计）检查"需求 vs 设计"一致性。
- 本 rule 检查"设计文档内部 ADR vs 正文"一致性。
- 二者互补：层 2 跨文档；本 rule 文档内。
- verify --docs 调用本 rule 实现需在 verify/SKILL.md 维度 A 加引用（不重复实现算法）。

---

### `submodule/pointer-drift`

**目的**：检测外壳仓记录的子模块指针与子模块实际状态不一致，防止「代码已提交但追溯链断裂」静默累积。

**检测对象**：握手 `workspace_context.code_roots` 里的每个 `path`（⛔ 不自行读声明文件、不解析 `.gitmodules`，见 [shared/constraints.md](../../shared/constraints.md) `workspace/context-over-declaration`）。

**适用性门**：`workspace_context.mode` 为 `inline` 或 `linked`，或字段缺失 → 输出 finding `{ status: not_applicable }`，早退。`linked` 的代码根不归本仓所有、无 gitlink，指针漂移概念不适用。

**判据**：对每个路径跑 `git submodule status`，按首字符分派；命中 `+`（有漂移）再用 `git -C <path> merge-base --is-ancestor <recorded> <actual>`（及反向）判祖先关系区分成因：

> ⛔ **进入祖先关系判定前必须先做显式相等门**：`recorded == actual` → 直接 pass，不进 is-ancestor 分支。理由：`git merge-base --is-ancestor X X` 退出码为 0（commit 是自己的祖先），所以一旦首字符分派没命中（解析写错、或实现跳过该步），正常的一致情形会被误判为「漏 bump」假阳性。首字符是 `git submodule status` 输出的**前导空格**，从文本里抠它容易出错（实测踩点：BSD `od -c` 把空格渲染成字面空格、GNU 渲染成 `sp`，据此写的解析在两平台行为不同）。加这道门后判定与首字符解析方式无关。

| 首字符 | 成因 | 严重度 |
|---|---|---|
| ` `（空格）| 一致 | pass |
| `-` | 未初始化 | ⚠️ warning |
| `+`，子模块领先记录（`is-ancestor recorded actual` 成立） | 漏 bump | ⚠️ warning |
| `+`，记录领先子模块（反向 `is-ancestor` 成立） | 未 update（本地滞后） | ⚠️ warning |
| `+`，两方向都不成立 | 分叉（互无祖先关系） | ⛔ blocker，须 AskUserQuestion 人工裁定，不自动选 |

**修复路径**：**不可自动修复**。三种成因的具体处置命令见 [workspace-topology/references/migration.md § 指针漂移修复](../../workspace-topology/references/migration.md#指针漂移修复)（本文不重复）。

**误报与边界**：

- 子模块目录为空（未 `submodule update --init`）→ 报 ⚠️ 而非 ⛔，因为这是本地环境问题不是仓库问题；不与 [workspace-topology/references/protocol.md § 校验规则](../../workspace-topology/references/protocol.md#3-校验规则fail-closed) 的 ⛔ 冲突——那条是**运行时校验门**（要用代码根干活，目录空了就得停），本 rule 是**只读扫描**报告，适用范围不同
- 素材 / vendor 子模块**不扫**——它们本就不在 `workspace_context.code_roots` 里，本 rule 看不到

---

## Baseline 与增量扫描

存量项目首次扫描违规量大，全量 ⛔ 不可用，因此用 baseline 记下当前状态，之后只报新增。

```bash
python3 health-lint.py --target <项目根> --baseline-init      # 写快照，⛔ 不报告违规
python3 health-lint.py --target <项目根> --since-baseline     # 只报 baseline 之后的新增
```

- 位置：`<项目根>/.claude/rules/.health-baseline.yml`（推荐 gitignore）。
- ⛔ **只由脚本写，不手写、不手改。** 读取器只认脚本自己写的固定结构，格式不符报 `health/baseline-corrupt`。它是机器快照，不是给人编辑的配置。
- ⛔ 日常扫描不刷新 baseline：每次重写等于把新出现的违规记成存量。要重置由用户显式跑 `--baseline-init`。

### Delta 计算规则

`--since-baseline` 只对下列 rule 过滤，其余（`state/line-length-cap`、`state/max-id-stale`、`layout/*`）每次全报。

- `state/total-size-cap`：比 baseline 增长不足 2 KiB 的不报。⛔ **但不吞掉严重度升级**：baseline 时是 ⚠️、现在已跨过阻断线，即便增长不足 2 KiB 也报（与 [realign.md](realign.md)「有 baseline」行的三触发条件一致）。
- `state/forbidden-content`：按（文件, 行号）比对，baseline 里有的算存量。
- `health/dead-link`：baseline 里已知的死链不重复报，新增的一律 ⛔。
- `id/unknown-prefix`：baseline 里的前缀不提示，新出现的前缀 ⚠️。
- `design/adr-only-revision`（Agent 执行）：baseline 不适用，它按 commit 时间窗判定，本身就是增量语义。
- `submodule/pointer-drift`（Agent 执行）：按（代码根 name, 漂移类型）去重，已知漂移不重复报，新增的按成因定严重度。
