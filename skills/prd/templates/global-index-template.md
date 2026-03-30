# PRD 全局索引

## PRD 清单

| prd_id | 标题 | 状态 | FR 范围 | NFR 范围 | 迭代自 | superseded_by | 创建日期 | 归档日期 |
|--------|------|------|---------|----------|--------|---------------|----------|----------|
| {{prd_id}} | {{标题}} | active | FR-XX~YY | NFR-XX~YY | — | | YYYY-MM-DD | |

**状态枚举**：active / superseded / archived

**supersedes 链不变式**：
- 禁止自指和环
- 每个 PRD 最多一个 `supersedes` 目标（记录在「迭代自」列）
- 写入 supersedes 时同步回填旧 PRD 的 `superseded_by`
- 仅 `active` 状态的 PRD 允许被 supersede

## 编号注册表

> FR/NFR 编号全局唯一，新 PRD 从最大值续编。ms-prd 编排层在调用 parser 前查询此表获取起始编号。

| 编号范围 | 所属 PRD | 状态 |
|----------|----------|------|
| FR-XX~YY | {{prd_id}} | active |
| NFR-XX~YY | {{prd_id}} | active |

**状态与 PRD 清单同步**：PRD 归档时，对应编号范围状态同步标记为 archived。
