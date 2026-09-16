# Realign 共享契约（规范升级回扫）

> 用户面向入口：`/pipeline realign`（推荐）/ `/feature <F-XX> realign` / `/bugfix <BUG-XX> realign`。底层 `--realign` flag 是实现细节，**由编排层自动调度**。

## 目录

- 定位
- 用户入口（只需记住 2 个命令）
- 编排层职责（`pipeline realign`）
- A/B 类 skill 的 realign 子流程骨架
- spec_version 规则
- 向后兼容（无元数据的旧产物）
- Dry-run 样例（首次调用 vs 二次调用）
- realign-log 格式
- 安全不变量（realign 必须遵守）
- 一次性升级提示（阶段 3）
- health drift 探针（阶段 3，与 schema drift 并列但语义不同）
- 与 retrofit 的边界
- 与 codebase-insight 的关系

## 定位

**realign = policy re-evaluation**：keel 规范升级后，让已完成的产物/任务按新规范"查漏补缺"。与 `dev-workflow` 的"中断续做（execution resume）"**语义不同**，不可混用。

| 维度 | 续做（resume）| realign |
|---|---|---|
| 触发 | 流程中断未闭环 | 规范升级后想对齐 |
| 输入 | 任务未完成 | 任务已完成但按旧规范 |
| 输出 | 恢复执行到完成 | 追加差距补齐 + realign-log |
| 证据 | 首次生成完整证据 | 保留原证据，**不作废** |

## 用户入口（只需记住 2 个命令）

```bash
# 整仓对齐（推荐日常）
/pipeline realign                     # 扫描全部产物 → 调度各 skill 补齐 → 汇总
/pipeline realign --dry-run           # 只出报告，不动文件

# 定向对齐
/feature F-01 realign                 # 只对齐 F-01 关联产物
/bugfix BUG-05 realign                # 只对齐 BUG-05 关联产物
```

底层 `--realign` 仅用于调试或编排层内部调用：`/system-design --realign=layer3-only`、`/dev-workflow T-03 --realign`。

### scope 专用执行接口

| scope | 入口 | 执行接口文件 | 定位 |
|-------|------|-------------|------|
| `spec` | `/pipeline realign --scope=spec` | 沿用本文 § "编排层职责" + 各 skill `references/realign.md` | spec_version 差距补齐 |
| `prd-mapping` | `/pipeline realign --scope=prd-mapping` | 沿用 `skills/prd/references/governance/prd-devdocs-mapping.md` | PRD ↔ keel 映射对齐 |
| `health` | `/pipeline realign --scope=health` | [realign-scope-health.md](realign-scope-health.md) | 文档健康度主动审查（结构 / 索引 / 过大 / SSOT）|

## 编排层职责（`pipeline realign`）

1. **扫描**：读取 `docs/devdocs/` 所有产物 frontmatter 的 `spec_version`（阶段 2 后生效）；阶段 1 无元数据时视为"用户显式触发即视为需对齐"。
2. **分组**：按 A 类（keel 主链路产物）与 B 类（PRD 流程 / insights / onboard）分别分组差距项，总览报告两段呈现。
3. **调度**：按三段式顺序依次调用底层 `--realign`（上游 → 主链路 → 旁路）：
   ```
   Phase 1（B 类上游，若文件存在）:
     prd-parser → prd-brainstorm
   Phase 2（A 类 keel 主链路）:
     requirements → system-design → test-cases → dev-tasks → dev-workflow
   Phase 3（B 类旁路，若文件存在）:
     insights → onboard → backlog（仅当 docs/devdocs/backlog.md 存在）→ retrofit（仅当 docs/devdocs/00-baseline.md 存在，见「与 retrofit 的边界」）
   ```
   每阶段补齐作为下一阶段 context。B 类为可选（根据文件存在性判断是否调用）。
4. **汇总**：yaml-summary-v1 信封汇总各子 skill 的 `summary.details`，向用户呈现"N 个产物、M 个任务、K 处差距补齐"。
5. **幂等**：二次运行无新差距即 no-op。

## A/B 类 skill 的 realign 子流程骨架

