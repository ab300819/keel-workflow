# backlog Realign 实例化

> 共享契约见 [../../pipeline/references/realign.md](../../pipeline/references/realign.md)。

## 当前 spec_version

**`backlog.v3`**（2026-11-19：条目状态移入 `docs/devdocs/state/backlog/`，由 keel 工具独占；`backlog.md` 整份由工具生成，长说明放 `backlog/<source_id>-<entry_no>.md`）

## Migration Matrix（spec_version 演进）

### v1 → v2

| 分级 | 变更项 | 修复动作 | 判据 |
|---|---|---|---|
| additive | `source_id` 白名单增加 `M-XXX`；`M-XXX` 来源同源第二条默认追加不再询问 | **无存量差距**——放宽值域不会让已有条目失效 | 不适用 |

> **零迁移动作**：这是一次纯放宽。存量条目无需改动（`backlog.md` 现为工具生成，`spec_version` 随下次生成自然更新）。
> 之所以仍要 bump：`source_id` 白名单是硬校验规则，改它命中 `realign/bump-required-structure`；不 bump 则消费方无从判断某个 `M-XXX` 条目是合法还是脏数据。

### v2 → v3

| 分级 | 变更项 | 修复动作 | 判据 |
|---|---|---|---|
| restructuring | 条目状态从 `backlog.md` 的 yaml 块移入 `state/backlog/`；`backlog.md` 改为生成文件 | ⛔ 本 skill 不手工迁移，由 `/pipeline realign` 调度 `.keel/bin/keel migrate`（见 [pipeline realign.md § 台账迁移](../../pipeline/references/realign.md#台账迁移)） | `backlog.md` 或 `backlog/*.md` 为 `backlog.v2`，且无 `docs/devdocs/state/meta.json` |

## Realign 子流程

- 主入口：由 `/pipeline realign` 编排调度。
- `backlog.v3` 起 `backlog.md` 由工具生成，本 skill 没有可手工补齐的结构：
  - 检测到 `backlog.v2` → 交给 `/pipeline realign` 的台账迁移（见上表），⛔ 不手工改 `backlog.md`。
  - 已是 `backlog.v3` → no-op。`backlog.md` 与状态不一致时执行 `.keel/bin/keel render` 重新生成。
- 详情文件 `backlog/<source_id>-<entry_no>.md` 只补缺失的 Context / Reactivation Criteria 小节，不改业务内容，不改条目状态。
- 输出 yaml-summary-v1 信封（details：`{from_spec, to_spec, additive_count, restructuring_count, scope, entries_affected}`）。
