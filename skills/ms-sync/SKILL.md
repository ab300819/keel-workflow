---
name: ms-sync
description: Sync documentation with implementation progress. Update traceability matrices, task statuses, and detect doc-code drift. Use when users need to update docs after development, verify doc-code consistency, or track progress. Triggers on "sync docs", "update progress", "doc consistency", "同步文档", "更新进度", "trace", "audit", "文档对齐", "进度更新", "追溯矩阵". NOT for verification/review (use ms-verify) or requirements editing (use ms-requirements).
allowed-tools: Read, Write, Glob, Grep, Bash, AskUserQuestion
metadata:
  patterns: [reviewer]
  interaction: multi-turn
  handoff: yaml-summary-v1
---

# 文档同步

保持 DevDocs 文档与实际实现进度一致，检测偏差并更新状态。

## 快速开始

**一句话**: 同步文档与实现进度，检测 doc-code 偏差。

**最常见用法**: `/ms-sync`（默认 trace+audit+check）、`/ms-sync --archive`（归档历史 docs）、`/ms-sync --back-propagate-prd`（反向同步 PRD mapping）

**不适合?** 验证对齐→`/ms-verify`，提取经验→`/ms-compound`

## 语言规则

- 支持中英文提问
- 统一中文回复
- 使用中文生成文档

## 触发条件

- 用户完成一个或多个开发任务后
- 用户要求检查文档与代码一致性
- 用户需要更新文档进度
- 定期同步（如 Sprint 结束时）

## 运行模式

```bash
/ms-sync                    → 默认：trace + audit + check，可带任务范围如 T-01 T-02
/ms-sync --archive [requirements|design|tests|tasks] [--release v1.0.0]  → 归档历史 docs
/ms-sync --back-propagate-prd  → 反向同步 prd 映射状态
```

### 默认模式变更

原 `--trace`、`--audit`、`--check`、`--absorb` 已合并到默认模式。无参数调用时自动执行 `trace → audit → check` 串行流程（audit/check 依赖 trace 的输出，因此不再作为独立用户命令）。低风险偏差吸收能力按原 absorb 规则纳入默认流程。

### 内部编排接口（非用户入口）

- `check`：默认流程内置检查，不再暴露 `/ms-sync --check`
- `absorb`：默认流程内置低风险吸收，不再暴露 `/ms-sync --absorb`
- `schema-drift`：迁移到 `/ms-verify --schema-drift`，sync 仅在 health report 合并 verify 产出的 drift 结果

### 模式对比

| 用户入口 | 检查 | 自动更新 | 用户确认 |
|----------|------|----------|----------|
| `/ms-sync` | ✅ trace+audit+check | ✅ 低风险吸收/状态更新 | ✅ 高风险/写入前 |
| `/ms-sync --archive` | ✅ 归档条件 | ✅ 归档文件 | ✅ 全部 |
| `/ms-sync --back-propagate-prd` | ✅ PRD mapping 对比 | ✅ 映射状态 | ✅ 写入前 |

## 核心理念

### 文档与代码的关系

```text
文档定义（计划）          代码实现（实际）
     │                        │
     ├── F-XXX 功能点    ←→   ├── 功能模块
     ├── AC-XXX 验收标准 ←→   ├── 业务逻辑
     ├── T-XX 开发任务   ←→   ├── 代码提交
     └── UT/IT/E2E 测试  ←→   └── 测试文件
```

**基线项目的追溯范围**：项目存在 `docs/devdocs/00-baseline.md` 时，追溯矩阵与覆盖率必须标注
`coverage_scope: post-baseline` 并写明 `adoption_commit`——追溯从接管点之后开始，基线前的存量
代码不在 F→US→AC→测试 链路内。不标注会把局部覆盖率误报成全系统覆盖率。

**核心原则**：
- 文档是计划，代码是实现
- 偏差是正常的，关键是及时同步
- 同步应该双向：文档→代码（指导）、代码→文档（记录）

### 同步时机

| 时机 | 同步内容 |
|------|----------|
| 任务完成后 | 更新任务状态、测试结果 |
| Sprint 结束 | 全量检查、进度报告 |
| 需求变更后 | 更新需求文档、影响分析 |
| 代码审查后 | 记录设计决策变更 |

## 工作流程

