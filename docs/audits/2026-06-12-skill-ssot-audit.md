# Skill 体系 SSOT 摸排报告

> 2026-06-12 · 范围：全部 32 个 skill + _shared + README/AGENTS · 方法：Claude 双探查 agent 全量扫描 + Codex 独立全仓审计，双向交叉复核后合并（Claude 侧剔除误报 1 条；Codex 独有发现 2 项 A 级经 grep 实证采纳）
> 基线治理原则：dev-workflow spec 1.1「权威文件唯一原则」——每个机制唯一权威文件，其余仅 2-3 行指针

## 一、SSOT 违反清单

### A 级：已漂移 / 语义冲突（须修）

| # | 冲突 | 两侧位置 | 漂移内容 |
|---|------|----------|----------|
| A1 | 重复代码边界谓词冲突 | `refactor/SKILL.md:129`（"≥ 3 处 → P0"）vs `code-quality/SKILL.md` 核心阈值表（"> 3 处 Blocker，≤3 合规"） | 3 处重复在一边是 P0 smell、另一边合规——与 2026-06-12 谓词统一直接冲突 |
| A2 | 覆盖率分级谓词权威倒挂 | `dev-workflow/references/verification-flow.md:375-376`（"<60% Blocker / 60-80% Suggestion"）vs `testing-guide/SKILL.md:65-66`（仅"≥80%"约束，无分级） | 分级谓词只存在于镜像处；标称权威 testing-guide 反而没有分级语义 |
| A3 | AC 矩阵指针指错方向 | stale 指针 6 处：`execution-flow.md:173,212`、`verification-flow.md:263,303`（指向 SKILL.md 但矩阵本体在本文件 §AC 完备性）、`verification-flow.md:261`（语义正确但缺锚点）、`ui-quality-checklist.md:85`；矩阵本体（权威）在 `verification-flow.md:220-241` | SKILL.md 只有约束清单（其指针正确）；修复=统一指向 `verification-flow.md#ac-完备性s8-权威定义` 锚点 |
| A4 | health-lint rule 数量漂移（Codex 发现，已复核） | `realign-scope-health.md:17`（"4 条 [新增] lint rule"）vs `health-lint-implementation.md:20`（"Rule 集（[新增] 5 条）"，AGENTS.md 同为 5 条） | 调用方少列 adr-only-revision；stale 在 realign-scope-health；同文件 ssot rule 数（8 vs layout 权威 12）亦待对账 |
| A5 | layout realign 入口双权威（Codex 发现） | `realign-scope-layout.md:3`（新入口权威）vs `docs-layout-migration.md:7,24`（仍自称执行状态权威并标 `--docs-layout` FUTURE）；README.md:482 | docs-layout-migration 应降级为迁移矩阵/legacy 说明，执行接口权威归 realign-scope-layout |
| A6 | Recovery 协议结构漂移（Codex 判级，已复核采纳） | `_shared/constraints.md:205-220` 要求 动作/执行者/验证/下一步 四字段模板 vs `requirements/SKILL.md:258`、`backlog/SKILL.md:195`、`prd-revision-policy.md:88` 等一句话"（恢复方式：…）" | 原判 B 偏轻：这不是重述而是结构不合规——本地门控业务事实可留，Recovery 结构须用共享模板或指针 |

### B 级：完整重述无标注（应修）

| # | 内容 | 重述位置 | 权威 |
|---|------|----------|------|
| B1 | MTE + 函数 50 行 + 参数 5 个 | `onboard/SKILL.md:240-242`（无任何链接） | code-quality 核心阈值表 |
| B2 | 函数 50 行 + 参数 5 个 | `dev-tasks/templates/task-template.md:119`（无标注） | 同上 |
| B3 | 覆盖率 80% + 弱断言黑名单（toBeDefined/toBeTruthy/not.toBeNull） | `verification-flow.md:118-126` Phase 2 清单（无"摘录自 testing-guide"标注——Phase 1 已治理，Phase 2 漏了） | testing-guide |
| B4 | 覆盖率 80% | `test-cases/SKILL.md:310` + 3 个模板（无标注） | testing-guide |
| B5 | yaml-summary-v1 status 枚举语义 | `iteration-policy/SKILL.md:294`（重述 4 保留值规则，无指针） | _shared/constraints.md |
| B6 | ~~Recovery 格式重述~~ → 升级为 A6（结构漂移） | 见 A6 | _shared/constraints.md |
| B9 | yaml-summary envelope 完整展开（Codex 补充取证） | `test-cases/SKILL.md:377`、`onboard/SKILL.md:416`（部分样例漏 `interrupted` 枚举） | _shared/constraints.md（与 B5 合并治理：envelope 见 _shared，本地只列 `summary.details` 私有字段） |
| B10 | frontmatter deprecated migration 残留（Codex 发现） | 9 个 A/B 类 skill frontmatter 仍写 `migration: /ms-pipeline realign --docs-layout`（requirements/system-design/test-cases/dev-tasks/dev-workflow/prd-parser/prd-brainstorm/insights/onboard 各 :16 附近） | alias 保留 1 版本故不阻塞，随 A5 一并改 `--scope=layout` |
| B7 | 质量地板通用化重述 | `dev-flow/SKILL.md` Verify Gate Evidence Check（5 条通用化，未标注源自 _shared 质量地板） | _shared/constraints.md |
| B8 | 提交 type 枚举 | `execution-flow.md:280`（feat/fix/refactor/test/docs/chore 重列；T-XX 格式与 trailers 属 dev-workflow 私有协议，合理保留） | commit-convention |

