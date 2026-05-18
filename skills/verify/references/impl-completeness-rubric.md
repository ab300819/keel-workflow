# --impl 完成度与一致性增强判定标准

ms-verify `--impl` 维度的两组增强约束（盲区 6 / 盲区 7）详细判定、源案例与变更日志。SKILL.md「检查约束」节列出短规则条目，本文件展开判定逻辑与历史背景。

## 盲区 6：IT 断言完备性 + DoD checkbox 粒度（P1）

### 检测触发条件

下列任一为真时启用本组检查：

1. 任务 spec / 03-test-cases.md / 04-dev-tasks.md 中 IT-XXX 条目显式提及"N 类断言 / N 类反射 + 文件扫描 / N 项校验 / 期望覆盖 N 个 case"等量化期望。
2. 任务 commit 引入新的 `@Test` 方法但 IT 用例所属测试类与 spec 期望断言类型集存在 diff。
3. 用户在 sprint closure 阶段调用 `--impl` 或 `--readiness`。

### 判定规则

| 情形 | 判定 | 行为 |
|------|------|------|
| 期望 N 类断言，实际落地 N 类（@Test 数 ≥ N 且类级断言粒度覆盖全部类型） | ✅ 满足 | 允许 DoD ✅ |
| 期望 N 类断言，实际落地 K 类（K < N），DoD 整项 ✅ 且无拆分 | ❌ P1 | ⛔ 阻断 DoD；必须拆分子任务或更新 spec 期望 |
| 期望 N 类断言，实际落地 K 类，DoD 显式标 `[完成 K/N 类]` 并把剩余转下版本 candidate | ⚠️ 部分满足（P2） | 允许通过但记录 deferred |
| spec 未量化期望（无 N 类描述） | ⏭️ 跳过 | 不触发本检查（依赖 B1 AC 语义判断） |

### 恢复方式

- 补齐缺失断言并重新跑测试用例 → 重新执行 `--impl --ac` 转 ✅ 满足。
- 拆分子任务：把剩余 (N - K) 类断言转为新任务（如 T-XXX-followup-1），DoD 标 `[完成 K/N 类，剩余 (N-K) 类转 T-XXX-followup-1]`。
- 更新 spec：若 N 期望本身过高，更新 03-test-cases.md 中 IT-XXX 期望数量并附调整理由（建议 cross-link 设计 trade-off 决策）。

### 源案例

**mic-en V0.9.x P15 T-157**（commit fd7fc2d 标 ✅，commit 0ed4c4aaa1 实际实现）

- IT-039 spec 期望覆盖 **8 类反射 + 文件扫描** 断言（验证 SPI 出参字段集与 PO 字段集对齐）。
- 实际落地 **3 类** 断言（聚焦核心字段），合并 P13+P14 旧断言后 14 tests 全绿。
- sprint closure commit fd7fc2d 将 T-157 标 ✅ 全收口，DoD 全勾。
- `/ms-verify --impl + --readiness` + `/ms-sync --check` **全部通过**，3/8 完成度差距未被任一维度检出。
- 根因：`--impl` 只看 IT 用例是否绿，不看断言数 vs spec 期望数；DoD checkbox 是文本级标记，无机器校验。

## 盲区 7：SPI DTO 字段透传完备性 cross-check（P1）

### 检测触发条件

下列任一为真时启用本组检查：

1. `--impl` 扫描 diff 发现 SPI / 对外契约 DTO（含 Result / Response / DTO / Reply 后缀的类）字段集变化（新增 / 删除 / 重命名 / 类型变更）。
2. 任务 spec 涉及"对外契约升级 / SPI 出参变更 / API 字段调整"等关键词。
3. INS-XXX 改进项明确包含"DTO 升级 / 接口字段重构"等措辞。

### 判定规则

| 情形 | 判定 | 行为 |
|------|------|------|
| 新 DTO 字段集 ⊇ 上游 PO 视觉展示性字段类型集（BigDecimal/String/LocalDateTime/Enum 等） | ✅ 完备 | 允许 SPI 升级合并 |
| 新 DTO 缺失部分 PO 字段，但 task spec "字段透传矩阵" 显式登记 `DEFER:<原因>` + cross-link Figma 节点 / UAT 文案 / 后续任务编号 | ⚠️ 部分（P2） | 允许通过但需 follow-up |
| 新 DTO 缺失字段且**无 DEFER 登记** | ❌ P1 | ⛔ 阻断 SPI 升级合并；必须补字段或显式 DEFER |
| task doc **不含**"字段透传矩阵"三列映射表（Upstream PO Field → New DTO Field → Frontend Display Anchor） | ❌ P1 | ⛔ 阻断 task DoD ✅；要求 task 作者补充矩阵 |

