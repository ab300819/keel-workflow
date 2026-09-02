# 制品型需求的追溯链（CON-XXX）

> ## ⛔ 本文已被推翻，不是现役规格
>
> 2026-09-02。本文记录的是**扩张版**方案：把 `CON` 做成全局一等公民、注入全部消费方（19 项改动清单、12 处消费方、执行层复用红绿）。
>
> **经 7 轮外部审查判定不会稳定收敛，已缩回。** 消费方计数 4 → 12 → 14 → 15 → 17 → 36 → 37，每轮都发现新形状；且本文 §2.8「复用既有红绿」的落地实现造出过死锁。
>
> 更根本的一条：本文把「非编码类任务被强制走 TDD」当成 CON 引入后的问题来解，而它 **CON 引入前就存在**（`⚪ 基础设施` 任务在强制矩阵三档下本就全 ■）。用户原始诉求是「挂不上追溯」，不是「跑不了 TDD」。
>
> **现役规格**：[_shared/constraints.md § CON 标识登记 / CON 的消费边界](../../../skills/_shared/constraints.md)
> **缩回记录与待办**：[audits/2026-09-01-con-traceability-backlog.md](../../audits/2026-09-01-con-traceability-backlog.md)
>
> 本文保留作为**推理过程与被否决路径的档案**——尤其 §1 的证据核对、§2.2 的命名裁决、§2.3 的 D4 塌缩理由仍然有效。


> 2026-09-01。**真因不是「NFR 没编号」，是追溯链只有「行为型需求」一种形状。** 触发场景（App Store 上架合规）只是暴露口，补丁不打在症状上。
>
> **R3 稿**。R1 → R2：Codex 裁定「削减后实施」，清单 20 → 13。R2 → R3：Codex 裁定 NO PASS（`readiness → dev-workflow → impl → sync` 仍走不通），清单 13 → 19，但**不新建执行分支**。轮次差异见 §8。
>
> 判据来源：[规则四分法](2026-08-26-devdocs-rule-triage-and-runlog-design.md) §2、[验收角色与能力表](2026-08-31-role-contract-and-acceptance-design.md) §2、[反向依赖追溯](2026-08-31-layout-v2-goal-attainment-design.md) §3。

## 0. 用户原话（逐字，不转述）

> 「这批工作在现有 DevDocs 里**无处可挂**，卡在 `/ms-dev-tasks` 的硬约束「每个任务必须关联 F-XXX 和 AC-XXX」上，只能编造 AC 或绕过流程直接改代码——两条都是错的。」

> 「D1 是真因，其余五条大半是它的下游。如果只加一个「上架合规」模板而不给 NFR 编号，下次换成「性能基线」「安全加固」「可观测性」，同样的挂靠失败会原样再来一次——T-23 日志规约那次其实已经来过了，只是当时靠跳过约束糊过去了。」

> 「D5 是这套体系里最贵的一条。文档漂移最多让人看错；而 ADR 推翻决定后留在旧世界的守卫脚本会主动阻塞正确的改动，且现场表现是「构建失败」，很容易被误判成自己改错了。」

> 「**构建守卫脚本是需求的可执行副本**，规约变了守卫必须跟着变，但没有任何链接告诉你这件事存在（也因此容易被误当成「绕过守卫」而不敢改）。」

红线（逐字）：

> 「⛔ 不新增流程阶段。⛔ 不把 NFR / 合规变成必填仪式。小项目零 NFR 也必须能跑完全流程。⛔ 不引入需要新工具链的自动化。⛔ 不为「上架」这一个场景做特化。」

验收（逐字）：

> 「「App Store 上架合规」这批工作能否在**不编造 AC、不绕过 /ms-dev-workflow** 的前提下走完 01→04 全链路」

## 1. 证据核对

现场项目（`~/Projects/Personal/video2image`）**不在本机**，用户已确认。项目侧证据（T-01 修辞式关联、T-23 挂 §12、§6.2 `.readWrite` vs AC-002 `.addOnly`、`verify-bundle.sh:14,18`、state 表停 062 而实际 064）按用户现场报告采信，**未独立复核**。技能侧全部实测。

