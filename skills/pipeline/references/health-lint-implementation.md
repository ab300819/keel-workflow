# Health Lint Implementation（health scope 可执行 lint rule 集）

> 把 [realign-scope-health.md](realign-scope-health.md) 维度 b/c 的检测要求落地为 Agent 可执行的 lint rule。
>
> 与 [layout/ssot-lint-implementation.md](layout/ssot-lint-implementation.md) 的区别：ssot-lint 治理 layout.v2 的 SSOT 强约束（v1 报 `not_applicable`）；本文件 4 条 rule **layout.v1+v2 通用**，专门解决 devdocs-state 膨胀 + 死链两类痛点。

## 定位

| 治理对象 | 文件 |
|---------|------|
| health scope 入口与执行接口 | [realign-scope-health.md](realign-scope-health.md) |
| **本文件**：4 条 [新增] rule 的检测算法、严重度、修复路径 | health-lint-implementation.md |
| layout.v2 专属 SSOT 强约束（12 条）| [layout/ssot-lint-implementation.md](layout/ssot-lint-implementation.md) |
| 既有偏差评分（layout.v1 legacy）| `../../sync/references/health-scoring.md` |

## Rule 集（[新增] 5 条）

| rule_id | 严重度 | 维度 | 适用 | 自动修复 |
|---------|--------|------|------|---------|
| `state/total-size-cap` | ⛔ / ⚠️ | c 过大 | v1+v2 | ❌（manual_decision）|
| `state/line-length-cap` | ⛔ | c 过大 | v1+v2 | ❌（manual_decision）|
| `state/forbidden-content` | ⚠️ | c 过大 + d SSOT | v1+v2 | ❌（manual_decision）|
| `health/dead-link` | ⛔ | b 索引/链接 | v1+v2 | ⚠️ 部分（删除引用可自动；补建定义需 manual）|
| `design/adr-only-revision` | ⚠️ | a 结构正确性 | v1+v2 | ❌（语义判断必须 manual）|

> 5 条全部 [新增]，本 commit 推到可执行；不依赖 layout.v2 启用。layout.v1 项目（mic-en 等）可直接调 `/ms-pipeline realign --scope=health` 受益。

---

## Rule 详情

### `state/total-size-cap`

**目的**：检测 `devdocs-state.md` 整体膨胀，防止"占位 + sprint 锚点"退化为"sprint 完整日志倾倒地"。

**检测对象**：`<repo_root>/.claude/rules/devdocs-state.md`（若不存在 → skip，输出 `not_applicable`）。

**阈值**：

| 阈值 | 字节 | 严重度 |
|------|------|--------|
| WARN | > 10240 (10 KiB) | ⚠️ |
| BLOCKER | > 40960 (40 KiB) | ⛔ |

**算法**（Agent 执行步骤）：

```text
1. 检查文件存在性
   path = <repo_root>/.claude/rules/devdocs-state.md
   如不存在：输出 finding { status: not_applicable }，return

2. 计算字节大小
   size_bytes = Bash: wc -c "$path" | awk '{print $1}'

3. 分级判定
   if size_bytes > 40960:
     severity = blocker
     verdict_msg = "devdocs-state.md 已 ${size_bytes} bytes（阈值 40 KiB），违反占位 + sprint 锚点设计"
   elif size_bytes > 10240:
     severity = warning
     verdict_msg = "devdocs-state.md 已 ${size_bytes} bytes（阈值 10 KiB），建议归档"
   else:
     return pass

4. 输出 finding（见下方"Finding 输出 schema"）
```

**修复路径**：

