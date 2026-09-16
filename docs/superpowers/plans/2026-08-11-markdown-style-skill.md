# markdown-style Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增独立 skill `markdown-style`，对 Markdown 文档（尤其 LLM 输出）做两个维度的只读审查——markdownlint 标记规范与中文排版规范。

**Architecture:** 纯只读审查器，不含可执行代码。M 组由 `markdownlint-cli2` 判定（工具缺失时询问用户，不静默安装）；T 组（中文排版）与 L 组（LLM 排版毛病）由 AI 按 references 规则表判定。全部检出只报告；修改走"落盘内容与推导内容哈希相等"的事务流程，git 干净时后置展示 diff。

**Tech Stack:** Markdown + YAML frontmatter（本仓为规格库，无构建/测试框架）；外部工具 `markdownlint-cli2`（Node）；验证靠实测告警计数与文本一致性检查。

**Spec:** [2026-07-31-markdown-style-skill-design.md](../specs/2026-07-31-markdown-style-skill-design.md)（已提交，commit `dada2bf`）。**本计划所有文档内容以该 spec 为唯一来源**，每个任务标注对应 spec 章节，实施时逐条搬运，不得自行发明规则或出处。

## Global Constraints

- `SKILL.md` ≤ 500 行（本仓硬约束）
- 全部文档用中文撰写
- **不得创建 `scripts/` 目录或任何可执行代码**——本仓为纯规格库，spec §8 明确此约束
- 规则表每条须标注权威出处（markdownlint 规则 ID、GB/T 条款号、或排版指北章节号）
- **不得凭记忆编造国标条款号**（spec §3.1）。可用条款号仅限 spec 中已出现的：GB/T 15834 §4.2.3.3、§4.3.3.3、§4.3.3.4、§4.11.2、§5.1.1、§5.1.2、前言
- 提交格式：Conventional Commits，中文描述，结尾附 `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`
- 每个新建的 `.md` 文件都须通过本 skill 自己的配置（dogfood，0 告警）
- 目录：`skills/markdown-style/`，frontmatter `name: markdown-style`

## File Structure

| 文件 | 职责 | 内容来源 |
|---|---|---|
| `skills/markdown-style/assets/markdownlint.jsonc` | M 组只读扫描配置（消噪） | spec §3.2 默认值调整表（13 行） |
| `skills/markdown-style/references/markdown-rules.md` | M 组 54 条规则表 + 「为何不用 `--fix`」盲区分类 + Google docguide 分歧 | spec §3.1、§3.2、§3.2.1 |
| `skills/markdown-style/references/cjk-typography.md` | T 组 7 条规则 + 逐条证伪记录 + 保护区清单 | spec §3.3、§6.2 |
| `skills/markdown-style/references/llm-artifacts.md` | L 组 3 条规则 + 语意承载豁免表 | spec §3.4 |
| `skills/markdown-style/templates/report.md` | 报告输出模板（含工具版本头） | spec §5、§3.2.2 |
| `skills/markdown-style/SKILL.md` | 主流程 + 三组概览 + 工具检测四选项 + 事务流程 + 生成时清单 | spec §1.1、§2、§4、§5、§6 |
| `skills/markdown-style/references/fixtures.md` | 验证样例集（保护区三反例 + T 组误检样例，各带期望结果） | spec §9——**此文件超出 spec §8 的文件结构，为 Task 8 承载运行期验证所需的新增项**，实施时须同步补进 spec §8 |
| `AGENTS.md:9` | 独立 skill 计数 13 → 14 | spec §10 |
| `README.md:7`、独立工具 Skill 表 | 总数 35 → 36 + 索引条目 | spec §10 |

---

### Task 1: markdownlint 配置与实测基线

先做配置，因为它是唯一有客观验收数字的产物（138 → 22），后续所有文档的 dogfood 检查都依赖它。

**Files:**
- Create: `skills/markdown-style/assets/markdownlint.jsonc`

**Interfaces:**
- Consumes: 无
- Produces: 配置文件路径 `skills/markdown-style/assets/markdownlint.jsonc`，供 Task 2–7 的 dogfood 检查与 SKILL.md 流程引用。配置为 cli2 包装格式 `{ "config": { <规则键值> } }`

- [ ] **Step 1: 先建立失败断言——确认基线噪音数**

工具未安装时 cli2 经 npx 取得。运行出厂默认配置，记录数字：

```bash
cd /Users/mason/Projects/skills
npx --yes markdownlint-cli2 AGENTS.md README.md docs/workflows.md 2>&1 \
  | grep -cE "\.md:[0-9]+"
```

Expected: `138`（若因文档修订而不同，记录实际值作为新基线，但须仍是"MD060 + MD013 占 8 成"的量级）

- [ ] **Step 2: 确认噪音构成**

```bash
npx --yes markdownlint-cli2 AGENTS.md README.md docs/workflows.md 2>&1 \
  | grep -oE "MD[0-9]+/[a-z-]+" | sort | uniq -c | sort -rn
```

Expected: `MD060` 与 `MD013` 合计约占 80%（实测 78 + 35 = 113/138）

- [ ] **Step 3: 写配置文件**

