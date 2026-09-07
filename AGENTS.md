<!-- 由 /agent-memory 生成，请通过该命令更新 -->

# AI Agent Skills

## 技术栈

- 规格库：Markdown + YAML skill 定义（非代码库）
- 无 build/test/lint 命令
- 21 个 ms- 流程 skill + 18 个独立 skill（workspace-topology 为仓库拓扑声明维护，dev-flow 为非 DevDocs 通用开发流程，idea-mcp-workflow 为 JetBrains idea MCP 操作手册，e2e-test-flow 为独立 E2E 实测流程，markdown-style 为 Markdown 标记与排版审查器，doc-organization 为文档信息组织指导原则，prior-art-scan 为开工前的先例扫描，python-spec 为 mise+uv 工具链规范）

## 架构决策

- 每个 skill 独立目录 `skills/<dir>/SKILL.md`，调用名为 frontmatter 的 `name` 字段
- **目录名恒等于 `name`**（如 `skills/ms-bugfix/` ↔ `name: ms-bugfix`）。这不是美观问题：`npx skills` 按 `name` 建安装目录，且每个 skill 目录整个拷成自足单元，两者一致时 `../<name>/…` 的跨 skill 链接在本仓与安装后同时成立
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
| design_context | 跨 skill 共享设计上下文 schema，定义于 `skills/ms-prd/references/design-context.md` |
| codebase-insight | 只读代码盘点，输出 `docs/codebase-insight.md`，供多 skill 消费 |
| Sprint Contract | 开发前 Test Agent 与编排器协商的可执行验收契约 |
| FUTURE 三态 | spec 存在但运行时未实现 |

## 当前状态

- 决策记录（21 条，含各自 spec / plan / audit 链接）：[docs/architecture.md § 决策记录索引](docs/architecture.md#决策记录索引)

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
- 编排层架构：[skills/ms-pipeline/SKILL.md](skills/ms-pipeline/SKILL.md)
- 经验模式库：`docs/devdocs/patterns/`（由 `/ms-compound` 生成）
