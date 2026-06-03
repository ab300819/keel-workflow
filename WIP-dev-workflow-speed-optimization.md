# 🚧 WIP — dev-workflow 速度优化 / 切机 handoff

> **⚠️ 临时文件 — 处理完计划后必须清理**
>
> **清理时机**(任一满足):
> - Phase 2 完成并合并到 main → 删除本文件 + commit `chore: cleanup WIP handoff (dev-workflow speed optimization closed)`
> - 项目放弃(决定不做 Phase 2)→ 删除本文件 + commit `chore: cleanup WIP handoff (dev-workflow speed optimization abandoned)`
>
> 本文件**不进入** SKILL.md / spec / plan 的内容范畴,仅作切机/会话切换时的状态指针。

---

## 当前状态:Phase 1 已完成,Phase 2 待观察期通过后启动

- **日期**:2026-06-03(brainstorm 起点 2026-05-21,Phase 1 落地 2026-05-25)
- **目标项目**:`ms-dev-workflow` skill 速度优化(代码项目场景,如 mic-en 类业务仓库)
- **当前分支**:`main`
- **工作树**:洁净

---

## 关键文档(切机后从这里恢复上下文)

| 文档 | 路径 | Commit |
|------|------|--------|
| 设计 spec(完整范围) | [`docs/superpowers/specs/2026-05-25-ms-dev-workflow-speed-optimization-design.md`](docs/superpowers/specs/2026-05-25-ms-dev-workflow-speed-optimization-design.md) | 9dd04fa |
| Phase 1 实施 plan | [`docs/superpowers/plans/2026-05-25-ms-dev-workflow-phase-1-doc-prune.md`](docs/superpowers/plans/2026-05-25-ms-dev-workflow-phase-1-doc-prune.md) | 3816812 |
| Phase 2 实施 plan | **尚未撰写**,待观察期通过后启动 | — |

---

## Phase 1 已落地内容(9 个实施 commits)

| Task | 内容 | Commits | 行数变化 |
|------|------|---------|---------:|
| 1 | skeleton-examples.md 长示例删除 + checklist 修复 | 05907e6 + f9481e3 | -79 |
| 2 | auto-mode.md 交付报告压缩 + Phase 4 dedupe + 失败续做清理 | 219f050 + 2aab0c7 | -93 |
| 3 | verification-flow.md "已前移到 S8" + Phase 2-UI dedupe + P0-A 真值表 + over-deletion 修复 | 84b464c + 5d81af6 | -28 |
| 4 | execution-flow.md Phase 2-UI + Phase 4 dedupe | 6766b03 | -28 |
| 5 | task-orchestration.md Phase 4 dedupe | 547e8f5 | -7 |
| 6 | SKILL.md P0-A 5 处 + `--single-commit` 进语法表 + 权威文件唯一原则 + spec_version 1.1 bump | b3d7c4a | +11 |

**净变化**:dev-workflow 总规模 2480 → 2256,**-224 行**(目标 -220 ±10,达标)。

---

## Phase 2 启动条件(spec §9.3)

**前置**:至少 1 个真实代码项目 🔴 任务跑过,确认 Phase 1 文档收敛 + 累计删减无回归。

**观察期检查清单**(下次跑真实 🔴 任务时核对):

- [ ] `--single-commit` 在 SKILL.md 语法表可见(原本只在 :276 单提)
- [ ] `--skip-external-review-reason` 行为与文档一致(EXT_PENDING ⛔ 拦截 Commit 1,语义不再矛盾)
- [ ] Phase 1~3 自审仍有 ≥3 findings 门槛 + 🔧/📋/💬 分类(Task 3 over-deletion 已修复并恢复)
- [ ] Phase 2-UI 工作流(🟢 UI 任务)指针链路能正确路由到 ui-quality-checklist.md
- [ ] 批量交付报告(headless)使用新的 batch_id 字段 schema
- [ ] Phase 4 状态机权威唯一在 verification-flow.md
- [ ] 🔴 任务执行墙钟与 Phase 1 之前接近(Phase 1 不动行为,只动文档)

**满足后**:重新进入 brainstorm → writing-plans → subagent-driven-development 流程做 Phase 2。

---

## Phase 2 范围(已对齐,不重新设计)

- **P1 S9 轻量并行化**:Phase 4 / ms-verify / Phase 1~3 默认并行 + 运行期 diff_hash 一致性校验 + Blocker 整体重跑 ≤2 次 + `--no-parallel` 安全阀
- **P2 批量末尾合并 sync**:`Batch-Id:` git commit trailer 标记批次 + Step 1.5[C] sync_pending 识别 + 单任务模式不变

**预估改动**:~200 行,涉及 SKILL.md / verification-flow.md / execution-flow.md / task-orchestration.md / auto-mode.md 五个文件。

**收益**:🔴 单任务墙钟 ↓~10%(总耗时口径)/ 5 任务批量 ↓~22%。

详细设计见 spec §4(P1)+ §5(P2)。

---

## Codex 复核轨迹(可追溯)

- T-125 — 独立根因分析 + 提原始 3 方案
- T-126 — 完整版方案复核(有条件通过,3 类必修)
- T-129 — 精简版方案复核(2 个有条件通过 + 1 个不通过,3 处必修已纳入)
- T-130 — 累计复杂度审计(找出 5 项删减,共 230 行)

---

## 切机/换会话恢复指引

新会话/新机器接手时,按顺序:

1. **快速恢复上下文**(5 分钟):
   ```bash
   cat WIP-dev-workflow-speed-optimization.md                                  # 本文件
   git log --oneline -15 -- skills/dev-workflow/                                # 实施轨迹
   wc -l skills/dev-workflow/SKILL.md skills/dev-workflow/references/*.md       # 当前规模
   grep "spec_version" skills/dev-workflow/SKILL.md                             # 确认 1.1
   ```

2. **深入背景**(15 分钟):
   - 读 spec(`docs/superpowers/specs/2026-05-25-...-design.md`)Section 1-7
   - 读 Phase 1 plan(`docs/superpowers/plans/2026-05-25-...-phase-1-doc-prune.md`)了解执行模式

3. **决定下一步**:
   - 观察期未过 → 继续日常使用 dev-workflow,等真实任务回归数据
   - 观察期过了 → 启动 Phase 2 brainstorm(参考本文件 "Phase 2 范围" 章节,已对齐 codex 复核)
   - 决定不做 Phase 2 → 删除本文件 + 删除 Phase 2 [FUTURE] 标记的 spec_version notes(可选,纯文档清理)

---

## 提醒

- **本文件不是 spec / 不是 plan / 不是规范产物**,仅是临时 handoff 指针,**完成或放弃后必须清理**
- 真正的设计权威是 `docs/superpowers/specs/...-design.md`,不要在本文件做新决策
- 切机后如果发现 spec 或 plan 与本文件描述不一致,**以 spec 为准**(本文件可能滞后)