13 条键值逐条来自 spec §3.2 默认值调整表。`.jsonc` 允许注释，每条带理由：

```jsonc
{
  "config": {
    // 关闭：Google docguide 的 80 列源于英文纯文本终端宽度，对中文段落不适用
    "MD013": false,
    // 关闭：<details> <br> 在技术文档中常用且必要
    "MD033": false,
    // 关闭：references 子文档、片段文档常不以 H1 开头
    "MD041": false,
    // 不同章节下的同名子标题合法
    "MD024": { "siblings_only": true },
    // 兼容 `1.` 全同与递增两种写法
    "MD029": { "style": "one_or_ordered" },
    "MD004": { "style": "dash" },
    "MD046": { "style": "fenced" },
    "MD048": { "style": "backtick" },
    // 下划线紧邻 CJK 字符时部分渲染器不生效
    "MD049": { "style": "asterisk" },
    "MD050": { "style": "asterisk" },
    // 本仓实测 54 处 2 空格、1 处 4 空格，从既有约定
    "MD007": { "indent": 2 },
    // 不得改动代码块内的 tab
    "MD010": { "code_blocks": false },
    // 实测噪音第一名（78 条）。padded 归零且仍能抓真不一致；compact 反升至 100
    "MD060": { "style": "padded" }
  }
}
```

- [ ] **Step 4: 验证配置生效且降噪达标**

```bash
npx --yes markdownlint-cli2 --config skills/markdown-style/assets/markdownlint.jsonc \
  AGENTS.md README.md docs/workflows.md 2>&1 | grep -cE "\.md:[0-9]+"
```

Expected: `22`

若报 `Unrecognized/unsupported config file name`，说明 cli2 不接受该文件名——改用 `.markdownlint-cli2.jsonc` 作为文件名放在 `assets/` 下，并在后续所有引用处同步。此为已知风险点，须实测确认而非假设。

- [ ] **Step 5: 验证残留 22 条全为真问题**

```bash
npx --yes markdownlint-cli2 --config skills/markdown-style/assets/markdownlint.jsonc \
  AGENTS.md README.md docs/workflows.md 2>&1 \
  | grep -oE "MD[0-9]+/[a-z-]+" | sort | uniq -c | sort -rn
```

Expected: `MD040`×11、`MD036`×4、`MD031`×4、`MD032`×2、`MD001`×1（合计 22，零 MD060、零 MD013）

- [ ] **Step 6: 提交**

```bash
git add skills/markdown-style/assets/markdownlint.jsonc
git commit -m "$(cat <<'EOF'
feat(markdown-style): 新增 markdownlint 只读扫描配置

13 条默认值调整消噪:实测本仓三篇文档 138 条 → 22 条,残留 100% 真问题。
MD060 取 style=padded(噪音第一名 78 条,padded 归零且仍抓真不一致)。

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: M 组规则参考（markdown-rules.md）

**Files:**
- Create: `skills/markdown-style/references/markdown-rules.md`

**Interfaces:**
- Consumes: Task 1 的配置路径（文档中引用配置文件说明各默认值调整）
- Produces: 供 SKILL.md 在"npx 不可用降级"路径引用的完整规则表；供将来有人提议启用 `--fix` 时必须逐条回答的盲区清单

- [ ] **Step 1: 写文件，四个必需章节**

内容逐条搬运 spec，不得自行增删规则：

1. **规则总表**——markdownlint MD001–MD060 共 54 条。每行含：规则 ID、alias、一句话说明、是否 fixable。数据源见 spec §3.1 抓取状态表说明（该表由摘要生成，**MD003 的 fixable 状态存在冲突证据，须在表中标注"存疑，须核对官方文档"**）
2. **本仓配置的默认值调整**——13 条，逐条含理由，来源 spec §3.2 表格
3. **与 Google docguide 的两处主动分歧**——80 列行长不采纳、4 空格嵌套缩进不采纳（取 2）；并说明 Google 其余可机械化主张已由 MD003 / MD040 / MD048 / MD009 / MD045 / MD029 覆盖，`[TOC]` 为 Google 内部渲染器专有不纳入。来源 spec §3.2
4. **「为何不使用 `--fix`」盲区分类**——来源 spec §3.2.1，须完整包含全部 10 类破坏模式及其涉及规则：

| 破坏模式 | 涉及规则 |
|---|---|
| 翻转强调语义 | MD049 · MD050 |
| 合并相邻列表 | MD004 |
| 创建结构 | MD011 · MD018 · MD020 · MD034 · MD037 |
| tight/loose 列表转换 | MD022 · MD031 · MD058 |
| 改变块归属 | MD012 |
| 改动数据 | MD038 · MD039 |
| 改动序号 | MD029 |
| 缩进未同步 | MD005 · MD007 · MD023 · MD027 · MD030 |
| 文档实现不一致 | MD060 |
| fixable 状态存疑 | MD003 |

每类须带 spec 中的具体反例（如 `*_foo_*` → `**foo**` 由 emphasis 套 emphasis 变 strong；`#Heading` 因缺空格本是普通文本，MD018 补空格后成为标题）。另须包含 MD009 判断错误记录（`br_spaces: 2` 只让"恰好两个尾随空格"不报错，三个及以上时 fixer 删除全部空格，硬换行消失）。

