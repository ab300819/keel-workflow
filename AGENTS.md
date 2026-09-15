<!-- 由 /agent-memory 生成，请通过该命令更新 -->

# AI Agent Skills

Markdown + YAML skill 规格库，兼容多个 AI 工具。`ms-` 为 DevDocs 流程，其余为独立工具。

## 架构决策

- 每个 skill 位于 `skills/<name>/SKILL.md`，目录名必须等于 frontmatter 的 `name`；安装按该名称复制整个目录，跨 skill 链接依赖此约定。
- `templates/` 子目录存输出模板，`references/` 子目录存评估标准 / rubric / 规则
- 编排层通过子代理调度原子 skill；规范中的 `Task` 是委托接口，实际执行前核对当前工具能力，不把文件中的工具名当作已安装能力。

## 修改 skill

- 共享规格同时服务 Claude Code、Codex 等工具；通用行为用工具无关表述，保留客户端元数据和导入约定，不将单一模型的能力假设写成通用保证。
- description 简短说明能力与适用任务，只有易混淆时才加排除项；避免靠宽泛关键词抢占无关任务。
- 正文保留目标、边界、验收条件和非显而易见的操作约束；模式细节按需引用。跨文件协议改动同时核对生产方与消费方。
- 用户明确的任务范围和已有授权优先于 skill 默认流程；可恢复的范围内编辑与检查持续做到完成。需要新的业务选择或范围外操作时，先准备可审阅结果，再说明具体待决项。
- 暂停若由 skill 引起，指出实际读取的文件及规则，区分明确要求与自己的推断。
- 本仓是流程规格的维护仓；修改这些规格不等于在此启动 DevDocs 产品开发全流程。
- 规格改动先算 ROI：单个项目的摩擦优先给绕法（[docs/workflows.md](docs/workflows.md)），改规格等**第二个项目撞同一堵墙**。每轮审查都冒出新耦合是过拟合信号，不是继续加固的理由——封存案例见 [模式 B 调研](docs/superpowers/specs/2026-09-14-mode-b-chg-design.md)。

## 验证

- 无统一 build/test/lint 命令。文案修改检查 `git diff --check`；名称、路径或协议变更另核对受影响的 frontmatter、引用与消费方。
- SKILL.md ≤ 500 行。行为或路由变化用代表性任务检查触发、执行和停止边界；格式检查不能证明行为有效。
- 相关检查通过即交付差异与验证结果；只有新变更、失败或未解决疑点才扩大或重复检查。

## 约定

- 提交：Conventional Commits — `feat/fix/refactor/docs(scope): description`
- 语言：接受中英文提问，统一中文回复，文档用中文

## 按任务查阅

- 用户上手 + skill 索引：[README.md](README.md)
- 调整流程衔接时：[docs/workflows.md](docs/workflows.md)。
- 查询架构决策、编号与文件结构时：[docs/architecture.md](docs/architecture.md)。
- 修改门控、子代理摘要、Recovery 或 spec_version 时：[skills/_shared/constraints.md](skills/_shared/constraints.md)。
- 修改 DevDocs 路由或升级入口时：[skills/ms-pipeline/SKILL.md](skills/ms-pipeline/SKILL.md)。
