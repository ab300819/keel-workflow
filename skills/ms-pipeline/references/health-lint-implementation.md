# Health Lint Implementation（health scope 可执行 lint rule 集）

> 把 [realign-scope-health.md](realign-scope-health.md) 维度 b/c 的检测要求落地为 Agent 可执行的 lint rule。
>
> 本文件 12 条 rule：8 条 **project scope**（解决 devdocs-state 膨胀 / 陈旧 + 死链 + 自造编号前缀），
> 4 条 **skill-library scope**（`flag/dangling-reference` + `skill/*`，⛔ 扫描对象不同，走 `--skills-dir`）。

## 目录

- 定位
- Rule 集（[新增] 12 条）
- Rule 详情
- Baseline 与增量扫描
- 退出码（CLI 集成）
- 性能预期
- Finding 输出 schema
- CLI 触发
- 历史项目兼容
- 变更日志

## 定位

| 治理对象 | 文件 |
|---------|------|
| health scope 入口与执行接口 | [realign-scope-health.md](realign-scope-health.md) |
| **本文件**：[新增] rule 的检测算法、严重度、修复路径（清单见下方 Rule 集表）| health-lint-implementation.md |
| 既有偏差评分 | `../../ms-sync/references/health-scoring.md` |

## Rule 集（[新增] 12 条）

| rule_id | 严重度 | 维度 | 适用 | 自动修复 |
|---------|--------|------|------|---------|
| `state/total-size-cap` | ⛔ / ⚠️ | c 过大 | v1+v2 | ❌（manual_decision）|
| `state/line-length-cap` | ⛔ | c 过大 | v1+v2 | ❌（manual_decision）|
| `state/forbidden-content` | ⚠️ | c/state-hygiene（c 维度子项）| v1+v2 | ❌（manual_decision）|
| `health/dead-link` | ⛔ | b 索引/链接 | v1+v2 | ⚠️ 部分（删除引用可自动；补建定义需 manual）|
| `design/adr-only-revision` | ⚠️ | a 结构正确性 | v1+v2 | ❌（语义判断必须 manual）|
| `submodule/pointer-drift` | ⛔ / ⚠️ | a 结构正确性 | v1+v2（仅 shell）| ❌（manual_decision）|
| `state/max-id-stale` | ⚠️ | c/state-hygiene（c 维度子项）| v1+v2 | ✅ 可自动（回填或删行，均需 manual_decision 选择）|
| `id/unknown-prefix` | ⚠️（永不升级 ⛔）| b 索引/链接 | v1+v2 | ❌（只报不判，manual_decision）|
| `flag/dangling-reference` | ⚠️ | b 索引/链接 | **skill 库**（非项目）| ❌（manual_decision）|
| `skill/size-cap` | ⛔ | a 结构正确性 | **skill 库** | ❌（manual_decision）|
| `skill/name-mismatch` | ⛔ | a 结构正确性 | **skill 库** | ❌（manual_decision）|
| `skill/dead-link` | ⚠️ | b 索引/链接 | **skill 库** | ❌（manual_decision）|

> 12 条全部 [新增]，可执行。⚠️ `flag/dangling-reference` 扫 skill 库不扫项目，走 `--skills-dir`，**不在** `--scope=health` 的 8 条之内。项目可直接调 `/ms-pipeline realign --scope=health` 受益。`submodule/pointer-drift` 仅在 shell 拓扑下生效，`inline` / `linked` 项目报 `not_applicable`。

---

### `skill/*` —— skill 库结构自检（3 条）

⛔ 与 `flag/dangling-reference` 同走 `--skills-dir`，扫 skill 库不扫项目。
落地 `repo-governance 1.2`「仓库无 validator」的首版高价值检查。

| rule_id | 检测 | 严重度 | 依据 |
|---|---|---|---|
| `skill/size-cap` | `SKILL.md` > 500 行 | ⛔ | [AGENTS.md](../../../AGENTS.md) 硬约束 |
| `skill/name-mismatch` | 目录名 ≠ frontmatter `name`，或目录缺 `SKILL.md` | ⛔ | 安装按 `name` 复制整个目录，跨 skill 相对引用依赖该约定 |
| `skill/dead-link` | 仓内相对链接（`./` `../` 开头）目标不存在 | ⚠️ | — |