| # | 断言 | 核实位置 | 结论 |
|---|---|---|---|
| D1 | §6 非功能性需求无编号 | `requirements/templates/requirements-template.md:150-170` | ✅ 三张散文表 + bullet |
| D1 | 任务必须关联 F+AC | `dev-tasks/SKILL.md:187` | ✅ |
| D1 | 任务必须关联 UT/IT/E2E | `dev-tasks/SKILL.md:188` | ✅ **用户未提，但同样挡人** |
| D2 | 无平台/合规采集入口 | `requirements/SKILL.md` 模式表 | ✅ 五种模式无一覆盖 |
| D3 | 待定项无生命周期 | `requirements/SKILL.md:323-327` | ✅ `needs review` 块无归属/无关闭条件/无报龄 |
| D4 | 漂移只覆盖 doc↔code | `verify/SKILL.md:86-137` | ✅ 三层全纵向；层 2「设计内部自洽」仅限 02 内部 |
| D5 | ADR 无影响回扫 | `design-template.md:441`、`incremental-design.md:150-165` | ✅ 且**模板主动排除**：`下游影响` 后注明「影响描述，非变更清单」；「修订清单」`§` 列只覆盖 02 章节 |
| D5 | 无 `superseded_by` | `dev-tasks/templates/task-template.md` | ✅ `已取代` 状态存在但无反向指针 |
| D6 | 编号最大值手工维护 | `agent-memory/templates/devdocs-state-template.md` | ✅ |

### 1.1 核对新发现

**① PRD 阶段本有编号，进 DevDocs 时被显式丢弃。**
`requirements/SKILL.md:89`：「`FR-XX` → 生成功能需求（F/US/AC）；**`NFR-XX` → 写入非功能需求章节**」。不是"忘了给编号"，是链路上有一处主动降级。

**② 分类学已承认制品型任务，追溯约束不承认。**
`dev-tasks/SKILL.md:139` 已有 `⚪ 基础设施 (DB/Config)`，`:109` 已有 `04-dev-tasks-infra.md`，`:161` 给它标了「设计稿关联：不适用」。**这个错配就是 D1 的发生机制**。

**③ 消费方全部只认 AC 链（R1 漏 4 处，R2 又漏 8 处）。** 完整清单见 §2.9 表。

**④ health-lint 把「声明不可信」的表当权威用（既存缺陷，与 D6 同源）。**
`devdocs-state-template.md` 自称「事实快照，不追踪 drift」，而 `health-lint-implementation.md:234` 的 `id-reference-check` 把它的「当前最大」列当作编号上界。用户实测的 062/064 就是它。

**⑤ dev-workflow 内部矛盾：非 TDD 出口被描述了，但被矩阵禁止（既存缺陷）。**
`execution-flow.md:82` 的 ■* 规则明写「只有在明确决定**不产出测试**（S3 为 ○ 或跳过）时才允许退化为 □/○」，而 `:89` 强制矩阵把 `S2/S3 骨架 + 测试骨架` 在 **fast / guarded / audit 三档全标 ■**。R3 顺带修掉。

### 1.2 对真因的修正

用户判定 D1 真因 = 「NFR 没编号」。方向同意，但**光给编号不够**——`dev-tasks/SKILL.md:188` 还要求「必须关联测试用例」。

R1 曾据此提议新增 `CK-XXX` 验证手段编号。**Codex 否决，已采纳**：`task-template.md:64,74,78` 的 ⚪ 基础设施卡**已经有**「测试方法」「验收标准」「TDD 模式 ⚪ 不适用」三字段。CK 的边际价值低于其全局成本。

**真正阻塞的是 `dev-tasks/SKILL.md:187-190` 四条无条件硬门 + §2.9 表里那 12 处消费方。**

## 2. 设计

### 2.1 平行链

```text
行为型（既有，不动）   F-XXX → US-XXX → AC-XXX → UT/IT/E2E-XXX → T-XXX
制品型（新增）         CON-XXX ──「验证方式」字段──────────────→ T-XXX
```

`CON-XXX`：**对制品/环境/流程的断言**（非对用户行为的断言）。承载性能基线、日志规约、安全加固、可观测性、上架合规、构建守卫——上架只是其中一类。

⛔ **`CON` 不进 F→US→AC 链**（写死）。否则会有人给 CON 造 US，重演 retrofit 逆向推导的循环论证。

「验证方式」是 CON 表的**字段**，不是编号实体，分两档：

| 档 | 内容 | 下游行为 |
|---|---|---|
| **`可执行`**（默认，优先） | 命令 / 脚本函数，如 `Scripts/verify-bundle.sh::check_category` | **完全复用既有 S2–S7 红绿**（§2.8） |
| `人工`（例外，须写明为何不可执行） | 核对步骤 + 判据，如「App Store Connect 后台发行区域设置」 | 走 ■* 规则本已描述的 S3 跳过出口（§2.8） |

> 用户裁定：**优先可执行，人工为例外**。理由：若两档平等，大量 CON 会默认写成「人工核对」而绕开红绿，用户原话担心的「跑到下次就没人知道它存在」会在这里重现。

### 2.2 编号命名

**命名跟判据走，不跟来源走。** 判据轴是「**行为可观测 vs 制品可检查**」，不是「功能 vs 非功能」。取 `CON`（Constraint 约束），不取 `N`（NFR）：

