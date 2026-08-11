# M 组规则参考

> 配合 [SKILL.md](../SKILL.md) 使用。本文件是 M 组（markdownlint 标记规则）的知识底座，供两处场景查阅：
>
> 1. `npx` 不可用时，AI 按本文件人工核对规则含义；
> 2. 将来若有人提议对 M 组启用 `markdownlint --fix`，须先逐条回答第 4 节的盲区清单。
>
> 本仓配置文件：[`assets/markdownlint.jsonc`](../assets/markdownlint.jsonc)。

## 1. 规则总表

出处：[markdownlint 官方 `doc/Rules.md`](https://github.com/DavidAnson/markdownlint/blob/main/doc/Rules.md)，2026-08-11 抓取，对应 `markdownlint` v0.41.1 / `markdownlint-cli2` v0.23.2（与本仓 `npx` 解析到的版本一致）。

**规则计数核实**：官方当前共定义 53 条规则，非设计方案 §3.1 估算的「54 条」——该估算标注为「由摘要生成」，此处以官方原文核实结果（53 条）为准予以更正。编号区间 `MD001`–`MD060` 内以下 7 个编号当前未定义（历史保留或从未启用）：`MD002`、`MD006`、`MD008`、`MD015`、`MD016`、`MD017`、`MD057`。

「Fixable」列取自官方文档每条规则正文是否含 `Fixable:` 声明；未声明一律记「否」。

| 规则 | Alias | 说明 | Fixable |
|---|---|---|---|
| `MD001` | `heading-increment` | 标题层级须逐级递增，不得跳级 | 否 |
| `MD003` | `heading-style` | 标题风格（ATX / Setext）须统一 | 否（官方未标注，见 4.1「fixable 状态已核实为否」） |
| `MD004` | `ul-style` | 无序列表标记符号须统一 | 是 |
| `MD005` | `list-indent` | 同级列表项缩进须一致 | 是 |
| `MD007` | `ul-indent` | 无序列表缩进空格数 | 是 |
| `MD009` | `no-trailing-spaces` | 行尾空格 | 是 |
| `MD010` | `no-hard-tabs` | 禁止硬制表符 | 是 |
| `MD011` | `no-reversed-links` | 链接语法颠倒（如 `(text)[url]`） | 是 |
| `MD012` | `no-multiple-blanks` | 禁止连续多个空行 | 是 |
| `MD013` | `line-length` | 行长度上限 | 否 |
| `MD014` | `commands-show-output` | 命令前 `$` 提示符与是否展示输出须一致 | 是 |
| `MD018` | `no-missing-space-atx` | ATX 标题 `#` 后缺少空格 | 是 |
| `MD019` | `no-multiple-space-atx` | ATX 标题 `#` 后有多个空格 | 是 |
| `MD020` | `no-missing-space-closed-atx` | 闭合 ATX 标题 `#` 内侧缺少空格 | 是 |
| `MD021` | `no-multiple-space-closed-atx` | 闭合 ATX 标题 `#` 内侧有多个空格 | 是 |
| `MD022` | `blanks-around-headings` | 标题前后须有空行 | 是 |
| `MD023` | `heading-start-left` | 标题必须从行首开始 | 是 |
| `MD024` | `no-duplicate-heading` | 同一文档内出现重复标题内容 | 否 |
| `MD025` | `single-h1` / `single-title` | 文档内出现多个一级标题 | 否 |
| `MD026` | `no-trailing-punctuation` | 标题末尾有多余标点 | 是 |
| `MD027` | `no-multiple-space-blockquote` | 引用符号 `>` 后有多个空格 | 是 |
| `MD028` | `no-blanks-blockquote` | 引用块内部出现空行 | 否 |
| `MD029` | `ol-prefix` | 有序列表编号前缀风格（全 `1.` / 递增） | 是 |
| `MD030` | `list-marker-space` | 列表标记后的空格数 | 是 |
| `MD031` | `blanks-around-fences` | 围栏代码块前后须有空行 | 是 |
| `MD032` | `blanks-around-lists` | 列表前后须有空行 | 是 |
| `MD033` | `no-inline-html` | 禁止内联 HTML | 否 |
| `MD034` | `no-bare-urls` | 禁止裸 URL（未用 `<>` 或链接语法包裹） | 是 |
| `MD035` | `hr-style` | 分隔线风格须统一 | 否 |
| `MD036` | `no-emphasis-as-heading` | 用强调（加粗/斜体）冒充标题 | 否 |
| `MD037` | `no-space-in-emphasis` | 强调标记内侧有多余空格 | 是 |
| `MD038` | `no-space-in-code` | 代码 span 内侧有多余空格 | 是 |
| `MD039` | `no-space-in-links` | 链接文本内侧有多余空格 | 是 |
| `MD040` | `fenced-code-language` | 围栏代码块须声明语言 | 否 |
| `MD041` | `first-line-h1` / `first-line-heading` | 文件首行须为一级标题 | 否 |
| `MD042` | `no-empty-links` | 禁止空链接 | 否 |
| `MD043` | `required-headings` | 文档须符合指定的标题结构 | 否 |
| `MD044` | `proper-names` | 专有名词大小写须正确 | 是 |
| `MD045` | `no-alt-text` | 图片须有替代文本 | 否 |
| `MD046` | `code-block-style` | 代码块风格（围栏式 / 缩进式）须统一 | 否 |
| `MD047` | `single-trailing-newline` | 文件须以单个换行符结尾 | 是 |
| `MD048` | `code-fence-style` | 围栏符号风格（`` ``` `` / `~~~`）须统一 | 否 |
| `MD049` | `emphasis-style` | 强调（斜体）标记风格须统一（`*` / `_`） | 是 |
| `MD050` | `strong-style` | 加粗标记风格须统一（`**` / `__`） | 是 |
| `MD051` | `link-fragments` | 链接锚点片段须有效 | 是 |
| `MD052` | `reference-links-images` | 引用式链接 / 图片须有对应标签定义 | 否 |
| `MD053` | `link-image-reference-definitions` | 链接 / 图片引用定义须被实际使用 | 是 |
| `MD054` | `link-image-style` | 链接 / 图片语法风格须统一 | 是 |
| `MD055` | `table-pipe-style` | 表格竖线风格须统一 | 否 |
| `MD056` | `table-column-count` | 表格各行列数须一致 | 否 |
| `MD058` | `blanks-around-tables` | 表格前后须有空行 | 是 |
| `MD059` | `descriptive-link-text` | 链接文本须有描述性（避免"点此"） | 否 |
| `MD060` | `table-column-style` | 表格列内边距风格须统一 | 是（见 4.1「文档实现不一致」） |

## 2. 本仓配置的默认值调整（13 条）

markdownlint 出厂默认是「全部规则打开 + 按英文散文调参数」。实测基线（2026-08-11，对 `AGENTS.md` + `README.md` + `docs/workflows.md`）：出厂默认告警 138 条，其中 `MD060` 占 78 条（57%）、`MD013` 占 35 条（25%），82% 是噪音；套用本仓配置后降至 22 条，逐条核对为 100% 真问题（`MD040` × 11、`MD036` × 4、`MD031` × 4、`MD032` × 2、`MD001` × 1）。以下 13 条默认值调整就是让报告从「不可用」变「可用」的全部理由。

首次真实运行复测（同日，本 skill 落地后）：出厂默认 **139**、本配置仍为 **22**，构成与上表逐项一致。多出的 1 条是 `MD013`（35 → 36），来自 `README.md` 新增本 skill 索引条目的那一行——**基线是活的**，绝对值随文档修订漂移，须保持的是「出厂默认百余条 / 本配置二十余条」这个量级差，以及本配置下 100% 真问题这条判断。

| 规则 | 配置 | 理由 |
|---|---|---|
| `MD013` line-length | 关闭 | Google 规定的 80 列源于英文纯文本时代的终端宽度，对中文段落与 LLM 输出的长句不适用 |
| `MD033` no-inline-html | 关闭 | `<details>`、`<br>` 在技术文档中常用且必要 |
| `MD041` first-line-h1 | 关闭 | `references`、片段文档常不以 H1 开头 |
| `MD024` no-duplicate-heading | `siblings_only: true` | 不同章节下出现同名子标题是合法结构（如「示例」在多节下重复出现） |
| `MD029` ol-prefix | `one_or_ordered` | 兼容「`1.` 全同」与「递增编号」两种写法，二者在本仓文档中都在用 |
| `MD004` ul-style | `dash` | 默认值 `consistent` 只保证单文档内部一致，不约束跨文档；固定为 `-` 是把本仓既有书写习惯显式声明为唯一答案，避免「新建文档第一笔用什么符号纯属偶然，之后全文档跟随」的漂移。若将来要放宽回 `consistent`，须先证明放宽后不会在多文档间引入新的风格不一致 |
| `MD046` code-block-style | `fenced` | 默认值 `consistent` 允许缩进式代码块；但缩进代码块无法声明语言，与本仓开启的 `MD040`（围栏代码块须声明语言）构成隐性冲突——遇到缩进式代码块时两条规则的要求无法同时满足。固定为 `fenced` 消除这个冲突，也避免缩进代码块与 4 空格嵌套列表在视觉上混淆 |
| `MD048` code-fence-style | `backtick` | 默认值 `consistent` 允许 `` ``` `` 与 `~~~` 混用；固定为反引号排除混用可能，反引号也是本仓现有约定 |
| `MD049` / `MD050` emphasis-style / strong-style | `asterisk` | 下划线 `_foo_` 紧邻 CJK 字符时部分渲染器不生效（`中文_foo_中文` 在这些渲染器中不会渲染为斜体），星号无此问题 |
| `MD007` ul-indent | `2` | 本仓实测既有文档中 54 处使用 2 空格缩进、1 处使用 4 空格，从多数既有约定 |
| `MD010` no-hard-tabs | `code_blocks: false` | 不得改动代码块内容本身包含的 tab 字符——那是数据，不是排版噪音 |
| `MD060` table-column-style | `style: "padded"` | 实测噪音第一名（78 条 / 57%）。本仓表格约定是内容行两侧加空格 + 分隔行 `\|---\|---\|`；`padded` 下该约定下降至 0 误报，`compact` 反而升至 100 条误报。取 `padded` 而非直接关闭规则——同样零误报，但仍能抓出真正的列宽不一致 |

## 3. 与 Google Markdown Style Guide 的两处主动分歧

以下两处须在此明确记录理由，避免后续被误当作「遗漏、待补的修正项」：

- **不采纳 80 列行长上限**：Google 的规定源于英文纯文本时代的终端宽度惯例，对中文段落、LLM 输出的长句均不适用（同 `MD013` 关闭的理由）。
- **不采纳 4 空格嵌套缩进，取 2**：从本仓既有约定（同 `MD007` 配置的理由），不跟随 Google 的建议值。

Google docguide 中其余可机械化落地的主张——ATX 标题、围栏代码块须声明语言、行尾禁空格、图片须有 `alt`、长列表用惰性编号（`1.` 全同）——已分别由 `MD003`、`MD040`、`MD048`、`MD009`、`MD045`、`MD029` 覆盖，无需额外配置。其 `[TOC]` 语法是 Google 内部渲染器专有指令，不纳入本仓规则集。

## 4. 为何不使用 `markdownlint --fix`

**首版不实现自动修复。`markdownlint-cli2` 只做只读扫描，全部检出走报告。**

原方案曾尝试建立「安全 fixer 白名单」支撑自动修复。`fixable` 只表示工具能修改文本，**不表示修改后语意仍然安全**——原判据「纯空白、纯标记等价变换即安全」经两轮审查证明存在多个盲区，白名单从 27 条逐次收缩至 9 条、再至 4 条（`MD019`、`MD021`、`MD032`、`MD047`）。这 4 条的实际价值只是修复罕见笔误与补一个文件末尾换行，其中 `MD032` 还是四条里风险最高者；而支撑它们需要临时目录隔离执行、`stdin` 切断配置发现、显式版本锁定、闭集配置校验一整套机制。收益与代价明显失衡，故整体放弃，改为**只报告，不自动改写**。

下表是本 skill 的核心知识资产：它回答「为什么不能无脑相信 `--fix`」，也是将来若有人提议重新启用自动修复时，必须先逐条给出反驳的清单。

### 4.1 十类破坏模式

| 破坏模式 | 涉及规则 | 说明与反例 |
|---|---|---|
| 翻转强调语义 | `MD049`、`MD050` | CommonMark 的 delimiter run 规则决定嵌套结构随符号变化而变化。举例：`` `*_foo_*` `` 是 emphasis 套 emphasis；若 `MD049`/`MD050` 统一为星号，改写为 `` `**foo**` ``，变成 strong——语义从「强调」升级为「加粗」。反向同理：`` `__*foo*__` ``（strong 套 emphasis）转为 `` `***foo***` `` 后，嵌套关系变成 emphasis 套 strong |
| 合并相邻列表 | `MD004` | CommonMark 中，相邻的 `*`、`+`、`-` 列表即使符号相邻也被视为**不同**列表。示例：`` `* A1` `` `` `* A2` `` 与 `` `- B1` `` `` `- B2` `` 之间只隔一个空行，是两个独立列表；若 `MD004` 把符号统一为 `-`，两者符号相同后会被重新识别为同一个列表，原有的「两组」结构消失 |
| 创建结构 | `MD011`、`MD018`、`MD020`、`MD034`、`MD037` | 修复对象本来是普通文本，修复后凭空变成 Markdown 结构。示例：`` `#Heading` `` 因 `#` 后缺空格，在 CommonMark 中只是一行普通文本；`MD018` 补上空格后变成 `` `# Heading` ``，成为一级标题——这是**造出新结构**，不是修正已有结构 |
| tight/loose 列表转换 | `MD022`、`MD031`、`MD058` | 在列表项内的标题、围栏代码块、表格外围插入空行，会把 tight list 转为 loose list，改变生成 HTML 的段落包裹方式（`<li>文本` 变成 `<li><p>文本</p>`），进而影响排版间距。示例：列表项内嵌一段未加空行包裹的围栏代码块，`MD031` 修复后在代码块前后插入空行，使原本紧凑的列表变松散 |
| 改变块归属 | `MD012` | 空行数量参与块结构的终止判定。示例：`` `- A1` ``、`` `- A2` `` 后跟两个连续空行，再接 `` `- B1` ``、`` `- B2` ``——部分渲染实现以「连续两个空行」判定列表在此终止，视为两个独立列表；`MD012` 把连续空行压缩为一个后，两处列表可能被重新识别为同一列表的延续，归属发生变化 |
| 改动数据 | `MD038`、`MD039` | code span 内容与链接文本是数据本身，不是排版空白。示例：`` `a[ b ]c` `` 中方括号内的空格若被 `MD039` 删除，`b` 前后的空格随之消失，链接文本从 `` `a b c` `` 收缩为 `` `abc` ``，与原始可见文本不再一致；`MD038` 对 code span 同理，会改变复制出来的字符串本身 |
| 改动序号 | `MD029` | 有序列表的首个数字决定渲染出的 `<ol start>` 起始值。示例：`` `2. Step two` `` `` `3. Step three` `` 若被 `MD029` 改写为从 `` `1.` `` 开始的连续编号，显示编号从「2、3」变为「1、2」——当编号对应外部文档的步骤号、法规条款号等来源编号时，这些编号本身承载信息，机械重排会丢失它 |
| 缩进未同步 | `MD005`、`MD007`、`MD023`、`MD027`、`MD030` | 修复只移动列表标记符号本身或删除行首缩进，不会同步移动该列表项的续行、嵌套子列表与内部围栏代码块。示例：外层 `` `* Item` `` 下嵌套 `` `    * Nested item` ``（4 空格缩进），若 `MD007` 把外层标记的缩进规则改为 2 空格但不重算嵌套项的缩进，嵌套项可能因缩进不再落在「属于父项」的判定范围内而脱离父列表，被重新解析为顶层列表或代码块 |
| 文档实现不一致 | `MD060` | 官方文档标注该规则 `Fixable`，但本仓实测 `markdownlint-cli2` 对 `MD060` 违规执行 `--fix` 后文件无变化，即实现未真正输出修复信息。若信任「文档说 fixable 就能修」会得到假阳性的安全感 |
| fixable 状态已核实为否 | `MD003` | 早期抓取的规则摘要表把 `MD003` 标为 fixable。经核对 markdownlint 官方 `doc/Rules.md` 原文（`MD003` 章节不含 `Fixable:` 声明）与官方配置 schema，确认 `MD003` **不是** fixable——摘要表的标注有误。此条目原为「存疑待核实」，现已核实并更正 |

### 4.2 MD009 的已知误判记录

原方案曾认为给 `MD009`（`no-trailing-spaces`）配置 `br_spaces: 2` 即可保留 Markdown 硬换行（行尾两个空格）。审查指出该参数只让「恰好两个尾随空格」不报错；一旦行尾有三个及以上尾随空格，fixer 会删除全部空格而非收敛为 2 个，硬换行随之消失，`--fix` 在这种输入下会静默破坏渲染结构。本仓未对 `MD009` 做默认值调整，此记录仅用于警示：即使某条规则「看起来」可以配参数保住语义，也须验证参数在边界输入下的实际行为。

## 5. 安全提示：配置发现风险

`markdownlint-cli2` 会沿被扫描的目标路径自动发现 `.markdownlint-cli2.*` 与 `.markdownlint.*` 配置文件，其中 `.cjs` / `.mjs` 形式的配置文件**会被当作代码执行**，且 CLI2 没有提供关闭「配置自动发现」的命令行参数。对不受信任的第三方仓库执行扫描——即便只是只读扫描——也存在代码执行风险，须在使用前明示给用户。

`--config` 传入的只是 base configuration：会被目标路径子目录下的配置覆盖，也会被文档内的 `markdownlint-enable` / `markdownlint-disable` / `markdownlint-configure-file` 注释覆盖（后者可用 `noInlineConfig: true` 禁用）。因为只读扫描不改动文件、误报的代价很低，本 skill **允许项目自有配置生效**——目标仓库自己的 markdownlint 约定优先于本 skill 默认值，这是合理行为。
