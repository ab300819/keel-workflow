<!-- 由 /agent-memory 生成，请通过该命令更新 -->

# AI Agent Skills

## 技术栈

- 规格库：Markdown + YAML skill 定义（非传统代码库）
- 无 build/test/lint 命令
- 19 个 ms- 流程 skill + 10 个独立工具 skill

## 架构决策

- 每个 skill 独立目录 `skills/<dir>/SKILL.md`，通过 SKILL.md 的 `name` 字段匹配调用；ms- 流程 skill 目录使用去前缀短名（如 `skills/bugfix/` ↔ `name: ms-bugfix`）
- 流程 skill 的 name 字段统一使用 `ms-` 前缀（如 `ms-prd`、`ms-requirements`）
- 详细模板放 `templates/` 子目录，SKILL.md 控制在 500 行以内
- `templates/` 子目录存放输出模板，`references/` 子目录存放评估标准/rubric/规则
- 编排层（ms-pipeline/ms-feature/ms-bugfix）通过 Task tool 调度原子 skill 作为子代理
- PRD 流程（ms-prd/ms-prd-brainstorm/ms-prd-parser）独立于 DevDocs，处理模糊想法和大型 PRD，通过 `--from-prd` 软集成
- ms-codebase-insight 为共享代码盘点 skill，ms-prd 和 ms-onboard 均消费其输出
- `skills/prd/references/design-context.md` 虽放在 prd 目录下，但作为**跨 skill 共享定义**，被 ms-prd、ms-requirements、ms-system-design、ms-dev-tasks、ms-dev-workflow、ms-verify 共同消费
- ms- 流程 skill 的 frontmatter 使用项目扩展字段 `metadata`（含 `patterns`、`interaction`、`handoff` 子键），用于标注 skill 的设计模式、交互方式和摘要契约类型；该字段不属于 Claude Code / Codex 官方 spec，由项目自行定义

## 流程分组

| 分组 | Skill | 说明 |
|------|-------|------|
| **PRD（需求发现）** | ms-prd, ms-prd-brainstorm, ms-prd-parser | 模糊想法/大型 PRD → 结构化 FR-XX/NFR-XX；支持多 PRD 隔离（`YYYYMMDD-slug` 目录）、状态追踪和归档 |
| **Dev（开发）** | ms-dev-tasks, ms-dev-workflow | 任务拆分与 TDD 执行（测试仍是开发闭环内阶段） |
| **Test（测试）** | ms-test-cases, ms-test-run | 测试设计与执行 |
| **Shared（共享）** | ms-pipeline, ms-requirements, ms-system-design, ms-feature, ms-bugfix, ms-verify, ms-sync, ms-compound, ms-onboard, ms-retrofit, ms-insights, ms-codebase-insight | 编排、编码、设计、验证、同步等 |

## 子 Agent 摘要契约（yaml-summary-v1）

所有 ms- skill 作为子 Agent 运行时，返回统一信封格式：

```yaml
skill: <ms-skill-name>
status: success | failed | interrupted | partial
summary:
  headline: "一句话总结"
  details: {}           # skill 私有字段放这里
blockers: []             # 通用：阻塞项列表
output_files: []         # 通用：产出/修改的文件
new_ids: {}              # 通用：生成的编号，键名按产物类型命名（如 chunks/requirements/F/US/AC/UT/IT/E2E/Journey/T/BUG/INS）
next_recommended:
  skill: <ms-next-skill>    # 可选
  args: ""               # 可选
```

**规则**：`status`/`blockers`/`output_files`/`new_ids`/`next_recommended` 为保留字段，skill 私有数据统一放 `summary.details`。各 skill 在摘要示例中列出自身适用的 `status` 值子集（完整值域见上方契约定义）。

## 门控标记规范

| 标记 | 语义 | 适用场景 |
|------|------|---------|
| `⛔ 禁止继续` | 硬阻塞，必须修复后才能继续 | 阶段边界、P1 阻塞、安全不变式 |
| `⚠️ 必须确认` | 需用户确认才可继续 | Inversion 问询、方案确认 |
| `ℹ️ 建议` | 推荐但可跳过 | P2/P3 建议、可选验证步骤 |

每个 `⛔` 门控必须附带**恢复方式**（如何解除阻塞）。

## 领域术语

| 术语 | 含义 |
|------|------|
| Skill | 可复用的 SKILL.md 定义文件，扩展 AI agent 能力 |
| ms- 前缀 | 流程 skill 的命名空间前缀，区分于独立工具 skill |
| PRD 流程 | 需求发现流程（模糊想法/大型 PRD → 结构化 FR-XX/NFR-XX），支持多 PRD 目录隔离（`docs/prd/<YYYYMMDD-slug>/`）、状态追踪（active/superseded/archived）和归档（`_archived/`） |
| PRD 全局索引 | `docs/prd/index.md`，PRD 清单 + 编号注册表的 source of truth |
| DevDocs | 文档驱动开发工作流（需求编码→设计→测试→任务→开发→验证→同步） |
| 编号体系 | F/US/AC/UT/IT/E2E/Journey/INS/BUG/T/BCA，链路：F→US→AC→测试 |
| FR-XX/NFR-XX | PRD 阶段需求编号（全局唯一，由全局索引编号注册表管理），通过 `--from-prd` 衔接 DevDocs |
| 质量锚 | 批量生成时首批输出作为后续批次的质量基准 |
| codebase-insight | 只读代码盘点，输出 docs/codebase-insight.md，供多个 skill 消费 |
| Sprint Contract | 开发前 Test Agent 与编排器协商的可执行验收契约（函数签名、边界条件） |
| 验证盲区 | ms-verify 未检出但后续发现的问题，沉淀于 docs/devdocs/patterns/verify-blindspots.md |
| Harness 深度 | Lite/Standard/Deep 三档自适应流程深度，基于变更影响面选择 |
| design_context | 跨 skill 共享的设计上下文 schema（设计稿来源+组件库信息），定义于 `skills/prd/references/design-context.md` |
| design_ref | 任务/需求项关联的设计稿页面/组件标识（如 D-01:登录页） |

## 命令

- 无 build/test/lint 命令
- 发现 skill：读取 `skills/*/SKILL.md` 的 `name` 字段

## 角色规范

- 高关注点分离需求的 skill 使用 `## 角色` 块（身份/关注/回避/判断倾向）
- 中等需求的 skill 使用 `> 视角：...` 一句话锚定
- 工具性/调度性 skill 不加角色
- 角色定义必须与工作流约束保持一致，不得冲突

## 约定

- 提交：Conventional Commits — `feat/fix/refactor/docs(scope): description`
- 语言：接受中英文提问，统一中文回复，文档用中文
- SKILL.md 不超过 500 行
- **Codex 审查边界**：审查 skill spec 时聚焦命名一致性、交叉引用完整性和契约兼容性。运行时 edge case（git 状态、文件时间戳、缓存失效条件等）属于实现层，不在 spec 审查范围内

## 详细文档

- Skill 结构规范：各 `skills/<dir>/SKILL.md`（目录短名，name 字段为调用名）
- 编排层架构：`skills/pipeline/SKILL.md`
- PRD 流程架构：`skills/prd/SKILL.md`
- 代码盘点：`skills/codebase-insight/SKILL.md`
- 经验模式库：`docs/devdocs/patterns/`（由 `/ms-compound` 生成）