所有支持 realign 的 skill 按同一骨架运行（由各 skill 的 `references/realign.md` 实例化）：

```
1. 加载本 skill 的 spec_version 当前常量（见各 skill references/realign.md 顶部"当前 spec_version"小节）
2. 对照产物 frontmatter.spec_version（阶段 1 无 frontmatter → 显式 --realign 时按 legacy 全量扫描；阶段 2 起无字段 → legacy 归 retrofit）
3. 按 skill 自身的 diff matrix（references/realign.md 维护）定位差距
4. 输出差距清单，分两级：
     - additive     → 规范新增的必填章节/字段，可直接补齐追加
     - restructuring → 产物结构不兼容，必须 AskUserQuestion 用户逐项确认
5. 执行补齐：
     - additive 项：直接 Edit 补齐
     - restructuring 项：呈现 before/after 草案 → 用户确认 → Edit
6. 在产物尾部追加 realign-log 小节（见下方格式）
7. 幂等保证：二次运行无新差距即 no-op（log 只记新增差距）
```

## spec_version 规则

- **粒度**：按产物模板版本（与 skill 语义版本解耦）。示例命名：`design.v2`、`req.v1`、`tasks.v1`、`test.v1`。
- **bump 白名单**（触发 spec_version bump）：
  - ✅ 产物必填章节/字段/结构变化
  - ✅ 校验规则白名单变化（如 SOLID 硬约束从 4 条变 6 条）
  - ❌ 纯流程细化（如文案措辞、交互步骤顺序）
  - ❌ 参考文档链接更新
- **常量位置**：每个 A/B 类 skill 的 `references/realign.md` 顶部"当前 spec_version"小节记录当前常量值（职责单一源）。SKILL.md 顶部**不**重复该信息，仅通过"详细参考"指针链接到 realign.md。
- **差异矩阵**：每个 A/B 类 skill 的 `references/realign.md` 维护 `v1→v2→v3` migration items。
- **bump 触发**：skill 作者在修改产物必填章节/字段/结构时，同步更新 `references/realign.md` 顶部常量 + 填写 Migration Matrix 的对应条目。未同步 = spec 漂移，verify --schema-drift（阶段 3）会报。

## 向后兼容（无元数据的旧产物）

- 阶段 1（纯 flag，无 frontmatter）：产物无 `spec_version` 字段 → 由用户显式 `/pipeline realign` 触发，skill 假设产物 = legacy，直接按当前规范做全量差距扫描。
- 阶段 2（有 frontmatter）：无字段 → `spec_version: legacy` → 归 `retrofit` 处理（大规模迁移），不由 realign 直接重写。
- 阶段 3（诊断入口）：`/verify --schema-drift` 扫描所有产物并报告 legacy / drift / current 三态。

## Dry-run 样例（首次调用 vs 二次调用）

> **说明**：以下为**示意**样例，用于展示报告格式与幂等性，非实际运行结果。`design.v1 → design.v2` 已是真实演进（2026-08-31，§0 摘要节，见 [system-design/references/realign.md](../../system-design/references/realign.md)）；其余 skill 的 `spec_version` 常量仍为 v1 首版、Migration Matrix 仍为"保留字段，未来启用"。本仓尚未真实触发过 realign 执行。

**假想场景**：仓库有 3 个产物，其中 `02-system-design.md` 是 `design.v1`（假设常量已升至 `design.v2`），`04-dev-tasks.md` 是 `tasks.v1`（当前常量 `tasks.v1`，无 drift），`00-context.md` 缺 frontmatter（legacy）。

### 首次调用 `/pipeline realign --dry-run`

```
# Realign Dry-Run Report

扫描：3 个产物（A 类 2 / B 类 1）

## 差距总览

| 产物 | spec_version | 状态 | additive | restructuring |
|---|---|---|---|---|
| docs/devdocs/02-system-design.md | design.v1 → design.v2 | drift | 2 | 0 |
| docs/devdocs/04-dev-tasks.md | tasks.v1 | current | 0 | 0 |
| docs/devdocs/00-context.md | (无 frontmatter) | legacy | — | — |

## 建议动作

- /system-design --realign  # 补齐 2 项 additive（§15 设计审查"原则校验"列、ADR"升级原因"条目）
- /retrofit docs/devdocs/00-context.md  # legacy 产物先由 retrofit 加 frontmatter
- （04-dev-tasks.md 无需动作）

未执行任何修改（dry-run）。运行 /pipeline realign 实际执行。
```

