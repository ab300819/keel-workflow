# prd-brainstorm Realign 实例化

> 共享契约见 [../../pipeline/references/realign.md](../../pipeline/references/realign.md)。

## 当前 spec_version

**`fr.v1`**（FR/NFR 结构起点）

## Migration Matrix（保留字段）

### v1 → v2（未来启用）

| 分级 | 变更项 | 修复动作 | 判据 |
|---|---|---|---|
| additive | （示例）FR 条目新增"验收意图"字段 | 追加字段，空值 `—` | FR 块缺字段 |
| additive | （示例）NFR 分类枚举扩展 | 按现有内容建议分类，用户确认 | 分类不在新枚举 |
| restructuring | （示例）用户角色描述结构重排 | AskUserQuestion 逐项确认 | 字段格式不匹配 |

## Realign 子流程

入口：`/ms-prd-brainstorm --realign`，或 `/ms-pipeline realign` 编排调度。

流程：扫描 `docs/prd/<prd_id>/requirements/*.md`（legacy: `docs/prd/requirements/*.md`）→ 对照 Matrix → 补齐 → Realign Log。

## 约束

- ❌ 不重启头脑风暴流程（5W1H / 用户角色 / 旅程 / MoSCoW）
- ❌ 不修改 FR/NFR 编号
- ✅ 保留现有"开放问题"条目