**`skill/dead-link` ⛔ 跳过 `templates/`**：模板会复制进用户项目，其中相对路径按**产物落点**算，
不是仓内路径。实测 `ms-prd/templates` 的 `../../codebase-insight.md` 在仓内不存在，但模板落到
`docs/prd/requirements/index.md` 后正好解析到 `docs/codebase-insight.md`，**完全正确**。
⇒ 按仓内文件系统校验模板 = 必然误报，正是 `repo-governance 1.2` 警告过的那一类。

豁免：`<!-- health-lint-disable-line skill/dead-link -->`。

---

### `flag/dangling-reference`

**目的**：检测 skill 之间互相引用的 `--flag` 在目标 skill 目录内是否存在。

**⛔ 扫描对象与其余 8 条不同**：其余扫用户项目的 `docs/devdocs/` 与 `devdocs-state.md`；
本条扫 **skill 库自身**，故走独立入口 `health-lint.py --skills-dir <skills/>`，
⛔ 不并入 `--target` 的 project-scope 扫描。

**为什么需要**：子指令**没有解析器**——skill 是 markdown，harness 把 flag 当 `args`
原样传给模型，模型读 SKILL.md 的表对着认。⇒ flag 打错 / 改名 / 删除，**没有任何东西会报错**。

实证（2026-09-16）：`--incremental` 在 `a925ab0`「用户面 flag 收敛 49→20」随生产方删除，
**3 个消费方未同步**，其一写「必须委托给」；另有 3 处在 `verify-report` 模板里，
会随模板复制进用户项目。共 6 处，全部静默通过。

**算法**：