- 「非功能」是**否定式定义**——只说不是什么。而「Info.plist 含类目」「图标 1024×1024」「文案不含第三方商标」不是质量属性；反过来「响应时间 < 2s」写成 AC 也成立。名字与内涵两头不对齐。
- 「约束」罩得住全部：质量约束（性能）、平台强制约束（上架）、工程规约约束（日志）、安全基线约束。

| PRD 阶段 | DevDocs 阶段 |
|---|---|
| `FR-XX` | `F-XXX`（既有） |
| `NFR-XX` | `CON-XXX`（**新增**，改名映射需在 `requirements/SKILL.md:89` 显式写一行） |

**用户原话里的 `C-XXX` 合规项是升格采纳，不是否决**：`CON` = Constraint，**合规降为它的 `类别` 字段值**（与性能、日志规约、安全并列）。被否决的是独立合规命名空间——合规是 NFR 的一个 category（ISO 25010 里 compliance 就是 sub-characteristic），拆开会让「日志规约」这类非合规项重演 D1。**类别用字段表达，不用命名空间表达。**

| | 语义贴判据 | grep 安全 | 同族 |
|---|---|---|---|
| `N-XXX` | ⚠️ 偏（继承否定式定义） | ✅ | F / T 单字母 |
| `C-XXX` | ✅ | ❌ 与 `AC-001` 字面碰撞 | F / T 单字母 |
| **`CON-XXX`** | ✅ | ✅ | **INS / BUG / ADR 三字母同族** |

> Codex 建议退回 `NFR-XXX`（改名映射有迁移与认知成本）。**不采纳**——它未回应位数冲突（PRD `NFR-XX` 两位 vs DevDocs 三位靠位数区分，脆弱），且用户已在三候选间权衡后选定。成本论据记录备翻。

### 2.2.1 与 `INS` 的边界

`ms-insights` 是**外部改进建议的暂存 + 采纳决策**，状态机 `⏳待确认 → ✅已确认 → 🔄已转化`，**终态是转化掉**。

| | 是什么 | 生命周期 |
|---|---|---|
| `INS` | 入口——外部建议要不要采纳 | 暂存物，转完不再是活对象 |
| `CON` | 需求本身的一类（制品型） | 与 F/AC 同级，长期存在 |

`CON` 不分担 INS 职责，反而给 INS **多开一个出口**——此前 INS 只能转 F/US/AC，一条「日志应该带 traceId」的调研洞察确认后无处可转（**正是 T-23 那次的形状**）。

与 `needs review`（§2.4）的判据：**问「做不做」→ INS；问「是什么」→ needs review。**

### 2.2.2 编号 grep 必须整词匹配 + 数值比较

DevDocs 编号存在**前缀字面包含**关系：`UT-001` / `IT-001` 里含 `T-001`（**既存**）；`AC-001` 里含 `C-001`（已通过选 `CON` 规避）。

R1 提议 `grep -oE "\bT-[0-9]{2}"` → **三个 bug**：`\b` 在 POSIX ERE 无保证语义；只有前边界，`T-106` 截成 `T-10`；`sort | tail -1` 是字典序。
R2 改 `(^|[^[:alnum:]_])T-[0-9]+([^[:alnum:]_]|$)` → **仍有 bug**：边界字符被消耗，`T-01,T-02,T-03` 只得 `T-01` `T-03`（Codex 指出，本地实测证实）。

**R3 定稿**（实测通过：`T-1`→1、`T-106`→106、`UT-001`→无、`T-01,T-02,T-03`→全中）：

```sh
# -w 整词匹配（'-' 非词构成字符，故 UT-001 中的 T-001 不匹配），-n 数值序
grep -owhE 'T-[0-9]+' docs/devdocs/04-dev-tasks*.md | sed 's/T-//' | sort -n | tail -1
```

⛔ 不得用裸 `grep -o` + 字典序 `sort`。落 `_shared/constraints.md`。

### 2.3 D4：明说做不到，只留人工 lens

**不做机械检测。** R1 曾提议 `FACT` 受管事实登记表 + 五类字面量互斥检测，**两条均已删除**：

- `FACT` 是必然衰败的**手工反向索引**——每次新增或移动复述点都须人工同步，而本体系没有执行器保证同步。它与 D6 的手工 state 表是**同一失效模式**，而 §2.5 正是用这条理由否决了「ADR 反查索引文件」。R1 自相矛盾。
- 「`.readWrite` 与 `.addOnly` 互斥」需领域知识；同文出现两值也可能是在描述**迁移前后**或不同 API，判成矛盾会误报。

先例一致：`doc-organization` 因判据无法机械化塌缩成纯原则，`markdown-style` 自动修复白名单 27→9→4→0 整体放弃。**发一个自己不信的检测器比不发更糟——它会稳定漏报，还让人以为有保护。**

**保留**：`ms-verify --docs` 增一条**人工审查项**（非机械门）——「权限级别 / 版本号 / 平台地板 / 键名常量 / 面向用户文案这五类值，是否在多处出现且不一致」。

