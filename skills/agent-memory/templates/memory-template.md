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

- 提交：<格式>
- 测试：≥80% 覆盖率
- 代码：MTE 原则

## 详细文档

完整 DevDocs 文档位于 `docs/devdocs/`：

- `01-requirements.md` - 需求文档
- `02-system-design.md` - 系统设计
- `03-test-cases.md` - 测试用例
- `04-dev-tasks.md` - 开发任务
```

## 质量守则

写入前按 [best-practices.md](best-practices.md) 的质量守则和内容筛选标准检查。
