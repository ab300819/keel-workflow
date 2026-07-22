# DevDocs 与 superpowers 单向兼容设计

- 日期:2026-07-22
- 状态:待评审
- 背景:调研结论——三个共存场景中两个已天然兼容(本规格仓元工作流共存;无 DevDocs 项目经 dev-flow 消费 superpowers plan)。唯一风险区是**"有 DevDocs 的消费项目 + 装了 superpowers 插件"**:superpowers 的 `using-superpowers` 以"1% 适用即必须调用"抢触发,其 brainstorming/executing-plans/finishing-a-development-branch 与 DevDocs 存在协议级冲突(双产物树、绕过双 Agent/质量地板、push 选项 vs "绝不推送远程")。

## 1. 设计原则

- **单向**:superpowers 是插件缓存,改其文件升级即失效;superpowers 侧零改动。
- **官方钩子**:`using-superpowers` 原文承认 "User instructions (CLAUDE.md, AGENTS.md, ...) take precedence over skills"——兼容 = 把一段路由声明变成 DevDocs 的标准发货物,写进消费项目的 AGENTS.md。
- **最薄剂量**:不做运行时检测、不做 21 个 ms- skill 的 NOT-for 扫射(description 是稀缺资源,121 描述溢出的教训)、不解析 superpowers 任何专有格式。

## 2. 改动清单(全部;R1 修订:发货链路闭环)

| # | 文件 | 改动 |
|---|------|------|
| 1 | `skills/agent-memory/templates/memory-template.md` | 新增可选节「工作流路由」模板(仅 DevDocs 项目包含,见 §3,**行为级措辞、不含插件名**) |
| 2 | `skills/agent-memory/SKILL.md` | `--update` 流程步骤 2 的"DevDocs 增强提取"下 +1 条:**幂等补节规则**——`docs/devdocs/` 存在且 AGENTS.md 缺「工作流路由」节 → 按模板补入;节已存在 → 保留原文不覆盖(用户自定义优先) |
| 3 | `skills/pipeline/SKILL.md` | ① `init` 入口调用链末尾追加 `→ agent-memory --update`(发货点 1:新项目);② 阶段检测「已有 DevDocs 文件时」表后 +1 行 ℹ️ 提示:AGENTS.md 缺路由节 → 建议 `/agent-memory --update`(不阻塞,存量项目兜底) |
| 4 | `skills/retrofit/SKILL.md` | Skill 协作表 +1 行:「记忆同步 `/agent-memory --update`(含工作流路由节)」(发货点 2:改造项目) |
| 5 | `skills/onboard/SKILL.md` | 「记忆文件同步 `/agent-memory`」行备注补一句:DevDocs 项目同步时包含工作流路由节(发货点 3:会话交接) |
| 6 | `docs/workflows.md` | 新增小节「与 superpowers 共存」:承载**全部具体名字**——superpowers process skill 清单、冲突面、两座产物桥(superpowers plan → `/dev-flow`,仅非 DevDocs 项目;一句话任务+AC → `/ms-dev-workflow --inline`) |

发货闭环:新项目(init 链末)/ 改造项目(retrofit 协作)/ 存量项目(pipeline ℹ️ 兜底 + onboard 交接),三路都落到 agent-memory 的同一条幂等补节规则。

## 3. 路由声明模板(写入 memory-template.md 的可选节;R1 修订:行为级、无插件名、轻量通道纠偏)

```markdown
## 工作流路由(仅 DevDocs 项目)

> 本项目由 DevDocs 管理(存在 `docs/devdocs/`)。依"用户指令(AGENTS.md/CLAUDE.md)优先于 skill 默认行为"的通用优先级,以下路由**覆盖**任何外部通用流程 skill 的默认触发:

- 需求/功能/bug/开发/验证/同步:一律走 `/ms-pipeline` 或对应 `ms-*` skill;外部端到端通用流程 skill(头脑风暴/计划编写/计划执行/调试流程/分支收尾类)**不得接管**这些工作。
- 轻量通道(DevDocs 体系内,不必走全链):一句话任务+验收标准 → `/ms-dev-workflow --inline "<任务>" --ac "<AC>"`(有追溯);bug → `/ms-bugfix`。
- 外部通用流程 skill 仅用于:DevDocs 体系外杂项(一次性脚本、非交付实验、对文档体系自身的元改造)。
- 收尾纪律:提交遵循 ms-dev-workflow 协议(原子提交、绝不推送远程),不使用外部 skill 的 merge/push 选项。
```

要点(F-002/F-003 修复):
- **无插件名、无具体 skill 名**——只写行为类别("端到端通用流程"),符合 agent-memory best-practices「工具无关」守则与「工具绑定」反模式;superpowers 具体清单与冲突面移至 workflows.md。
- **DevDocs 项目内不推荐 `/dev-flow`**——它是"无 DevDocs 项目"的通道(其自身路由判定亦如此:有 `docs/devdocs/` → ms-dev-workflow);体系内轻量 = `--inline` / `ms-bugfix`,消除"开发一律 ms-*"与轻量通道的自相矛盾。

## 4. 明确不做(YAGNI)

- ❌ 不改 superpowers 任何文件(单向;缓存升级即失效)。
- ❌ 不做运行时检测"是否装了 superpowers"(声明无条件包含,无害)。
- ❌ 不给 ms- skill description 加 superpowers NOT-for(项目级声明一次解决,粒度更对)。
- ❌ 不解析 superpowers 专有计划语法(dev-flow 已声明只认 Markdown checklist)。
- ❌ 不新增 skill、flag、门控标记、health 维度。

## 5. 验收标准(R1 修订)

1. `memory-template.md` 含「工作流路由」可选节,标注包含条件(`docs/devdocs/` 存在),措辞行为级、无插件名/skill 名。
2. `agent-memory SKILL.md` `--update` 流程含幂等补节规则:缺节补入、已存在保留原文;新建走模板天然包含(规格层走查)。
3. 发货三路齐备:pipeline init 链末 `agent-memory --update`;retrofit 协作表含记忆同步行;pipeline 阶段检测 ℹ️ 兜底(不阻塞)+ onboard 备注。
4. workflows.md 共存小节:superpowers process skill 清单 + 冲突面 + 两座桥(dev-flow 标注"仅非 DevDocs 项目"),链接有效。
5. 模板轻量通道只含 `--inline` 与 `ms-bugfix`,不含 dev-flow(消除自相矛盾)。
6. 全部改动为文档增量,不触碰 superpowers 目录、不改 constraints.md。