```text
1. 读取 DevDocs 文档
   │
   ▼
2. 扫描代码库（工作区状态）
   ├── 检查文件是否存在（Glob）
   ├── 运行测试（获取实时结果）
   ├── 检查未提交变更（git status）
   └── 参考提交记录（git log，辅助）
   │
   ▼
3. 对比分析
   ├── 任务完成状态
   ├── 测试覆盖情况
   └── 功能实现状态
   │
   ▼
4. 生成偏差报告
   │
   ▼
5. 询问用户确认更新
   │
   ▼
6. 更新文档
```

**重要**：检查基于**当前工作区状态**，而非仅依赖 git 提交历史。

## 模式详解

### 默认模式（trace → audit → check 自动串行）

无参数调用时自动执行三段流程：

1. **trace 阶段**：校验追溯矩阵的「变更来源」列（⛔ 不扫描代码——代码里没有 DevDocs 编号）。详见 [trace-mode.md](references/trace-mode.md)
2. **audit 阶段**：检测编号体系完整性，防止文档维护债积累。检查 AC 覆盖、F 任务闭环、INS 转化、孤立编号、**CON 闭环、needs review 未闭合项报龄**。详见 [audit-mode.md](references/audit-mode.md)
3. **check 阶段**：输出偏差报告与 health report；schema drift 诊断统一委托 `/ms-verify --schema-drift`，本 Skill 只合并其结果。

> audit/check 依赖 trace 的扫描结果，因此自动串行执行，不再作为独立子命令。

### 默认吸收规则

从"检查员"进化为"记录员"，支持代码优先开发路径。低风险偏差自动吸收，高风险需确认。自动包含 trace 步骤。

详见 [absorb-mode.md](references/absorb-mode.md)

### 文档归档 (--archive)

支持所有文档类型的归档，控制文档膨胀，同时保留历史记录便于追溯：

| 文档类型 | 归档条件 | 归档文件 |
|---------|---------|---------|
| 需求 | 功能已完成/已废弃 | `archive/01-requirements-archive.md` |
| 设计 | 关联功能已归档 | `archive/02-system-design-archive.md` |
| 测试 | 关联 AC 已归档 | `archive/03-test-cases-archive.md` |
| 任务 | 已完成 > 15 个 | `archive/04-dev-tasks-archive.md` |

归档时支持级联：归档 F-001 时可同时归档关联的设计/测试/任务。

详见 [archive.md](references/archive.md)

## 同步命令

### 完整同步（默认）

```bash
/ms-sync
# 流程: trace 扫描 → audit/check → 自动吸收低风险 → 确认高风险/写入 → 更新文档
```

## 输出文件

### 进度报告

生成 `docs/devdocs/00-progress-report.md`，包含总体进度、偏差汇总、下一步建议。

> **注意**：默认流程会先返回检查结果并等待写入确认；用户未确认时不生成进度报告也不更新文档。

### 文档更新

| 文档 | 更新内容 |
|------|----------|
| `04-dev-tasks.md` | 任务完成状态、执行检查清单 |
| `03-test-cases.md` | 追溯矩阵状态、测试通过状态 |
| `01-requirements.md` | 功能点实现状态（如有状态列） |

## 约束

### 检查约束

- [ ] **必须读取所有 DevDocs 文档后再进行检查**
- [ ] **必须生成偏差报告**
- [ ] **更新文档前必须询问用户确认**（吸收模式低风险除外）
- [ ] 检查结果必须可追溯（显示检查方法）

### 更新约束

- [ ] **不自动删除文档内容，只标记状态**
- [ ] **不自动修改代码，只更新文档**
- [ ] 更新时记录时间戳

### 吸收模式约束

- [ ] **低风险吸收仅限状态字段更新**
- [ ] 新增内容必须指定关联编号（AC/F/US）
- [ ] 无法确定关联的内容标记为"待手动处理"

### 安全约束

- [ ] 不执行未知的 shell 命令
- [ ] 测试命令使用项目配置的命令

## Skill 协作

