# backlog Realign 实例化

> 共享契约见 [../../ms-pipeline/references/realign.md](../../ms-pipeline/references/realign.md)。

## 当前 spec_version

**`backlog.v1`**（MVP 起点，集中索引 + source_id/entry_no 局部锚点）

## Migration Matrix（spec_version 演进）

### v1 → v2（保留字段，未来启用）

| 分级 | 变更项 | 修复动作 | 判据 |
|---|---|---|---|
| additive | （示例）条目新增 `reactivation_criteria` 结构化字段 | 从正文 `#### Reactivation Criteria` 摘要为字段；无法判断则留空并标记待确认 | parked 条目缺 `reactivation_criteria` |
| additive | （示例）Index 新增 `superseded` 统计列 | 在 Index 表补列并从 Entries 重建统计 | Index 表头缺目标列 |
| restructuring | （示例）条目 frontmatter 从 fenced YAML 改为 HTML 注释块 | AskUserQuestion 展示 before/after，逐条确认后改写 | 条目块格式与当前模板不兼容 |

## Realign 子流程

### 入口

- 主入口：由 `/ms-pipeline realign` 编排调度。
- 底层直用：`/ms-backlog --realign[=scope]`，scope ∈ {frontmatter / index / entries / status-fields}。

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

