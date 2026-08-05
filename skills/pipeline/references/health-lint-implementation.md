# Health Lint Implementation（health scope 可执行 lint rule 集）

> 把 [realign-scope-health.md](realign-scope-health.md) 维度 b/c 的检测要求落地为 Agent 可执行的 lint rule。
>
> 与 [layout/ssot-lint-implementation.md](layout/ssot-lint-implementation.md) 的区别：ssot-lint 治理 layout.v2 的 SSOT 强约束（v1 报 `not_applicable`）；本文件 6 条 rule **layout.v1+v2 通用**，专门解决 devdocs-state 膨胀 + 死链两类痛点。

## 定位

| 治理对象 | 文件 |
|---------|------|
| health scope 入口与执行接口 | [realign-scope-health.md](realign-scope-health.md) |
| **本文件**：6 条 [新增] rule 的检测算法、严重度、修复路径 | health-lint-implementation.md |
| layout.v2 专属 SSOT 强约束（12 条）| [layout/ssot-lint-implementation.md](layout/ssot-lint-implementation.md) |
| 既有偏差评分（layout.v1 legacy）| `../../sync/references/health-scoring.md` |

## Rule 集（[新增] 6 条）

| rule_id | 严重度 | 维度 | 适用 | 自动修复 |
|---------|--------|------|------|---------|
| `state/total-size-cap` | ⛔ / ⚠️ | c 过大 | v1+v2 | ❌（manual_decision）|
| `state/line-length-cap` | ⛔ | c 过大 | v1+v2 | ❌（manual_decision）|
| `state/forbidden-content` | ⚠️ | c/state-hygiene（c 维度子项）| v1+v2 | ❌（manual_decision）|
| `health/dead-link` | ⛔ | b 索引/链接 | v1+v2 | ⚠️ 部分（删除引用可自动；补建定义需 manual）|
| `design/adr-only-revision` | ⚠️ | a 结构正确性 | v1+v2 | ❌（语义判断必须 manual）|
| `submodule/pointer-drift` | ⛔ / ⚠️ | a 结构正确性 | v1+v2（仅 shell）| ❌（manual_decision）|

> 6 条全部 [新增]，本 commit 推到可执行；不依赖 layout.v2 启用。layout.v1 项目（mic-en 等）可直接调 `/ms-pipeline realign --scope=health` 受益。`submodule/pointer-drift` 仅在 `workspace_mode: shell` 下生效，`inline` 项目报 `not_applicable`。

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

**禁止模式**（canonical regex，PCRE / grep -P 兼容）：

#### `commit-hash`

```regex
(?:^|[@\s(\[])[0-9a-f]{7,40}(?=[\s.,;:)\]'"`]|$)
```

命中：`trade@0c263bf4d4` / `commit 51593927ee` / ``` `abc1234` ```
不命中：`AC-1234567`（前置是 `-` 而非 `@`/空白）/ `2026-05-22`（hex 但有非 hex 上下文 `-`）

#### `loc-count`

```regex
(?:[+-]?\d+(?:\.\d+)?\s*(?:LOC|loc|lines?|行)\b|净\s*[+-]\d+\s*LOC)
```

命中：`732 LOC` / `净 -85 LOC` / `+184 lines`
不命中：`AC-148` / `第 3 行`（"行" 前无数字且无 + /-）

#### `codex-score`

```regex
(?:\bR\d+\s*(?:health\s*=)?\s*\d{2,3}(?:\s*PASS)?\b|\bR\d+\s+\d{2,3}\s*[→\->]+\s*R\d+\s+\d{2,3}\b|双\s*\d{2,3}\s*分)
```

命中：`R1 88 → R2 92` / `R2 health=92 PASS` / `双 96 分`
不命中：`R1`（仅版本号无分数）

#### `diff-net`

```regex
(?<![\w\-])[+\-]\d+\s*/\s*[+\-]\d+(?![\w])
```

命中：`+184/-5` / `+2501/-39` / `2 files +184/-5`
不命中：`2026/05/22`（日期）/ `1/2`（无 +/- 前缀）

#### `file-path`

```regex
\b[\w./\-]*\.(?:java|ts|tsx|js|jsx|py|go|kt|swift|md)(?::L?\d+)?\b
```

命中：`OssFundTraceProviderImpl.java:L54` / `src/foo.ts` / `04-dev-tasks-p19.md`
不命中：`https://example.com`（无 `.<ext>` 段）

