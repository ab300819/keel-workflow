# 仓库治理待办

> **与 DevDocs 治理是两条轴。** 这里是发布、发现、跨客户端能力、工具漂移——不涉及 skill 内容规则。
>
> 来源：2026-08-10 Codex 对本仓的独立盘点（`SKILL-OPTIMIZATION-HANDOFF.md`，794 行）。该文件已删除——它携带 3 处已被证伪的结论，留着的风险大于残值。原文在历史里：`git show 0e10bbd:SKILL-OPTIMIZATION-HANDOFF.md`。
>
> 本文是 2026-08-31 逐条复查后的**存活项**。

## 1. 存活项（3 条）

### 1.1 `idea-mcp-workflow` 引用不存在的 MCP 工具名

**已实证**：以下工具名在当前 Claude Code runtime 的 `mcp__idea__*` 列表中**不存在**。交接文档当时从 Codex 侧观察到同一问题，两侧一致。

| 位置 | 写的 | 实际有的 |
|---|---|---|
| `SKILL.md:102` | `find_files_by_glob` | `search_file` |
| `SKILL.md:102` | `search_in_files_by_regex` | `search_regex` |
| `references/refactor.md:24` | `search_in_files_by_text` | `search_text` |
| `references/refactor.md:9` | `replace_text_in_file` / `search_in_files`（作为反例出现，但名字同样不存在）| — |

⚠️ `references/debug.md` 里的 `start_debugger_session` / `get_debugger_status` / `get_stack` / `get_threads` / `run_to_line` / `set_variable` 是 `xdebug_*` 的**简写**（同文件已写过全名 `xdebug_control_session`），推得出来，**算不一致不算硬错**——修不修看顺手。

**修法**（交接 §6.1 的建议，仍然成立）：SKILL.md 只留稳定纪律（`projectPath` / 输出防爆 / 依赖未解析 vs 真 bug / Maven reload 边界），工具选择表沉到按 runtime 更新的 reference；**不记录工具总数**（易漂）。

### 1.2 仓库无 validator

40 个 skill、179 个文件，全靠人肉核对。本轮规则收敛删 222 条时，`⛔` 语义、悬挂引用、双删全是人工发现的，其中 9 条**漏到外部评审之后**才抓出来。

首版只做高价值检查（交接 §4.2）：frontmatter 可解析 / `name` 唯一 / 目录短名↔runtime name 映射 / `SKILL.md ≤ 500` / README 声明数量与实际一致 / 仓库内链接存在 / SKILL.md 引用的 references·templates 存在 / internal skill 不暴露为用户入口。

⚠️ 链接检查必须区分真实相对链接、模板中的示例路径、FUTURE 产物路径、代码块内伪链接、带 anchor 的链接。**不要用「所有 `[x](y)` 都必须存在」的裸正则阻断**——会把模板输出路径误判成死链。

⚠️ 零依赖实现。交接实测外部 `quick_validate.py` 因缺 PyYAML 直接跑不起来。

### 1.3 根 `AGENTS.md` 缺元开发路由

`docs/workflows.md` 说明**消费方** DevDocs 项目会由 `agent-memory` 写入「工作流路由」节压制外部 process skill 误触发。但本仓根 `AGENTS.md` 只有决策记录（第 45 行），没有实际生效的路由块。

**本次会话即实证**：做 skill 元开发时，superpowers 的 `brainstorming` / `writing-plans` / `subagent-driven-development` 三个 process skill 全被自动加载。

需要定的：skill 元设计 / 协议调整 / DevDocs skill 开发时，哪个是唯一 process owner；何时允许 superpowers 产物作为输入；明确禁止双重门控。

## 2. 已解决 / 已证伪（勿再照原文去修）

| 交接原文 | 2026-08-31 复查 |
|---|---|
| §3.1 安装漂移：6 个落后、3 个缺失 | **40/40 内容一致**，全部按 frontmatter `name` 安装（`npx skills` 所为，副本非符号链接） |
| §3.2 短名残留 `bugfix` vs `ms-bugfix` | **零残留** |
| §3.3 README 安装命令路径错 | **该判断本身是错的**：`git clone …/skills.git` 会建出 `skills/`，故 `bash skills/scripts/deploy-skills.sh` 路径正确 |
| §3.4 部署脚本用 basename 命名 | 已由 `01816e8` **删除脚本**解决——它没人跑（实际安装走 `npx skills`），跑一次反而会在 22 个正确副本旁造出 22 个错名链接 |
| 1.4 `ms-iteration-policy` 仍在默认发现集 | **已解决**：2026-08-31 随 layout.v2 删除——它 `user-invocable: false`，唯一调用者是 layout.v2 的 `realign --scope=layout`，依赖坍塌成孤儿。反模式诊断救成 `00-baseline.md` §2.1 的一条纪律 |
| §8 六大入口瘦身 | 本轮规则收敛顺带做了一部分（dev-workflow 422→386、system-design 465→441、verify 446→436），但交接要的**结构性重排**未做 |
| §7.2 单一 process owner | 部分覆盖：本轮建的 `task/intent-normalization` 是 **skill 内部**的意图→参数归一化，不是 **skill 之间**的 owner 仲裁。§7.3 那层仍空（见 1.3）|

## 3. 未复查（原文列了，本次没验）

- §5 跨客户端 capability 抽象（协议绑死 `Task` tool，Codex 侧是 `spawn_agent`）
- §6.2 `ui-orchestrator` 是否仍有独立价值（交接建议「薄路由层」或「退役」，需 prompt eval 决定）
- §6.3 `ms-board` / `e2e-test-flow` 硬编码 `mcp__chrome-devtools__*`，缺 capability preflight
- §10 `agents/openai.yaml` UI metadata

> 这四条都需要在**多个客户端上实测**才能判断，本仓单侧观察不足以下结论。

## 4. 本台账证不了什么

- 1.2 的 validator 检查项清单来自交接文档的建议，**未验证误报率**。
- 1.4 的三个选项没有实测依据——「三个目标客户端是否都尊重 `user-invocable: false`」本身就是未验证的假设。
- §3 未复查项的现状可能与 2026-08-10 已经不同，照原文行动前须重新观察。
