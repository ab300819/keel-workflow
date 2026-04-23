# system-design Realign 实例化

> 共享契约见 [../../pipeline/references/realign.md](../../pipeline/references/realign.md)。本文件只维护 system-design 自身的 spec_version 演进与差异矩阵。

## 当前 spec_version

**`design.v1`**（MVP 阶段，尚未发生首次 bump）

> 当 SKILL.md 强化"top-down L1~L4 + SOLID/LoD 校验表 + 设计边界自查"的改动被用户实际触发 realign 时，再统一 bump 到 `design.v2` 并填写下方 migration matrix。当前 `design.v1` 是起点定义，无需回填。

## Migration Matrix（spec_version 演进）

### v1 → v2（保留字段，未来启用）

触发条件：用户确认需要 bump 时，按以下模板补齐。

| 分级 | 变更项 | 修复动作 | 判据（如何识别缺失）|
|---|---|---|---|
| additive | （示例）§15 设计审查表新增「原则校验」三态字段 | 在审查表末尾追加列，空值填 `—` 待用户补齐 | 审查表列数 < 当前模板列数 |
| restructuring | （示例）§5 核心接口从"签名+描述"改为"签名+前置/后置/错误契约"三分 | 呈现 before/after → AskUserQuestion 用户确认后改写 | 接口块缺 `前置条件:` / `后置条件:` / `错误契约:` 字段 |

## Realign 子流程（`--realign[=scope]`）

### 输入

- 现有 `docs/devdocs/02-system-design*.md`（拆分文件全扫）
- 产物 frontmatter 的 `spec_version`（详见共享契约"向后兼容"章节）：
  - **阶段 1**（当前，尚无 frontmatter 元数据）：无字段 → 用户显式 `--realign` 视为对 legacy 全量扫描（按当前规范差距补齐）
  - **阶段 2**（加 frontmatter 之后）：无字段 → 标 `spec_version: legacy` → 由 ms-retrofit 首次迁移；已有 frontmatter 且落后 → 走 realign
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
- ✅ 如用户要求重新审查 → 提示运行 `/ms-system-design`（增量模式），而非扩大 realign 职责

## 与 system-design 其他模式的关系

| 模式 | 触发 | 产出 |
|---|---|---|
| 初始设计 | 02-system-design.md 不存在 | 完整 L1~L4 设计 |
| 增量设计 | 存在 + 未覆盖 F-XXX 或新 INS | 影响分析 + 修订清单 + 正文更新 |
| **Realign** | 存在 + spec_version 落后（或用户 `--realign`） | 差距补齐，**不触发** L1~L4 重做 |

> Realign 补齐的是"按新规范的结构/字段差距"；需求变更或设计方案调整仍属增量设计范畴，**不混用**。
