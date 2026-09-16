# system-design Realign 实例化

> 共享契约见 [../../pipeline/references/realign.md](../../pipeline/references/realign.md)。本文件只维护 system-design 自身的 spec_version 演进与差异矩阵。

## 当前 spec_version

**`design.v3`**（2026-09-01：推翻 / 取代类 ADR 新增 `取代` + `已知受影响制品` 两必填字段）

## Migration Matrix（v2 → v3）

| 分级 | 变更项 | 修复动作 | 判据 |
|---|---|---|---|
| additive | **推翻 / 取代类 ADR** 新增 `取代` + `已知受影响制品` 表（三跳检索产生范围）| ⛔ **不回溯补填历史 ADR**——当时的受影响范围已无法可靠重建，硬填会产生假证据。仅对**新增**的推翻类 ADR 强制 | ADR 状态为「已取代」但无 `取代` 字段 → ℹ️ **仅提示，不阻断** |
| — | 普通选型 ADR **不填**上述两字段 | **无**——这是防止必填仪式的唯一闸门 | 不适用 |
| — | 覆盖门对 `CON-XXX` 输出 `N/A（制品型）` | **无**——旧文档无 CON 则不触发 | 不适用 |
| — | 增量设计检查清单删除一处重复行（「已自动扫描」/「已自动识别」受影响文档）| **无**——纯去重，语义不变 | 不适用 |

> **legacy 子分支（本次 bump 的兼容基石）**：存量文档**无 `CON` 行**时，消费方**只跳过 CON 子检查**，原有 F/US/AC 检查完整继续。
> ⛔ **不得整个维度 / 整个流程 skip**——那会把老项目的既有检查一并关掉，比不改更糟。
> 逐消费方的 legacy 行为见各自文件：[verify D1/D4](../../verify/SKILL.md)、[verify impl B1](../../verify/SKILL.md)、[test-cases](../../test-cases/SKILL.md)、[sync trace/audit](../../sync/references/)。

## Migration Matrix（v1 → v2，历史）

> v1 阶段累积的 SKILL.md 强化（top-down L1~L4 / SOLID·LoD 校验表 / 设计边界自查）**不产生存量差距**（改的是产出方法，不是产物必填章节），随本次 bump 一并归入 v2，无独立修复动作。

## Migration Matrix（spec_version 演进）

### v1 → v2

| 分级 | 变更项 | 修复动作 | 判据（如何识别缺失）|
|---|---|---|---|
| additive | **§0 摘要**：文档顶部新增人读摘要节（要解决什么 / 怎么解决 / 定了哪些方向 / 还没定的 / 最可能后悔的地方） | 由现有正文 + ADR 节推导生成，落 `推导待确认`；「最可能后悔的地方」推不出时留空并提示用户补 | 文档无 `## 0. 摘要` 标题 |
| — | 确认时机改为按「有没有岔路」判定（原：L1~L4 每层独立确认 + 无判据的「快速档」） | **无**——改的是产出过程，已完成文档无结构差距 | 不适用 |
| — | agent 自查产物（模块划分 / 接口概要 / 数据模型 / 原则校验 / 对抗审查）移出确认界面 | **无**——这些本就写入文档，位置未变 | 不适用 |

## Realign 子流程（`--realign[=scope]`）

### 输入

- 现有 `docs/devdocs/02-system-design*.md`（拆分文件全扫）
- 产物 frontmatter 的 `spec_version`（详见共享契约"向后兼容"章节）：
  - **阶段 1**（当前，尚无 frontmatter 元数据）：无字段 → 用户显式 `--realign` 视为对 legacy 全量扫描（按当前规范差距补齐）
  - **阶段 2**（加 frontmatter 之后）：无字段 → 标 `spec_version: legacy` → 由 retrofit 首次迁移；已有 frontmatter 且落后 → 走 realign
- 可选 scope：`layer1` / `layer2` / `layer3` / `layer4` / `<section-name>`

### 流程

```text
1. 读取现有设计 + 本 skill 当前 spec_version 常量
     │
     ▼
2. 对照 Migration Matrix 扫描差距
     ├── additive 项 → 直接补齐草案
     └── restructuring 项 → 呈现 before/after 逐项确认
     │
     ▼
3. 差距清单展示（含分级统计）
     │
     ▼
4. 用户确认（⚠️ restructuring 项必须逐项 apply）
     │
     ▼
5. Edit 补齐 → 文档尾部追加 Realign Log 小节
     │
     ▼
6. 幂等校验：二次运行无新差距 = no-op
```

### 输出

- 补齐后的设计文档（结构保留，仅 append/restructure 差距项）
- 产物尾部 `## Realign Log` 新增一行（格式见共享契约）
- yaml-summary-v1 信封（status / summary.headline / summary.details.{from_spec,to_spec,additive_count,restructuring_count,scope}）

### 约束

- ❌ 不删除现有章节（除非 restructuring 且用户逐项确认）
- ❌ 不重新运行 L1~L4 分层设计交互（那是初始/增量模式的职责）
- ❌ 不覆盖 ADR 原有记录（只追加"realign 原因" ADR 条目）
- ✅ 所有原则校验、设计审查结论如果**按新规范缺字段**则 additive 补齐，不重跑 L3 边界自查
- ✅ 如用户要求重新审查 → 提示运行 `/system-design`（增量模式），而非扩大 realign 职责

## 与 system-design 其他模式的关系

| 模式 | 触发 | 产出 |
|---|---|---|
| 初始设计 | 02-system-design.md 不存在 | 完整 L1~L4 设计 |
| 增量设计 | 存在 + 未覆盖 F-XXX 或新 INS | 影响分析 + 修订清单 + 正文更新 |
| **Realign** | 存在 + spec_version 落后（或用户 `--realign`） | 差距补齐，**不触发** L1~L4 重做 |

> Realign 补齐的是"按新规范的结构/字段差距"；需求变更或设计方案调整仍属增量设计范畴，**不混用**。