### C 级：轻微可容忍（可顺手治理，不立项）

- 模板 frontmatter 协议段（generated_by/spec_version/generated_at）在 6 个 skill 模板逐字重复
- FUTURE 三态在各 realign.md 分散使用，非每处带指针
- system-design SKILL.md 复述 MTE 三行表（其设计级权威 mte-rubric.md 与 code-quality 代码级"两套不合并"的分层已在 solid-principles-guide 声明，仅缺一行指针）
- ui-quality-checklist ↔ ms-verify --ui ↔ ui-orchestrator：边界声明完备（运行态归 --ui/--live），无实质重复

**已剔除误报**：探查 agent 报告的"verification-flow 完整重述六原则表"不成立（该文件无 SRP/OCP 表）。

## 二、可拆除为 SSOT 的候选（按收益排序）

### S1. 测试质量核心阈值表（testing-guide 升格）｜优先级 P0

- **现状散布**：覆盖率 80% 约束（testing-guide）、<60%/60-80% 分级谓词（verification-flow，事实权威倒挂 A2）、test-cases SKILL+3 模板、onboard、变异得分 60/80（testing-guide）
- **建议**：复制 code-quality「核心阈值表」模式——testing-guide 设统一谓词阈值表（行/分支覆盖建议 80 / 下限 60、弱断言黑名单、变异得分），verification-flow Phase 2 与 test-cases 改为带"摘录自+同 commit 同步"标注的短镜像
- **理由**：与 2026-06-12 code-quality 重构完全同构，缺口已验证（A2/B3/B4）

### S2. INT_*/EXT_*/review_pending/review_profile 协议分层｜优先级 P1（双审计对齐后采纳 Codex 变体）

- **现状**：真值表与 canonical state 定义在 `dev-workflow/references/verification-flow.md:463`（一个 skill 的 reference），但被 7 个 dev-workflow 文件 + **跨 skill 的 ms-verify、adversarial-review、ms-dev-tasks** 消费
- **建议**（分层，而非整体上提）：**状态枚举 + 质量地板归 `_shared/constraints.md`**；执行细节留 dev-workflow references
- **落地偏差（批次 3）**：原拟新建 `review-profile-protocol.md`，实施时发现 _shared 已承载三档/质量地板/review_pending/基础 trailers——新建文件会制造第三个权威。实际落地：_shared 补「独立审查状态机枚举」+「Commit trailers 协议」两节（协议层），verification-flow 真值表标注为"判定规则执行细节权威"、execution-flow 提交格式标注为"模板呈现"（执行层），不新建文件
- **理由**：跨 skill 协议放在单 skill reference 里违反 _shared 架构定位；e89caae（EXT_PENDING 语义对齐）类漂移已发生过一次

### S3. AC 类型分类 + AC 类型×证据类型分级矩阵｜优先级 P1

- **现状**：本体在 verification-flow:241，SKILL.md 指针正确，但 execution-flow/verification-flow 内 4 处指针指错（A3）；ms-verify 与质量地板（_shared 第 4 条"行为型 AC"）亦依赖该分类
- **建议**：最小动作=修正 4 处指针 + verification-flow 矩阵章节挂稳定锚点；如 ms-verify 消费加深，再考虑分类定义上提 _shared（矩阵执行细节留 verification-flow）

