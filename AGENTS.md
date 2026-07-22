<!-- 由 /agent-memory 生成，请通过该命令更新 -->

# AI Agent Skills

## 技术栈

- 规格库：Markdown + YAML skill 定义（非代码库）
- 无 build/test/lint 命令
- 21 个 ms- 流程 skill + 12 个独立 skill（含 3 个 internal-only；dev-flow 为非 DevDocs 通用开发流程，idea-mcp-workflow 为 JetBrains idea MCP 操作手册）

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
- 综合方案落地：flag 收敛 49→20、shared-constraints SSOT、realign --scope 四入口
- 治理盲区收敛：scope=health（结构/索引/过大/SSOT 4 维）+ health-lint 5 条 [新增] rule（state/* + dead-link + adr-only-revision），layout.v1+v2 通用
- 新增 skill：ms-backlog（暂缓任务池）
- 新增 skill：idea-mcp-workflow（独立，非 DevDocs）：通过 JetBrains `idea` MCP（`mcp__idea__*` deferred 工具）操作项目的决策/踩坑手册。承载 4 条跨切面纪律（projectPath 必填且须绝对路径 / build 输出防爆=`filesToRebuild` 源头缩范围而非落盘 jq / 依赖未解析 vs 真 bug 强信号 / Maven reload 是 UI 动作 MCP 不暴露）+ 编译主链路，debug·database·refactor 沉 references 按需加载。经 Codex 独立调研（8 条反馈对齐）+ live MCP 实证（纪律 1 报错文案、envo/trade）+ 只读行为抽查。注：skill-creator 触发评测在嵌套 claude -p 环境非判别性（本仓 skill 靠目录发现、非真 Skill 注册），未采纳其分数
- **dev-workflow inline 轻量入口**：`--inline "<任务>" --ac "<AC>"` 无 04 也可进入，物化 stub（AC 落 01 唯一编号源、review_profile 下限 guarded、`grep "来源: inline"` 即回填台账）；协议私有于 [dev-workflow references/inline-entry.md](skills/dev-workflow/references/inline-entry.md)（constraints.md 零改动），spec_version bump devflow.v2，方案见 [specs/2026-07-22-inline-input-satisfaction-design.md](docs/superpowers/specs/2026-07-22-inline-input-satisfaction-design.md)（codex 2 轮审查）
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
