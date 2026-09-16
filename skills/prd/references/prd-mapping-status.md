# PRD ↔ keel 映射状态规范

映射表唯一存储位置：`index.md` 的"keel 映射"章节。

## 列定义

| 列 | 说明 |
|----|------|
| `product_id` | FR-XX / NFR-XX |
| `devdocs_id` | F-XXX |
| `mapping_status` | `active` / `outdated` / `remapped` / `removed` |
| `mapped_at` | 首次映射时间 |
| `remapped_at` | 重新映射时间（仅 remapped 时有值）|

## 状态枚举

- `active`：FR 与 F 内容一致（由 requirements --from-prd 在导入成功时写入）
- `outdated`：FR 已修改但 F 未更新（由 prd --revise 在修改 FR 内容时写入）
- `remapped`：FR 重新导入后 F 已更新（由 requirements --from-prd 在重新导入时写入）
- `removed`：对应 F-XXX 已从 keel 移除（由 sync --back-propagate-prd 在检测到废弃时写入）

## authoritative row

同一 `product_id` 存在多条映射历史时，以表中最后一条记录为准。旧行仅作审计历史，不删除。