5. **安全提示**——CLI2 沿目标路径发现 `.markdownlint-cli2.*` / `.markdownlint.*`，其中 `.cjs` / `.mjs` **会执行代码**，且无关闭配置发现的命令行参数。来源 spec §3.2.2

- [ ] **Step 2: 验证盲区分类完整**

```bash
cd /Users/mason/Projects/skills
for id in MD049 MD050 MD004 MD011 MD018 MD020 MD034 MD037 MD022 MD031 MD058 \
          MD012 MD038 MD039 MD029 MD005 MD007 MD023 MD027 MD030 MD060 MD003 MD009; do
  grep -q "$id" skills/markdown-style/references/markdown-rules.md || echo "MISSING: $id"
done; echo "check done"
```

Expected: 只输出 `check done`，无 `MISSING`

- [ ] **Step 3: 验证规则总表覆盖 54 条**

```bash
grep -oE "MD0[0-9]{2}" skills/markdown-style/references/markdown-rules.md \
  | sort -u | wc -l
```

Expected: ≥ 54

- [ ] **Step 4: dogfood——文件须通过本 skill 自己的配置**

```bash
npx --yes markdownlint-cli2 --config skills/markdown-style/assets/markdownlint.jsonc \
  skills/markdown-style/references/markdown-rules.md 2>&1 | grep -cE "\.md:[0-9]+"
```

Expected: `0`

- [ ] **Step 5: 提交**

```bash
git add skills/markdown-style/references/markdown-rules.md
git commit -m "$(cat <<'EOF'
docs(markdown-style): 新增 M 组规则参考

54 条 markdownlint 规则表 + 本仓 13 条默认值调整理由 + 与 Google docguide
两处分歧 + 「为何不用 --fix」10 类盲区分类(含 MD049/050 翻转强调语义、
MD018 创建结构等具体反例)。

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: T 组中文排版参考（cjk-typography.md）

**Files:**
- Create: `skills/markdown-style/references/cjk-typography.md`

**Interfaces:**
- Consumes: 无
- Produces: T1–T4、T6、T7、T9 七条规则的判定依据，供 SKILL.md 流程步骤 3 引用；保护区清单供 §6.2 修改纪律引用

- [ ] **Step 1: 写文件，四个必需章节**

1. **权威源与降级说明**——来源 spec §3.1。须写明：以 Node 版 markdownlint 与国标/排版指北为准，本地两个参考项目降为二手；GB/T 15835 **不纳入**（管用字选择非排版，且 2011 版允许两种形式并存，机械检查必然误报），T2/T3 依据是排版指北，**不得引用该标准条款号**

2. **七条规则表**——来源 spec §3.3，每条须带出处：

| ID | 规则 | 出处 |
|---|---|---|
| T1 | 中文与半角英文之间加一个半角空格 | 排版指北 §1 |
| T2 | 中文与数字之间的空格风格须统一（判据：同一文档内同时出现"5 台"与"5台"） | document-style-guide text.md（2） |
| T3 | 数字与英文单位之间加空格（`°` `%` 例外） | 排版指北 §3/§4 |
| T4 | 全角标点两侧不留**行内横向**空格 | 排版指北 §5；GB/T 15834 §5.1.1 |
| T6 | 问号/叹号叠用超过三个 | GB/T 15834 §4.2.3.3、§4.3.3.3 |
| T7 | 全角字母数字宜用半角 | 排版指北 §8 |
| T9 | 中文省略号须为六连点 `……` | GB/T 15834 前言、§4.11.2 |

**全部为只报告**，无自动修复项。

3. **逐条证伪记录**——来源 spec §3.3，六条必须全部保留（它们是最容易被后续"优化"重新引入的错误）：
   - T1 原含"与数字"，与 T2 直接矛盾（`2026年7月31日`、`第3章`、`3个节点` 会被强制加空格）→ 中数关系全归 T2
   - T3 白名单答不了"此处是不是单位"（`iPhone 5s` → `iPhone 5 s`；CSS `margin: 2em` → `2 em` 变无效值）→ 白名单仅用于降低误报
   - T4 会删除 Markdown 硬换行（行尾两空格是 hard break）→ 限定"同一行内部的横向空格"
   - T6 改语气强度属语意；国标 §4.3.3.3 允许叠用最多三个（原文示例"我要揭露！我要控诉！！我要以死抗争！！！"），§4.3.3.4 允许 `？！` 连用，§5.1.2 为二叠三叠问叹连用规定占位宽度 → 仅报"超过三叠"，二至三叠不提示
   - T7 全角字符可能是数据本身（`系统必须拒绝用户名 ａｄｍｉｎ` 转半角后测试对象即改变；全角 `＠` 可能刻意避免触发 mention）→ 检出须附风险提示
   - T9 与 document-style-guide 冲突：该项目主张 `⋯⋯`（U+22EF），国标前言规定六连点 `……`（U+2026 × 2）→ 以国标为准；`...` → `……` 仅在紧邻 CJK 时报告，英文语境 `...`、`foo(...)`、`a...b` 范围语法一律不报

4. **保护区清单**——来源 spec §6.2 第 3 条。八项：围栏代码块（含 blockquote 与列表内的围栏）、缩进代码块、行内 code span（含跨行与多反引号）、YAML frontmatter、HTML 块、链接与图片的 URL 与 title、autolink。另含"行内标记外侧落点"规则（`中文**abc**` → `中文 **abc**`，空格加在标记符外侧）与"结构不确定时跳过并标注"

5. **争议项**——排版指北标注为争议项的两条（链接两侧是否加空格、是否使用直角引号「」）为 ℹ️，仅在文档内写法不统一时提示，不给强制主张。来源 spec §3.3

- [ ] **Step 2: 验证七条规则齐备且各带出处**

```bash
cd /Users/mason/Projects/skills
F=skills/markdown-style/references/cjk-typography.md
for t in T1 T2 T3 T4 T6 T7 T9; do grep -q "| $t " "$F" || echo "MISSING rule: $t"; done
grep -q "GB/T 15834" "$F" || echo "MISSING: 国标出处"
grep -q "排版指北" "$F" || echo "MISSING: 排版指北出处"
echo "check done"
```

Expected: 只输出 `check done`

- [ ] **Step 3: 验证未编造国标条款号**

只允许 spec 中已出现的条款号：

```bash
grep -oE "§[0-9]+(\.[0-9]+)*" skills/markdown-style/references/cjk-typography.md \
  | sort -u