### 二次调用（realign 已完成后）

```
# Realign Dry-Run Report

扫描：3 个产物（A 类 2 / B 类 1）

## 差距总览

| 产物 | spec_version | 状态 | additive | restructuring |
|---|---|---|---|---|
| docs/devdocs/02-system-design.md | design.v2 | current | 0 | 0 |
| docs/devdocs/04-dev-tasks.md | tasks.v1 | current | 0 | 0 |
| docs/devdocs/00-context.md | context.v1 | current | 0 | 0 |

## 建议动作

无差距。幂等校验通过。
```

二次调用无新差距 → no-op，验证幂等性。

## realign-log 格式

每次 realign 完成后，在产物尾部追加：

```markdown
## Realign Log

| 时间 | 从 spec_version | 到 spec_version | 补齐项（additive）| 重构项（restructuring）| 触发者 |
|---|---|---|---|---|---|
| 2026-04-22T10:30+08:00 | design.v1 | design.v2 | SOLID 校验表、ADR"升级原因" | — | /pipeline realign |
```

dev-workflow 的 realign 在任务正文追加一行：`Realigned-From: <old_spec> at <iso-timestamp>`，原证据保留。

## 安全不变量（realign 必须遵守）

- ❌ **不**破坏原完成证据（AC 表、外审记录、测试证据一律保留）
- ❌ **不**修改已合规段落（只追加/重构差距项）
- ❌ **不**并入 dev-workflow 的 12 种续做信号（语义污染）
- ❌ **不**在 headless 模式隐式触发 realign（必须显式 `--realign`）
- ✅ 所有 restructuring 项必须 `⚠️ 必须确认`
- ✅ 工作区必须洁净才能执行 realign（同续做约束）
- ✅ 每 skill 阶段单独 commit，便于回滚

## 一次性升级提示（阶段 3）

`pipeline` 阶段检测完成、返回路由建议之前，执行 schema drift 轻量检查。

### 触发流程

```text
1. 检查 .devdocs-realign-ack 标记
     ├── 存在且未失效 → 跳过提示（用户已做决策）
     └── 不存在或失效 → 继续 step 2
     │
2. 委托 /verify --schema-drift（只读扫描，≤2s）
     │
3. drift_count > 0 或 legacy_count > 0
     ├── 是 → 打印提示（见下），继续原路由（不阻塞）
     └── 否 → 跳过
```

### 提示格式

```
ℹ️ 规范升级提示
   检测到 <N> 个产物按旧规范生成（drift: <X>, legacy: <Y>）
   建议：
     /pipeline realign --dry-run    先预览差距
     /pipeline realign              按新规范查漏补缺
     /pipeline realign --no-realign 跳过本次（记录决策，不再提示）
   此提示在用户做任一决策后写入 .devdocs-realign-ack，之后不再出现
```

### `.devdocs-realign-ack` 标记

- 位置：仓库根目录，git 管理
- 内容（YAML）：`{ acked_at: <iso-ts>, acked_decision: realign|no-realign, acked_drift_count: <N>, acked_spec_versions: {design: design.v1, req: req.v1, ...} }`
- 写入方：用户执行 `/pipeline realign` 或 `--no-realign` 后，由编排层写入（非 pipeline 入口本身）

### 标记失效（自动重新提示）

当以下任一条件成立时，旧 ack 失效、重新提示：
- 任一 skill 的 spec_version 常量 bump（`acked_spec_versions` 记录与当前常量不一致）
- 新增 drift 产物（`drift_count` 数值变大）

用户不需要手动删除 ack，机制自动处理。

## health drift 探针（阶段 3，与 schema drift 并列但语义不同）

