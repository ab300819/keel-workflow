# PRD 全局编号 SSOT

> 本 spec 收纳 PRD 阶段 FR/NFR 编号的既有规则，明确 `docs/prd/index.md` 的权威边界。它不新增命令，也不把 DevDocs 的 layout/id/trace 版本体系复制到 PRD。

## 目标

- 明确 `docs/prd/index.md` 是 PRD 阶段 FR/NFR 编号、PRD 清单和生命周期状态的唯一权威源。
- 统一多 PRD 场景下的编号续编、范围登记、冲突检测和失败处置。
- 明确 PRD `FR-XXX/NFR-XXX` 与 DevDocs `F-XXX/FEAT-XXX` 的关系是映射，不是同号继承。

## 现状证据

| 机制 | 证据 | 状态 |
|---|---|---|
| 全局 index 作为 multi-PRD 判定入口 | `skills/prd/SKILL.md:64-72`：存在 `docs/prd/index.md` 且含 PRD 清单表时进入 multi-PRD；新建 PRD 时读取全局 index 编号注册表获取 `fr_start/nfr_start` | [现状] |
| 编号分配职责链 | `skills/prd/SKILL.md:72-74`：ms-prd 取起始编号，传给 parser，parser 续编，brainstorm 沿用 chunk 编号 | [现状] |
| 全局索引模板 | `skills/prd/templates/global-index-template.md:1-26`：包含 PRD 清单、状态枚举、编号注册表和“FR/NFR 编号全局唯一，新 PRD 从最大值续编” | [现状] |
| parser 入参和续编 | `skills/prd-parser/SKILL.md:58-62`、`skills/prd-parser/SKILL.md:111-113`：由 ms-prd 传入 `fr_start/nfr_start`，multi-PRD 从该值续编 | [现状] |
| brainstorm 编号规则 | `skills/prd-brainstorm/SKILL.md:216-222`：FR/NFR 为产品阶段全局唯一标识，multi-PRD 起始值来自全局注册表 | [现状] |
| DevDocs 边界 | `skills/prd/SKILL.md:303-305`：PRD 不分配 F/US/AC，FR/NFR 进入 DevDocs 后映射为 F-XXX | [现状] |

## 规则

### 1. SSOT 声明

[现状] `docs/prd/index.md` 是 PRD 阶段以下信息的唯一权威源：

- PRD 清单：`prd_id`、标题、状态、FR 范围、NFR 范围、迭代关系、日期。
- 编号注册表：每个 PRD 已占用的 FR/NFR 范围及状态。
- PRD 生命周期状态：`active / superseded / archived`。

[现状] per-PRD `docs/prd/<prd_id>/requirements/index.md` 只保存本 PRD 的总纲、需求清单、DevDocs 映射和全局 index 字段的只读镜像。`skills/prd/templates/requirements-index-template.md:7-9` 已声明 `prd_status/supersedes` 的 source of truth 在全局 index。

### 2. 唯一键定义

[现状] PRD 阶段的唯一键是完整 `product_id`，即带前缀的 `FR-XXX` 或 `NFR-XXX`，不是 `(prd_dir, fr_id)` 复合键。

- `prd_dir/prd_id` 是 ownership 元数据，用于定位和生命周期管理。
- 同一个 `FR-005` 不得被两个 PRD 同时拥有，即使它们位于不同目录。
- `FR-005` 与 `NFR-005` 是不同 `product_id`，但都必须登记在同一个全局编号注册表中。

### 3. 编号范围分配

[现状] 默认策略是“最大值续编”，不是固定 100 段预分配。

```text
已有编号注册表：
  PRD-A: FR-001~FR-014, NFR-001~NFR-003

新建 PRD-B：
  fr_start = FR-015
  nfr_start = NFR-004
  parser/brainstorm 完成后写回实际占用范围，如 FR-015~FR-021, NFR-004~NFR-005
```

[新增] 全局 index 中的“FR 范围 / NFR 范围”按实际占用结果登记；只有在用户明确要求预留编号时，才允许登记未完全使用的预留范围，并必须在状态/备注中标明 `reserved`。理由：现有模板已有范围字段，但没有说明预留语义；补齐后可避免把空洞误判为已生成需求。

### 4. 跨 PRD 引用规则

[新增] 另一个 PRD 可以引用 `FR-005`，但必须写成“引用关系”，不能重新声明 ownership。

- 推荐写法：`引用: FR-005 (owner: 20260518-prd-a)`。
- 引用方不得在自己的编号范围内登记 `FR-005`。
- 被引用 FR 修订时，引用方不会自动同步；是否需要生成新 PRD 或更新引用，由用户确认。

理由：现有机制定义了全局唯一编号，但没有明确跨 PRD 引用是否合法；允许只读引用比禁止引用更贴合产品需求之间的依赖表达，同时不破坏 SSOT。

### 5. 与 DevDocs F-XX 的边界

[现状] `FR-005 -> F-005` 不是同号规则，而是映射结果。