```text
1. names = skills/ 下全部目录名
2. 遍历 skills/**/*.md（跳过 ``` 代码块内的行）
3. 匹配 /([a-z][a-z0-9-]{2,})\s+(--[a-z][a-z-]*)
4. target ∈ names 时，读 skills/<target>/**/*.md 全文
5. flag 不在该全文中 → finding（severity = warning）
```

**严重度为何是 ⚠️ 而非 ⛔**：死 flag **降级是柔性的**——子 Agent 收到不认识的参数，
会按上下文自行解释，不像 `health/dead-link` 那样断掉用户产物里的追溯链。⛔ 但它仍是真漂移。

**豁免**：行内加 `<!-- health-lint-disable-line flag/dangling-reference: <理由> -->`。
用于反例（如「⛔ 不为 X 新建 `/skill --flag` 一类的入口」这种否定句）。

**已知盲区**：判据是「flag 在目标目录内能否搜到」⇒ **skill 引用自己的 flag 必然自证通过**。
实测的 6 处漂移全为跨 skill，v1 接受该盲区。

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
  1. 遍历定义源文件（**注意：devdocs-state.md 既不是定义源，也不是编号上界源**）：
       - docs/devdocs/**/*.md（排除 _archived/、.realign-plan.md、.health-report.md）
       - ⛔ **不从 devdocs-state.md 取"当前最大"作为上界**——该文件自称"事实快照，不追踪
         drift"，把它的手填值当上界会在它滞后时把合法新编号误报为 out-of-range
         （实测：state 表停在 AC-062 而资源文件已到 AC-064）。上界改由资源文件推导。
  2. 在每个定义源文件中识别"定义位置"模式：
       - heading：^(#{1,4})\s+(F|US|AC|CON|T|T-RF|ADR|INS|BUG|UT|IT|E2E|Journey)-\d+[a-z]?\b
       - 表格行（首列）：^\|\s*(F|US|AC|CON|...)-\d+[a-z]?\s*\|
       - 列表项 + 状态：^[-*]\s+\*?\*?(F|US|CON|...)-\d+[a-z]?\b
  3. 收集为 index：{ id: <编号>, defined_in: [<file>:<line>, ...] }
  4. 从 **Phase A 已建的 definition index** 推导 max_caps（⛔ 不读 state.md）：
       max_caps[<type>] = max(定义索引中该 type 的全部数值部分)
       仅用于 phase B 的 "out-of-range" 区分
  5. 另读 state.md "## 编号状态"表的"当前最大"列为 state_caps，**只用于 state/max-id-stale
     比对**（见该 rule），⛔ 不参与 phase B 判定

Phase B：扫描引用 + 范围编号展开
  1. 遍历同一批文件
  2. 提取所有引用 occurrence：
       a. 单点 regex：`\b(F|US|AC|CON|T|T-RF|ADR|INS|BUG|UT|IT|E2E|Journey)-\d+[a-z]?\b`
       b. 范围 regex（先 match 展开为单点列表）：
          `\b(F|US|AC|CON|T|T-RF|ADR|INS|BUG|UT|IT|E2E|Journey)-(\d+)~(?:\1-)?(\d+)\b`
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
              hint: "超出资源文件中该类型的最大已定义编号，可能是未来引用或拼写错误"
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

### `id/unknown-prefix`

**目的**：报出 `health/dead-link` 白名单外的编号前缀候选，供人工判断它的消费边界。⚠️ **非阻断提示，⛔ 不判违规、⛔ 不给归并建议**——前缀语义看名字猜不出来，工具无权替人分类。对应 `../../_shared/constraints.md` 的 `id/prefix-consumption-contract`。

**它治理什么**：白名单外的编号 `health/dead-link` 不查、`state/max-id-stale` 不推上界 ⇒ 打错一个号、引用一个已删除的号，**没有任何门会发现**。本 rule 只负责让这些前缀在报告里可见，⛔ 不主张它们不该存在。

**背景**：实战项目 `ai-code`（2026-09-10 按本节算法的文本原型抽样）有 **29 类**白名单外前缀候选、**3017 次** occurrence（口径：51 个 devdocs 文件，去代码块与 URL / 文件路径，**保留**行内代码；⛔ 非完整 Markdown 解析，是量级而非精确值）。其中 `D-`(853，决策) 与既有 `ADR-`(282) 并存且边界从未写下，是本 rule 想让人看见的那类；同一批里也有 `R-`(211，重定向安全判定规则) / `B-`(217，改动白名单放宽登记) 这类**合理的项目局部标识**，以及 `UTF`(11) 这类纯形态噪声。⇒ 三者工具分不开，**只报不判**。

**检测对象**：与 `health/dead-link` 同一批文件（`docs/devdocs/**/*.md`，排除 `_archived/`、`.realign-plan.md`、`.health-report.md`）。

**算法**（与 dead-link 共用一次文件遍历，⛔ 但词法独立，见下方"与 dead-link 的词法差异"）：

```text
1. 候选 regex（⛔ 不能用 \b 开头——`T-RF-001` 会被 \bRF-001\b 抓出幻影前缀 RF）：
     (?<![\w-])([A-Z][A-Za-z0-9]{0,5})-\d{1,4}[a-z]?(?![\w-])
   跳过：代码块 ``` ``` 内；_archived/ 内打 low-priority

2. 逐条过滤（命中任一即跳过）：
     a. prefix ∈ dead-link 白名单
        （F|US|AC|CON|T|T-RF|ADR|INS|BUG|UT|IT|E2E|Journey）—— dead-link 已管
     b. prefix ∈ 已登记但故意不入白名单的标识：
          M         —— 里程碑（constraints.md 已登记）
          FR / NFR  —— PRD 层官方编号，DevDocs 侧合法引用（阶段映射
                       NFR-XX → CON-XXX）。⛔ 必须硬跳过，每个项目都会命中
     c. prefix ∈ baseline 已抑制的前缀（见「Baseline 与增量扫描」）
     d. occurrence 落在 URL 或文件路径内
        ⛔ 不跳过行内代码 span —— 实测项目大量用反引号包裹真实编号
          （`04-dev-tasks-api.md:34` 的 `MR-038`），跳过会漏掉主要用法