- **不可自动修复**。归档目标决策必须 AskUserQuestion（每条超长行的明细应归到 04-dev-tasks-pNN.md / ADR-NNN.md / archive 哪个文件）。
- 修复执行由 `--scope=health --apply` Phase 1 调度（详见 [realign-scope-health.md § Phase 1](realign-scope-health.md#phase-1维度-c-自动归档state-size--size-cap)）。

**误报与边界**：

- `_archived/` 目录下的 devdocs-state.md 副本不扫（属历史归档）。
- 跨 worktree 多份 devdocs-state.md 时只扫主 worktree。

---

### `state/line-length-cap`

**目的**：检测单行超长（多个 sprint 报告塞进一行用 `；` 拼接的反模式）。

**检测对象**：`<repo_root>/.claude/rules/devdocs-state.md` 每一行。

**阈值**：单行字符数 > 500（计 unicode codepoint，非 byte）。

**算法**：

```text
1. 读取文件，按 \n 切分行
2. 对每一行 i：
     line_len = len(line_i)  # 字符数
     if line_len > 500:
       record finding {
         line: i,
         length: line_len,
         preview: line_i[:80] + "…",
         hint: 检测到的拆分锚点（按优先级匹配第一个）：
           - "；" 中文分号
           - "**T-RF-" / "**T-" task 标记
           - "; " ASCII 分号 + 空格
           - 其他：标记 "无明显拆分点，需 manual"
       }
3. severity = blocker（无 WARN 等级，超长即阻断）
4. 输出所有 findings
```

**修复路径**：

- **不可自动修复**。拆分边界（按 `；` 还是按 task ID）必须用户确认；同行内混杂多个 task 时，每个 task 的明细去向也需独立决策。
- `--scope=health --apply` Phase 1 执行：将每条 task 明细按确认目标搬到对应资源文件，原行替换为简洁占位（≤ 200 字符）。

**误报与边界**：

- 表格行（以 `|` 开头）若内容确为单行数据（不含嵌套 task 明细）→ 仍判违规，但 hint 标记 `table-row: yes`，用户可选择忽略（输出 `<!-- health-lint-disable-next-line state/line-length-cap -->` 注释）。
- frontmatter yaml 单行不扫（yaml 不应超 500 字符；如超则属另一类问题）。

---

### `state/forbidden-content`

**目的**：检测占位 prose 内嵌入了应该属于资源文件的实现明细（commit hash / LOC / codex 分数 / 文件路径）。

**检测对象**：`<repo_root>/.claude/rules/devdocs-state.md` 全文。

**禁止模式**（regex，按出现频率排序）：

| pattern_id | regex | 命中含义 |
|-----------|-------|---------|
| `commit-hash` | `` `\b[0-9a-f]{7,40}\b` `` | git commit short/full hash（命中需文本上下文含 "commit" / "@" / "shipped" 关键词，避免误报 AC 编号末位数字）|
| `loc-count` | `\b[+-]?\d+(\.\d+)?\s*(LOC\|loc\|lines?\|行)\b` | LOC 净增减（如 `+184/-5`、`732 LOC`）|
| `codex-score` | `\bR\d\b.*\bhealth\s*=\s*\d+\b` 或 `\bR\d\s*\d{2,3}\s*→\s*R\d\s*\d{2,3}\b` | codex review 分数（R1 88 → R2 92）|
| `diff-net` | `\b[+-]\d+/[+-]\d+\b` | diff 净增减 (+184/-5)|
| `file-path` | `\b[\w./-]+\.(java\|ts\|tsx\|js\|jsx\|py\|go\|kt\|swift)\b` | 源码文件路径 |
| `submodule-ref` | `\b(trade\|envo\|app\|mstatic\|trade-oss)@\b` | 跨仓 submodule + commit 引用 |

**算法**：

```text
1. 跳过文件前 50 行的"规则声明"区域（line 1-30 通常是约定表格 + 规则文本，允许出现 commit/path 示例）
   实现：找到第一个 "## 编号状态" heading 之后才开始扫描

2. 对每个 pattern_id 在剩余正文做 regex 全匹配：
   matches = Bash: grep -nP "<regex>" "$path" | tail -n +<header_end_line>

3. 对每个 match 记录 finding：
   {
     line: <line_num>,
     pattern_id: commit-hash | loc-count | codex-score | diff-net | file-path | submodule-ref,
     matched_text: "<最多 80 字符截断>",
     surrounding_context: "<该行前后 ±30 字符>"
   }

4. severity = warning（不阻断，但建议清理）
5. 汇总 findings，按 line 升序输出
```

**修复路径**：

- **不可自动修复**。每条禁止内容的去向（搬到哪个 task 文件 / ADR / 直接删除）需要 manual_decision。
- 修复模板：占位行替换为
  ```
  - <编号> — <一句话状态>（→ <资源文件路径>）
  ```

**误报与边界**：

- 文件头部"单一事实源约定"段落允许出现 file-path 示例（前 50 行豁免）。
- 如某行的 `commit-hash` 实际是 AC 编号末 7 位（`AC-1234567` 不太可能但语义可能误判），加上下文关键词约束（必须邻近 "commit" / "shipped" / "@" 字符）才命中。
- 用户可在违规行末加 `<!-- health-lint-disable-line state/forbidden-content -->` 单行豁免（必须给豁免理由：在 disable 注释后续行加 `<!-- reason: ... -->`）。

---

### `health/dead-link`

**目的**：检测 DevDocs 产物里引用的编号（F/US/AC/T/T-RF/ADR/INS/BUG/UT/IT/E2E/Journey）是否有对应定义；引用了不存在的编号 = 死链。

**检测对象**：`docs/devdocs/**/*.md`（排除 `_archived/`、`.realign-plan.md`、`.health-report.md`）。

**算法**（两遍扫描）：

```text
Phase A：构建编号定义索引（definition index）
  1. 遍历所有产物文件 + .claude/rules/devdocs-state.md
  2. 在每个文件中识别"定义位置"模式：
       - heading：^(#{1,4})\s+(F|US|AC|T|T-RF|ADR|INS|BUG|UT|IT|E2E|Journey)-\d+[a-z]?\b
       - 表格行：^\|\s*(F|US|AC|...)-\d+[a-z]?\s*\|
       - 列表项 + 状态：^[-*]\s+\*?\*?(F|US|...)-\d+[a-z]?\b
       - frontmatter id 字段（layout.v2）：^id:\s+(F|US|...)-\d+
  3. 收集为 index：{ id: <编号>, defined_in: [<file>:<line>, ...] }

Phase B：扫描引用
  1. 遍历同一批文件
  2. 用 regex `\b(F|US|AC|T|T-RF|ADR|INS|BUG|UT|IT|E2E|Journey)-\d+[a-z]?\b` 提取所有引用
  3. 排除"定义位置"自身（一个 occurrence 在 Phase A 中已记为 definition）
  4. 对剩余引用查 index：
       - 命中 → 跳过
       - 未命中 → finding {
           ref_id: <编号>,
           file: <file>,
           line: <line>,
           context: <±60 字符>,
           hint: "可能拼写错误 / 未创建 / 已删除"
         }
  5. severity = blocker
```

**修复路径**（auto_fixable 部分）：

- **可自动**：引用上下文明显是"删除目标"（如出现在 `~~text~~` 删除线内 / "已取消" / "cancelled by"）→ 提议删除引用，需用户最终确认。
- **manual_decision**：补建定义 / 替换为正确编号 / 标 `[FUTURE]`（暂未实现）。

**误报与边界**：

- 代码块内的编号引用（``` ``` 包围）不扫，避免命中示例代码。
- 引用在 `_archived/` 内的产物 → finding 标 `low-priority`，不阻断。
- 同一文件内多次引用同一死链编号 → 合并为一条 finding，`occurrences: [<line>, <line>, ...]`。

---

### `design/adr-only-revision`

**目的**：检测系统设计文档（`02-system-design*.md` 或 layout.v2 `design/current.md`）的增量修订中，**ADR 章节有新增/修改但正文相关章节无同期更新**的反模式，对应 system-design/SKILL.md:336 的硬约束 `⛔ 禁止继续（增量设计）：仅追加 ADR 而正文相关章节未更新`。

**背景**：用户实战反馈"每次修订只加增量修订记录、不改正文，正文偏差越来越大"。原硬约束依赖人工/Agent 自检，本 rule 把它落地为可自动扫描的检测。

**检测对象**：

- `docs/devdocs/02-system-design.md` 主文档
- `docs/devdocs/02-system-design-api.md` / `02-system-design-data.md`（v1 拆分文件）
- `docs/devdocs/design/current.md`（layout.v2 [FUTURE]）

**算法**（基于 git 历史扫描）：

```text
1. 列出最近 N 个 commit（N=20，可通过 --since=<date> 收窄）
   commits = Bash: git log --oneline --since="<window>" -- <design_files>

2. 对每个 commit：
   a. 取 commit diff：
      diff = Bash: git diff <commit>^ <commit> -- <design_files>
   b. 分类 hunk：
      adr_hunks = diff 中命中以下模式的 hunk：
        - hunk header 含 "## 16." / "## 设计变更记录" / "## ADR" / "### ADR-"
        - 新增/修改行含 "ADR-NNN" 或 "ADR-NNN.vN" 标记
      body_hunks = diff 中除 adr_hunks 外的所有 hunk：
        - 命中正文章节标识：## 1.~## 15. 或 § 4 模块设计 / § 5 核心接口 / § 9 API 设计 等
   c. 判定：
      if adr_hunks 非空 AND body_hunks 为空:
        → 候选违规 commit

3. 候选 commit 进一步过滤（降假阳性）：
   a. commit message 含以下关键词 → 跳过：
      - "typo" / "format" / "措辞" / "排版" / "rename ADR" / "ADR 编号调整"
   b. ADR 内容含 "无影响范围" / "仅记录原因" / "不涉及正文修改" → 跳过
   c. ADR 字数 < 100（短笔记类 ADR）→ 跳过

4. 对剩余候选 commit：
   - 提取 ADR 编号
   - 提取 ADR 中声明的"影响范围"字段内容（如 `影响范围：§4 模块设计、§5 核心接口`）
   - 输出 finding（见下方 schema）

5. 时间窗口配置：
   - 默认 --since="30 days ago"
   - 用户可传 --since=<date> 覆盖（如全量扫 --since="1970-01-01"）
```

**严重度**：⚠️ warning（不阻断 health 评分 < 60 直接挂掉，但要求用户回看）。

> 不设为 ⛔ 的理由：纯文本启发式有一定假阳性可能性（如 ADR 描述本身复述了模块结构图 → 误判为"未改正文"）。warning 让用户复核而非强阻塞，比 ⛔ 更稳妥。已经在 system-design/SKILL.md:336 有 ⛔ 人工自检兜底。

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
- ADR 章节位置识别基于 SKILL.md § 文档结构 第 16 章定义；项目使用其他章节号时，rule 通过 markdown heading 内"设计变更记录" / "ADR" 关键字识别。
- 用户主动豁免：在 commit message 加 `[adr-only-ok]` 或 `[skip-revision-check]` 标记 → 跳过该 commit。

**与 ms-verify --docs 层 2 的关系**：

- ms-verify --docs 层 2（需求文档 → 系统设计）检查"需求 vs 设计"一致性。
- 本 rule 检查"设计文档内部 ADR vs 正文"一致性。
- 二者互补：层 2 跨文档；本 rule 文档内。
- ms-verify --docs 调用本 rule 实现需在 verify/SKILL.md 维度 A 加引用（不重复实现算法）。

---

## Finding 输出 schema

所有 4 条 rule 的 finding 统一格式，与 `.health-report.md` § dimensions 字段对齐：

```yaml
- rule_id: state/total-size-cap | state/line-length-cap | state/forbidden-content | health/dead-link
  severity: blocker | warning
  file: <relative-path>
  line: <int 或 null>
  actual: <实际值，如 size_bytes / line_length>
  threshold: <阈值，如有>
  message: "<人类可读描述>"
  context: "<可选，违规内容片段>"
  fix_suggestion: "<修复建议或 'manual_decision'>"
  auto_fixable: true | false | partial
```

## CLI 触发

| 命令 | 执行的 rule |
|------|------------|
| `/ms-pipeline realign --scope=health --dry-run` | 全部 4 条 |
| `/ms-pipeline realign --scope=health --fix=state/total-size-cap` | 仅该 rule |
| `/ms-pipeline realign --scope=health --apply` | 修复 auto_fixable + 已 AskUserQuestion 的 manual_decision |

不提供单独的 `--health-lint` 入口，统一通过 health scope 调用。

## 与 ssot-lint 的去重

| 关注点 | 本文件（health-lint） | ssot-lint（layout.v2）|
|--------|---------------------|---------------------|
| 适用 layout | v1 + v2 | 仅 v2 |
| 检测对象 | devdocs-state.md + 全产物死链 | layout.v2 owner / aliases.yml / traceability.yml 等 |
| size 检测 | 按 byte（针对 state.md）+ 按行（针对全产物的单行）| 按行数（current.md ≥ 1500 / file ≥ 3000 / modules ≥ 800）|
| restatement 检测 | 不做（v2 才有 SSOT 强约束）| `ssot/no-restatement` |
| 调用入口 | `--scope=health` | `--scope=layout` 或独立 `--ssot-lint` |

未来 layout.v2 启用后，`ssot/current-md-size` 与本文件 `state/*` 互补，不重叠。

## 历史项目兼容

- **mic-en 等 layout.v1 项目**：本 4 条 rule 全部可用，直接通过 `/ms-pipeline realign --scope=health --dry-run` 调用。
- 不依赖 `aliases.yml` / `traceability.yml`（这两个文件是 layout.v2 产物）。
- 不依赖 `agents.md devdocs.docs_layout_version` 字段。

## 变更日志

| 日期 | 变更 |
|------|------|
| 2026-05-22 | 初始版本（health scope 4 条 [新增] rule 落地）|
| 2026-05-25 | 新增 `design/adr-only-revision`（维度 a 结构正确性），落地 system-design 增量修订正文偏差检测 |
