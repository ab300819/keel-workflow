<!-- 由 /agent-memory 生成，请通过该命令更新 -->

# keel

keel 文档驱动开发流程的 skill 规格库（Markdown + YAML），以**插件**形式分发到
Claude Code / Codex CLI / OpenCode 三端。21 个流程 skill + 12 个被流程依赖的通用 skill。
与本仓零依赖的独立 skill 在 `skills-local` 仓，⛔ 不在此维护。

## 架构决策

- **`keel` 是工作流的名字，`devdocs` 是它产出的文档目录名**——两者不一致是有意的。`docs/devdocs/`、`.claude/rules/devdocs-state.md`、`devdocs_id` 等路径与字段一律保留 `devdocs`，⛔ 不要「顺手」统一成 keel：那是协议改动，不是改名。
- 每个 skill 位于 `skills/<name>/SKILL.md`，目录名必须等于 frontmatter 的 `name`；安装按该名称复制整个目录，跨 skill 链接依赖此约定。
- `templates/` 子目录存输出模板，`references/` 子目录存评估标准 / rubric / 规则
- `skills/shared/` 是共享资源目录（constraints.md / runlog.md），**不是 skill**（无 SKILL.md）；整包分发后不再需要 skill 身份这层包装。
- **三端共用同一份 `skills/`**，⛔ 不建 `dist/` 构建产物。manifest 各走各端的**主路径**，⛔ 不靠 legacy 别名：
  Claude Code = `.claude-plugin/{plugin,marketplace}.json`；Codex = 根 `plugin.json`（Agent Plugins 可移植格式 + `extensions.com.openai`）
  与 `.agents/plugins/marketplace.json`；OpenCode 无 plugin 发 skill 的机制，只按目录扫描。
  ⛔ 不再有 `.codex-plugin/`——官方标为兼容回退，根 `plugin.json` 带 `extensions.com.openai` 时整个失效。skill 名不带前缀；调用形式按端不同：Claude Code / Codex 可用 `/keel:<name>`，**OpenCode 无命名空间只能裸名**。
  ⇒ **写进执行路径的委托一律用裸名**（`Task: /agent-memory`），带 `keel:` 的只出现在给人看的文档里。
- 编排层通过子代理调度原子 skill；规范中的 `Task` 是委托接口，实际执行前核对当前工具能力，不把文件中的工具名当作已安装能力。

## 修改 skill

- 共享规格同时服务 Claude Code、Codex 等工具；通用行为用工具无关表述，保留客户端元数据和导入约定，不将单一模型的能力假设写成通用保证。
- description 简短说明能力与适用任务，只有易混淆时才加排除项；避免靠宽泛关键词抢占无关任务。
- 正文保留目标、边界、验收条件和非显而易见的操作约束；模式细节按需引用。跨文件协议改动同时核对生产方与消费方。
- 用户明确的任务范围和已有授权优先于 skill 默认流程；可恢复的范围内编辑与检查持续做到完成。需要新的业务选择或范围外操作时，先准备可审阅结果，再说明具体待决项。
- 暂停若由 skill 引起，指出实际读取的文件及规则，区分明确要求与自己的推断。
- 本仓是流程规格的维护仓；修改这些规格不等于在此启动 keel 产品开发全流程。
- 规格改动先算 ROI：单个项目的摩擦优先给绕法（[docs/workflows.md](docs/workflows.md)），改规格等**第二个项目撞同一堵墙**。每轮审查都冒出新耦合是过拟合信号，不是继续加固的理由——封存案例见 [模式 B 调研](docs/superpowers/specs/2026-09-14-mode-b-chg-design.md)。

## 工作流路由

> 本仓是 **skill 规格维护仓**，不是 keel 产品项目。依「用户指令优先于 skill 默认行为」，
> 以下路由**覆盖**任何外部通用流程 skill 的默认触发。

- **本仓元开发没有 process owner skill，本文件就是流程**：ROI 判据（见「修改 skill」末条）、
  外科式改动、验证要求。⛔ 不要为了「先跑个流程」去触发头脑风暴 / 计划编写 / 计划执行 / 分支收尾类 skill——
  多数改动是规格文本的定点修改，套端到端流程是过度形式化。
- **⛔ 不在此启动 keel 全流程**。修改这些规格 ≠ 在本仓开发 keel 产品。
- **允许的外部 skill 用法**：把它们的**产物约定**当落点，不启动它们的门。
  设计稿写进 `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`（既成事实，本仓设计稿都在那）。
- **例外（走 superpowers 完整流程）**：新建整个 skill、跨 skill 协议改动、推翻既有架构决策。
  依次 `brainstorming` → `writing-plans` → `executing-plans`；先出设计稿再动手，产物同样进 `docs/superpowers/specs/`。
- **独立审查**：需要第二意见时用 codex（`/adversarial-review` 或直接 `codex exec`），
  ⛔ 不用外部 skill 的 review 流程门——本仓无代码可审，审的是规格推理。

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
- 修改门控、子代理摘要、Recovery 或 spec_version 时：[skills/shared/constraints.md](skills/shared/constraints.md)。
- 修改 keel 路由或升级入口时：[skills/pipeline/SKILL.md](skills/pipeline/SKILL.md)。