### 字段透传矩阵格式（task spec 必填）

```markdown
## 字段透传矩阵

| Upstream PO Field | Type | New DTO Field | Frontend Display Anchor | Status |
|-------------------|------|---------------|------------------------|--------|
| FundGpTraceNodePO.origAmount | BigDecimal | FundTraceFlowResult.origAmount | Figma:供应商-底部"整笔来账金额" | ✅ 透传 |
| FundGpTraceNodePO.origCurrency | String | FundTraceFlowResult.origCurrency | Figma:供应商-币种标签 | ✅ 透传 |
| FundGpTraceNodePO.receiveAmount | BigDecimal | - | Figma:买家-Sent 节点"到账金额" | ❌ DEFER → T-XXX |
```

### UI 视觉对齐 review 提前触发

当任务命中"DTO 升级影响前端"条件时，工作流必须前置：

1. **设计稿提取阶段**：先从 Figma / Pencil / 截图提取 `visual_anchor_field_set`（所有视觉展示锚点用到的字段集）。
2. **DTO 设计阶段**：DTO 字段集必须 ⊇ visual_anchor_field_set；缺口必须 DEFER 登记。
3. **`--ui --design` 提前执行**：在 DTO 字段定稿前（**不是**实现完成后）调用，避免后期发现字段缺失补字段 churn（典型反模式：发现视觉缺字段 → 补 DTO 字段 → 改前端 → 改 Mapper → 改 PO → 改 SQL 全链路 churn）。

### 恢复方式

- 补齐透传字段并新增对应单测（IT 验证字段非 null + 类型正确）→ 重新执行 `--impl`。
- 显式登记 DEFER：在 task spec "字段透传矩阵"中标 `DEFER:<原因>` + 创建 follow-up task（如 T-XXX-buyer-fields）。
- 重设计 DTO：若 PO 字段过多，可考虑分层 DTO（核心字段直出 + 扩展字段惰性加载），但需 cross-link 设计 trade-off 决策。

### 源案例

**mic-en V0.9.x P15 INS-018 T-145**（SPI 出参契约升级）

- 升级 `FundTraceContextDTO → FundTraceFlowResult`，新 DTO 透传子表 `fund_gp_trace_route` 6 字段（per-hop bankName + chargeAmount 等）。
- **未透传** 主表 `fund_gp_trace_node` 的 4 个视觉展示性字段（origAmount / origCurrency / receiveAmount / receiveCurrency）。
- `/ms-verify --impl` + Phase 4 codex 外审 health 92+ **全通过**，sprint 标 ✅。
- 视觉对齐阶段（BUG-043 顺带核对 Figma）才暴露：
  - 供应商端底部"整笔来账金额"视觉锚点 → BUG-045
  - 买家端 Sent 节点"汇出 → 到账"双金额单行箭头 → BUG-046（sequel buyer-side）
- 根因：`--impl` 基于 AC 检查，AC 未细化具体字段名；codex 看 diff 字段新增 ≠ 完备 cross-check 上游 PO；视觉对齐 review 触发时机过晚。

## 变更日志

| 日期 | 版本 | 变更 | 来源案例 / 项目级 cross-link |
|------|------|------|---------|
| 2026-05-12 | v1.0 | 初始版本：纳入盲区 6（IT 断言完备性 + DoD 粒度）、盲区 7（SPI DTO 字段透传 + 字段透传矩阵 + UI 提前 review）为 ms-verify skill 级默认约束 | mic-en V0.9.x P15 T-157 / INS-018 T-145 / BUG-045 / BUG-046；项目级 AGENTS.md 升级 commit c557791；项目 patterns/verify-blindspots.md 第 6 + 7 条 |

> 升级路径：项目级 `docs/devdocs/patterns/verify-blindspots.md` → 项目级 `AGENTS.md` 开发约定 → skill 级默认约束（本次）。下次 `/ms-verify` 调用起对所有项目生效，**不回扫历史项目**。