3. 按 prefix 聚合，⛔ 不逐条报：
     finding {
       rule_id: id/unknown-prefix,
       severity: warning,
       file:   <样本首个文件>,      # 对齐统一 schema
       line:   <样本首个行号>,
       actual: <该前缀的 occurrence 数>,
       message: "未知前缀 <P>：<N> 次 occurrence，不在 dead-link 白名单内",
       context: "<最多 5 个 file:line 样本>",
       fix_suggestion: "manual_decision",
       auto_fixable: false
     }

4. check 计数单位 = **出现过的 prefix 数**（⛔ 不按 occurrence 计），
   避免单个前缀的引用量把 b 维度分母冲垮
```

**与 dead-link 的词法差异（⛔ 两者计数不可互相引用）**：

| 项 | `health/dead-link` | 本 rule |
|---|---|---|
| 数字段 | `\d+[a-z]?`（无上界）| `\d{1,4}[a-z]?`（限位数，避免吞掉 `SIDM-71103` 这类外部单号）|
| 范围展开 | `AC-148~152` 展开成 5 个 | ⛔ 不展开——按 prefix 报警不需要成员粒度 |
| 边界 | `\b` | `(?<![\w-])` / `(?![\w-])`——必须排除 `T-RF-001` 的幻影 |

⇒ **本 rule 的 occurrence 数与 dead-link 的引用组数是两套口径**，⛔ 不得相加或互相校验。

**人工处置**（`manual_decision`，⛔ 无自动改写，⛔ 工具不给建议）：按 `id/prefix-consumption-contract` 补一份消费契约（作用域 / 消费方 / 检查归属）。三种合法结局：登记进白名单、明确"人工核对、不进机器检查"、或确认无消费方后删除。⛔ 报告不预设哪一种。

**豁免走 baseline，⛔ 不走 devdocs-state 表**：`.health-baseline.yml` 的 `baseline_findings['id/unknown-prefix'].prefixes` 记**本机已看过的**前缀。

⛔ **baseline 不是语义审批**：该文件推荐 gitignore（见「Baseline 文件」），换机器 / 换人会重新报一遍；且一个前缀进 baseline 后，它未来新增的 `D-999` 也不再提示，本 rule ⛔ 不治理已有命名空间的后续增长。它只做**本机历史噪声抑制**。⇒ 想让一个局部前缀被团队持续接受，落点是产物内的消费契约声明（受版本控制），⛔ 不是 baseline。

⛔ **不用 state 表「## 编号状态」的行做白名单**——该表自称「事实快照，不追踪 drift，允许滞后」（模板 84~87 行），把它当豁免权威会重蹈 `state/max-id-stale` 的坑。

**误报与边界**：

- 形态相同的非编号必然命中：`UTF-8`、`P1-01` 这类审查发现编号、外部单号。⛔ 不硬编码黑名单——落进 baseline 消化。
- 存量项目首扫会一次性报出全部历史前缀 ⇒ 必须先 `--baseline-init`。这是本 rule 唯一可用的落地方式。
- 严重度统一 ⚠️ 且**永不升级为 ⛔**：它报的是"这里工具看不见"，不是"这里错了"。已有引用仍指向真实内容。
- 按 prefix 去重，同一前缀在 N 个文件出现只报一条。

---

### `design/adr-only-revision`

**目的**：检测系统设计文档（`02-system-design*.md`）的增量修订中，**ADR 章节有新增/修改但正文相关章节无同期更新**的反模式，对应 system-design/SKILL.md:336 的硬约束 `⛔ 禁止继续（增量设计）：仅追加 ADR 而正文相关章节未更新`。

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

### `state/max-id-stale`

**目的**：检测 `devdocs-state.md` 「## 编号状态」表的「当前最大」列与资源文件推导值不一致。

**为什么只是 ⚠️ 而不阻断**：该表**不再是编号权威**（`id-reference-check` 的上界已改从资源文件推导，分配新编号也直接扫资源文件）。它滞后不会导致错误的编号分配，只是让「单页速读」读到旧数字。所以这条 rule 报的是**缓存过期**，不是数据损坏。

> 改前该表被 `id-reference-check` 当作编号上界使用，而文件自称「事实快照，不追踪 drift」——**声明不可信却被当权威**。实测症状：state 表停在 `AC-062`，资源文件已到 `AC-064`，再新增就撞号。本 rule 与那次改动同批落地。

**检测对象**：`<repo_root>/.claude/rules/devdocs-state.md` 的「## 编号状态」表（不存在 → skip，输出 `not_applicable`）。

**算法**：

```text
1. 解析 state.md「## 编号状态」表，得 state_caps：{ F: 28, AC: 62, CON: 3, T: 23, ... }
   （占位符行如 `F-XXX` 跳过——那是未实例化的模板）