> ⚠️ **代价明说，两轮 Codex 均确认**：用户给的 `.readWrite` vs `.addOnly` 回归场景**没有自动断言**能证明它被报出。按缺陷复现口径，**D4 未修**。用户已裁定接受。

### 2.4 D3：`needs review` 补三字段，不造新语法

R1 曾提议 `Pending-<宿主编号>`。**Codex 否决，已采纳**——`requirements/SKILL.md:323-327` 的 `needs review` 块已有「标注关联 F/US/AC、问题、建议确认人、对下游影响」，缺的只是三个字段。造新语法等于第四个命名空间（独立语法 + 后缀 + 扫描 + 生命周期 + 阻塞规则）。

新增必填字段：`归属`（谁/哪个任务在什么条件下必须关掉它）、`关闭条件`（可判定，不是「再看看」）、`提出`（ISO 日期）。

| 条件 | 级别 | 执行者 |
|---|---|---|
| 缺 `归属` 或 `关闭条件` | ⚠️ **立即** | `ms-sync --audit` |
| `提出` 距今 ≥60 天 | ⚠️ | `ms-sync --audit` |
| `提出` 距今 ≥120 天 | **P1 阻塞** | `ms-verify --readiness`（**须同批改 verify，R2 漏了这处断链**）|

> R1 曾用「躺过 N 个已发布版本」。**Codex 否决，已采纳**——「已发布版本」无权威源（git tag / 商店版本 / release note / 里程碑各不相同），LLM 算出的版本龄不可复核；且本仓上一个 sprint 刚做过发布状态源头治理，同一个坑。**只用 ISO 日期与天数。**
>
> ⚠️ 60/120 天是**拍的默认值，非实测**。项目侧 `AGENTS.md` 可覆盖。

### 2.5 D5：supersedes + 已知受影响制品（三跳检索）

推翻/取代类 ADR 必填（**普通选型 ADR 不填**）：

```markdown
- **取代**：ADR-006（其状态改「已取代」）
- **已知受影响制品**：
  | 类别 | 编号/路径 | 复查结论 |
  |------|----------|---------|
  | 约束 | CON-004 | 已改：授权级别 .readWrite → 删除 |
  | AC | AC-002 | 无需改 |
  | 任务 | T-01（✅ 已完成）| 已标 superseded_by: ADR-015 |
  | 守卫 | Scripts/verify-bundle.sh:14,18 | 已改：移除两项必需检查 |
```

**三跳检索**（R2 的两步够不到用户原话那三处，Codex 指出，已采纳）：

1. `grep -rn "ADR-006" docs/` —— 直接引用点
2. 被取代 ADR 的 `关联` 字段列出的编号 → **逐个查其定义处与全部引用处**（这一跳找到 01 的 CON-004 规约与关联到它的 T-01）
3. 上一跳得到的 CON → 其「验证方式」指向的**脚本路径**（这一跳走出 `docs/`，找到 `verify-bundle.sh`）+ 其关联任务的 `涉及文件`

> R2 只有前两步的一半，必然找不到脚本——`# verifies: CON-002` 里不含 `ADR-006`，而检索范围又只有 `docs/`。**验收声称与机制不符**，Codex 抓得对。
>
> ⛔ **只能声称「已知引用」，不得声称「完整影响范围」**——检索找不到从未登记、改名、间接依赖或生成产物。
> ⛔ **反查不建索引文件**——表就在 ADR 正文，`grep -A20 "ADR-015"` 即得。再建一张手工索引表会原样重演 D6。

**任务卡失效可见**：`task-template.md` 属性表新增可选 `superseded_by`，标题旁标 `⚠️ 已失效`。⛔ 不删改历史执行步骤（历史不可变）。`ms-dev-workflow` 执行前置：读到带 `superseded_by` 的任务卡 → ⛔ 停，先读指向的 ADR。**直接消灭「重做时照它把缺陷复原」。**

**守卫脚本反向链接**：CON 的「验证方式」填脚本路径；脚本内加一行 `# verifies: CON-002, CON-005`。双向可查成立，**不给脚本分配编号**。唯一碰代码的地方。

### 2.6 D6：把权威挪走，而不是把手填表修准

- `devdocs-state.md` 「当前最大」列改标「**推导值，勿手填**」，表上方写死 §2.2.2 的推导命令
- **凡分配新编号的 skill 一律改为「⛔ 不读 `devdocs-state.md`，直接扫资源文件取 max+1」**。state 表降级为只读速览，与其自称的「不追踪 drift」对齐
- 顺手修 §1.1-④：`id-reference-check` 上界改从资源文件推导；state 值与推导值不符 → 新报 `state/max-id-stale`（⚠️，修复=回填或删列）

### 2.7 D2：问卷降为按需 reference，文件信号只给一行提示

