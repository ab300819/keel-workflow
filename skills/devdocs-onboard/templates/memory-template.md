# AGENTS.md 模板

使用此模板生成目标项目的 `AGENTS.md`（由 `/devdocs-onboard --memory` 生成）。

CLAUDE.md 为 AGENTS.md 的完整镜像，头部加上：

```markdown
<!-- 由 AGENTS.md 镜像，请勿直接编辑 -->
<!-- 运行 /devdocs-onboard --memory 更新 -->
```

---

```markdown
<!-- 由 /devdocs-onboard --memory 生成，请通过该命令更新 -->

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

写入 AGENTS.md 前检查：

1. **短而稳定**：可删则删，AGENTS.md 不超过 60 行
2. **广泛适用**：仅保留跨任务高频规则，不写单次使用的信息
3. **可执行**：优先命令、约束、检查点，而非长篇解释
4. **避免重复**：领域流程放到 Skill，不塞进记忆文件
5. **详情留原地**：具体实现细节、逐文件说明禁止写入常驻记忆
6. **工具无关**：不包含特定 AI 工具的专属语法或指令