2. 复用 id-reference-check Phase A 的 definition index，按 type 取数值最大值
   得 derived_caps：{ F: 28, AC: 64, CON: 3, T: 23, ... }
3. 逐 type 比对：
     - state_caps[t] == derived_caps[t]        → 通过
     - state_caps[t] <  derived_caps[t]        → finding sub_type = "stale"（表滞后，最常见）
     - state_caps[t] >  derived_caps[t]        → finding sub_type = "phantom"
           hint: "表里的编号在资源文件中找不到定义——可能是编号被删除后未同步，
                  或该编号从未真正创建"
     - t 在 state 表有行但 derived 无该 type   → 同 "phantom"
     - t 在 derived 有但 state 表无行          → finding sub_type = "missing-row"（⚠️ 低优先）
4. 严重度统一 ⚠️
```

**修复动作**（`manual_decision` 二选一，⛔ 不默认自动改写）：

| 选项 | 动作 |
|---|---|
| 回填 | 把「当前最大」列改为 `derived_caps` 值 |
| 删行 | 删掉该类型的行——**若该项目从不看这张表，删掉比维护它更诚实** |

> `phantom` 子类型额外提示先查是否有编号被误删（那可能是 `health/dead-link` 的同源问题）。

**边界**：
- `_archived/` 下的副本不扫。
- 跨 worktree 多份 state.md 时只扫主 worktree（与 `state/total-size-cap` 一致）。
- 模板占位（`F-XXX` / `AC-XXX` 这类字面）不参与比对，避免对未实例化模板误报。

---

### `submodule/pointer-drift`

**目的**：检测外壳仓记录的子模块指针与子模块实际状态不一致，防止「代码已提交但追溯链断裂」静默累积。

**检测对象**：握手 `workspace_context.code_roots` 里的每个 `path`（⛔ 不自行读声明文件、不解析 `.gitmodules`，见 [_shared/constraints.md](../../_shared/constraints.md) `workspace/context-over-declaration`）。

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

### Baseline 文件

存量项目首次扫描违规量大，全量 ⛔ 阻断不可用。引入轻量 baseline 机制：

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
  id/unknown-prefix:
    prefixes: [D, MR, GAP, BLK]   # 本机已看过、暂不再提示的前缀；⛔ 非语义审批
notes: |
  首次扫描快照；新增违规以此为基线计算 delta。
```

### 可执行实现（v1）

**⛔ 先跑脚本，不要逐条人肉扫。** [`../scripts/health-lint.py`](../scripts/health-lint.py) —— 零依赖 stdlib。

⚠️ **改本文算法后跑一次 `--selftest`**（内置夹具，覆盖 9 条）。本仓无 CI，它是唯一会响的东西。

```bash
python3 <skill_dir>/scripts/health-lint.py --target <项目根> [--changed-only] [--fix=<rule_id>]
```

| | rule |
|---|---|
| ✅ 脚本已覆盖 | `state/total-size-cap` · `state/line-length-cap` · `state/forbidden-content` · `health/dead-link` · `state/max-id-stale` · `id/unknown-prefix` |
| ⚠️ 仍需 Agent 按本文算法执行 | `design/adr-only-revision`（git diff 行范围 × heading map）· `submodule/pointer-drift`（仅 shell 拓扑）|

脚本对后两条输出 `not_implemented` 到 stderr，⛔ **不得当作 pass**。
脚本 stdout 即本文「Finding 输出 schema」格式，退出码见下方「退出码（CLI 集成）」。

