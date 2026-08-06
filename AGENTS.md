<!-- 由 /agent-memory 生成，请通过该命令更新 -->

# AI Agent Skills

## 技术栈

- 规格库：Markdown + YAML skill 定义（非代码库）
- 无 build/test/lint 命令
- 22 个 ms- 流程 skill + 16 个独立 skill（含 3 个 internal-only；dev-flow 为非 DevDocs 通用开发流程，idea-mcp-workflow 为 JetBrains idea MCP 操作手册，e2e-test-flow 为独立 E2E 实测流程，markdown-style 为 Markdown 标记与排版审查器，doc-organization 为文档信息组织指导原则，prior-art-scan 为开工前的先例扫描）

## 架构决策

- 每个 skill 独立目录 `skills/<dir>/SKILL.md`，调用名为 frontmatter 的 `name` 字段
- ms- 流程 skill 目录使用去前缀短名（如 `skills/bugfix/` ↔ `name: ms-bugfix`）
- `templates/` 子目录存输出模板，`references/` 子目录存评估标准 / rubric / 规则
- 编排层（ms-pipeline / ms-feature / ms-bugfix）通过 Task tool 调度原子 skill 作为子代理
- 跨 skill 协议级 SSOT：[skills/_shared/constraints.md](skills/_shared/constraints.md)（门控标记 / yaml-summary-v1 / Recovery 格式 / FUTURE 三态 / realign / spec_version）
- 统一升级 + 健康度入口：`/ms-pipeline realign --scope=<spec|layout|prd-mapping|health>`

## 领域术语

| 术语 | 含义 |
|------|------|
| Skill | 可复用的 SKILL.md 定义文件，扩展 AI agent 能力 |
| ms- 前缀 | DevDocs 流程 skill 命名空间，区分独立 skill（非 ms-，如 dev-flow / code-quality） |
| PRD 流程 | 模糊想法/大型 PRD → FR-XX/NFR-XX，单需求一次性脚手架（扁平 `docs/prd/`，close 后清理）|
| DevDocs | 文档驱动开发工作流（需求→设计→测试→任务→开发→验证→同步）|
| 编号体系 | F/US/AC/UT/IT/E2E/Journey/INS/BUG/T，链路 F→US→AC→测试 |
| design_context | 跨 skill 共享设计上下文 schema，定义于 `skills/prd/references/design-context.md` |
| codebase-insight | 只读代码盘点，输出 `docs/codebase-insight.md`，供多 skill 消费 |
| Sprint Contract | 开发前 Test Agent 与编排器协商的可执行验收契约 |
| FUTURE 三态 | spec 存在但运行时未实现 |

## 当前状态