#### `submodule-ref`

```regex
\b(?:trade|envo|app|mstatic|trade-oss)@[0-9a-f]{7,40}\b
```

命中：`trade@0c263bf4d4` / `envo@0a22d80eb0`
不命中：`trade@` 单独（无 hash 跟随）

> ⚠️ 上述 regex 经验证：对 mic-en 实物 `devdocs-state.md` line 50 的 `trade@0c263bf4d4` / `+184/-5` / `R1 88 → R2 92` 均能命中。

**算法**：

```text
1. 定位扫描起始行：找到第一个 "## 编号状态" heading 行号 header_end_line（前序"## 单一事实源约定" + 边界声明段落豁免）
   fallback：若文件无 "## 编号状态"，从 line 51 开始扫描

2. 对每个 pattern_id 在 header_end_line 之后做 PCRE 全匹配：
   matches = Bash: awk "NR > $header_end_line" "$path" | grep -nP --line-number "<regex>"

3. 对每个 match 记录 finding：
   {
     line: <line_num + header_end_line>,
     pattern_id: <id>,
     matched_text: "<最多 80 字符截断>",
     surrounding_context: "<该行前后 ±30 字符>"
   }

4. severity = warning（不阻断，但建议清理）
5. 汇总 findings，按 line 升序输出；同行多 pattern 合并为一条 finding（patterns 字段为数组）
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
  1. 遍历定义源文件（**注意：devdocs-state.md 不是定义源**）：
       - docs/devdocs/**/*.md（排除 _archived/、.realign-plan.md、.health-report.md）
       - .claude/rules/devdocs-state.md 仅扫"## 编号状态"表的"当前最大"列，
         视为"编号空间上限"约束，**不视为单点定义**（state 是占位引用源，权威定义在资源文件）
  2. 在每个定义源文件中识别"定义位置"模式：
       - heading：^(#{1,4})\s+(F|US|AC|T|T-RF|ADR|INS|BUG|UT|IT|E2E|Journey)-\d+[a-z]?\b
       - 表格行（首列）：^\|\s*(F|US|AC|...)-\d+[a-z]?\s*\|
       - 列表项 + 状态：^[-*]\s+\*?\*?(F|US|...)-\d+[a-z]?\b
       - frontmatter id 字段（layout.v2）：^id:\s+(F|US|...)-\d+
  3. 收集为 index：{ id: <编号>, defined_in: [<file>:<line>, ...] }
  4. 从 state.md 的"当前最大"列收集 max_caps：{ F: F-028, AC: AC-210, ... }（仅用于 phase B 的 "out-of-range" 区分）

Phase B：扫描引用 + 范围编号展开
  1. 遍历同一批文件
  2. 提取所有引用 occurrence：
       a. 单点 regex：`\b(F|US|AC|T|T-RF|ADR|INS|BUG|UT|IT|E2E|Journey)-\d+[a-z]?\b`
       b. 范围 regex（先 match 展开为单点列表）：
          `\b(F|US|AC|T|T-RF|ADR|INS|BUG|UT|IT|E2E|Journey)-(\d+)~(?:\1-)?(\d+)\b`
          示例：AC-148~152 → [AC-148, AC-149, AC-150, AC-151, AC-152]
                AC-006~AC-008 → [AC-006, AC-007, AC-008]
                AC-148~AC-152（带前缀重复）→ 同上展开
       c. 代码块 ``` ``` 内的 occurrence 跳过（不视为有效引用）
       d. _archived/ 内的引用打 low-priority 标记
  3. 排除"定义位置"自身（Phase A 中已记为 definition 的 occurrence 不计为引用）
  4. 对剩余引用查 index：
       - 命中 → 跳过
       - 未命中 → 查 max_caps：
           a. 若 ref_id 数值部分 > max_caps[<type>] → finding sub_type = "out-of-range"
              hint: "超出 devdocs-state.md 声明的当前最大编号，可能是未来引用或拼写错误"
           b. 若 ref_id ≤ max_caps[<type>] 但定义索引未命中 → finding sub_type = "missing-definition"
              hint: "编号在声明范围内但找不到定义；可能拼写错误 / 未创建 / 已删除"
           c. finding {
                ref_id: <编号>,
                file: <file>,
                line: <line>,
                context: <±60 字符>,
                sub_type: out-of-range | missing-definition,
                hint: <按上述>
              }
  5. severity = blocker（low-priority 标记的不阻断主流程）
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
   - 输出 finding（见下方 schema）
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

### `submodule/pointer-drift`

**目的**：检测外壳仓记录的子模块指针与子模块实际状态不一致，防止「代码已提交但追溯链断裂」静默累积。

**检测对象**：`AGENTS.md` 的 `code_roots` 解析出的每个子模块路径。

**适用性门**：读 `AGENTS.md` 的 `workspace_mode`；非 `shell`（含字段缺失）→ 输出 finding `{ status: not_applicable }`，return。

**算法**（Agent 执行步骤）：

```text
1. 适用性门
   mode = AGENTS.md devdocs.workspace_mode
   if mode != "shell": 输出 not_applicable，return

