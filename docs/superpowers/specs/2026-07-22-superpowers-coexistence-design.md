# DevDocs 与 superpowers 单向兼容设计

- 日期:2026-07-22
- 状态:待评审
- 背景:调研结论——三个共存场景中两个已天然兼容(本规格仓元工作流共存;无 DevDocs 项目经 dev-flow 消费 superpowers plan)。唯一风险区是**"有 DevDocs 的消费项目 + 装了 superpowers 插件"**:superpowers 的 `using-superpowers` 以"1% 适用即必须调用"抢触发,其 brainstorming/executing-plans/finishing-a-development-branch 与 DevDocs 存在协议级冲突(双产物树、绕过双 Agent/质量地板、push 选项 vs "绝不推送远程")。

## 1. 设计原则

- **单向**:superpowers 是插件缓存,改其文件升级即失效;superpowers 侧零改动。
- **官方钩子**:`using-superpowers` 原文承认 "User instructions (CLAUDE.md, AGENTS.md, ...) take precedence over skills"——兼容 = 把一段路由声明变成 DevDocs 的标准发货物,写进消费项目的 AGENTS.md。
- **最薄剂量**:不做运行时检测、不做 21 个 ms- skill 的 NOT-for 扫射(description 是稀缺资源,121 描述溢出的教训)、不解析 superpowers 任何专有格式。

## 2. 改动清单(全部)

| # | 文件 | 改动 |
|---|------|------|
| 1 | `skills/agent-memory/templates/memory-template.md` | 新增可选节「工作流路由」模板(仅 DevDocs 项目包含,见 §3);AGENTS.md 唯一编辑权在 agent-memory,故模板 SSOT 落此 |
| 2 | `skills/pipeline/SKILL.md` | 阶段检测「已有 DevDocs 文件时」表后 +1 行提示:AGENTS.md 缺路由声明节 → ℹ️ 建议 `/agent-memory --update` 补齐(不阻塞) |
| 3 | `skills/onboard/SKILL.md` | 「记忆文件同步 `/agent-memory`」行备注补一句:DevDocs 项目同步时包含工作流路由节 |
| 4 | `docs/workflows.md` | 新增小节「与 superpowers 共存」:路由声明说明 + 两座产物桥点名(superpowers plan → `/dev-flow`;一句话任务+AC → `/ms-dev-workflow --inline`) |

不改 `ms-retrofit`(其 AGENTS.md 写入本就委托 agent-memory 链路,模板生效即覆盖)。

## 3. 路由声明模板(写入 memory-template.md 的可选节)

```markdown
## 工作流路由(仅 DevDocs 项目)

> 本项目由 DevDocs 管理(存在 `docs/devdocs/`)。依 AGENTS.md > skills 的优先级,以下路由**覆盖**通用流程 skill 的默认触发:

- 需求/功能/bug/开发/验证/同步:一律走 `/ms-pipeline` 或对应 `ms-*` skill,**不触发**外部通用流程 skill(如 superpowers 的 brainstorming / systematic-debugging / writing-plans / executing-plans / subagent-driven-development / finishing-a-development-branch)。
- 例外(通用流程 skill 可用):DevDocs 体系外的杂项——一次性脚本、非交付实验、对本项目文档体系自身的元改造。
- 轻量通道(不必走全链):计划文档/issue 直接开发 → `/dev-flow`(零追溯);一句话任务+验收标准 → `/ms-dev-workflow --inline "<任务>" --ac "<AC>"`(有追溯)。
- 收尾纪律:DevDocs 任务提交遵循 ms-dev-workflow 协议(原子提交、绝不推送远程),不使用外部 skill 的 merge/push 选项。
```

要点:命名 superpowers 仅作**举例**,声明对任何"通用流程 skill"生效;无 superpowers 的项目包含此节也无害(等价于重申 ms- 入口)。

## 4. 明确不做(YAGNI)

- ❌ 不改 superpowers 任何文件(单向;缓存升级即失效)。
- ❌ 不做运行时检测"是否装了 superpowers"(声明无条件包含,无害)。
- ❌ 不给 ms- skill description 加 superpowers NOT-for(项目级声明一次解决,粒度更对)。
- ❌ 不解析 superpowers 专有计划语法(dev-flow 已声明只认 Markdown checklist)。
- ❌ 不新增 skill、flag、门控标记、health 维度。

## 5. 验收标准

1. `memory-template.md` 含「工作流路由」可选节,标注包含条件(`docs/devdocs/` 存在)。
2. `/agent-memory --update` 在 DevDocs 项目生成/更新 AGENTS.md 时,按模板包含该节(规格层走查)。
3. pipeline 阶段检测提示为 ℹ️ 级(不阻塞),缺节仅建议。
4. workflows.md 共存小节列出两座桥且链接有效。
5. 全部改动为文档增量,不触碰 superpowers 目录、不改 constraints.md。