```

Expected: 输出只含 `§1`、`§3`、`§4`、`§5`、`§8`（排版指北章节）与 `§4.2.3.3`、`§4.3.3.3`、`§4.3.3.4`、`§4.11.2`、`§5.1.1`、`§5.1.2`（国标条款）。出现任何其他国标条款号即为编造，须删除。

- [ ] **Step 4: 验证 T5/T8 未复活**

原方案的 T5（半角标点转全角）与 T8（英文整句保持半角标点）已删除，不得出现为规则：

```bash
grep -nE "^\| T[58] " skills/markdown-style/references/cjk-typography.md \
  && echo "ERROR: T5/T8 复活" || echo "ok"
```

Expected: `ok`

- [ ] **Step 5: dogfood**

```bash
npx --yes markdownlint-cli2 --config skills/markdown-style/assets/markdownlint.jsonc \
  skills/markdown-style/references/cjk-typography.md 2>&1 | grep -cE "\.md:[0-9]+"
```

Expected: `0`

- [ ] **Step 6: 提交**

```bash
git add skills/markdown-style/references/cjk-typography.md
git commit -m "$(cat <<'EOF'
docs(markdown-style): 新增 T 组中文排版参考

七条规则(全部只报告)+ 逐条证伪记录 + 八项保护区清单 + 两条争议项。
关键裁决:国标 §4.3.3.3 允许问叹号叠用最多三个,故"消除重复标点"违反国标;
国标前言规定省略号六连点,document-style-guide 主张的 ⋯⋯ 不合规;
GB/T 15835 管用字选择非排版,不纳入。

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: L 组 LLM 排版毛病参考（llm-artifacts.md）

**Files:**
- Create: `skills/markdown-style/references/llm-artifacts.md`

**Interfaces:**
- Consumes: 无
- Produces: L1–L3 三条规则的可量化判据与豁免表，供 SKILL.md 流程步骤 3 引用

- [ ] **Step 1: 写文件**

来源 spec §3.4。三条规则，判据须可量化（否则 AI 每次判定不一致），全部只报告：

| ID | 规则 | 判据 |
|---|---|---|
| L1 | emoji 装饰滥用 | 标题行含 emoji；或同级列表中 ≥ 3 项以 emoji 开头 |
| L2 | 加粗滥用 | 单段内 ≥ 3 处 `**`；或整段/整句被加粗包裹；或独占一行的加粗文本后紧跟正文（与 MD036 重叠时以 MD036 为准） |
| L3 | 结构滥用 | 列表嵌套 > 3 层；或列表仅含 1 项 |

**语意承载豁免表**（不计入 L1）：表格单元格内的 emoji；作为级别标记紧邻说明文字的（⛔ ⚠️ ℹ️ ✅）；承载信息的标记——状态标记（🟢 🟡 🔴）、权限标记（🔒），删除即丢信息。

L2 检出须附提示：`**必须**` 这类加粗承载规范强度，删除会削弱语义；独占一行的加粗改为标题会改变目录、锚点与层级。

另须写明**边界原则**（来源 spec §2）：本组只碰标记与结构，不删内容。原方案曾包含"结尾套话""无信息量总结""表格滥用改写"三项，因涉及删改内容已删除；并记录两个自欺点——"只改 Markdown 标记"不等于"不改语意"、"需要人确认的 assist"不等于"在边界内"。

- [ ] **Step 2: 验证三条规则与豁免表齐备**

```bash
cd /Users/mason/Projects/skills
F=skills/markdown-style/references/llm-artifacts.md
for t in L1 L2 L3; do grep -q "$t" "$F" || echo "MISSING: $t"; done
grep -q "🔒" "$F" || echo "MISSING: 权限标记豁免"
grep -q "🟢" "$F" || echo "MISSING: 状态标记豁免"
echo "check done"
```

