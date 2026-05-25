# ms-dev-workflow 速度优化 — 设计文档

- **日期**:2026-05-25
- **作者**:Mason(brainstorm with Claude + 4 轮 codex 复核 T-125/T-126/T-129/T-130)
- **状态**:design,待写实施 plan
- **范围**:ms-dev-workflow skill 速度优化,代码项目场景
- **dev-workflow spec_version bump**:1.0 → 1.1

## 1. 概述与目标

### 1.1 问题陈述

用户反馈 `/ms-dev-workflow` 在代码项目(如 mic-en 类业务仓库)开发任务时速度慢。Codex 独立分析(T-125)定位根因为 **"单任务也走完整治理链路"**:
- 双 Agent + 红绿两轮 + S8 完备性表 + S9 多次 ms-verify
- 🔴 任务默认 Phase 4 外审(codex CLI,max_rounds=3,单任务最大外部等待点)
- Commit 2 后置同步(每任务 sync + compound 重复开销)

每环都摊到单任务上,串行累积导致 🔴 单任务 S9 总耗时 120-270s。

### 1.2 目标

1. **🔴 单任务墙钟 ↓25-40%**(P1 并行化主因)
2. **5 任务批量节省 ~360s**(P2 末尾合并主因)
3. **零回归**:standard profile / 代码项目 / 旧任务行为完全不变
4. **零复杂度净增**:配套累计删减审计,目标净变化 ≤ 0 行

### 1.3 非目标

- 不引入新的对抗审查 provider(沿用 codex CLI / codex-mcp)
- 不改 SKILL.md 主入口的 11 步流程骨架
- 不引入 no-runtime / doc-spec profile(skills 仓库本身改动用 ms-bugfix 或直编,不走 dev-workflow)
- 不动 layout.v1/v2 兼容性、id_scheme v1/v2 兼容性

## 2. 范围

### 2.1 三项修订(加)

| 修订 | 类型 | 改动量估计 |
|------|------|-----------:|
| P0-A 文档级 | 矛盾消除 + 暴露已有 flag | ~10 行 |
| P1 S9 轻量并行化 | 行为变更(默认并行 + 运行期校验) | ~120 行 |
| P2 批量末尾合并 sync | 行为变更(Batch-Id git trailer) | ~70 行 |
| **合计新增** | | **~200 行** |

### 2.2 五项删减(减,来自累计审计 T-130)

| 删减项 | 位置 | 行数 |
|--------|------|-----:|
| 无人值守"交付报告"大模板压缩 | auto-mode.md:166-268 | 70 |
| skeleton-examples.md 完整实现示例(layout.v1 标注与 v2 方向冲突)立即删 | skeleton-examples.md:72-178 | 70 |
| "已前移到 S8" 机制原文(与 P0-A 重叠) | verification-flow.md:249-317 | 40 |
| Phase 2-UI 在三处重复转述,权威留 ui-quality-checklist.md | execution-flow.md:106-131 + verification-flow.md:154-163 | 22 |
| Phase 4 状态/重试多文件重复,权威留 verification-flow.md | auto-mode.md:91-121 + execution-flow.md:253-259 + task-orchestration.md:137-148 | 28 |
| **合计删减** | | **230** |

### 2.3 净变化

```
+200 (新增) - 230 (删减) = -30 行
```

dev-workflow 总规模:**2442 → 2412 行**,略减。

## 3. P0-A 文档级修订

### 3.1 `--skip-external-review-reason` 语义收敛

**矛盾现状**(SKILL.md:67 ↔ SKILL.md:215):
- SKILL.md:67 描述"自动标 EXT_PENDING、Step 1.5[D2] 拦截"
- SKILL.md:215 说"`EXT_PENDING` ⛔ 阻塞 Commit 1"
- 用户读到:"能跳过吗?好像能(有 flag);能 Commit 吗?好像不能(被拦截)"

**收敛规则**:
```
--skip-external-review-reason 不是 Commit 1 放行手段,
仅用于"临时中断登记":记录跳过原因 + 标 EXT_PENDING + 留尾注,
便于后续 /ms-pipeline realign 或人工补跑 Phase 4 时追溯。
"被拦截"是预期行为。
```