- PRD 阶段只拥有 `FR/NFR`。
- DevDocs 阶段拥有 `F/US/AC` 或 layout.v2 [FUTURE] 的 `FEAT/STORY/AC`。
- `FR-005` 可以映射到 `F-001`、`F-005` 或其他编号；编号是否相同不构成合同。
- 映射状态由 per-PRD `requirements/index.md` 的 `## DevDocs 映射` 章节记录，详见 `skills/prd/references/prd-mapping-status.md:3-24`。

## 冲突检测算法

### 触发时机

- [现状] 新建 PRD 前：ms-prd 读取全局编号注册表以取得 `fr_start/nfr_start`（`skills/prd/SKILL.md:72-74`）。
- [现状] parser/brainstorm 输出前：按上游起始值续编，不从 01 起始（`skills/prd-parser/SKILL.md:111-113`、`skills/prd-brainstorm/SKILL.md:216-222`）。
- [FUTURE] 写回全局 index 前：执行显式冲突检测并输出冲突报告。当前 skill spec 已声明编号来源，但没有独立 runtime lint 或自动修复实现。

### 检测输入

1. `docs/prd/index.md` PRD 清单和编号注册表。
2. 当前 PRD 本次计划写入的 `product_id` 列表。
3. 当前 PRD 实际输出目录中的 `requirements/FR-*`、`requirements/NFR-*` 文件名和 frontmatter `id`。

### 检测项

| 检测项 | 规则 | 失败处置 |
|---|---|---|
| `prd_id` 唯一 | `docs/prd/<prd_id>/` 和 `_archived/<prd_id>/` 不能已有同名 active/superseded owner | ⛔ 禁止继续：改用同日 `-2/-3` 后缀或由用户确认 supersede |
| 范围重叠 | 同前缀范围不得与任何已登记范围重叠（active/superseded/archived/reserved 均不可复用） | ⛔ 禁止继续：修正全局 index 或改用下一个可用编号 |
| 实际 ID 重复 | 本次输出的 `product_id` 不得已被其他 PRD 登记 | ⛔ 禁止继续：停止写回，重新从全局最大值续编 |
| 文件名/frontmatter 不一致 | `FR-005-*.md` 的 frontmatter `id` 必须为 `FR-005` | ⛔ 禁止继续：修正文件或 frontmatter 后重试 |
| 已归档范围复用 | archived PRD 的编号不可复用 | ⛔ 禁止继续：编号一旦分配不可复用，恢复方式是选择新编号 |

## 门控

- ⛔ 禁止继续：发现重复 `product_id`、范围重叠、frontmatter/file id 不一致。恢复方式：修正全局 index 或本次输出编号后重新检测。
- ⚠️ 必须确认：用户要求预留编号范围、跨 PRD 引用被修订项、或 legacy 单 PRD 迁移到 multi-PRD。恢复方式：用户确认 owner 和编号策略。
- ℹ️ 建议：编号范围存在空洞但无冲突时，不阻断；建议在全局 index 备注原因。

## 验证

- 文件检查：确认新增或修改的 PRD 文件使用全局 index 分配的 `FR/NFR` 起始值。
- 表格检查：确认 `docs/prd/index.md` 的 PRD 清单和编号注册表状态同步。
- 映射检查：确认 per-PRD `requirements/index.md` 的 `DevDocs 映射` 不被当作编号 SSOT。
- [FUTURE] 自动检查：可由后续 `ms-verify` 类能力读取全局 index 并执行本 spec 的冲突检测；当前不新增命令。

## FAQ

### 为什么不用 `FR-001~099` 固定分段？

现有证据指向最大值续编：`global-index-template.md:19` 和 `ms-prd/SKILL.md:66` 都写的是读取最大编号/起始值。固定分段会制造大量未使用编号，且不是现状机制。

### `FR-005` 能否被另一个 PRD 复用？

不能复用为 owner。可以只读引用，但引用方必须写明 owner，不得登记到自己的编号范围。

### `FR-005` 是否必须映射为 `F-005`？

不必须。`FR` 是产品阶段编号，`F/FEAT` 是 DevDocs 阶段编号；两者通过 mapping 表连接。

## Related Specs

- [prd-revision-policy.md](./prd-revision-policy.md)
- [prd-devdocs-mapping.md](./prd-devdocs-mapping.md)
- [prd-mapping-status.md](../prd-mapping-status.md)
- [global-index-template.md](../../templates/global-index-template.md)
- [requirements-index-template.md](../../templates/requirements-index-template.md)

## 可能的失败模式

1. 当前仓库没有实际 `docs/prd/index.md` 样例，规则主要基于 skill spec 和模板；真实数据迁移时可能暴露未覆盖的历史格式。
2. “最大值续编”在并发运行两个 `/ms-prd` 会话时可能竞争；当前 spec 未定义锁文件或事务机制，需由操作者避免并发写入。
3. 跨 PRD 引用规则是 [新增] 边界声明，当前没有 runtime 检查引用 owner 是否存在。
4. 预留范围是 [新增] 可选语义，若滥用会让编号表出现大量空洞，降低可读性。
