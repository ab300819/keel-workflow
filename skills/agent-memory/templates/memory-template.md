# AGENTS.md 模板

使用此模板生成目标项目的 `AGENTS.md`（由 `/agent-memory` 生成）。

章节按实际需要选用；已有文件保留适用结构。只写来源可核实的项目事实与约定，删除空占位，不为填满模板新增流程、覆盖率门槛或版本策略。

CLAUDE.md 通过 `@AGENTS.md` 导入通用信息，并可追加 Claude Code 专属补充。
首次创建时内容：

```markdown
<!-- 运行 /agent-memory 更新 AGENTS.md -->

@AGENTS.md

## Claude Code 补充

<!-- Claude Code 专属信息，/agent-memory 不会覆盖此区域 -->
```

---

```markdown
<!-- 由 /agent-memory 生成，请通过该命令更新 -->

# <项目名称>

## 技术栈

<简述已核实的技术栈；来源可为配置、README 或系统设计>

## 架构决策

- ADR-001: <决策摘要>
- ADR-002: <决策摘要>

## 领域术语

| 术语 | 含义 |
|------|------|
| <术语> | <解释> |

## 当前状态

- <任务台账或状态文档链接；有必要且能维护时才保留当前任务摘要>

## 命令

- 运行：`<command>`
- 测试：`<command>`
- 构建：`<command>`

## 约定

- **发布状态**：<未发布 | 已发布>
- **版本与进度**：<项目已有约定；无法确认则省略>
- 提交：<格式>
- 验证：<相关检查命令与完成条件；仅填写项目已有要求>

## 详细文档

- <任务场景>：<现有权威文档链接，仅在该场景需要时查阅>

<!-- agent-memory:managed -->
## 工作流路由

> 本项目由 DevDocs 管理(存在 `docs/devdocs/`)。依"用户指令(AGENTS.md/CLAUDE.md)优先于 skill 默认行为"的通用优先级,以下路由**覆盖**任何外部通用流程 skill 的默认触发:

- 需求/功能/bug/开发/验证/同步:一律走 `/pipeline` 或对应 DevDocs 流程 skill;外部端到端通用流程 skill(头脑风暴/计划编写/计划执行/调试流程/分支收尾类)**不得接管**这些工作。
- 轻量通道(DevDocs 体系内):一句话任务+验收标准 → `/dev-workflow --inline "<任务>" --ac "<AC>"`;bug → `/bugfix`。
- 外部通用流程 skill 仅用于:DevDocs 体系外杂项(一次性脚本、非交付实验、文档体系自身的元改造)。
- 收尾纪律:提交遵循 dev-workflow 协议(原子提交、绝不推送远程),不使用外部 skill 的 merge/push 选项。
```

**「工作流路由」节使用规则**：仅 DevDocs 项目包含；`<!-- agent-memory:managed -->` 标记可再生章节。已有自定义路由保留；需要压缩时按 [SKILL.md 的授权与 60 行处理规则](../SKILL.md) 执行。

## 质量守则

写入前按 [best-practices.md](best-practices.md) 的质量守则和内容筛选标准检查。
