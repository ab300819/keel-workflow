# PRD ↔ DevDocs Mapping 状态机与回扫责任

> 本 spec 收纳 `mapping_status`、`--from-prd` 和 `--back-propagate-prd` 的既有桥接规则，明确 PRD 不直接追代码。PRD 的责任到 DevDocs 映射为止，代码追溯属于 DevDocs 链路。

## 目标

- 显性化 `active / outdated / remapped / removed` 的语义、触发条件和责任方。
- 明确 `/ms-sync --back-propagate-prd` 能自动完成什么，不能自动完成什么。
- 建立 PRD 修订到 DevDocs drift 感知的最小链路，同时诚实标注未实现的自动语义 diff。

## 现状证据

| 机制 | 证据 | 状态 |
|---|---|---|
| mapping 表唯一位置 | `skills/ms-prd/references/prd-mapping-status.md:3`：唯一存储位置是 index.md 的 "DevDocs 映射" 章节 | [现状] |
| mapping 字段与状态全集 | `skills/ms-prd/references/prd-mapping-status.md:5-24`：列定义、状态枚举、authoritative row 规则 | [现状] |
| FR revise 写 outdated | `skills/ms-prd/SKILL.md` § --revise 模式：FR 已映射时将 `mapping_status` 置为 outdated，并链接 mapping 规范 | [现状] |
| `--from-prd` 消费与回写 | `skills/ms-requirements/SKILL.md` § --from-prd：读取 PRD index、处理 outdated、新增 FR、写回 mapping、remapped 保留历史 | [现状] |
| `--back-propagate-prd` 回扫 | `skills/ms-sync/SKILL.md` § --back-propagate-prd：对比 `01-requirements.md` 与 PRD mapping，废弃 F 标记 removed，只写映射状态不改 FR 内容 | [现状] |
| PRD/DevDocs 编号边界 | `skills/ms-prd/SKILL.md` § DevDocs 桥接：PRD 不分配 F/US/AC，FR/NFR 进入 DevDocs 后映射为 F-XXX | [现状] |

## 规则

### Mapping 状态全集

| 状态 | 语义 | 触发条件 | 写入方 | 下一步 |
|---|---|---|---|---|
| `active` | PRD FR/NFR 与 DevDocs F/FEAT 当前被认为一致 | 首次 `/ms-requirements --from-prd` 成功导入 | [现状] ms-requirements | 无需动作 |
| `outdated` | PRD FR/NFR 已修改，但对应 DevDocs 尚未更新 | `/ms-prd --revise` 修改已映射 FR/NFR | [现状] ms-prd | 运行 `/ms-requirements --from-prd` 或人工处理 |
| `remapped` | 已重新导入，DevDocs 对应内容已更新；旧行保留审计 | `/ms-requirements --from-prd` 处理 outdated 或重新导入 | [现状] ms-requirements | 以最后一行为 authoritative row |
| `removed` | 对应 DevDocs F/FEAT 已被移除或废弃 | `/ms-sync --back-propagate-prd` 检测到映射的 F 已不在 DevDocs 需求文件 | [现状] ms-sync | 人工判断 PRD 是否保留或修订 |

### Authoritative Row

[现状] 同一 `product_id` 可以保留多条映射历史，表中最后一条记录为权威行，旧行只作审计历史（`skills/ms-prd/references/prd-mapping-status.md:22-24`）。

[新增] 对状态解释时必须始终读取最后一条记录；不得因为旧行仍为 `active` 就忽略后续 `outdated/remapped/removed`。理由：现有规范已有 authoritative row 规则，但未把它写入各状态判定步骤。

## 回扫责任分界

| 场景 | 自动完成 | 必须人工 |
|---|---|---|
| PRD 修订后 DevDocs 过期 | [现状] `/ms-prd --revise` 把 mapping 置为 `outdated` | 决定是否立即运行 `/ms-requirements --from-prd`；确认需求语义是否仍成立 |
| `--from-prd` 重新导入 | [现状] 处理 outdated 时原地更新对应 F/US/AC，不创建新编号；追加 `remapped` 历史行 | 判断复杂拆分/合并场景是否需要新增 DevDocs 功能而非原地更新 |
| DevDocs 删除 F | [现状] `/ms-sync --back-propagate-prd` 标记 `mapping_status: removed` | 判断 FR 是否也应废弃、改写、迁移到新版 PRD 或保留为产品历史 |
| DevDocs 新增 F 无 PRD 来源 | [现状] `/ms-sync --back-propagate-prd` 标注“DevDocs 侧新增，无 prd 来源” | 是否补充 PRD、接受 DevDocs-only 需求、或启动 PRD 修订 |
| DevDocs 内容语义变化但编号仍存在 | [FUTURE] 当前无自动语义 diff | 人工审查 F/US/AC 是否偏离 PRD；必要时回写 mapping 或修订 PRD |

## 回扫算法

1. 定位 PRD requirements index：固定为 `docs/prd/requirements/index.md`（单需求脚手架，无跨需求选择）。
2. 读取 mapping 表并按 `product_id` 取最后一条 authoritative row。
3. 读取 DevDocs 需求文件中的当前 F/FEAT 列表。
4. 对每个 authoritative row 执行对比：目标 F/FEAT 存在则保持；目标不存在则追加 `removed` 行；DevDocs 中无 PRD 来源的新 F/FEAT 只报告，不自动创建 FR。
5. 写回时只修改 `## DevDocs 映射` 章节；不得改 FR 内容、不得重排其他章节。

