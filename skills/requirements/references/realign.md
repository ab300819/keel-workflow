# requirements Realign 实例化

> 共享契约见 [../../pipeline/references/realign.md](../../pipeline/references/realign.md)。

## 当前 spec_version

**`req.v3`**（2026-09-08：§2 功能点表新增「归属里程碑」列；新增 `## 2.5 里程碑（可选）` 章节）

## Migration Matrix（spec_version 演进）

### v1 → v2

| 分级 | 变更项 | 修复动作 | 判据（如何识别缺失）|
|---|---|---|---|
| restructuring | **§6 非功能性需求**：三张散文表 / bullet → 编号表 `编号/类别/约束/验证方式/档/状态` | AskUserQuestion 逐条呈现 before/after；每条散文项转一行 `CON-XXX`。**「验证方式」推不出时填 `—` 并标 `推导待确认`，⛔ 不自动编造**（沿用 `design.v2` §0 做法）| §6 标题为「非功能性需求」，或其下无 `CON-` 编号 |
| additive | **§5.3 约束 → 任务**段（追溯矩阵新增，`CON → T`）| 由 §6 与 04 任务卡的关联反推；无关联的 CON 留空待补 | §5 无「约束 → 任务」小节 |
| additive | §5.1 概览表新增「约束（CON）」行 | 计数填入 | 概览表无该行 |
| additive | `needs review` 条目新增 `归属` / `关闭条件` / `提出` 三必填字段 | 逐条 AskUserQuestion 补；⛔ **不猜归属人，也不用文件 mtime 顶替 `提出` 日期**（那会让报龄失真）| 条目缺任一字段 |
| — | 发布合规清单（`references/release-compliance.md`）两级触发 | **无**——按需加载，不产生存量结构差距 | 不适用 |

> **legacy 子分支（本次 bump 的兼容基石）**：存量文档**无 `CON` 行**时，消费方**只跳过 CON 子检查**，原有 F/US/AC 检查完整继续。
> ⛔ **不得整个维度 / 整个流程 skip**——那会把老项目的既有检查一并关掉，比不改更糟。
> 逐消费方的 legacy 行为见各自文件：[verify D1/D4](../../verify/SKILL.md)、[verify impl B1](../../verify/SKILL.md)、[test-cases](../../test-cases/SKILL.md)、[sync trace/audit](../../sync/references/)。

### v2 → v3

| 分级 | 变更项 | 修复动作 | 判据 |
|---|---|---|---|
| additive | **§2 功能点表新增「归属里程碑」列**（位于「优先级」与「来源」之间）| 追加列，**存量行一律填 `—`** | §2 表头无「归属里程碑」 |
| additive | **新增 `## 2.5 里程碑（可选）`** 章节 | ⚠️ 必须确认：问用户「剩余未做的功能要不要分段交付」。答「不分」→ ⛔ 不建表，归属列保持全 `—`，迁移到此结束 | 无 `## 2.5` 且用户未答过 |

> **迁移铁律（本次 bump 的兼容基石）**：
>
> - ⛔ **不自动划 M**。归属列一律 `—`，里程碑表**零 M 时不建**。里程碑是人按需求规模决定的产品切片，⛔ 不得从优先级、依赖、模块归属推断——那是「推导出没人决定过的结论」。
> - ⛔ **不回溯补划**。已完成的 F 永远填 `—`。用户想用里程碑时，只对**剩余未做的 F** 划段。
> - legacy 子分支：存量文档归属列全 `—` 或整列缺失时，`dev-workflow` **不分段**，行为与 v2 完全一致；⛔ 不得因此跳过其他检查。

## Realign 子流程

### 入口

- **用户面唯一入口**：`/pipeline realign --scope=spec`（内部委托本 skill 的子动作）
- 底层子动作（**编排实现细节，⛔ 不作为用户面命令暴露**，见 [constraints.md](../../shared/constraints.md) `realign/no-direct-user-call`）：`--realign[=scope]`，scope ∈ {features / stories / ac / trace / **con** / **milestone** / needs-review}

> `con` 子动作即 §6 散文 → `CON-XXX` 编号表的迁移（v1→v2 的 restructuring 行）。
> `milestone` 子动作即 §2 归属列 + §2.5 章节的补齐（v2→v3 两行）；用户答「不分段」时该子动作为空操作。
> 原枚举写的是 `nfr`，**此前无实体**；本次落地时随编号命名一并改为 `con`。

### 流程

```text
1. 加载当前 spec_version 常量 + Migration Matrix
     │
     ▼
2. 扫描 01-requirements.md（含拆分文件）
     │
     ▼
3. 按 Matrix 定位差距
     ├── additive：章节/字段缺失
     └── restructuring：结构不兼容
     │
     ▼
4. 差距清单展示（按章节分组）
     │
     ▼
5. 用户确认（restructuring 逐项）
     │
     ▼
6. Edit 补齐 + 尾部追加 Realign Log
     │
     ▼
7. 幂等校验
```

### 输出

- 补齐后的 `01-requirements.md`
- `## Realign Log` 小节（格式见共享契约）
- yaml-summary-v1 信封（details：`{from_spec, to_spec, additive_count, restructuring_count, scope}`）

### 约束

- ❌ 不触发新一轮 Inversion gate（需求假设挑战）— 那是初始模式职责
- ❌ 不修改已确认的 F/US/AC 编号
- ❌ 不重算追溯矩阵语义（仅补齐列结构）
- ✅ 已有内容一律保留；realign 只做"按新规范的结构/字段差距"补齐

## 与其他模式边界

| 模式 | 触发 | realign 职责 |
|---|---|---|
| 初始 | 无 01-requirements.md | 不适用 |
| 增量 | 新增 F/US/AC | 不适用（由增量模式处理） |
| `--context` | 补充背景 | 不适用 |
| `--from-prd` | 消费 PRD 包 | 不适用（PRD 自有映射机制） |
| **Realign** | spec_version 落后 | 按规范结构差距补齐，**不新增/修改业务内容** |