六组清单（分发平台元数据 / 图标与视觉资产 / 发行区域与本地化 / 第三方商标与文案红线 / 隐私清单与数据披露 / 平台备案资质）落 `requirements/references/`，**按需加载，不进默认流程**。

| 级别 | 条件 | 行为 |
|---|---|---|
| 加载问卷 | 用户明说「发布 / 上架 / 合规 / 平台配置」，或 01 §6 已有该类别 CON | 展开对应组 |
| 一行提示 | 仅检测到 `Info.plist` / `AndroidManifest.xml` / `manifest.json` / `*.xcodeproj` / `pubspec.yaml` | ℹ️ 一行「检测到平台制品，需要过一遍发布合规清单吗？」**不展开问卷** |

> Codex 主张文件存在不得单独触发（任意 iOS 项目几乎必然有 `Info.plist`，「允许填不适用」仍是仪式）。**折中采纳**——纯文件信号只给一行提示，保住「在用户想到之前提醒」的价值，又不强推问卷。

每组必带 `⏭️ 不适用` 出口（对齐 retrofit「每次提问必有『我也不清楚』出口」纪律）。

### 2.8 CON 型任务复用既有红绿，⛔ 不新建执行分支

Codex 要求「给 dev-workflow 建立真正的 `TDD 模式=不适用` 执行分支，覆盖 S1、Contract、骨架、红绿、S8、Step 1.5、auto-mode」。**修法不采纳**——那是一整个子系统，且没必要。

**`验证方式=可执行` 的 CON 任务本身就是一个完整红绿循环**：

| 步骤 | 行为型任务 | CON 型任务（可执行档） |
|---|---|---|
| S1 读任务 | 读 F/AC/UT/IT/E2E 关联 | 读 CON 关联 + 其验证方式 |
| S1.5 Sprint Contract | Test Agent 基于 AC 生成可执行验收契约 | 基于**验证命令的通过判据**生成契约 |
| S2/S3 骨架 | 实现骨架 + 测试骨架 | 实现骨架 + **守卫脚本检查项骨架** |
| S4 编写断言 | `expect(...)` | `plutil -extract LSApplicationCategoryType ...` |
| **S5 红验** | 测试必须失败 | **脚本必须失败**（键还没加） |
| **S6 绿验** | 实现后通过 | **加键后脚本通过** |
| S8 完成检查 | AC 完备表 | **CON 完备表**（同构，换编号类型） |

**这是用户原话「构建守卫脚本是需求的可执行副本」的字面实现**——守卫脚本**就是** CON 的测试，不是它的替代品。零新分支，S1~S11 全程走既有通路。

`验证方式=人工` 的 CON 任务走 **§1.1-⑤ 那条已被描述但被矩阵禁止的出口**：

- 修 `execution-flow.md:89` 矩阵：`S2/S3` 由三档全 ■ 改为 **■\*（条件必须）**，条件 = 「任务关联的 AC 存在，或关联 CON 的验证方式为 `可执行`」
- `人工` 档任务：S3 为 ○，按 ■* 规则原文「明确决定不产出测试」退化为 □/○，S4–S7 随之退化；执行步骤走 `dev-tasks/SKILL.md:72` 已有的「实现→集成测试验证（普通执行步骤）」
- S8 完成检查改为**核对人工判据已执行并留证**

> 这一改同时修掉 §1.1-⑤ 的既存矛盾（出口被 ■* 规则描述、被矩阵禁止），**不是本方案新引入的口子**。

### 2.9 消费方全清单（12 处）与统一 N/A 判据

R1 漏 4 处、R2 又漏 8 处。完整清单：

| # | 消费方 | 位置 | 现状 | 改法 |
|---|---|---|---|---|
| 1 | `ms-system-design` 模式检测 + 覆盖门 | `system-design/SKILL.md:58,107` | 只找未覆盖的 `F-XXX` | 引用统一 N/A 判据 |
| 2 | readiness D1 | `verify/SKILL.md:284-291` | 只查 AC → UT/IT/E2E | 增「CON → 验证方式非空且可复核」 |
| 3 | readiness D2 | `verify/SKILL.md:291` | 「测试方法须指定测试类型和**编号**」 | CON 允许「验证方式 + 可复核判据」代替编号 |
| 4 | readiness D4 前两项 | `verify/SKILL.md:309-313` | 任务须对应 02 模块/接口 + 代码落位 | 引用统一 N/A 判据 |
| 5 | readiness D4 第三项 | `verify/SKILL.md:315` | 孤立任务 = 未关联任何 `F-XXX`/`AC-XXX` | 追加 `CON-XXX` |
| 6 | `--impl` B1 | `verify/SKILL.md:153-160` | 从追溯矩阵取 `变更来源`；CON 不进 03 则无来源路径 | 明确走 `CON → T → commits/涉及文件` |
| 7 | `--impl` B2 | `verify/SKILL.md` 设计符合度 | 无「不涉及设计」判据 | 引用统一 N/A 判据 |
| 8 | `--impl` B3 | `verify/SKILL.md:179` | 只定义行为型 AC 的独立证据 | 增 CON 追溯闭环（否则不拦但漏检） |
| 9 | `ms-test-cases` 工作流第 2 步 | `test-cases/SKILL.md` | 只提取 F/US/AC | 增 CON；不强制生成 UT/IT/E2E |
| 10 | `ms-dev-workflow` S1/S1.5/S8 + `execution-flow` 矩阵 | `dev-workflow/SKILL.md:94-95`、`execution-flow.md:89` | S1 只读 F/AC/测试关联；S1.5 基于 AC；S2/S3 三档全 ■ | 按 §2.8 |
| 11 | `ms-sync --trace` | `sync/references/trace-mode.md:18` | 只读 03 矩阵的 AC | 认 `CON → T → commits` |
| 12 | `ms-sync --audit` 孤立编号 | `sync/references/audit-mode.md:50` | 「T-12 未关联任何 F」 | 追加 CON |

