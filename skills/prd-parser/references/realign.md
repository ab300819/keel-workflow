# prd-parser Realign 实例化

> 共享契约见 [../../pipeline/references/realign.md](../../pipeline/references/realign.md)。

## 当前 spec_version

**`chunk.v1`**（chunk 结构起点）

## Migration Matrix（保留字段）

### v1 → v2（未来启用）

| 分级 | 变更项 | 修复动作 | 判据 |
|---|---|---|---|
| additive | （示例）chunk frontmatter 新增 `initial_classification` 字段 | 追加字段；已有 chunk 默认 `—` | frontmatter 缺字段 |
| restructuring | （示例）指纹计算规则变更（影响已有 fingerprint） | 必须用户确认；重算 fingerprint 并在 chunk 尾部追加"fingerprint-rehash" 尾注 | 指纹算法版本不匹配 |

## Realign 子流程

入口：`/prd-parser --realign`，或 `/pipeline realign` 编排调度。

流程：扫描 `docs/prd/source/` 与 `docs/prd/chunks/` → frontmatter/分段字段差距 → additive 补齐 / restructuring 逐项确认 → Realign Log。

## 约束

- ❌ 不重新切分 PRD（chunk 边界保持）
- ❌ 不修改 chunk 正文（仅 frontmatter/元数据结构补齐）
- ✅ fingerprint 算法变更触发的 rehash 必须用户确认，并保留旧值于尾注
