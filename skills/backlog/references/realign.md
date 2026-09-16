# backlog Realign 实例化

> 共享契约见 [../../pipeline/references/realign.md](../../pipeline/references/realign.md)。

## 当前 spec_version

**`backlog.v2`**（2026-09-08：`source_id` 白名单增加 `M-XXX`，承接里程碑段内冒出、尚无编号的新需求）

## Migration Matrix（spec_version 演进）

### v1 → v2

| 分级 | 变更项 | 修复动作 | 判据 |
|---|---|---|---|
| additive | `source_id` 白名单增加 `M-XXX`；`M-XXX` 来源同源第二条默认追加不再询问 | **无存量差距**——放宽值域不会让已有条目失效 | 不适用 |

> **零迁移动作**：这是一次纯放宽。存量 `backlog.md` 无需改动，只需 frontmatter 的 `spec_version` 随下次写入自然更新。
> 之所以仍要 bump：`source_id` 白名单是硬校验规则，改它命中 `realign/bump-required-structure`；不 bump 则消费方无从判断某个 `M-XXX` 条目是合法还是脏数据。

## Realign 子流程

### 入口

- 主入口：由 `/pipeline realign` 编排调度。
- 底层直用：`/backlog --realign[=scope]`，scope ∈ {frontmatter / index / entries / status-fields}。

### 流程

```text
1. 加载当前 spec_version 常量 + Migration Matrix
     │
     ▼
2. 扫描 docs/devdocs/backlog.md
     │
     ▼
3. 按 Matrix 定位差距
     ├── additive：章节/字段/表头缺失
     └── restructuring：条目块结构不兼容
     │
     ▼
4. 差距清单展示（按 status 分组）
     │
     ▼
5. 用户确认（restructuring 逐项）
     │
     ▼
6. 补齐结构 + 追加 Change Log
     │
     ▼
7. 幂等校验
```

### 输出

- 补齐后的 `docs/devdocs/backlog.md`
- `## Change Log` 中的 realign 记录
- yaml-summary-v1 信封（details：`{from_spec, to_spec, additive_count, restructuring_count, scope, entries_affected}`）

### 约束

- 不新增 `B-XXX` 或任何 backlog 专属编号。
- 不修改原 `F/US/AC/T/INS/BUG/FR/NFR` 文件。
- 不把 `parked` 自动迁移为 `reactivated`、`closed` 或 `superseded`；realign 只补结构，不改业务状态。
- 不重算 `source_id + entry_no` 语义；发现重复锚点时返回 `partial` 并请求用户确认。
- 保留正文内容；只在结构字段缺失或格式不兼容时补齐。