### S4. Blocker/Suggestion/Question/Nice 反馈分级元语义｜优先级 P2

- **现状**：code-quality 反馈分级表、verification-flow Blocker 判定、ui-quality-checklist、adversarial-review、mic-review 各自定义"什么算 Blocker"
- **建议**：分级**元语义**（Blocker=必须修复才能合并；Suggestion=不阻塞……）一处权威（code-quality 反馈分级表已最完整，或上提 _shared），各处仅保留领域特定判定条目 + 指针

### S5. 模板 frontmatter 协议段｜优先级 P2

- **现状**：6 个模板逐字重复 generated_by/spec_version/generated_at 段
- **建议**：`_shared/constraints.md` 增加（或已有 spec_version 章节扩展）"模板 frontmatter 最小字段"小节，6 个模板改一行指针 + 保留字段本体（模板需自包含可复制，保留字段、删解释性文字）

### S6. 优先级术语撞车声明｜优先级 P3

- **现状**：test-cases 的 P0-P2 = 测试用例优先级；verify p-severity-rubric 的 P0-P3 = 问题严重度——同名不同义
- **建议**：不合并（语义确实不同），在两处各加一行"与 X 的 P 级无关"消歧声明，并在 AGENTS.md 术语表登记

### S7. DevDocs commit trailers 与提交标题规范分离（Codex 提议）｜优先级 P2

- **现状**：提交标题规范（commit-convention，含"优先学习项目 git log"）、AGENTS.md 仓库约定（Conventional Commits）、dev-workflow 私有 trailers（Review-Batch-Id/External-Review-Verdict 等，散在 SKILL.md/execution-flow/verification-flow/_shared review_pending 行）三者交叠
- **建议**：标题规范权威归 `/commit-convention`；DevDocs trailers 拆 `dev-workflow/references/commit-trailers.md`（或并入 S2 的 review-profile-protocol.md）；execution-flow type 枚举指针化（B8）

### 不建议拆除

- **编号体系**：权威已在 `pipeline/references/layout/id-scheme-implementation.md`，requirements/dev-tasks/README 为消费级描述，未见双权威
- **行为契约**：system-design（定义方）与 dev-workflow（消费方）分工清晰
- **UI 检查清单**：三方边界声明完备（见 C 级）

## 三、修复路线建议

| 批次 | 内容 | 规模 |
|------|------|------|
| 批次 1（修漂移 + 加指针） | A1 refactor 谓词对齐、A3 指针修正（7 处并集）、A4 health-lint 数量对账、A5 layout 入口降级、A6 Recovery 结构化；B1/B2/B5/B7/B8/B9 加指针或标注 | 小-中（~15 文件，多为单行级） |
| 批次 2（S1） | testing-guide 核心阈值表升格 + Phase 2/test-cases 镜像标注（A2/B3/B4 一并闭环） | 中（同 code-quality 重构模式） |
| 批次 3（S2+S3） | 协议分层：枚举/地板归 _shared + 新建 review-profile-protocol.md + AC 矩阵锚点 | 中（涉及 9+ 文件指针调整，需 Codex 对齐方案后实施） |
| 批次 4（S4-S7 + B10） | 分级元语义 / 模板 frontmatter / 术语消歧 / trailers 拆分 / frontmatter migration 清理 | 小 |
| 持续 | health-lint 镜像一致性 rule（已 deferred 登记）扩展为覆盖 code-quality + testing-guide 双阈值表 | 随 realign --scope=health 扩展 |

## 四、双审计对齐记录

- 双方独立完成（Claude：双探查 agent + 定向复核；Codex：全仓 rg 取证），结论高度收敛：A1/A2/A3、测试质量 S1=P0、yaml-summary、MTE 复述、P 级术语撞车、全部"不建议拆"项（编号体系/设计代码级 SOLID 分层/dev-flow 质量地板加指针不并入）双方一致
- 采纳 Codex 独有：A4（health-lint 4≠5，grep 复核成立）、A5（layout 入口双权威）、B10（9 处 deprecated migration）、S7（trailers 拆分）、A6 判级（Recovery 由 B 升 A，四字段模板 vs 一句话已复核）、S2 分层变体（枚举归 _shared、执行细节留 reference）
- 保留 Claude 独有（grep 实证，未再发 Codex 确认轮）：B1（onboard 裸写 MTE+阈值）、S4（分级元语义）、S5（模板 frontmatter 段 ×6）
- 误报剔除：Claude 侧探查 agent"verification-flow 重述六原则表"不成立