**改动点**:
| 位置 | 改动 |
|------|------|
| SKILL.md:67 | 描述末尾加 "⚠️ 不构成 Commit 1 放行,需后续补跑 Phase 4" |
| SKILL.md:215 | 加交叉引用 [对抗式验证#Skip 参数] |
| SKILL.md:249 | 同步追加"不放行"提示 |
| SKILL.md:362 提交模板 | 注释明确"留作追溯;Commit 1 仍要求 EXT_REVIEWED" |
| verification-flow.md Phase 4 真值表 | 明确 EXT_PENDING 在所有放行路径都为 ⛔ |

### 3.2 `--single-commit` 进语法表

**现状**:仅在 SKILL.md:276 提到一句,未进语法表,用户看快速开始时发现不了。

**改动点**:SKILL.md:62-69 语法表在 `--auto-commit` 后插入一行:
```markdown
| 单次提交 | `--single-commit` | 代码+文档合并为单次提交(适合无文档变更) |
```

## 4. P1 S9 轻量并行化

### 4.1 当前 S9 串行链路

```
S8 完成 → S9.1 /ms-verify --impl (阻塞,~30-60s)
       → S9.2 Phase 1~3 内置自审 (阻塞,~30s)
       → S9.3 Phase 4 外审 (阻塞,~60-180s,brief 依赖 Phase 1~3 综合报告)
```

单任务 🔴 S9 总耗时:**120-270s**(全串行)

### 4.2 并行后链路

```
S8 完成 → 计算 diff_hash_at_s8 (运行期内存,不持久化)
       → 并行启动 3 分支:
            ├─ /ms-verify --impl       (输入: S8 快照)
            ├─ Phase 1~3 内置自审      (输入: S8 快照)
            └─ Phase 4 外审            (输入: S8 快照,新 brief)
       → 等所有分支完成 OR 任一 Blocker
       → Commit 1 前: 重算 diff_hash,与 diff_hash_at_s8 比对
            ├─ 相等 → 接受 verdict
            └─ 不等 → 丢弃全部 verdict,从 S9 整体重跑 (rerun_count++)
```

单任务 🔴 S9 并行耗时:**约 max(60, 30, 180) ≈ 180s,墙钟 ↓25-40%**

### 4.3 Phase 4 brief 改造

新 brief 消费 S8 稳定快照,**不再依赖 Phase 1~3 综合报告**:

```yaml
phase_4_brief:
  source: "S8 stable snapshot"
  task: T-XX
  ac_table: <S8 AC 完备性表>
  sprint_contract: <S1.5 Contract>
  test_evidence_digest: <S6 绿验摘要>
  code_diff: <git diff S8 时点>
  expected_focus: [算法正确性, 边界条件, 数据一致性]
```

### 4.4 运行期 diff_hash 一致性校验

- S8 完成时算 `diff_hash_at_s8 = SHA(git diff)[:16]`(内存持有)
- 并行期间 **禁止任何 Agent 写文件**(此时 Test/Impl Agent 已完成,仅剩 3 个验证分支)
- Commit 1 前重算 diff_hash 比对,不等则丢弃 verdict 整体重跑
- **不持久化**(不入 commit、不写文件),纯运行期一致性保险

### 4.5 Blocker → 整体重跑

```
任一分支报 Blocker:
  - 中止全部并行分支
  - 等待用户/编排器修复
  - 修复后重新跑 S8 (生成新 diff_hash) → 从 S9 入口整体重跑
  - rerun_count += 1
```

**防卡死**:
- `max_rerun = 2`(F0 + F1 + F2)
- 超额 → `EXT_BLOCKED`,交互模式 AskUserQuestion,headless 模式 fail-fast

### 4.6 回退安全阀

加 `--no-parallel` flag:
- 出现并行调度 bug 时,用户可手动回退到串行
- Phase 1 实施时 default = parallel
- 稳定后(>3 个月,无 bug 报告)考虑去掉 flag

## 5. P2 批量末尾合并 sync

### 5.1 当前批量链路

```
T-01: S1~S11 → Commit 1 → /ms-sync (Commit 2) → /ms-compound
T-02: 同上
...
T-05: 同上
```

5 任务批量同步开销:**5 × (sync ~30s + compound ~60s) ≈ 450s 重复**

### 5.2 优化后链路

```
批量启动 → 生成 batch_id = "B-<timestamp>-<seq>" (内存)

每任务:
  S1~S11 → Commit 1 (代码)
  Commit 1 trailer 末尾追加:
    Batch-Id: B-2026-05-25-001

批量末尾(单次):
  /ms-sync --batch=B-2026-05-25-001
  Commit 2 message:
    chore(sync): batch B-2026-05-25-001 — T-01,T-02,T-03,T-04,T-05
  /ms-compound --batch
```

**批量同步开销:30s + 60s ≈ 90s,节省约 360s**

### 5.3 Batch-Id git trailer(而非持久化文件)

**为什么不用 `.batch-state.yml`**:
- 多批次同分支并发时 yaml 文件可能冲突
- 中断恢复需要解析两份状态(yaml + git history)
- 用户手动 sync 介入难以协调

**git trailer 优势**:
- 100% 从 git history 可恢复,无额外文件
- 多批次并发天然隔离(每个 Commit 1 各自携带 batch_id)
- Step 1.5[C] sync_pending 判定通过 `grep Commit 1 trailer + 找对应 Commit 2`

### 5.4 Step 1.5[C] sync_pending 识别

```
对每个有 Commit 1 但无 Commit 2 的任务:
  ├─ 读 Commit 1 trailer 的 Batch-Id
  ├─ 找批次 Commit 2 (grep "chore(sync): batch B-XXX")
  ├─ 若 Commit 2 不存在 → sync_pending=true (等末尾合并)
  ├─ 若 Commit 2 存在但 task list 不含本任务 → sync_pending=true (异常,需补 sync)
  └─ 若 Commit 2 存在且含本任务 → sync_pending=false (已完成)
```

### 5.5 中断恢复(沿用现有断点续做)

- **场景 A 批量中途崩溃**:续做时 Step 1.5 检测到一批 sync_pending 任务 → 补跑剩余任务 → 末尾统一 sync
- **场景 B Commit 1 完成但末尾 sync 失败**:续做命令 `/ms-sync --resume-batch=B-XXX`
- **场景 C 用户手动 `/ms-sync` 介入**:允许。手动 `/ms-sync` 扫描所有 Commit 1 trailer 的 Batch-Id,处理 trace 未更新的任务,已更新的跳过。末尾 `/ms-sync --batch=B-XXX` 通过相同的 trace 状态判定幂等跳过已处理任务

### 5.6 单任务模式不变

- 单任务模式始终立即 sync + compound
- 不接受 `--defer-sync` 等新 flag
- 单任务 Commit 1 不携带 Batch-Id trailer

## 6. 累计删减审计

### 6.1 删减明细

#### 6.1.1 auto-mode.md:166-268 交付报告大模板(-70)
当前模板假设"每任务 Commit 2",与 P2 末尾合并冲突。压缩为字段清单 + 1 个极简示例。

#### 6.1.2 skeleton-examples.md:72-178 layout.v1 完整实现示例(-70)
立即删。理由:`@satisfies/@verifies` 与 layout.v2 外置追溯方向冲突。删除范围在 72-178 区间内,保留约 37 行最小骨架示例(只留接口签名 + 一条 layout.v2 traceability.yml 风格的引用),足够培训用。

#### 6.1.3 verification-flow.md:249-317 "已前移到 S8" 机制原文(-40)
S8 完备性表已是权威,此段是历史残留,合并到 AC 完备性章节,只留"S9 复用 S8 表"一句指针。

#### 6.1.4 Phase 2-UI 多处重复转述(-22)
权威保留 ui-quality-checklist.md,execution-flow.md:106-131 和 verification-flow.md:154-163 改为 2-3 行指针。

#### 6.1.5 Phase 4 状态/重试多文件重复(-28)
权威保留 verification-flow.md:386-520,删除 auto-mode.md:91-121 / execution-flow.md:253-259 / task-orchestration.md:137-148 的重复转述。

### 6.2 关键约束(必须守住,写入 SKILL.md 顶部)

```
P1 / P2 新增内容必须只落入"权威文件"一次:
  - Phase 4 / 并行调度 / diff_hash / 重跑 → verification-flow.md
  - Step 1.5[C] sync_pending / Batch-Id 识别 → task-orchestration.md
  - 不允许在 auto-mode.md / execution-flow.md / SKILL.md 重复转述
  - 仅允许 2-3 行指针引用
```

不守这条规则,未来又会回到"加固时多点漂移"的老路,这次净减就白费。

## 7. spec_version 与兼容性

### 7.1 dev-workflow spec_version

```yaml
# SKILL.md frontmatter
spec_version: 1.0 → 1.1
```

P0-A 是文字澄清不 bump;P1 (Phase 4 brief 改造) + P2 (Step 1.5[C] 语义变更) 触发 1.1 bump。

### 7.2 向后兼容矩阵

| 场景 | 期望行为 |
|------|---------|
| 旧项目 + 标准 🔴 任务 | 行为完全不变(回归基线) |
| 旧任务(spec_version 1.0 时完成)续做 | Step 1.5 不强制 diff_hash / Batch-Id 字段 |
| 用户 `--no-parallel` | 完全等价于 P1 实施前的串行行为 |
| 旧批次(无 Batch-Id trailer)续做 | 编排器视为"独立单任务依次执行",不强制末尾合并 |
| `_shared/constraints.md` | **不 bump**(`No-Test-Available` 已被砍,无协议层变更) |

### 7.3 迁移路径

```bash
/ms-pipeline realign --scope=spec
```

可识别 1.0 → 1.1 差距并提示用户。P0-A 修订在 bump 时同步落入 SKILL.md。

## 8. 验证策略

### 8.1 静态验证

- `grep -c "skip-external-review-reason"` 5 处描述完全一致
- `grep -c "\-\-single-commit"` 出现在 SKILL.md:62-69 语法表
- verification-flow.md Phase 4 brief 不再 grep 到 "Phase 1~3 综合报告"作为输入
- Phase 4 / Phase 2-UI / Phase 4 状态多文件转述已删除(grep 验证唯一权威)
- 总行数从 2442 → 2412(wc 验证)

### 8.2 动态验证(1 次墙钟实测)

代码项目(如 mic-en)选 1 个真实 🔴 任务:
- 串行模式(`--no-parallel`):记录 T_serial
- 并行模式(默认):记录 T_parallel
- **期望:T_parallel ≤ 0.75 × T_serial**(↓25-40%)

### 8.3 三个静态演练(Codex T-129 必修)

| 演练 | 目的 |
|------|------|
| 外审 Blocker 重跑 | 验证 P1 diff_hash 校验 + Blocker 整体重跑 + rerun_count |
| 批量中途崩溃 | 验证 P2 Batch-Id trailer + 续做时正确识别批次边界 |
| 用户手动 `/ms-sync` 介入 | 验证 P2 末尾合并幂等性 |

### 8.4 回归验证

代码仓库未启用任何新行为时(即沿用 spec_version 1.0 时的调用方式):
- 跑 1 个 🔴 任务,行为与 abaea06(瘦身后基线)完全一致
- 跑 1 个批量(3 任务),行为完全一致

## 9. 实施分阶段

### 9.1 Phase 1 = P0-A + 删减审计(低风险,先做)

- P0-A 文档级修订(~10 行新增)
- 五项删减全部落地(-230 行)
- spec_version bump 至 1.1(部分,标记 P1/P2 为 [FUTURE])

**收益**:文字澄清 + 复杂度净减,无行为变更,可立即合入。

### 9.2 Phase 2 = P1 + P2(行为变更,Phase 1 稳定后做)

- P1 S9 轻量并行化(~120 行)
- P2 批量末尾合并 sync(~70 行)
- spec_version 1.1 完成(标 [FUTURE] → 落地)
- 1 次墙钟实测 + 3 个静态演练

**收益**:实质墙钟降低。

### 9.3 间隔时间

Phase 1 合入后,**用户实际跑过至少 1 个代码项目任务确认无回归** → 才进 Phase 2。

## 10. 验收标准

### 10.1 Phase 1 验收
- [ ] P0-A 改动点全部落实(5 处文字)
- [ ] 五项删减全部完成,grep 验证唯一权威
- [ ] dev-workflow 总规模 ≤ 2412 行
- [ ] SKILL.md ≤ 500 行(目前 393,加 10 行后 ≤ 403)
- [ ] spec_version 1.1 标记 P1/P2 为 [FUTURE]
- [ ] 代码仓库回归测试 0 失败

### 10.2 Phase 2 验收
- [ ] P1 并行化 + diff_hash 校验落地
- [ ] P2 Batch-Id trailer + 末尾合并 sync 落地
- [ ] `--no-parallel` 安全阀生效
- [ ] 1 次墙钟实测达成 ↓25-40% 目标
- [ ] 3 个静态演练全部 PASS
- [ ] 关键约束(权威文件唯一)在 grep 验证下成立

### 10.3 复杂度验收(贯穿)
- [ ] dev-workflow 总规模净变化 ≤ 0 行(不允许净增)
- [ ] 未来 6 个月若再出现"P1/P2 内容被复制到 auto-mode.md 等转述文件" → 视为复杂度退化,必须 revert

## 附录:Codex 复核轨迹

- T-125:独立分析根因 + 提原始 3 方案
- T-126:复核完整版方案(有条件通过,3 类必修)
- T-129:复核精简版方案(2 个有条件通过 + 1 个不通过,3 处必修 — 已纳入本设计)
- T-130:累计复杂度审计(5 项删减,净 -30 行)
