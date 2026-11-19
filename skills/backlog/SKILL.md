---
name: backlog
description: 管理 keel 中暂缓但需追踪的事项：登记、查询、重新激活或关闭。不用于 Jira/Linear 或 Sprint 容量管理。
allowed-tools: Read, Write, Glob, Grep, AskUserQuestion, Bash
metadata:
  patterns: [registry, workflow-bridge]
  interaction: command-driven
  handoff: yaml-summary-v1
user-invocable: true
writes_backlog: backlog.v3
---

# Backlog 暂缓任务池

- 共享约束 SSOT：[../shared/constraints.md](../shared/constraints.md)

> 本 skill 遵循共享约束 SSOT：门控标记、yaml-summary-v1、Task 委托、用户确认、Recovery 格式、只读 / dry-run、FUTURE 三态、realign / spec_version 见 [skills/shared/constraints.md](../shared/constraints.md)。本文件只描述 backlog 私有规则。

## 定位

`backlog` 是 keel 的**暂缓任务池**：记录已经有来源编号、暂时不进入当前开发闭环、但未来需要追溯的项。

条目状态存于 `docs/devdocs/state/backlog/`，只经 `.keel/bin/keel backlog …` 写入；`docs/devdocs/backlog.md` 是工具生成的索引，⛔ 不手工编辑。每条的长说明写在可编辑的 `docs/devdocs/backlog/<source_id>-<entry_no>.md`。不创建新编号体系，不修改原编号文件。条目通过 `source_id + entry_no` 做局部锚点（如 `F-01#1`），允许同一来源产生多条暂缓项。

边界：

- 区分于 PO grooming：不做产品排序、价值评审、负责人分配。
- 区分于 Jira / Linear：不维护看板、泳道、Sprint 容量。
- 区分于 `04-dev-tasks.md`：不表示当前已排期任务，只表示暂缓且可追溯。

## 入口与触发词

### CLI 入口