2. 解析各代码根路径
   for name in code_roots:
     path = Bash: git config -f .gitmodules submodule.$name.path
     if 解析失败: severity = blocker
                  verdict_msg = "code_roots 中的 $name 不存在于 .gitmodules"
                  继续下一个

3. 读指针状态
   status = Bash: git submodule status -- "$path"
   首字符判定：
     ' ' (空格) → 一致，pass
     '+'        → 漂移，进第 4 步定性
     '-'        → 未初始化
                  severity = warning
                  verdict_msg = "$name 未初始化，跑 git submodule update --init $path"
                  继续下一个

4. 漂移定性（区分三种成因，见 workspace-shell.md § 指针漂移修复）
   recorded = Bash: git ls-tree HEAD "$path" | awk '{print $3}'
   actual   = Bash: git -C "$path" rev-parse HEAD
   if Bash: git -C "$path" merge-base --is-ancestor "$recorded" "$actual" 成功:
     severity = warning   # 漏 bump：子模块领先
     verdict_msg = "$name 已领先记录 N 个 commit，外壳仓漏 bump 指针"
   elif Bash: git -C "$path" merge-base --is-ancestor "$actual" "$recorded" 成功:
     severity = warning   # 未 update：本地滞后
     verdict_msg = "$name 落后外壳仓记录，跑 git submodule update $path"
   else:
     severity = blocker   # 分叉
     verdict_msg = "$name 与外壳仓记录已分叉（互无祖先关系），需人工裁定"

5. 输出 finding（见"Finding 输出 schema"）
```

**修复路径**：**不可自动修复**。三种成因的处置见 [layout/workspace-shell.md § 指针漂移修复](layout/workspace-shell.md#指针漂移修复)（本文不重复）。分叉情形必须 AskUserQuestion。

**误报与边界**：

- 子模块目录为空（未 `submodule update --init`）→ 报 ⚠️ 而非 ⛔，因为这是本地环境问题不是仓库问题
- `.gitmodules` 中存在但不在 `code_roots` 里的子模块（素材 / vendor）**不扫**

---

## Baseline 与增量扫描

### Baseline 文件

存量项目首次扫描违规量大，全量 ⛔ 阻断不可用。引入 baseline 机制（参考 ssot-lint baseline 设计但更轻量）：

位置：`<repo_root>/.claude/rules/.health-baseline.yml`（推荐 gitignore）

```yaml
schema: health-baseline.v1
generated_at: <iso-ts>
source_git_commit: <sha>
baseline_findings:
  state/total-size-cap:
    devdocs_state_size_bytes: 250574
  state/forbidden-content:
    count: 1247
    files: [".claude/rules/devdocs-state.md"]
  health/dead-link:
    count: 0
    refs: []
notes: |
  首次扫描快照；新增违规以此为基线计算 delta。