v1 **不含 baseline / `--apply` / 自动修复** —— 存量项目首扫噪声大属预期（尤见 `id/unknown-prefix`），
判读时按本文各 rule 的「误报与边界」处置。

## CLI 触发

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
- `id/unknown-prefix`：按 prefix 去重；baseline `prefixes` 列表内的不提示，新出现的前缀 ⚠️。⛔ 该列表只是本机噪声抑制，不代表这些前缀已被接受，也不追踪它们后续新增的编号
- `submodule/pointer-drift`：按 (code_root name, 漂移类型) 元组去重；baseline 中已知漂移不重复报，新增漂移一律按第 4 步算法定性的严重度（warning 或 blocker）报告。仅 shell 拓扑生效

## 退出码（CLI 集成）

| 退出码 | 含义 |
|--------|------|
| 0 | 无违规（或全部在 baseline 内）|
| 1 | 仅 warning 违规（state/forbidden-content / design/adr-only-revision / submodule/pointer-drift）|
| 2 | 有 blocker 违规（state/total-size-cap / state/line-length-cap / health/dead-link 新增 / submodule/pointer-drift）|
| 3 | lint 自身错误（git 不可用 / baseline 文件损坏 / report stale）|

> `submodule/pointer-drift` 按成因分级，同一条 rule 可能落在退出码 1 或 2：漏 bump / 未 update / 未初始化 → ⚠️ warning（退出码 1）；分叉 → ⛔ blocker（退出码 2）。仅 `shell` 拓扑生效，`inline` / `linked` 项目报 `not_applicable`，不计入任一退出码。

错误码（细分诊断，写入 finding.error_code）：

| error_code | 触发 |
|------------|------|
| `health/report-stale` | report_hash 校验失败或 source_git_commit 与 HEAD 不一致 |
| `health/baseline-missing` | `--since-baseline` 但 `.health-baseline.yml` 不存在 |
| `health/baseline-corrupt` | baseline schema 不匹配或 YAML 解析失败 |
| `health/manual-pending` | `--apply` 时存在 `status: pending` 的 manual_decision |
| `health/git-unavailable` | git 命令失败或 repo 不在 git 控制下（影响 dead-link / adr-only-revision / submodule/pointer-drift，仅 shell 拓扑时后者适用）|
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

所有 12 条 rule 的 finding 统一格式，与 `.health-report.md` § dimensions 字段对齐：

```yaml
- rule_id: state/total-size-cap | state/line-length-cap | state/forbidden-content | health/dead-link | design/adr-only-revision | submodule/pointer-drift | state/max-id-stale | id/unknown-prefix
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
| `/ms-pipeline realign --scope=health --dry-run` | project scope 的 8 条（⛔ 不含 `flag/dangling-reference`）|
| `/ms-pipeline realign --scope=health --fix=state/total-size-cap` | 仅该 rule |
| `/ms-pipeline realign --scope=health --apply` | 修复 auto_fixable + 已 AskUserQuestion 的 manual_decision |

不提供单独的 `--health-lint` 入口，统一通过 health scope 调用。

## 历史项目兼容

- project scope 的 8 条全部可用，直接通过 `/ms-pipeline realign --scope=health --dry-run` 调用。

## 变更日志

| 日期 | 变更 |
|------|------|
| 2026-05-22 | 初始版本（health scope 4 条 [新增] rule 落地：state/* + dead-link）|
| 2026-05-25 | 新增 `design/adr-only-revision`（维度 a 结构正确性），落地 system-design 增量修订正文偏差检测 |
| 2026-08-05 | 新增 `submodule/pointer-drift`（维度 a 结构正确性，仅 shell 拓扑生效），落地 devdocs 工作区模式外壳仓子模块指针漂移检测 |
| 2026-09-10 | 新增 `id/unknown-prefix`（维度 b 索引/链接，⚠️ 非阻断提示），落地 `_shared/constraints.md` `id/prefix-consumption-contract` 的可见性支撑。与 dead-link 共用文件遍历但**词法独立**（负向边界排除 `T-RF-001` 幻影、限位数、不展开范围），两者计数口径 ⛔ 不可互引 |