**统一 N/A 判据**（一处定义，#1/#4/#7 三处引用，⛔ 不写三遍）：

> **CON 型任务的「无对应设计章节」是合法结论，不是缺陷。**
> 判据：任务只关联 `CON-XXX`（无 `F-XXX`/`AC-XXX`），且该 CON 的类别属制品/环境/流程（非跨模块行为）→ 02 无需为它产出模块/接口章节，覆盖门与一致性检查对该任务输出 `N/A（制品型）`。
> ⛔ 反向禁止：任务同时关联 `F-XXX` 时不得走此出口。

## 3. 改动清单（19 项）

| # | 文件 | 改什么 | 对应 |
|---|---|---|---|
| 1 | `requirements/templates/requirements-template.md` | §6 散文表 → 编号表 `编号/类别/约束/验证方式(可执行\|人工)/状态`；§5 追溯矩阵加 `CON → T` 段。**零 CON 时 §6 可为空** | D1 |
| 2 | `requirements/SKILL.md:89` | `NFR-XX → 写入非功能需求章节` 改 `→ CON-XXX`；增量模式从已有 CON 最大号续编 | D1-① |
| 3 | `dev-tasks/SKILL.md:187-190` | 四条硬门改为：行为型 → `F+AC`；制品/配置/流程型 → `CON`；**仅行为型强制 UT/IT/E2E**；CON 型「测试方法」须引用验证方式并给可复核判据；**TDD 引用 AC/测试编号仅适用 `TDD 模式 ≠ 不适用`**；⛔ 有用户可观测行为不得用 CON 绕过 AC | D1 |
| 4 | `verify/SKILL.md` 新增「统一 N/A 判据」小节 | §2.9 那段，供 #5/#7/#9 引用 | §2.9 |
| 5 | `system-design/SKILL.md:58,107` | 模式检测 + 覆盖门引用 N/A 判据 | §2.9-1 |
| 6 | `verify/SKILL.md:284-291`（readiness D1/D2） | D1 增 CON 验证方式检查；D2 放宽（CON 允许判据代编号） | §2.9-2,3 |
| 7 | `verify/SKILL.md:309-315`（readiness D4） | 前两项引用 N/A 判据；孤立判据追加 `CON-XXX` | §2.9-4,5 |
| 8 | `verify/SKILL.md:153-179`（impl B1/B2/B3）+ 维度 A | B1 走 `CON → T → commits`；B2 引用 N/A 判据；B3 增 CON 闭环；`--docs` 增五类值人工审查项 | §2.9-6,7,8 + D4 |
| 9 | `verify/SKILL.md`（readiness） | `needs review` ≥120 天升 P1（**R2 断链**） | D3 |
| 10 | `test-cases/SKILL.md` 工作流第 2 步 | 提取范围加 CON；不强制生成 UT/IT/E2E | §2.9-9 |
| 11 | `dev-workflow/SKILL.md:94-95` | S1 读 CON 关联 + 验证方式；S1.5 契约基于验证命令通过判据；S8 CON 完备表 | §2.8 |
| 12 | `dev-workflow/references/execution-flow.md:89` | `S2/S3` 三档全 ■ → ■*（条件 = AC 存在或 CON 验证方式可执行）。**顺带修 §1.1-⑤ 既存矛盾** | §2.8 |
| 13 | `sync/references/trace-mode.md` + `audit-mode.md` | trace 认 `CON → T → commits`；audit 孤立判据追加 CON；新增 `needs review` 按天数报龄 | §2.9-11,12 + D3 |
| 14 | `requirements/references/release-compliance.md`（新） | 六组清单，按需加载 + 一行提示触发 | D2 |
| 15 | `requirements/SKILL.md` | `needs review` 补 `归属`/`关闭条件`/`提出` 三字段 | D3 |
| 16 | `system-design/templates/design-template.md` + `references/incremental-design.md` | ADR 增 `取代` + `已知受影响制品` 表，**仅推翻/取代类必填**；三跳检索。顺手清 `incremental-design.md:195-196` 重复行 | D5 |
| 17 | `dev-tasks/templates/task-template.md` + `dev-workflow/SKILL.md` | 属性表增可选 `superseded_by` + `⚠️ 已失效`；dev-workflow 前置读到即 ⛔ 停 | D5 |
| 18 | `agent-memory/templates/devdocs-state-template.md` + 六个分配编号的 skill + `health-lint-implementation.md:234` | 最大值改推导；⛔ 不读 state 分配编号；上界改推导 + 新增 `state/max-id-stale` | D6 |
| 19 | 四张 Migration Matrix（`requirements`/`dev-tasks`/`test-cases`/`system-design` 的 `references/realign.md`）+ `_shared/constraints.md` | 各写 legacy 子分支（§4）；constraints 登记 `CON` 归属与续编源、补 §2.2.2 grep 规则、bump `shared-constraints.v9 → v10` | 兼容 + 协议层 |

