<!-- 由 /agent-memory 生成，请通过该命令更新 -->

# AI Agent Skills

## 技术栈

- 规格库：Markdown + YAML skill 定义（非代码库）
- 无 build/test/lint 命令
- 21 个 ms- 流程 skill + 10 个独立工具 skill（含 3 个 internal-only）

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
| ms- 前缀 | 流程 skill 命名空间，区分独立工具 skill |
| PRD 流程 | 模糊想法/大型 PRD → FR-XX/NFR-XX，支持多目录隔离（`docs/prd/<YYYYMMDD-slug>/`）|
| DevDocs | 文档驱动开发工作流（需求→设计→测试→任务→开发→验证→同步）|
| 编号体系 | F/US/AC/UT/IT/E2E/Journey/INS/BUG/T，链路 F→US→AC→测试 |
| design_context | 跨 skill 共享设计上下文 schema，定义于 `skills/prd/references/design-context.md` |
| codebase-insight | 只读代码盘点，输出 `docs/codebase-insight.md`，供多 skill 消费 |
| Sprint Contract | 开发前 Test Agent 与编排器协商的可执行验收契约 |
| FUTURE 三态 | spec 存在但运行时未实现 |

## 当前状态

- 综合方案落地：flag 收敛 49→20、shared-constraints SSOT、realign --scope 四入口
- 治理盲区收敛：scope=health（结构/索引/过大/SSOT/三层分离 5 维）+ health-lint 5 条 [新增] rule（state/* + dead-link + adr-only-revision），layout.v1+v2 通用
- 新增 skill：ms-backlog（暂缓任务池）
- internal-only：ms-iteration-policy（由 realign --scope=layout 调度）

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

- 项目总览 + 流程分组：[README.md](README.md)
- 跨 skill 共享约束：[skills/_shared/constraints.md](skills/_shared/constraints.md)
- 编排层架构：[skills/pipeline/SKILL.md](skills/pipeline/SKILL.md)
- PRD 流程架构：[skills/prd/SKILL.md](skills/prd/SKILL.md)
- 经验模式库：`docs/devdocs/patterns/`（由 `/ms-compound` 生成）