Expected: 只输出 `check done`

- [ ] **Step 3: 验证被删规则未复活**

```bash
grep -nE "套话|无信息量总结|表格滥用改写" skills/markdown-style/references/llm-artifacts.md \
  | grep -v "已删除\|不实现\|曾包含" \
  && echo "ERROR: 越界规则复活" || echo "ok"
```

Expected: `ok`

- [ ] **Step 4: dogfood**

本文件含 emoji 豁免示例，须自身通过配置：

```bash
npx --yes markdownlint-cli2 --config skills/markdown-style/assets/markdownlint.jsonc \
  skills/markdown-style/references/llm-artifacts.md 2>&1 | grep -cE "\.md:[0-9]+"
```

Expected: `0`

- [ ] **Step 5: 提交**

```bash
git add skills/markdown-style/references/llm-artifacts.md
git commit -m "$(cat <<'EOF'
docs(markdown-style): 新增 L 组 LLM 排版毛病参考

三条可量化判据(emoji 装饰 / 加粗滥用 / 结构滥用,全部只报告)+ 语意承载
豁免表(状态标记、权限标记删除即丢信息)。记录被删的三项越界规则与两个自欺点。

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: 报告模板（report.md）

**Files:**
- Create: `skills/markdown-style/templates/report.md`

**Interfaces:**
- Consumes: Task 2–4 的三组规则 ID 命名（M 组用 `MDxxx`，T 组用 `Tx`，L 组用 `Lx`）
- Produces: 报告结构，供 SKILL.md 流程步骤 4 引用

- [ ] **Step 1: 写模板**

来源 spec §5 步骤 4、§3.2.2 版本记录要求。必需要素：

- **报告头**：目标文件、语言判定结果（中文 / 英文 / 混合）、**markdownlint-cli2 实际版本号**（spec §3.2.2：报告可复现的实质是知道出自哪个规则集）、扫描时间
- **按组分节**：M 组 / T 组 / L 组，每组一张表
- **每条含**：行号 · 规则 ID · 严重级（⛔ / ⚠️ / ℹ️）· 说明 · 权威出处
- **降级标注**：若走了 AI 兜底扫描（markdownlint 不可用），须在 M 组标题处明示"AI 兜底扫描，非工具判定"
- **结构不确定项**：单列一节，标注"结构不确定，未处理"
- **修改结果区**（应用修改后填）：git 干净时的后置 diff 展示位，并写明可用 `git checkout --` 回滚

- [ ] **Step 2: 验证模板含版本占位与三组分节**

```bash
cd /Users/mason/Projects/skills
F=skills/markdown-style/templates/report.md
grep -q "版本" "$F" || echo "MISSING: 工具版本"
grep -q "git checkout" "$F" || echo "MISSING: 回滚提示"
for g in "M 组" "T 组" "L 组"; do grep -q "$g" "$F" || echo "MISSING: $g"; done
echo "check done"
```

Expected: 只输出 `check done`

- [ ] **Step 3: dogfood**

```bash
npx --yes markdownlint-cli2 --config skills/markdown-style/assets/markdownlint.jsonc \
  skills/markdown-style/templates/report.md 2>&1 | grep -cE "\.md:[0-9]+"
```

Expected: `0`

- [ ] **Step 4: 提交**

```bash
git add skills/markdown-style/templates/report.md
git commit -m "$(cat <<'EOF'
docs(markdown-style): 新增报告输出模板

三组分节 + 每条含行号/规则 ID/严重级/权威出处 + 报告头记录 cli2 实际版本
(报告可复现的实质)+ 降级标注 + 结构不确定项单列 + 回滚提示。

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: SKILL.md 主文件

放在最后，因为它引用前五个任务的全部产物路径。

**Files:**
- Create: `skills/markdown-style/SKILL.md`

**Interfaces:**
- Consumes: `assets/markdownlint.jsonc`（Task 1）、`references/markdown-rules.md`（Task 2）、`references/cjk-typography.md`（Task 3）、`references/llm-artifacts.md`（Task 4）、`templates/report.md`（Task 5）——全部按相对路径引用
- Produces: 可发现的 skill 定义，frontmatter `name: markdown-style`

- [ ] **Step 1: 写 frontmatter**

参照本仓既有独立 skill（`skills/e2e-test-flow/SKILL.md` 为最近范例）。`allowed-tools` 只列实际需要的——无 MCP 依赖：

```yaml
---
name: markdown-style
description: 审查 Markdown 文档(尤其 LLM 输出)的标记与排版规范:markdownlint 标记检查 + 中文排版检查(GB/T 15834 与中文文案排版指北)+ LLM 排版毛病检查。只碰排版与标记,不改原文语意;全部只报告,修改经确认后走哈希校验事务。Triggers on "/markdown-style", "markdown 规范", "排版检查", "markdownlint", "中英文空格", "文档格式检查", "规范文档". NOT for 文风与语言润色(长句/被动语态/的地得)、代码规范检查(用 code-quality)、提交信息规范(用 commit-convention)。
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion, TodoWrite
metadata:
  patterns: [tool-wrapper, checklist]
  interaction: multi-turn
user-invocable: true
---
```