- **PRD 扁平化（移除多需求并行）**：mic-en 实践证伪「多需求并行」，已**删除**整套 multi-PRD 机器（全局 `index.md` + 跨 PRD 编号注册表 / `<prd_id>` 子目录 / supersedes / `_archived` / 顶层 `synthesis/` / 跨 PRD 引用+冲突检测 / `list`·`status`·`archive`·`migrate` / `prd-index-ssot.md` + `global-index-template.md`）。`docs/prd/` 改为**扁平·单需求一次性脚手架**，FR/NFR 当前需求内续编、新需求从 FR-01 重起（受 ms-prd 新建门禁保护）；需求 close（上线）后由 `/ms-prd clear`（`/ms-pipeline close` 末步委托）清理。删除而非封存 FUTURE（已证伪，逻辑同废弃 health 维度 e）。方案见 [specs/2026-06-23-prd-flatten-remove-multi-requirement-parallel-design.md](docs/superpowers/specs/2026-06-23-prd-flatten-remove-multi-requirement-parallel-design.md)
- **工作区模式（inline / shell）**：新增与 layout/id/trace **正交**的维度——`shell` 模式下文档在外壳仓 `docs/`，代码作 git 子模块挂在同级（服务「维护开源项目」「自有项目待公开」两类零污染场景）。`code_roots` 记 submodule name（`.gitmodules` 为路径唯一真源），多代码根为一等场景。核心：零污染红线（LLM 不主动往子模块写非代码文件）+ N+1 仓提交协议（detached HEAD 前置门 / 外壳仓 commit 为追溯枢纽 / 跨仓 Recovery 三类）+ inline→shell 迁移七步（dry-run 优先，前 5 步可逆）。协议 SSOT 在 [_shared/workspace-mode.md](skills/_shared/workspace-mode.md)，操作手册在 [layout/workspace-shell.md](skills/pipeline/references/layout/workspace-shell.md)，方案见 [specs/2026-08-05-devdocs-shell-workspace-mode-design.md](docs/superpowers/specs/2026-08-05-devdocs-shell-workspace-mode-design.md)。**无 `workspace_mode` 字段 = `inline` = 现状，存量项目零影响**
- 综合方案落地：flag 收敛 49→20、shared-constraints SSOT、realign --scope 四入口
- 治理盲区收敛：scope=health（结构/索引/过大/SSOT 4 维）+ health-lint 5 条 [新增] rule（state/* + dead-link + adr-only-revision），layout.v1+v2 通用
- 新增 skill：ms-backlog（暂缓任务池）
- 新增 skill：idea-mcp-workflow（独立，非 DevDocs）：通过 JetBrains `idea` MCP（`mcp__idea__*` deferred 工具）操作项目的决策/踩坑手册。承载 4 条跨切面纪律（projectPath 必填且须绝对路径 / build 输出防爆=`filesToRebuild` 源头缩范围而非落盘 jq / 依赖未解析 vs 真 bug 强信号 / Maven reload 是 UI 动作 MCP 不暴露）+ 编译主链路，debug·database·refactor 沉 references 按需加载。经 Codex 独立调研（8 条反馈对齐）+ live MCP 实证（纪律 1 报错文案、envo/trade）+ 只读行为抽查。注：skill-creator 触发评测在嵌套 claude -p 环境非判别性（本仓 skill 靠目录发现、非真 Skill 注册），未采纳其分数
- **dev-workflow inline 轻量入口**：`--inline "<任务>" --ac "<AC>"` 无 04 也可进入，物化 stub（AC 落 01 唯一编号源、review_profile 下限 guarded、`grep "来源: inline"` 即回填台账）；协议私有于 [dev-workflow references/inline-entry.md](skills/dev-workflow/references/inline-entry.md)（constraints.md 零改动），spec_version bump devflow.v2，方案见 [specs/2026-07-22-inline-input-satisfaction-design.md](docs/superpowers/specs/2026-07-22-inline-input-satisfaction-design.md)（codex 2 轮审查）
- **superpowers 共存(单向)**：AGENTS.md「工作流路由」节压制外部 process skill 误触发（agent-memory 幂等维护+managed 标记；init/retrofit 实际委托发货、pipeline ℹ️ 兜底）；能力吸收三方对齐结论=9 项已有等价/更强、唯一内化 bugfix 根因门、worktree 并行 FUTURE、"委托+fallback"否决改"可选增强+单一路径"；方案见 [specs/2026-07-22-superpowers-coexistence-design.md](docs/superpowers/specs/2026-07-22-superpowers-coexistence-design.md)（codex 3 轮）+ [workflows.md 共存节](docs/workflows.md#与-superpowers-共存)
- **新增 skill：ms-board（可视化评审面板）**：01/02 → 自包含 HTML 评审页（临时目录不入库），chrome-devtools MCP 双向桥（board_id fail-closed / 读 `window.__review` 写 `agent-*` 白名单），意见经评审修订协议回流（编号不变/新增委托 ms-requirements 增量/删除标废弃/02 走增量设计+ADR），mermaid 渲染须网络 deny-all 沙箱（macOS 配方已实证，含 unix-socket 放行坑）；协议 SSOT 在 [board references/board-protocol.md](skills/board/references/board-protocol.md)，方案见 [specs/2026-07-22-devdocs-review-board-design.md](docs/superpowers/specs/2026-07-22-devdocs-review-board-design.md)（codex 6 轮 R6 PASS）；E2E 冒烟通过（注入转义/状态恢复/导出/沙箱渲染）
- **新增 skill：e2e-test-flow（独立 E2E 实测，非 DevDocs）**：消费已有用例文档（md/html）对**运行中系统**做黑盒 E2E —— 录制真实请求取代猜接口、写型用例只执行一次（含铺数）、DB 只读观测、影响分析仅提升优先级永不缩小范围、只做功能不做视觉断言；单 skill + 4 references 分层，白盒/黑盒由子 Agent 工具集隔离。FUTURE：影响分析可独立抽取（code review 范围评估/回归范围界定），触发=真实跨场景复用需求，参照 worktree 并行 FUTURE 同类封存。方案见 [specs/2026-07-27-ai-e2e-test-flow-design.md](docs/superpowers/specs/2026-07-27-ai-e2e-test-flow-design.md)（codex 7 轮 R7 PASS，R4 熔断后简化重写 568→237 行）
- **新增 skill：markdown-style（Markdown 标记与排版只读审查器，独立，非 DevDocs）**：三组分工 —— M 组 markdownlint（`MD001`–`MD060` 共 **53** 条，7 个编号未定义）由工具判定、T 组中文排版（GB/T 15834 + 排版指北，ID `T1`–`T4`·`T6`·`T7`·`T9`，`T5` 否决 / `T8` 并入 T7）与 L 组 LLM 排版毛病由 AI 通读。**经三轮塌缩为纯只读审查器**：自动修复白名单 27→9→4→0 条整体放弃（`fixable` ≠ **语意安全**，十类破坏模式是核心知识资产）、附带脚本取消（保护区识别 = 实现 CommonMark 子解析器）、W 组文风审查删除（属语意改写，边界原则无例外）。价值内核 = 规则的**出处、冲突与裁决**，非配置本身：GB/T 15834 允许叹号叠用**最多三叠**（推翻排版指北"不重复使用标点"）、省略号以国标六连点 `……` 为准（推翻本地参考项目的 `⋯⋯`）、GB/T 15835 数字用法不纳入（管用字选择非排版）、T2 相对指北 §2 硬规则**主动降级**为只报告。修改走哈希事务，唯一硬不变量 = 落盘与推导逐字节相等（行号子集断言已证伪）。方案见 [specs/2026-07-31-markdown-style-skill-design.md](docs/superpowers/specs/2026-07-31-markdown-style-skill-design.md)（Codex 三轮 + 首次真实运行验证：暴露并回修 8 项缺陷，含 T4 与 `MD060: padded` 表格 padding 互斥、L2 判据 3 因 MD036 尾标点启发式对中文整体沉默而**无处让位**故删除、确认时机判据由整仓改逐文件）
- **新增 skill：doc-organization（文档信息组织指导原则，独立，非 DevDocs）**：五条原则——当前状态与变更历史分离 / 编号先定义再使用 / 引言职责 / 结论单一出处 / 写给缺少你现在上下文的人。**只给原则不做检测**：判据无法机械化（正则会把 `B2B` `HTTP2` `H1` 当编号），修法无法保证语义中立（补定义=猜事实、改引用=丢本地语境）。`ms-system-design` 引用其中两条。
- **新增 skill：prior-art-scan（开工前先例扫描，独立非 DevDocs）**：多角度检索 GitHub/生态找同类项目 → 5 维健康度评估 → 缺口四分类 → 六路径决策（use-as-is / 插件 / 上游贡献 / vendor+patch / 硬 fork / 自建）。三条跨切面纪律：**证据门**（未经工具确认的候选与数字一律不得入报告，幻觉是本 skill 头号风险）、**只读**（allowed-tools 排除全部 GitHub 写工具，fork/issue/PR 只作为行动项交用户批准）、**覆盖门**（6 检索角度全跑留证）。关键判断：star 与 `pushed:` 是假信号（后者匹配任意分支，bot 提交能伪造活跃）；「外部 PR 受纳度」（`author_association` 分布）是独立于健康度的维度，决定"贡献"路径可不可行；默认反对 fork（成本被系统性低估），vendor+patch 为默认优先项。产出 cwd 单文件 md，零污染。github MCP 能力已 live 实测（无 `get_repository`；`minimal_output:true` 不含 license/`pushed_at`；`reason:not-planned` 查询 vs `not_planned` 返回值），坑记录在 [discovery-matrix.md](skills/prior-art-scan/references/discovery-matrix.md)。方案见 [specs/2026-08-06-prior-art-scan-skill-design.md](docs/superpowers/specs/2026-08-06-prior-art-scan-skill-design.md)
- **bugfix 根因诊断门**：原因不明的简单 Bug 必过"复现基线→假设清单→最小仪器化→证伪确认"，根因未证实 ⛔ 不得修复；连续 2 轮证伪 ⚠️ 升级 dev-tasks（吸收自 superpowers systematic-debugging 纪律，内化非委托）
- internal-only：ms-iteration-policy（由 realign --scope=layout 调度）
- code-quality 重构为代码质量 SSOT：核心阈值表（统一谓词）+ 命名/注释/日志规范 + 设计原则（代码级），示例拆 references/；日志规范=编码纪律 SSOT（级别纪律/最小上下文/异常纪律/安全红线/事实优先 6 条），system-design log-design-guide 留设计阶段"在哪打点"并指针回此；dev-flow/dev-workflow 编码纪律 + verification-flow 日志卫生审查项已并列接入；deferred：health-lint 镜像一致性 rule（见 [plans/2026-06-12-code-quality-restructure-naming.md](docs/superpowers/plans/2026-06-12-code-quality-restructure-naming.md) §4）
- 新增 skill：dev-flow（非 DevDocs 通用开发执行器：契约先行 + 红绿 + 质量地板 + fresh-context 契约审查；与 ms-dev-workflow 双向 NOT-for，方案见 [plans/2026-06-12-dev-flow-standalone-skill.md](docs/superpowers/plans/2026-06-12-dev-flow-standalone-skill.md)）
- **分层记忆原则（已落地为 SSOT）**：决策/执行/数据三层分离，权威在 [_shared/constraints.md §9](skills/_shared/constraints.md)。在 layout.v1 **结构基础已存在**（编号文件提供三层 owner 位置），现役 `state/*`、`adr-only-revision` 只兜**部分**退化症状，**主要靠人工 review lens 承载**（非自动兜底）。
  - **维度 e「三层分离自动检测」已废弃**：关键词扫描复杂度不匹配收益，skill 宜简，不再保留为 FUTURE。
  - 区别：layout.v2 / trace.v1 / 维度 d 仍为**封存 FUTURE**（触发=真实项目痛点），未废弃；登记册见 [docs-layout-migration.md 执行接口落地状态](skills/pipeline/references/layout/docs-layout-migration.md#-执行接口落地状态future)。本仓现役全跑 layout.v1，不执行对使用零影响

## 命令

- 无 build/test/lint 命令
- 发现 skill：读取 `skills/*/SKILL.md` 的 `name` 字段
- 升级 + 健康度：`/ms-pipeline realign --scope=<spec|layout|prd-mapping|health>`

## 约定

- 提交：Conventional Commits — `feat/fix/refactor/docs(scope): description`
- 语言：接受中英文提问，统一中文回复，文档用中文
- SKILL.md ≤ 500 行（硬约束）
- 子 Agent 摘要契约 / 门控标记 / Spec Version Bump 规则：见 [skills/_shared/constraints.md](skills/_shared/constraints.md)

## 详细文档

> 本文是**维护者 / AI 架构备忘**（技术栈、架构决策、约定）。用户上手见 [README.md](README.md)。

- 用户上手 + skill 索引：[README.md](README.md)
- 各流程逐步走查：[docs/workflows.md](docs/workflows.md)
- 治理体系 + 编号规则 + 文件结构：[docs/architecture.md](docs/architecture.md)
- 跨 skill 共享约束：[skills/_shared/constraints.md](skills/_shared/constraints.md)
- 编排层架构：[skills/pipeline/SKILL.md](skills/pipeline/SKILL.md)
- 经验模式库：`docs/devdocs/patterns/`（由 `/ms-compound` 生成）