**部署**：改完同步 `~/.agents/skills/`（源与部署是两份**拷贝**，非符号链接）。

## 4. 迁移与向后兼容

**按 Codex 修正后的准确表述**（R1 的「全部 additive、零 restructuring、存量一行不动」过度声称）：

- ✅ **既有已合法关联 F/AC/测试的 23 个任务无需修改**；⛔ **不重写 64 条 AC**
- ⚠️ **要让存量项目新增 CON 型任务，必须给本批涉及的约束局部编号**（把 §6 里相关的那几条散文转成 CON 行）。不是全量迁移，也不是零迁移

**legacy 子分支**（Codex 指出 R2 的「该维度 skip」表述错误——会把整个维度跳掉，已采纳）：

| 消费方 | 旧文档（§6 无 CON 行）行为 |
|---|---|
| readiness D1 | **只跳过 CON 子检查**，原 AC → UT/IT/E2E 检查继续 |
| readiness D4 | **只不执行 CON 分支**，原 F/AC 一致性检查继续 |
| impl B1 | **只跳过 CON 遍历**，原 AC 满足度审查继续 |
| test-cases | **只跳过 CON 提取**，原 F/US/AC 流程继续 |

| 项 | 策略 |
|---|---|
| `dev-tasks` 硬门 | 是**放宽**（`F+AC` → `F+AC 或 CON`），老文档零影响 |
| `execution-flow` 矩阵 | `S2/S3` 由 ■ 改 ■*，条件含「AC 存在」→ 所有行为型任务判定不变，老项目零影响 |
| §6 模板 | 散文 → 编号表**是 restructuring**（不掩饰） |
| `spec_version` | `req.v1→v2`、`tasks.v1→v2`、`test.v2→v3`、`design.v2→v3`、`devflow.v3.1→v3.2`。五张 Migration Matrix 均须写明上表的 legacy 子分支 |
| §6 迁移入口 | `/ms-pipeline realign --scope=spec` 内部委托 requirements 的 nfr 子动作。⛔ **不暴露 `/ms-requirements --realign=nfr`**——违反 `constraints.md:291` `realign/no-direct-user-call` |
| 旧守卫脚本 | 无 `# verifies:` 注释则得不到反向链接。**按需补，不做批量回填** |
| 编号起点 | `CON-001` 起，独立计数 |

## 5. 可回归的验收方式

⚠️ **本仓无测试运行器、无 CI。以下是「实施验收清单」，不是可持续回归能力**（Codex 指出，已采纳）。一次人工走查可验收设计，不能证明以后每次都执行一致。

| 缺陷 | 步骤 | 通过判据 |
|---|---|---|
| **端到端** | 造 CON-002「Info.plist 含 `LSApplicationCategoryType`」+ 验证方式 `Scripts/verify-bundle.sh::check_category`，逐站走 01 → 02 → 03 → 04 → readiness → dev-workflow → impl → sync | **12 站全放行**，且 S5 红验时脚本确实失败、S6 绿验时通过 |
| D1 | 同上第 04 站 | 「关联需求」填 `CON-002`；`grep -rnE "全部 F\|会导致.*AC.*失败" docs/` 零命中 |
| D2 | 有 `Info.plist` 的项目跑 `/ms-requirements`（不提发布）；再明说「要上架」重跑 | 前者**只出一行提示**；后者展开六组 |
| D3 | 造 `needs review` 条目 `提出` 填 150 天前 → `/ms-sync --audit` → 再 `/ms-verify --readiness`；另删 `归属` 重跑 | audit ⚠️ 给出天数；**readiness 报 P1**；缺 `归属` 立即 ⚠️ |
| D4 | — | **无自动断言**（§2.3，用户已裁定）。人工审查项存在性可查 |
| D5 | 造 ADR-015 取代 ADR-006 → `/ms-system-design`；给 T-01 加 `superseded_by` → `/ms-dev-workflow T-01` | ①要求填「已知受影响制品」表 ②**三跳检索列出 T-01 与 `verify-bundle.sh`**（R2 会在此失败）③dev-workflow ⛔ 停 |
| D6 | 手工把 state 表 AC 最大改 062、实际造 AC-064 → 分配下一个 AC；跑 `realign --scope=health`；另造 `T-01,T-02,T-03` 与 `T-106` 验证 grep | 得 **065**（非 063）；报 `state/max-id-stale`；grep 得 `01 02 03` 与 `106`（R2 会漏 `T-02`）|
| 兼容 | 取一份无 CON 行的旧 01 跑 readiness / impl / test-cases | 三处**只跳 CON 子检查**，原 AC 检查照常报结果（不是整维度 skip）|