- [ ] **Step 2: 写正文，八个必需章节**

内容来源逐节标注：

1. **身份与边界**（spec §1.1、§2）——"审查策略 skill，非自动格式化 skill"；只碰排版与标记不碰语意；含存废判据（若只剩配置加一句"AI 通读"则不配做 skill）
2. **三组概览**（spec §3）——M/T/L 表格，含判定者与默认状态；指针到三个 references
3. **工具获取**（spec §3.2.2）——检测顺序（项目 `node_modules/.bin/` → `PATH` → 询问）；四选项表（brew / npm -g 并标 mise 失效风险 / npx 临时 / 跳过降级）；**不得静默安装**；安全提示（`.cjs`/`.mjs` 配置会执行代码）
4. **执行流程**（spec §5）——0 前置检查 → 1 语言判定（英文文档跳过 T 组）→ 2 M 组扫描 → 3 T+L 组 AI 通读 → 4 报告 → 5 询问是否应用 → 6 二次验证
5. **严重级别**（spec §4）——⛔ / ⚠️ / ℹ️ 三级判据；并明写"全部检出一律只报告，不存在自动修改路径"
6. **事务流程**（spec §6.1）——**须包含**：不提供结构安全保证的声明；确认时机分两种情况的表格（git 干净则后置、否则前置）；八步流程；唯一硬不变量 `hash(A) == hash(E)`
7. **修改纪律**（spec §6.2）——七条，第一条为**禁止正则全文替换**（禁用 `sed` / `perl -pi` / 全局 `replace_all`）
8. **生成时清单**（spec §8）——约 15 条最高频约束，**内嵌不读 references**，供会话或其他 skill 直接引用。从 M 组高频项（代码块标语言、标题不跳级、围栏与列表环绕空行）+ T 组（中英空格、全角标点两侧不留空格）+ L 组（不用 emoji 装饰标题、不用加粗代替标题）中选取

- [ ] **Step 3: 验证行数硬约束**

```bash
wc -l < skills/markdown-style/SKILL.md
```

Expected: ≤ 500

- [ ] **Step 4: 验证引用路径真实存在**

```bash
cd /Users/mason/Projects/skills
grep -oE "(references|assets|templates)/[a-z0-9.-]+" skills/markdown-style/SKILL.md \
  | sort -u | while read -r p; do
  [ -f "skills/markdown-style/$p" ] || echo "BROKEN LINK: $p"
done; echo "check done"
```

Expected: 只输出 `check done`

- [ ] **Step 5: 验证八个必需章节齐备**

```bash
F=skills/markdown-style/SKILL.md
for s in "边界" "工具" "流程" "严重" "事务" "纪律" "清单"; do
  grep -q "$s" "$F" || echo "MISSING section: $s"
done
grep -q "不得静默安装" "$F" || echo "MISSING: 静默安装禁令"
grep -q "禁止正则全文替换\|禁止.*全文替换" "$F" || echo "MISSING: 全文替换禁令"
echo "check done"
```

Expected: 只输出 `check done`

- [ ] **Step 6: dogfood**

```bash
npx --yes markdownlint-cli2 --config skills/markdown-style/assets/markdownlint.jsonc \
  skills/markdown-style/SKILL.md 2>&1 | grep -cE "\.md:[0-9]+"
```

Expected: `0`

- [ ] **Step 7: 提交**

```bash
git add skills/markdown-style/SKILL.md
git commit -m "$(cat <<'EOF'
feat(markdown-style): 新增 SKILL.md 主流程

身份(审查策略 skill 非自动格式化器)+ 三组概览 + 工具获取四选项(不静默安装)
+ 六步执行流程 + 事务流程(git 干净则后置确认,硬不变量为哈希相等)
+ 七条修改纪律(首条禁止正则全文替换)+ 内嵌生成时清单。

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 7: 仓库索引同步与全目录自检

**Files:**
- Modify: `AGENTS.md:9`
- Modify: `README.md:7`、`README.md` 独立工具 Skill 表（约 104–113 行）

**Interfaces:**
- Consumes: Task 1–6 全部产物
- Produces: 无（终结任务）

- [ ] **Step 1: 确认当前计数**

```bash
cd /Users/mason/Projects/skills
ls skills/ | grep -v '^_' | wc -l
grep -n "个 ms- 流程 skill" AGENTS.md
grep -n "共 35 个 skill" README.md
```

Expected: 目录数 `36`（Task 1 已建 `markdown-style/`）；AGENTS.md:9 仍写 `13 个独立 skill`；README.md:7 仍写 `共 35 个`

- [ ] **Step 2: 改 AGENTS.md:9**

将 `22 个 ms- 流程 skill + 13 个独立 skill` 改为 `22 个 ms- 流程 skill + 14 个独立 skill`，并在括号内的说明列表末尾追加 `markdown-style 为 Markdown 标记与排版审查器`。

- [ ] **Step 3: 改 README.md:7**

将 `共 35 个 skill` 改为 `共 36 个 skill`。

- [ ] **Step 4: 在 README.md「独立工具 Skill」表中追加一行**

插入位置：`| E2E 实测 | ...|` 之后、`| UI 调度 / 自描述 / 记忆 / 报告 | ...|` 之前。表格为 padded 风格，须与相邻行一致：

```markdown
| Markdown 规范 | `/markdown-style` | 标记与排版审查（markdownlint + GB/T 15834 中文排版 + LLM 排版毛病），只报告不改语意 |
```

- [ ] **Step 5: 验证计数一致**

```bash
cd /Users/mason/Projects/skills
D=$(ls skills/ | grep -v '^_' | wc -l | tr -d ' ')
grep -q "共 $D 个 skill" README.md || echo "MISMATCH: README 计数 ≠ $D"
grep -q "14 个独立 skill" AGENTS.md || echo "MISMATCH: AGENTS 独立计数"
grep -q "markdown-style" README.md || echo "MISSING: README 索引条目"
echo "check done"
```

Expected: 只输出 `check done`

- [ ] **Step 6: 全目录 dogfood——整个 skill 须通过自己的配置**

```bash
npx --yes markdownlint-cli2 --config skills/markdown-style/assets/markdownlint.jsonc \
  "skills/markdown-style/**/*.md" 2>&1 | grep -cE "\.md:[0-9]+"