## PRD 修订到 DevDocs Drift 链路

```text
FR/NFR 内容修订
  -> /ms-prd --revise 保持 product_id 不变
  -> requirements/index.md 的 DevDocs 映射置 outdated
  -> /ms-requirements --from-prd 读取 outdated
  -> 原地更新对应 F/US/AC 或追加新映射
  -> mapping_status 追加 remapped，最后一行成为 authoritative row
```

[现状] 上述链路中的状态写入和回写点已在 skill spec 中声明。

[FUTURE] 自动 Drift 检测只到“mapping_status 可报告”的层级；当前没有 PRD 内容和 DevDocs 内容的自动语义等价验证，也没有 PRD 直接追踪代码实现的机制。

## DevDocs 反向影响 PRD

### F 被删除

[现状] `/ms-sync --back-propagate-prd` 对比 PRD mapping 表和 `docs/devdocs/01-requirements.md` 的 F 列表；已映射但不存在的 F 标记为 `removed`。

处置边界：

- 自动：只更新 mapping 表。
- 人工：判断对应 FR/NFR 是否仍是产品需求。如果仍有效，应重新导入或在 DevDocs 恢复；如果不再有效，应考虑 FR revise 或在收尾时清理。

### F 被新增但没有 PRD 来源

[现状] 回扫只标注“DevDocs 侧新增，无 prd 来源”，不自动创建 FR。

[新增] 若团队要求所有正式功能都有 PRD 来源，应由人工补充 PRD 或在 DevDocs 明确记录豁免。理由：现有回扫能识别无来源 F，但没有规定是否必须补 PRD。

### F 被重命名或拆分

[FUTURE] 当前没有自动识别重命名/拆分的机制。应由人工决定：

- 原 FR 对应一个新 F：追加 `remapped`。
- 原 FR 拆成多个 F：保留历史行，新增多条映射行，并在备注中说明拆分。
- 多个 FR 合并成一个 F：需要用户确认，因为可能改变产品需求边界。

## 诚实边界

- [现状] PRD 不直接追代码，不维护代码位置、不承担测试覆盖验证。
- [现状] PRD 通过 `--from-prd` 把 FR/NFR 交给 DevDocs；之后的 F/US/AC、测试、任务和代码追溯由 DevDocs skill 负责。
- [FUTURE] 若未来需要 PRD 到代码的直连视图，应作为报告/查询能力建立在 DevDocs trace 之上，而不是让 PRD 文件直接写代码引用。

## 门控

- ⛔ 禁止继续：在 back-propagate 中改 FR 内容、把 `removed` 当作删除 PRD 文件。恢复方式：只写 mapping 表、保留文件并由用户确认后处理。
- ⚠️ 必须确认：F 删除导致 mapped FR 失去 DevDocs 目标、FR 拆分/合并到多个 F。恢复方式：用户确认保留/废弃/重映射策略。
- ℹ️ 建议：发现 DevDocs-only F 或 long-lived outdated mapping 时提示处理；不强制阻断 PRD 文档维护。

## 验证

- 状态全集验证：mapping 表只出现 `active/outdated/remapped/removed`。
- authoritative row 验证：同一 `product_id` 以最后一条记录作为当前状态。
- 回扫验证：`--back-propagate-prd` 只修改 `## DevDocs 映射` 章节，不重排其他章节，不改 FR 内容。
- 边界验证：PRD 文件中不出现代码路径追溯字段；代码追溯留在 DevDocs。
- [FUTURE] 内容漂移验证：如后续实现，应把语义 diff 报告为建议或阻塞项，不自动改写 PRD 业务内容。

## FAQ

### `outdated` 是否表示 DevDocs 一定错了？

不是。它只表示 PRD 已修订且 DevDocs 尚未通过桥接流程重新确认。是否需要改 DevDocs，仍需用户或 requirements 阶段确认。

### `removed` 是否要删除 FR 文件？

不删除。`removed` 表示 DevDocs 映射目标被移除，不等同于 PRD 需求失效。FR 是否保留是产品层判断。

### PRD 能不能直接写代码路径？

不能作为当前机制。PRD 阶段只对接 DevDocs mapping；代码路径、测试覆盖和实现状态由 DevDocs trace/sync 负责。

## Related Specs

- [prd-revision-policy.md](./prd-revision-policy.md)
- [prd-mapping-status.md](../prd-mapping-status.md)
- [ms-requirements --from-prd](../../../ms-requirements/SKILL.md)
- [ms-sync --back-propagate-prd](../../../ms-sync/SKILL.md)

## 可能的失败模式

1. `mapping_status` 是桥接信号，不是语义证明；`active` 仍可能存在未被发现的内容偏差。
2. `--back-propagate-prd` 当前只读 DevDocs 需求文件的 F 列表，无法识别 F 内容被大幅改写但编号仍保留的情况。
3. 多 FR 到多 F 的拆分/合并需要人工判断；若直接用最后一行覆盖，可能丢失历史映射语义。
4. PRD 不追代码是清晰边界，但用户可能期望从 PRD 直观看到实现状态；需要通过 DevDocs 报告满足，而不是污染 PRD。
