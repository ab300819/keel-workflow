<!-- 由 /agent-memory 生成，请通过该命令更新 -->

# AI Agent Skills

## 技术栈

- 规格库：Markdown + YAML skill 定义（非传统代码库）
- 无 build/test/lint 命令
- 27 个 skill：DevDocs 工作流（开发侧）+ Product Pipeline（产品侧）

## 架构决策

- 每个 skill 独立目录 `skills/<name>/SKILL.md`，通过 description 字段自动发现
- 详细模板放 `templates/` 子目录，SKILL.md 控制在 500 行以内
- `templates/` 子目录存放输出模板，`references/` 子目录存放评估标准/rubric/规则
- DevDocs 编排层（pipeline/feature/bugfix）通过 Task tool 调度原子 skill 作为子代理
- Product Pipeline（product-pipeline/brainstorm/prd-parser）独立于 DevDocs，处理模糊想法和大型 PRD，通过 `--from-product` 软集成

## 子 Agent 摘要契约（yaml-summary-v1）

所有 DevDocs 和 Product Pipeline skill 作为子 Agent 运行时，返回统一信封格式：

```yaml
skill: <skill-name>
status: success | failed | interrupted | partial
summary:
  headline: "一句话总结"
  details: {}           # skill 私有字段放这里
blockers: []             # 通用：阻塞项列表
output_files: []         # 通用：产出/修改的文件
new_ids: {}              # 通用：生成的编号 (F/US/AC/UT/IT/E2E/Journey/T/BUG/INS)
next_recommended:
  skill: <next-skill>    # 可选
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
| DevDocs | 文档驱动开发工作流（需求→设计→测试→任务→开发→验证→同步） |
| 编号体系 | F/US/AC/UT/IT/E2E/Journey/INS/BUG/T/BCA，链路：F→US→AC→测试 |
| Product Pipeline | 独立的产品需求处理流程，使用 FR-XX/NFR-XX 编号，通过 `--from-product` 衔接 DevDocs |
| 质量锚 | 批量生成时首批输出作为后续批次的质量基准 |

## 命令

- 无 build/test/lint 命令
- 发现 skill：读取 `skills/*/SKILL.md` 的 description 字段

## 角色规范

- 高关注点分离需求的 skill 使用 `## 角色` 块（身份/关注/回避/判断倾向）
- 中等需求的 skill 使用 `> 视角：...` 一句话锚定
- 工具性/调度性 skill 不加角色
- 角色定义必须与工作流约束保持一致，不得冲突

## 约定

- 提交：Conventional Commits — `feat/fix/refactor/docs(scope): description`
- 语言：接受中英文提问，统一中文回复，文档用中文
- SKILL.md 不超过 500 行

## 详细文档

- Skill 结构规范：各 `skills/<name>/SKILL.md`
- DevDocs 完整架构：`skills/devdocs-pipeline/SKILL.md`
- Product Pipeline 架构：`skills/product-pipeline/SKILL.md`
- 经验模式库：`docs/devdocs/patterns/`（由 `/devdocs-compound` 生成）