```

Expected: `0`

- [ ] **Step 7: 验证未违反「无可执行代码」约束**

```bash
find skills/markdown-style -type f ! -name "*.md" ! -name "*.jsonc" | head
```

Expected: 无输出（只允许 `.md` 与 `.jsonc`，不得有 `scripts/` 或任何脚本）

- [ ] **Step 8: 验证 skill 可被发现**

```bash
grep -h "^name:" skills/markdown-style/SKILL.md
```

Expected: `name: markdown-style`

- [ ] **Step 9: 提交**

```bash
git add AGENTS.md README.md
git commit -m "$(cat <<'EOF'
docs: 同步 markdown-style skill 索引计数 35→36

AGENTS.md 独立 skill 计数 13→14;README.md 总数 35→36 并在独立工具表
追加索引条目。全目录 dogfood 通过(0 告警),无可执行代码。

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Self-Review

**1. Spec coverage**

| Spec 章节 | 落点 |
|---|---|
| §1 问题 | Task 6 步骤 2 章节 1 |
| §1.1 价值内核与身份 | Task 6 步骤 2 章节 1 |
| §2 边界原则 | Task 6 章节 1；Task 4 步骤 1（两个自欺点） |
| §3 规则分组 | Task 6 章节 2 |
| §3.1 权威源与抓取状态 | Task 2 章节 1（MD003 存疑标注）；Task 3 章节 1（GB/T 15835 不纳入） |
| §3.2 配置默认值 + Google 分歧 | Task 1 步骤 3；Task 2 章节 2、3 |
| §3.2.1 「为何不用 --fix」盲区 | Task 2 章节 4 + 步骤 2 校验 |
| §3.2.2 工具获取 + 安全提示 | Task 6 章节 3；Task 2 章节 5 |
| §3.3 T 组七条 + 证伪记录 + 争议项 | Task 3 全部 |
| §3.4 L 组三条 + 豁免表 | Task 4 全部 |
| §4 严重级别 + 只报告 | Task 6 章节 5 |
| §5 执行流程 | Task 6 章节 4；Task 5（报告结构） |
| §6 / §6.1 事务流程 | Task 6 章节 6 |
| §6.2 修改纪律 + 保护区 | Task 6 章节 7；Task 3 章节 4（保护区清单） |
| §8 文件结构 + 命令接口 | 本计划 File Structure；Task 6 frontmatter 与章节 8 |
| §9 验证方式 1（工具检测询问） | **未覆盖**——见下 |
| §9 验证 2（噪音基线） | Task 1 步骤 1–5 |
| §9 验证 3（保护区零误伤） | **未覆盖**——见下 |
| §9 验证 4（T 组检出准确性） | **未覆盖**——见下 |
| §9 验证 5（事务不变量） | **未覆盖**——见下 |
| §9 验证 6（端到端冒烟） | **未覆盖**——见下 |
| §10 仓库改动 | Task 7 |

**发现的缺口**：spec §9 的验证项 1、3、4、5、6 都是**运行期行为验证**，需要实际调用 skill 才能测——而本计划的七个任务只产出静态文档，无法在文档写作阶段验证"AI 通读时是否误伤保护区"或"事务哈希断言是否中止"。

这不是遗漏而是阶段差异：这些验证只能在 skill 建成后、首次真实运行时执行。**补 Task 8 承载**，见下。

**2. Placeholder scan**：无 TBD / TODO；每个写作任务都指向 spec 具体章节并列出必需要素与可量化校验命令；无"类似 Task N"式引用。

**3. Type consistency**：规则 ID 命名三处一致（M 组 `MDxxx`、T 组 `Tx`、L 组 `Lx`）；配置文件路径 `skills/markdown-style/assets/markdownlint.jsonc` 在 Task 1–7 全部一致；Task 1 步骤 4 已标注该文件名可能被 cli2 拒绝的风险与改名预案（若改名，Task 2–7 引用须同步）。