## 6. 明确不做

| 不做 | 理由 |
|---|---|
| `CK-XXX` 验证手段编号 | §1.2——任务卡已有「测试方法/验收标准/TDD 不适用」三字段 |
| `FACT` 受管事实登记表 | §2.3——必然衰败的手工反向索引，与 D6 同一失效模式 |
| 五类字面量互斥检测 | §2.3——同文两值可能在描述迁移前后 |
| 独立 `Pending` 语法 | §2.4——`needs review` 补三字段即可 |
| `verify --docs` 层 4 机械门 | §2.3——降为人工审查项 |
| 版本报龄 | §2.4——「已发布版本」无权威源 |
| 默认展开的平台问卷 | §2.7——降为一行提示 + 按需加载 |
| **dev-workflow 非 TDD 执行分支** | §2.8——可执行档复用红绿，人工档走 ■* 已描述的出口 |
| 新增流程阶段 | CON 落在既有 01/02/03/04 内 |
| 新工具链 | 全部 `grep`/`sed`/`sort` + skill 指令；唯一碰代码的是脚本内一行 `# verifies:` |
| ADR→产物 反查索引文件 | §2.5——又一张手工表，重演 D6 |
| `C-XXX` 独立合规命名空间 | §2.2——合规是 CON 的 category |
| 为「上架」特化 | D2 六组里分发平台只占一组；CON 同时承载性能基线/日志规约/安全加固/可观测性 |

## 7. 已知代价（不掩饰）

1. **D4 未修**（§2.3）。两轮 Codex 均确认。用户裁定接受。
2. **存量项目非零迁移**（§4）。新增 CON 型任务须局部编号。
3. **验收清单 ≠ 回归能力**（§5）。无 runner 无 CI。
4. **60/120 天阈值是拍的**（§2.4），非实测。
5. **三跳检索只给「已知引用」**（§2.5），不是完整影响范围。
6. **用户被推着多写守卫脚本**（§2.1）。这是「优先可执行」的直接成本，用户已裁定接受。

## 8. 轮次差异（Codex 评审对齐）

### R1 → R2（Codex 裁定「削减后实施」）

**采纳 12**：①补四处消费方门 ②删 `CK` ③删 `FACT` ④`Pending` 合并进 `needs review` ⑤消除「验证方式必须是 CK」的必填链 ⑥grep 补后边界 ⑦`sort` 改数值比较 ⑧realign 改走 pipeline 入口 ⑨迁移声称改准确 ⑩报龄只用天数 ⑪回扫改称「已知引用」⑫删字面量互斥检测

**不采纳 2**：`CON` 退回 `NFR-XXX`（未回应位数冲突，且用户已裁定）；「新增流程阶段」红线（用户原文指**阶段**非**检查项**）

**折中 1**：平台问卷触发降为一行提示

清单 20 → 13。

### R2 → R3（Codex 裁定 NO PASS）

**采纳 7**：①消费方从 4 处补到 **12 处**（§2.9）②readiness D2 放宽 ③统一 N/A 判据供 system-design / readiness D4 / impl B2 引用 ④sync trace/audit 认 CON ⑤D5 补第三跳（走出 `docs/`）⑥grep 改 `-owE`（R2 式子边界被消耗，本地实测证实漏 `T-02`）⑦legacy 子分支 + Migration Matrix 入清单，且「跳整个维度」改为「只跳 CON 子检查」⑧`needs review` ≥120 天的 readiness P1 断链补上

**不采纳 1（仅修法，缺陷本身承认）**：「给 dev-workflow 建非 TDD 执行分支」→ 改为 §2.8 **复用既有红绿**（可执行档）+ 打开 ■* 规则已描述的 S3 出口（人工档），顺带修掉 §1.1-⑤ 既存矛盾

清单 13 → 19，**无新建执行分支**。