```

### CLI 触发

| 命令 | 行为 |
|------|------|
| `/ms-pipeline realign --scope=health --baseline-init` | 创建 baseline（不报告违规，记录当前状态）|
| `/ms-pipeline realign --scope=health --changed-only` | 仅扫 `git diff HEAD` 新增/变更行（增量模式）|
| `/ms-pipeline realign --scope=health --since-baseline` | 与 baseline 比对，只报告新增违规 |

### Delta 计算规则

- `state/total-size-cap`：报告 `delta = current_size - baseline_size`；delta < 2 KiB 视为可忽略小增长
- `state/forbidden-content`：按 (file, line) 元组 hash；baseline 中存在的视为存量，新增的报告为 violation
- `health/dead-link`：baseline 中已知死链不重复报；新增死链一律 ⛔
- `design/adr-only-revision`：baseline 不适用（按 commit 时间窗判定，本身就是增量语义）
- `submodule/pointer-drift`：按 (code_root name, 漂移类型) 元组去重；baseline 中已知漂移不重复报，新增漂移一律按第 4 步算法定性的严重度（warning 或 blocker）报告。仅 `workspace_mode: shell` 生效

## 退出码（CLI 集成）

| 退出码 | 含义 |
|--------|------|
| 0 | 无违规（或全部在 baseline 内）|
| 1 | 仅 warning 违规（state/forbidden-content / design/adr-only-revision / submodule/pointer-drift）|
| 2 | 有 blocker 违规（state/total-size-cap / state/line-length-cap / health/dead-link 新增 / submodule/pointer-drift）|
| 3 | lint 自身错误（git 不可用 / baseline 文件损坏 / report stale）|

> `submodule/pointer-drift` 按成因分级，同一条 rule 可能落在退出码 1 或 2：漏 bump / 未 update / 未初始化 → ⚠️ warning（退出码 1）；分叉 → ⛔ blocker（退出码 2）。仅 `workspace_mode: shell` 生效，`inline` 项目报 `not_applicable`，不计入任一退出码。

错误码（细分诊断，写入 finding.error_code）：

| error_code | 触发 |
|------------|------|
| `health/report-stale` | report_hash 校验失败或 source_git_commit 与 HEAD 不一致 |
| `health/baseline-missing` | `--since-baseline` 但 `.health-baseline.yml` 不存在 |
| `health/baseline-corrupt` | baseline schema 不匹配或 YAML 解析失败 |
| `health/manual-pending` | `--apply` 时存在 `status: pending` 的 manual_decision |
| `health/git-unavailable` | git 命令失败或 repo 不在 git 控制下（影响 dead-link / adr-only-revision / submodule/pointer-drift，仅 `workspace_mode: shell` 时后者适用）|
| `health/scan-timeout` | 扫描超过性能阈值（见下表）|

## 性能预期

| Repo 规模（docs/devdocs/**/*.md 数）| 全量扫 | --changed-only | 备注 |
|----|----|----|----|
| < 50 文件 | < 1 s | < 200 ms | mic-en 当前规模 |
| 50-200 文件 | < 3 s | < 500 ms | |
| 200-500 文件 | < 10 s | < 1 s | dead-link Phase B 是 O(N×M)，N 文件数 M 平均引用密度 |
| > 500 文件 | 推荐 `--changed-only` | < 2 s | 全量扫触发 `health/scan-timeout`（默认 30 s）|

性能瓶颈：

- `health/dead-link` 两遍扫描：O(N×M)，500 文件 + 平均 20 引用/文件 ≈ 10k 查询
- `design/adr-only-revision`：依赖 `git log` + `git show` + `git diff`，30 天窗口 commit 数为主导
- `state/forbidden-content`：单文件 PCRE，几乎与文件大小线性

降级策略：

- `--changed-only` 默认仅扫 `git diff HEAD~1..HEAD` 变更行 + 受影响文件
- `health/dead-link` 在 > 500 文件时建议加 `--skip-rule health/dead-link`，按需单独触发

## Finding 输出 schema

所有 6 条 rule 的 finding 统一格式，与 `.health-report.md` § dimensions 字段对齐：

```yaml
- rule_id: state/total-size-cap | state/line-length-cap | state/forbidden-content | health/dead-link | design/adr-only-revision | submodule/pointer-drift
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
| `/ms-pipeline realign --scope=health --dry-run` | 全部 6 条 |
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

- **mic-en 等 layout.v1 项目**：本 6 条 rule 全部可用，直接通过 `/ms-pipeline realign --scope=health --dry-run` 调用。
- 不依赖 `aliases.yml` / `traceability.yml`（这两个文件是 layout.v2 产物）。
- 不依赖 `agents.md devdocs.docs_layout_version` 字段。

## 变更日志

| 日期 | 变更 |
|------|------|
| 2026-05-22 | 初始版本（health scope 4 条 [新增] rule 落地：state/* + dead-link）|
| 2026-05-25 | 新增 `design/adr-only-revision`（维度 a 结构正确性），落地 system-design 增量修订正文偏差检测 |
| 2026-08-05 | 新增 `submodule/pointer-drift`（维度 a 结构正确性，仅 `workspace_mode: shell` 生效），落地 devdocs 工作区模式外壳仓子模块指针漂移检测 |