---

### Task 8: 首次真实运行验证

覆盖 spec §9 的运行期验证项（1、3、4、5、6）。这些无法在文档写作阶段完成，须在 skill 建成后实跑。

**Files:**
- Create: `skills/markdown-style/references/fixtures.md`（验证样例集，纯文档形式）
- Modify: 视运行结果修正 Task 1–6 产物

**Interfaces:**
- Consumes: Task 1–7 全部产物
- Produces: 验证记录；发现的缺陷回修到对应文件

- [ ] **Step 1: 写验证样例集**

`references/fixtures.md` 收录 spec §9 要求的全部陷阱样例，每个用围栏代码块包裹（保证自身不被检出）：

- **保护区三反例**（spec §9 项 3）：blockquote 内围栏 `> ```yaml` 内含 `中文abc: 10GB`；跨行多反引号 code span；含平衡括号的链接 `[中文API](https://example.com/a_(b)?q=中文ABC "版本v2")`
- **T 组误检样例**（spec §9 项 4）：`iPhone 5s`、`margin: 2em`、`2026年7月31日`、全角 `ａｄｍｉｎ`、三叠叹号 `！！！`、英文语境 `...`
- **每个样例标注期望结果**（应检出 / 不应检出 + 理由）

- [ ] **Step 2: 验证工具检测与询问路径（spec §9 项 1）**

在 `PATH` 中临时屏蔽 markdownlint-cli2 的环境下调用 skill，确认：不静默安装、四个选项都呈现、选"跳过"能走 AI 兜底降级。

```bash
env PATH=/usr/bin:/bin bash -c 'command -v markdownlint-cli2 || echo "not found — 应触发询问"'
```

Expected: 输出 `not found — 应触发询问`；随后调用 skill 须询问而非自行安装

- [ ] **Step 3: 验证保护区零误伤（spec §9 项 3）**

对 `fixtures.md` 运行完整流程并应用修改，然后逐字节比对保护区：

```bash
cd /Users/mason/Projects/skills
cp skills/markdown-style/references/fixtures.md /tmp/fixtures-before.md
# 运行 skill 并应用修改后：
diff <(sed -n '/^```/,/^```/p' /tmp/fixtures-before.md) \
     <(sed -n '/^```/,/^```/p' skills/markdown-style/references/fixtures.md) \
  && echo "保护区未被改动" || echo "ERROR: 保护区被改动"
```

Expected: `保护区未被改动`

- [ ] **Step 4: 验证 T 组检出准确性（spec §9 项 4）**

对 `fixtures.md` 的 T 组样例段跑审查，逐条核对报告与样例标注的期望结果一致。特别确认：`iPhone 5s` 未被要求加空格、`margin: 2em` 未被要求加空格、`2026年7月31日` 走 T2 只报风格统一性、三叠 `！！！` 不报（未超三叠）、英文语境 `...` 不报。

Expected: 零错误检出

- [ ] **Step 5: 验证事务不变量（spec §9 项 5）**

两个场景：

1. **并发写入中止**：预览生成后、落盘前用外部命令修改目标文件，确认 §6.1 步骤 4 的 `hash(B)` 断言中止事务
2. **确认时机分支**：git 工作区干净时确认后置（直接改完展示 diff）；`git stash` 制造脏工作区后确认前置（阻塞等待）

Expected: 场景 1 中止并重新生成；场景 2 两条分支行为符合 spec §6.1 表格

- [ ] **Step 6: 端到端冒烟（spec §9 项 6）**

对本仓一篇真实中文文档（建议 `docs/workflows.md`，Task 1 实测已知含 MD001 × 1、MD040 × 7、MD032 × 2）跑完整流程，人工核对报告与改动。

Expected: M 组检出与 Task 1 步骤 5 的实测构成一致；T/L 组检出经人工判断无误报

- [ ] **Step 7: fixtures.md 自身须通过 dogfood**

样例集中的"坏 Markdown"全部包在围栏代码块内，故文件自身应零告警：

```bash
npx --yes markdownlint-cli2 --config skills/markdown-style/assets/markdownlint.jsonc \
  skills/markdown-style/references/fixtures.md 2>&1 | grep -cE "\.md:[0-9]+"
```

Expected: `0`

- [ ] **Step 8: 把 fixtures.md 补进 spec §8 文件结构**

Modify: `docs/superpowers/specs/2026-07-31-markdown-style-skill-design.md` §8 的目录树，在 `references/` 下追加 `fixtures.md  # 验证样例集`，保持 spec 与实现一致。

- [ ] **Step 9: 回修发现的缺陷并提交**

```bash
cd /Users/mason/Projects/skills
git add skills/markdown-style/ docs/superpowers/specs/2026-07-31-markdown-style-skill-design.md
git commit -m "$(cat <<'EOF'
test(markdown-style): 首次真实运行验证与样例集

新增 fixtures.md 收录保护区三反例与 T 组误检样例(各带期望结果标注)。
验证覆盖 spec §9 的五项运行期检查:工具检测询问、保护区零误伤、
T 组检出准确性、事务不变量(并发中止 + 确认时机分支)、端到端冒烟。

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```
