<!-- 由 /agent-memory 生成，请通过该命令更新 -->

# keel

keel 是以插件形式分发的通用开发 harness，为 AI 辅助开发提供任务编排、执行约束、检查与验证能力，服务 Claude Code / Codex CLI / OpenCode。skill 是能力载体，文档驱动开发是其中一套工作流；本仓维护整个插件，包括 skills、共享协议、模板、检查脚本、hooks 和客户端适配与分发配置。安装方式与能力索引见 [README.md](README.md)。与本仓零依赖的独立 skill 在 `skills-local` 仓，不在此维护。

## 工作流路由

本仓维护 harness 插件本身，不因修改插件而自动启动其文档驱动开发全流程。以下维护规则覆盖外部通用流程 skill 的默认触发。

- **默认路径**：本仓元开发没有 process owner skill，本文件就是流程。遵循 ROI 判据、外科式改动和下述验证要求，不为定点修改启动头脑风暴、计划编写、计划执行或分支收尾类 skill。
- **ROI 判据**：新增通用机制、流程或抽象前，单个项目的摩擦优先给绕法（见 [docs/workflows.md](docs/workflows.md)），等第二个项目遇到同一问题再推广；已确认的错误或协议矛盾按最小范围修复。每轮审查都冒出新耦合是过拟合信号，不是继续加固的理由；封存案例见 [模式 B 调研](docs/superpowers/specs/2026-09-14-mode-b-chg-design.md)。
- **例外：走 superpowers 完整流程**。新建整个 skill、跨 skill 协议改动或推翻既有架构决策时，依次执行 `brainstorming` → `writing-plans` → `executing-plans`，先出设计稿再动手。
- 执行上述例外前检查所需技能是否可用；缺失时说明缺失项及受阻步骤，提出替代路径供用户决定，不声称已执行缺失技能。无依赖的资料核对可继续。
- 除上述例外，不启动外部端到端流程 skill 的流程门，可采用其产物约定；`agent-memory`、环境管理等专项技能可按需使用。设计稿统一放在 `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`。
- **独立审查**：需要第二意见时用 codex（`/adversarial-review` 或直接 `codex exec`）；规格改动审查规则与协议，脚本和 hooks 改动审查代码行为，不另套外部 review 流程门。

## 架构与分发

- `keel` 是 harness 与插件名，`devdocs` 是其文档驱动工作流使用的文档目录与协议命名。`docs/devdocs/`、`.claude/rules/devdocs-state.md`、`devdocs_id` 等路径与字段保留 `devdocs`；改成 keel 属于协议改动，不能作为改名顺手处理。
- 每个 skill 位于 `skills/<name>/SKILL.md`，目录名必须等于 frontmatter 的 `name`；安装按该名称复制整个目录，跨 skill 链接依赖此约定。
- skill 内的 `templates/` 存输出模板，`references/` 存评估标准、rubric 和规则。`skills/shared/` 存共享资源（`constraints.md` / `runlog.md`），无 SKILL.md，不是 skill，随整包分发。
- 三端共用同一份 `skills/`，不建 `dist/`。manifest 使用各端主路径，不依赖 legacy 别名：

  | 客户端 | 分发入口 | 调用形式 |
  | --- | --- | --- |
  | Claude Code | `.claude-plugin/{plugin,marketplace}.json` | 可用 `/keel:<name>` |
  | Codex | 根 `plugin.json`（Agent Plugins 可移植格式 + `extensions.com.openai`）、`.agents/plugins/marketplace.json` | 可用 `/keel:<name>` |
  | OpenCode | 直接扫描 skill 目录，无 plugin 分发 skill 的机制 | 无命名空间，只能裸名 |

- 不使用 `.codex-plugin/` 兼容回退；根 `plugin.json` 带 `extensions.com.openai` 时该回退整体失效。
- skill 名不带前缀；执行路径中的委托一律用裸名（如 `Task: /agent-memory`），`keel:` 前缀只用于给人看的文档。
- 编排层通过子代理调度原子 skill；`Task` 是规范中的委托接口，执行前核对当前工具能力，不能把文件中的工具名当作已安装能力。

## 修改约束

- 外科式修改，只改任务所需内容。共享规格使用工具无关表述，保留客户端元数据和导入约定，不将单一模型的能力假设写成通用保证。
- description 简短说明能力与适用任务，仅在易混淆时加排除项，避免用宽泛关键词抢占无关任务。
- 正文保留目标、边界、验收条件和非显而易见的操作约束；模式细节按需引用。跨文件协议改动同时核对生产方与消费方。
- 用户明确的任务范围和已有授权优先于 skill 默认流程；可恢复的范围内编辑与检查持续做到完成。需要新的业务选择或范围外操作时，先准备可审阅结果，再说明具体待决项。
- 若因 skill 暂停，指出实际读取的文件及规则，区分明确要求与自己的推断。

## 验证与交付

- 无统一 build/test/lint 命令。文案修改检查 `git diff --check`；名称、路径或协议变更另核对受影响的 frontmatter、引用与消费方。
- 脚本或 hooks 改动做对应语言的语法检查，并用代表性输入验证受影响行为；分发配置改动核对入口、资源路径与客户端加载方式。未能实测的部分明确说明。
- SKILL.md ≤ 500 行。行为或路由变化用代表性任务检查触发、执行和停止边界；格式检查不能证明行为有效。
- 相关检查通过即交付差异与验证结果；只有新变更、失败或未解决疑点才扩大或重复检查。
- 提交使用 Conventional Commits：`feat/fix/refactor/docs(scope): description`。
- 接受中英文提问，统一中文回复，文档用中文。

## 按任务查阅

- 用户上手与 skill 索引：[README.md](README.md)。
- 调整流程衔接：[docs/workflows.md](docs/workflows.md)。
- 查询架构决策、编号与文件结构：[docs/architecture.md](docs/architecture.md)。
- 修改门控、子代理摘要、Recovery 或 spec_version：[skills/shared/constraints.md](skills/shared/constraints.md)。
- 修改 keel 路由或升级入口：[skills/pipeline/SKILL.md](skills/pipeline/SKILL.md)。