| 场景 | 协作 Skill | 说明 |
|------|-----------|------|
| 开发完成 | `/ms-dev-workflow` | 被调用：任务完成后触发 trace 阶段 |
| 任务完成后 | `/ms-dev-tasks` | 执行任务后触发同步 |
| 测试追溯 | `/ms-test-cases` | 协作：更新追溯矩阵代码位置 |
| 需求变更 | `/ms-feature` | 新功能添加后同步 |
| Bug 修复 | `/ms-bugfix` | Bug 修复后更新文档 |
| 洞察确认 | `/ms-insights` | 改进建议确认后同步 |
| 项目改造 | `/ms-retrofit` | 改造后全量同步 |

## 参考资料

- [absorb-mode.md](references/absorb-mode.md) - 吸收模式详解
- [audit-mode.md](references/audit-mode.md) - 追溯健康度检查
- [trace-mode.md](references/trace-mode.md) - 代码追溯扫描
- [archive.md](references/archive.md) - 任务归档功能
- [examples.md](references/examples.md) - 使用示例与偏差类型

## 偏差修复路由（调度器功能）

当检测到偏差时，必须在报告中指派下一步修复 Skill：

| 偏差类型 | 修复 Skill | 说明 |
|----------|-----------|------|
| 设计缺失/漂移 | `/ms-system-design` | 代码有新接口但文档未记录 |
| AC 缺测试 | `/ms-test-cases` | 验收标准无对应测试用例 |
| F 缺任务闭环 | `/ms-dev-tasks` | 功能点无关联开发任务 |
| 代码已实现文档落后 | `/ms-sync` | 状态未更新、新内容未登记，默认流程处理低风险吸收 |
| 追溯矩阵代码位置缺失 | `/ms-sync` | 代码标注未扫描到矩阵 |

> **调度器原则**：偏差报告不能只列出问题，必须给出明确的修复路由。

## 调用说明

任务完成后直接运行：

```text
/ms-sync            # trace → audit → check 自动串行 → 显示报告 → 确认更新
```

> 默认模式已将 trace、audit、check 和低风险吸收合并为自动串行流程，无需手动分步调用。

## 批量确认优化

同一会话内的低风险变更（状态更新、进度统计等）合并为文档级批量确认，而非逐个确认。

## --back-propagate-prd 模式

反向同步 DevDocs 需求变更到 prd 映射表。仅在用户显式调用时执行。

```text
/ms-sync --back-propagate-prd
    |
    v
1. 定位 PRD requirements index（写路径）：固定为 docs/prd/requirements/index.md（单需求脚手架，扁平唯一路径）
   ├── 未找到 → 提示「无 prd 映射表，无需反向同步」
   └── 找到 → 继续
    |
    v
2. 读取 docs/devdocs/01-requirements.md 的 F-XXX 列表
    |
    v
3. 对比 index.md 映射表 vs 01-requirements.md
   ├── 新增 F-XXX（无对应 FR-XX 映射）→ 标注「DevDocs 侧新增，无 prd 来源」
   ├── 废弃 F-XXX（已从 01-requirements.md 移除）→ 标注 mapping_status: removed（规范见 skills/ms-prd/references/prd-mapping-status.md）
   └── 已有映射未变 → 保持
    |
    v
4. 更新 index.md 的「DevDocs 映射」章节
```

**写权限边界**：
- 只允许修改 index.md 的「DevDocs 映射」章节
- 若章节不存在，只允许在文末创建该章节，不得重排其他章节
- 只写映射状态，不改 FR 内容

## 子 Agent 摘要格式

当本 Skill 作为子 Agent 运行时，返回以下结构化摘要：

```yaml
skill: ms-sync
status: success | partial
summary:
  headline: "同步完成，健康度 85%，2 个偏差已修复"
  details:
    mode: default | archive | back_propagate_prd
    internal_operations: [trace, audit, check, absorb]
    trace_results:
      satisfies_found: X
      verifies_found: X
      coverage: "XX%"
      coverage_scope: "post-baseline | full"    # post-baseline 时必填 adoption_commit
      adoption_commit: ""                        # coverage_scope 为 post-baseline 时填
    audit_results:
      orphan_ids: []
      missing_tests: []
      health_score: "XX%"
    deviations:
      total: X
      auto_absorbed: X
      needs_confirm: X
blockers: []
output_files:
  - docs/devdocs/00-progress-report.md  # 仅确认写入后生成；检查-only 内部调用为空
new_ids: {}
next_recommended:
  skill: ms-compound
  args: ""
```

## 下一步

同步完成后，根据进度报告中的**偏差修复路由**执行对应 Skill。
