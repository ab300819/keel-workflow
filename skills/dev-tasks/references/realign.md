# dev-tasks Realign 实例化

> 共享契约见 [../../pipeline/references/realign.md](../../pipeline/references/realign.md)。

## 当前 spec_version

**`tasks.v2`**（2026-09-01：追溯约束由「必须 F+AC」放宽为「F+AC 或 CON」，非编码类任务不强制测试编号；任务卡新增可选 `superseded_by`）

## Migration Matrix（spec_version 演进）

### v1 → v2

| 分级 | 变更项 | 修复动作 | 判据 |
|---|---|---|---|
| — | **追溯约束放宽**：`F+AC` → `F+AC` 或 `CON-XXX`（制品型任务）| **无**——放宽不产生存量差距，既有任务全部仍合法 | 不适用 |
| — | 行为型任务才强制 `UT/IT/E2E`；TDD 引用 AC/测试编号仅适用 `TDD 模式 ≠ 不适用` | **无**——存量行为型任务判定完全不变 | 不适用 |
| additive | 任务卡属性表新增**可选** `superseded_by`（+ 标题 `⚠️ 已失效`）| 仅在 ADR 推翻决策时按「已知受影响制品」表回填；⛔ **不批量扫描存量任务卡**（谁失效需要语义判断）| 无判据——按需触发，不做全量检测 |

> **legacy 子分支（本次 bump 的兼容基石）**：存量文档**无 `CON` 行**时，消费方**只跳过 CON 子检查**，原有 F/US/AC 检查完整继续。
> ⛔ **不得整个维度 / 整个流程 skip**——那会把老项目的既有检查一并关掉，比不改更糟。
> 逐消费方的 legacy 行为见各自文件：[verify D1/D4](../../verify/SKILL.md)、[verify impl B1](../../verify/SKILL.md)、[test-cases](../../test-cases/SKILL.md)、[sync trace/audit](../../sync/references/)。

### v2 → v3（保留字段，未来启用）

| 分级 | 变更项 | 修复动作 | 判据 |
|---|---|---|---|
| additive | （示例）任务块新增 `design_ref` 字段（关联设计章节） | 追加字段；已有任务默认 `—`（依据关联 F/AC 自动建议） | 任务块缺 `design_ref:` |
| additive | （示例）任务分层标记枚举扩展（🔴🟡🟢⚪ → 新增 ⚫ 数据层） | 按现有任务属性自动分类；无法判定的标记"待确认" | 任务标记不在新枚举内 |
| restructuring | （示例）依赖关系从"纯文字描述"改为"结构化字段 `depends_on: [T-XX]`" | AskUserQuestion 逐任务呈现 before/after 确认 | 依赖字段格式不匹配 |

## Realign 子流程

### 入口

- 主入口：`/pipeline realign` 编排调度
- 底层：`/dev-tasks --realign[=scope]`，scope ∈ {layering / deps / design-ref / frontmatter}

### 流程

```text
1. 加载 spec_version 常量 + Matrix
     │
     ▼
2. 扫描 04-dev-tasks*.md（含拆分文件）
     │
     ▼
3. 定位差距
     ├── additive：字段/列缺失
     └── restructuring：依赖格式、分层枚举不兼容
     │
     ▼
4. 差距清单展示（按任务分组）
     │
     ▼
5. 用户确认（restructuring 逐项）
     │
     ▼
6. Edit 补齐 + 尾部 Realign Log
     │
     ▼
7. 幂等校验
```

### 输出

- 补齐后的 `04-dev-tasks*.md`
- `## Realign Log` 小节
- yaml-summary-v1（details：`{from_spec, to_spec, additive_count, restructuring_count, scope, tasks_affected}`）

### 约束

- ❌ 不新增/删除任务（那是初始/增量 dev-tasks 职责）
- ❌ 不改动任务"状态"字段（realign 不等于状态迁移）
- ❌ 不重算依赖拓扑（仅结构化补齐；语义未变时保留原依赖关系）
- ✅ 已完成任务的正文保留，仅补齐规范缺字段
- ✅ design_ref 建议值可基于关联 F/AC 自动推导，但必须由用户确认

## 与 dev-workflow --realign 的协同

dev-tasks --realign **只动文档**（任务清单），不动代码/测试。

如果新 spec_version 要求"已完成任务按新规范补齐证据"（如补 Phase 4 外审、补测试），由 `dev-workflow --all --realign` 在文档 realign 之后执行。
