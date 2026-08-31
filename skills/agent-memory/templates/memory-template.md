# AGENTS.md 模板

使用此模板生成目标项目的 `AGENTS.md`（由 `/agent-memory` 生成）。

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

<3-5 行，从 02-system-design.md 提取>

## 架构决策

- ADR-001: <决策摘要>
- ADR-002: <决策摘要>

## 领域术语

| 术语 | 含义 |
|------|------|
| <术语> | <解释> |

## 当前状态

- 活跃：T-XX <任务名>
- 下一步：T-YY <任务名>
- 进度：X/Y 任务完成

## 命令

- 运行：`<command>`
- 测试：`<command>`
- 构建：`<command>`

## 约定

- **发布状态**：<未发布 | 已发布>
- **版本与进度**：<未发布用 Sprint / 里程碑 / 待办池表达进度，⛔ 不套 semver；已发布正常用 semver>
- 提交：<格式>
- 测试：≥80% 覆盖率
- 代码：MTE 原则

## 详细文档

完整 DevDocs 文档位于 `docs/devdocs/`：

- `01-requirements.md` - 需求文档
- `02-system-design.md` - 系统设计
- `03-test-cases.md` - 测试用例
- `04-dev-tasks.md` - 开发任务

<!-- agent-memory:managed -->
## 工作流路由

> 本项目由 DevDocs 管理(存在 `docs/devdocs/`)。依"用户指令(AGENTS.md/CLAUDE.md)优先于 skill 默认行为"的通用优先级,以下路由**覆盖**任何外部通用流程 skill 的默认触发:

- 需求/功能/bug/开发/验证/同步:一律走 `/ms-pipeline` 或对应 `ms-*` skill;外部端到端通用流程 skill(头脑风暴/计划编写/计划执行/调试流程/分支收尾类)**不得接管**这些工作。
- 轻量通道(DevDocs 体系内):一句话任务+验收标准 → `/ms-dev-workflow --inline "<任务>" --ac "<AC>"`;bug → `/ms-bugfix`。
- 外部通用流程 skill 仅用于:DevDocs 体系外杂项(一次性脚本、非交付实验、文档体系自身的元改造)。
- 收尾纪律:提交遵循 ms-dev-workflow 协议(原子提交、绝不推送远程),不使用外部 skill 的 merge/push 选项。
```

**「工作流路由」节使用规则**:仅 DevDocs 项目(`docs/devdocs/` 存在)包含;`<!-- agent-memory:managed -->` 标记 = agent-memory 可再生章节(60 行超限时仅此类章节可压缩);节已存在时保留原文不覆盖(用户自定义优先)。

## 质量守则

写入前按 [best-practices.md](best-practices.md) 的质量守则和内容筛选标准检查。