> **语义分叉**：schema/layout drift 是一次性版本升级决策，受 `.devdocs-realign-ack` 控制（上文）。health drift 是**持续退化的监控信号**，**不读不写 `.devdocs-realign-ack`、不受 `--no-realign` 控制**；每次进入路由按 baseline 重评估。维护者勿把 health 接回 ack。

### 廉价探针（路由时 ≤2s，不全量扫描）

只 stat 一个文件，不碰 frontmatter / 死链 / ADR（那些留全量 `--scope=health`）：

```text
1. stat <repo_root>/.claude/rules/devdocs-state.md
     ├── 不存在 → 跳过（无 health drift 信号）
     └── 存在 → 读 size_bytes + 扫该文件单行最大长度 max_line
2. 命中阈值判定（复用 state/total-size-cap + line-length-cap 阈值）：
     ├── size > 40 KiB → blocker 级（state/total-size-cap）
     ├── size > 10 KiB → warn 级（state/total-size-cap）
     └── max_line > 500 字符 → blocker 级（state/line-length-cap，权威定义即 blocker）
3. baseline 比对（见下）决定是否提示
```

### baseline-aware 静默（承认存量债、只报新增退化）

读 `<repo_root>/.claude/rules/.health-baseline.yml`（若存在）：

| baseline 状态 | 提示条件 |
|--------------|---------|
| 无 baseline | 命中即提示（尤其 size > 40 KiB blocker 级必提示） |
| 有 baseline | 仅当 `delta = current_size − baseline_size ≥ 2 KiB` / warn→blocker 升级 / baseline 不可读 时才提示（与 [health-lint-implementation.md](health-lint-implementation.md) 的 state/total-size-cap delta 规则一致） |

> **`state/line-length-cap`（max_line > 500）独立判定，不受 size baseline delta 静默**——baseline 仅记录 size delta（无 max_line 字段），故新增单行超长一律提示，避免 size delta < 2 KiB 时漏报。

### 会话内去重（非持久，下会话重评估）

同一 `repo + rule_id + severity_bucket` 在**单个会话内只提示一次**；不写任何持久标记（区别于 ack）。下个会话重新评估——这不是永久静默，是避免同一会话反复进出 pipeline 被同一条刷屏。

### 提示格式

```
ℹ️ 健康度提示（不阻塞）
   devdocs-state.md 已 <size> KiB（阈值 warn 10 / blocker 40）<，较 baseline +<delta> KiB>
   建议：/pipeline realign --scope=health    跑全量健康扫描
   （此提示按 baseline 重评估，修复后自动消失；非升级决策，不写 ack）
```

> 全量 health 扫描（4 维度 / 死链 / ADR 漂移 / 所有文档）仍由显式 `/pipeline realign --scope=health` 执行，见 [realign-scope-health.md](realign-scope-health.md)。探针只决定"要不要提示去跑全量"。

## 与 retrofit 的边界

> 本节与上方"向后兼容"章节自洽：**阶段 1**（当前，产物尚无 frontmatter 元数据）下，表格内"无 frontmatter"场景尚未触发；用户显式 `/pipeline realign` 统一归 realign 的 legacy 全量扫描。**阶段 2 起**（产物引入 frontmatter 之后），下表规则生效。

| 场景 | 归属 |
|---|---|
| 无 keel → keel 首次化 | **retrofit**（现状不变） |
| 阶段 2 起：产物无 frontmatter 或无 F/US/AC 体系（**基线项目除外**：有 `00-baseline.md` 且无 `01`~`04` 时属终态，retrofit 会驳回） | **retrofit**（M1 流程） |
| 阶段 1：产物无 frontmatter（尚未引入元数据） | **realign**（用户显式 --realign 时按 legacy 全量扫描） |
| 已合规 keel + 单个 skill 的 spec_version 升级 | **realign**（本契约） |
| 已合规 keel + 跨多 spec 大版本升级 | `pipeline realign` 依次调度各 skill realign |
| 产物 frontmatter 标 `legacy` | 归 retrofit 处理 |

## 与 codebase-insight 的关系

`codebase-insight` 有独立的 `schema_version + commit_hash` 失效机制，**不纳入** realign 编排。但 `/verify --schema-drift`（阶段 3）扫描时会读取其元数据并统一报告。
