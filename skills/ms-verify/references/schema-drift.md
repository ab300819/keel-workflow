# `--schema-drift` 诊断模式

> 共享契约见 [../../ms-pipeline/references/realign.md](../../ms-pipeline/references/realign.md)。

## 职责

只读扫描所有 DevDocs 产物的 `spec_version` frontmatter 字段，对照各 skill `references/realign.md` 顶部"当前 spec_version"常量，输出结构化报告。**不触发 realign**，不修改任何文件。

## 扫描范围

| 产物 | 来源 skill | spec_version 常量位置 |
|---|---|---|
| `docs/devdocs/01-requirements.md`（含拆分文件） | ms-requirements | `skills/ms-requirements/references/realign.md` |
| `docs/devdocs/02-system-design*.md` | ms-system-design | `skills/ms-system-design/references/realign.md` |
| `docs/devdocs/03-test-*.md`（含 `03-test-cases.md` 与 `03-test-unit.md` / `03-test-integration.md` / `03-test-e2e.md` 拆分文件） | ms-test-cases | `skills/ms-test-cases/references/realign.md` |
| `docs/devdocs/04-dev-tasks*.md` | ms-dev-tasks | `skills/ms-dev-tasks/references/realign.md` |
| `docs/devdocs/05-insights.md` | ms-insights | `skills/ms-insights/references/realign.md` |
| `docs/devdocs/00-baseline.md` | ms-retrofit | `skills/ms-retrofit/references/realign.md` |
| `docs/devdocs/00-context.md` | ms-onboard | `skills/ms-onboard/references/realign.md` |
| `docs/prd/chunks/*.md` | ms-prd-parser | `skills/ms-prd-parser/references/realign.md` |
| `docs/prd/requirements/*.md` | ms-prd-brainstorm | `skills/ms-prd-brainstorm/references/realign.md` |

⛔ **`00-baseline.md` 只做结构性 drift 检测**（缺失章节 / frontmatter 字段），
realign **不得改写**其带 `用户确认` / `已有文档` / `推导待确认` 标注的正文——
那些内容问人和挖证据才得来，重生成产不出来。详见
[retrofit/references/realign.md](../../ms-retrofit/references/realign.md)。

**独立扫描（在主报告独立章节呈现，不并入 A/B 类产物主统计）**：
- `docs/codebase-insight.md` — 按其自有 `schema_version + commit_hash` 字段扫描（ms-codebase-insight 独立机制；判据：`schema_version` 不匹配 skill 常量或 `commit_hash` 与 git HEAD 不一致 = 需要重扫，由 ms-codebase-insight 自身处理，**不**纳入 realign 编排）

**特殊检测：ms-dev-workflow（无文档产物的证据链 drift）**：

dev-workflow 的产物是代码 + 证据链（AC 表、内审/外审记录、测试代码）而非 markdown 文档，**无 frontmatter 可扫**。其 spec drift 通过间接证据检测：

- 读取 `skills/ms-dev-workflow/references/realign.md` 顶部当前 `spec_version`（如 `devflow.v1`）
- 扫描 `04-dev-tasks*.md` 中"状态=已完成"任务是否含 `Realigned-From: <old_spec>` 尾注
- 若当前 `spec_version` 有效且任务无 `Realigned-From` 尾注 → 视为"可能需要 realign"（态：`drift`，详因由 dev-workflow 自身 Step 1.5 + Migration Matrix 最终判定）
- 若当前 `spec_version` 是 `devflow.v1`（首版，无前置版本）→ 所有已完成任务视为 `current`（无历史可 drift）

报告时 dev-workflow 产物以任务粒度统计（例：`T-01 ~ T-12 中 3 个任务疑似 drift`），建议动作为 `/ms-dev-workflow <task-id> --realign` 或 `/ms-pipeline realign`。

**判据精确性局限**：上述检测为启发式（基于尾注存在性），实际 drift 最终由 `ms-dev-workflow --realign` 子流程的证据复核判定。`--schema-drift` 只做"建议性"标记，不作为阻断依据。

## 输出三态

| 状态 | 判据 | 示例 |
|---|---|---|
| **current** | `spec_version` 字段存在且等于当前常量 | `design.v1 == design.v1` → current |
| **drift** | `spec_version` 字段存在但落后 | `design.v1 < design.v2` → drift |
| **legacy** | 无 `spec_version` 字段 | 旧产物未迁移，建议 `/ms-retrofit` 首次化 |

## 报告格式

```markdown
# Schema Drift Report

生成时间: 2026-04-23T10:30:00+08:00

## 总览

| 状态 | 产物数 |
|---|---|
| current | 5 |
| drift | 2 |
| legacy | 1 |

## 详情

### Drift 产物（需要 realign）

| 产物 | 当前 spec_version | 目标 spec_version | 建议动作 |
|---|---|---|---|
| docs/devdocs/02-system-design.md | design.v1 | design.v2 | /ms-pipeline realign 或 /ms-system-design --realign |

### Legacy 产物（需要首次迁移）

| 产物 | 建议动作 |
|---|---|
| docs/devdocs/01-requirements-legacy.md | /ms-retrofit |

### ms-codebase-insight（独立）

| 状态 | commit_hash |
|---|---|
| schema_version=1 / commit_hash=abc1234（匹配 HEAD） | current |
```

## 权重与阻塞性

- `--schema-drift` 作为**诊断模式**，不阻塞任何下游流程
- ms-sync 的 health report 可选择性合并 drift 列（权重低，见 `skills/ms-sync/`）
- 不与 `--docs` / `--impl` / `--ui` 的主流程判定耦合

## 实现约束

- ❌ 只读，不写任何文件
- ❌ 不触发 realign 或 retrofit（只报告）
- ❌ 不调用其他 skill 的 realign 子流程
- ✅ 输出可独立保存到 `docs/devdocs/schema-drift-report.md`（可选，由用户决定）
- ✅ yaml-summary-v1 信封：details 含 `{current_count, drift_count, legacy_count, drift_items, legacy_items}`
