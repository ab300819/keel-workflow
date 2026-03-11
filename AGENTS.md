<!-- 由 /agent-memory 生成，请通过该命令更新 -->

# AI Agent Skills

## 技术栈

- 规格库：Markdown + YAML skill 定义（非传统代码库）
- 无 build/test/lint 命令
- 24 个 skill，核心为 DevDocs 工作流

## 架构决策

- 每个 skill 独立目录 `skills/<name>/SKILL.md`，通过 description 字段自动发现
- 详细模板放 `templates/` 子目录，SKILL.md 控制在 500 行以内
- DevDocs 编排层（pipeline/feature/bugfix）通过 Task tool 调度原子 skill 作为子代理

## 领域术语

| 术语 | 含义 |
|------|------|
| Skill | 可复用的 SKILL.md 定义文件，扩展 AI agent 能力 |
| DevDocs | 文档驱动开发工作流（需求→设计→测试→任务→开发→验证→同步） |
| 编号体系 | F/US/AC/UT/IT/E2E/INS/BUG/T/BCA，链路：F→US→AC→测试 |
| 质量锚 | 批量生成时首批输出作为后续批次的质量基准 |

## 命令

- 无 build/test/lint 命令
- 发现 skill：读取 `skills/*/SKILL.md` 的 description 字段

## 约定

- 提交：Conventional Commits — `feat/fix/refactor/docs(scope): description`
- 语言：接受中英文提问，统一中文回复，文档用中文
- SKILL.md 不超过 500 行

## 详细文档

- Skill 结构规范：各 `skills/<name>/SKILL.md`
- DevDocs 完整架构：`skills/devdocs-pipeline/SKILL.md`
- 经验模式库：`docs/devdocs/patterns/`（由 `/devdocs-compound` 生成）