每个动作对应一条 keel 命令（垫片缺失、退出码与被拦处理见 [§ keel 工具](../shared/constraints.md#keel-工具)）：

| 动作 | 命令 |
|---|---|
| `--park <source_id>` | `.keel/bin/keel backlog park <source_id> --note "<一句话>" --by <来源 skill> [--related <编号,…>] [--append]` |
| `--note <锚点>` | `.keel/bin/keel backlog note <锚点> --note "<一句话>"`（改既有条目的摘要） |
| `--reactivate <锚点>` | `.keel/bin/keel backlog reactivate <锚点> --target-flow <skill> --target-id <编号>` |
| `--close <锚点>` | `.keel/bin/keel backlog close <锚点> --reason "<原因>"` |
| `--supersede <锚点>` | `.keel/bin/keel backlog supersede <锚点> --by-id <编号或锚点>`（可选终态） |
| `--list[=status]` | `.keel/bin/keel backlog list [--status <status>]`；单条用 `backlog get <锚点>` |

- 需要长说明（Context / Reactivation Criteria）时，park 前先按 [templates/backlog-template.md](templates/backlog-template.md) 写 `docs/devdocs/backlog/<source_id>-<entry_no>.md`（`entry_no` = 该来源已有条目数 + 1，见 `backlog list`）；park 时该文件存在才会挂上详情链接。
- `backlog.md` 在首条入池后由工具生成。

### 编排入口

`/pipeline backlog` 路由到本 skill，传入：

```yaml
skill: backlog
mode: read | dry-run | apply
inputs:
  command: park | note | reactivate | close | supersede | list
  source_id: F-01
expected_output: yaml-summary-v1
```

### 触发词

明确管理暂缓项时触发：`暂缓`、`任务暂缓`、`先记下`、`暂时不做`、`回到 backlog`、`backlog 管理`、`backlog entry`、`park`、`reactivate`。

触发词冲突处理：

| 用户意图 | 路由 |
|---|---|
| “这个 P3 先记下 / 暂时不做 / 放 backlog” | `backlog` |
| “列出 backlog / 重新激活 F-01 的暂缓项” | `backlog` |

## 条目字段

字段与取值见 `.keel/bin/keel schema backlog`；`source_id` 前缀白名单（禁 `B-XXX` 等新编号体系）、按状态的条件必填、`note` 长度由 K5 保证，被拦时按提示处理。原 `F/US/AC/T/INS/BUG/FR/NFR` 文件不加状态字段。

工具不判定的语义：

- `M-XXX` 是**唯一允许承接「尚无任何编号」的来源**：开发过程中冒出的新需求挂到「它是在哪一段冒出来的」上。⛔ 仅此一个例外；挂得上已有编号的按对应编号入池。
- `reactivated` 的 `target_flow` / `target_id` 指已转入的目标流程与编号，如 `dev-tasks` + `T-08`；`closed` 的 `reason` 写不再处理的原因；`superseded` 的 `superseded_by` 写替代它的来源或条目。

## 状态机

`parked` 是唯一初始状态，只能迁到 `reactivated` / `closed` / `superseded` 三个终态之一（由命令保证）。

- `reactivated` 表示已消费到目标流程，不等于 done。
- 没有 `done` 状态；完成度由目标流程自身记录。

## 生产侧衔接

入池只有一条路：用户或编排层显式调用 `backlog --park`（即 `keel backlog park`）。⛔ 其他 skill 不输出候选字段，也不自行拼命令写 backlog——保持单一入口。

适合入池的场景（由用户或编排层判断后调用）：

| 来源 skill | 入池场景 |
|---|---|
| `dev-tasks` | 任务暂缓、依赖未就绪、超出当前迭代但需追踪 |
| `verify` | P3 问题可入池（⛔ 目前不自动）；P1/P2 不应直接 parked，需按 verify 路由处理 |
| `insights` | 跨任务优化机会，已确认但暂不转为需求 |
| `prd` | FR/NFR 搁置，尚不导入 keel 或等待业务确认 |
| `dev-workflow` | **里程碑段内 / 段末**冒出的新想法（`source_id` = 当前 `M-XXX`）：用户自然语言说出，由子代理摸查后写入。挂得上已有 `F`/`AC` 的按对应编号入池，⛔ 不挂到 M |

## 消费侧转化路径

重新激活时，根据 `source_id` 类型路由：

| source_id | target_flow |
|---|---|
| `F-XX` / `US-XX` / `AC-XX` | `requirements` |
| `T-XX` | `dev-tasks` |
| `INS-XX` | `insights` |
| `BUG-XX` | `bugfix` |
| `FR-XX` / `NFR-XX` | `prd` |
| `M-XXX` | 按条目**形态**定，⛔ 无固定去向：新需求 → `requirements`；缺陷 → `bugfix`；已足够明确可直接排期 → `dev-tasks` |

若目标流程尚未生成编号，保持 `parked` 并返回 `partial`，提示先运行目标 skill。

## 门控

缺必填字段、非法前缀、非 `parked` 条目再迁移，由命令当场拒绝，按提示处理。

⚠️ 必须确认：`park` 报出同一 `source_id` 已有 `parked` 条目。
恢复方式：问用户是追加新条目（重跑并加 `--append`）还是更新既有条目（`backlog note <锚点>`）；无确认时不写入。`M-XXX` 来源默认追加，工具不拦，⛔ 不问——段内冒出多个想法是常态，每条都问会把「记一笔」变成打断。

## 追溯能力

- 主锚点：`source_id + entry_no`，例如 `F-01#1`。
- `related_ids` 用于记录辅助关联，不改变主锚点。
- 状态迁移历史看 `docs/devdocs/state/backlog/` 的 git 历史。

## 不做什么

- 不维护负责人、优先级看板、泳道、Sprint 容量。
- 不替代 Jira / Linear / GitHub Issues。
- 不新增 `B-XXX` 或任何 backlog 专属编号。
- 不修改原 `F/US/AC/T/INS/BUG/FR/NFR` 文件。
- 不把 `reactivated` 解释为完成，也不提供 `done` 状态。
- 不自动改 `pipeline` / `dev-tasks` / `verify` / `insights` / `prd`，仅声明后续集成契约。

## 模板与 Realign

- 详情文件模板：[templates/backlog-template.md](templates/backlog-template.md)
- 结构演进：[references/realign.md](references/realign.md)

`backlog.v3` 是当前 spec 版本。修改模板必填章节、字段、状态枚举或硬校验规则时，必须同步更新 [`references/realign.md`](references/realign.md) 的当前版本与 Migration Matrix。

## 子 Agent 摘要格式

**yaml-summary-v1 envelope**：见 [skills/shared/constraints.md § 2](../shared/constraints.md#2-yaml-summary-v1-envelope-ssot)

**summary.details 私有字段**：

| 字段 | 值域 / 示例 |
|---|---|
| `mode` | `park` / `note` / `reactivate` / `close` / `supersede` / `list` / `realign` |
| `backlog_path` | `docs/devdocs/backlog.md` |
| `entries_added` / `entries_updated` | 本次新增或更新条目数 |
| `status_counts` | `{parked: 3, reactivated: 1, closed: 2, superseded: 0}` |
| `affected_entries` | `["F-01#1", "AC-05#2"]` |
| `target_flow` / `target_id` | reactivated 时写入目标 |
| `pending_confirmation` | 同源 active parked 冲突等待确认 |

**产物字段**：`output_files` 列出 `docs/devdocs/backlog.md` 与本次写的详情文件；`new_ids.backlog_entries` 记录局部锚点（如 `F-01#1`），不记录 `B-XXX`。
