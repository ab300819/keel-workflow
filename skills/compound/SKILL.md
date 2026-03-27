---
name: ms-compound
description: Extract patterns, lessons learned, and key decisions from completed development cycles. Writes structured pattern docs to docs/devdocs/patterns/ and recommends running /agent-memory to update AGENTS.md. Run after ms-sync to compound knowledge across sessions. Triggers on "compound", "沉淀", "经验提取", "模式提取", "lessons learned", "知识沉淀", "复盘", "总结经验", "what did we learn". NOT for syncing docs (use ms-sync) or onboarding (use ms-onboard).
allowed-tools: Read, Write, Glob, Grep, Edit, AskUserQuestion
metadata:
  patterns: [generator]
  interaction: multi-turn
  handoff: yaml-summary-v1
---

# 知识复利沉淀

在开发周期完成后，提取本次开发中的模式、陷阱和关键决策，沉淀为可复用的结构化知识。

## 语言规则

- 支持中英文提问
- 统一中文回复
- 使用中文生成文档

## 定位

```
ms-sync：同步文档状态、追溯矩阵          → 文档层面的完成
ms-compound：提取经验、沉淀模式          → 知识层面的复利
```

**互补关系**：ms-sync 确保"这次做对了"，本 Skill 确保"下次也能做对"。

## 触发条件

- ms-sync 完成后（推荐）
- 一轮开发迭代结束后
- 用户主动要求提取经验教训
- 发现值得记录的模式或陷阱

## 运行模式

```bash
/ms-compound                    → 完整流程（提取 + 写入 + 更新）
/ms-compound --extract-only     → 仅提取，不写入文件（预览模式）
/ms-compound --check            → 系统学习检查（仅评估是否有未沉淀的经验）
```

## 工作流程

```text
1. 回顾本次开发
   ├── 读取 verify-report.md（若存在）
   ├── 读取 04-dev-tasks*.md 了解完成的任务
   ├── 读取 git log 了解提交历史
   └── 回顾对话中的关键决策点
   │
   ▼
2. 提取候选模式
   ├── 有效的解决方案（正面模式）
   ├── 踩过的坑和修复方式（陷阱）
   ├── 关键技术决策及其理由（决策记录）
   ├── 可复用的代码模式或架构模式
   └── 验证盲区（ms-verify 未捕捉但后续发现的问题）
   │
   ▼
3. 去重检查
   ├── 扫描 docs/devdocs/patterns/ 已有模式
   └── 跳过已存在的相似模式，或标记为"更新"
   │
   ▼
4. 与用户确认
   ├── 展示提取的候选模式列表
   └── 用户选择：写入 / 跳过 / 修改
   │
   ▼
5. 写入模式文档
   ├── 新模式 → 创建 docs/devdocs/patterns/<pattern-name>.md
   └── 已有模式更新 → 编辑现有文件
   │
   ▼
6. 建议运行 `/agent-memory` 更新 AGENTS.md（可选）
   ├── 项目特定知识更新
   └── 仅当模式具有项目级影响时
   │
   ▼
7. 系统学习检查
   ├── 本次遇到的问题是否已沉淀为规则/模板/检查器？
   ├── 若没有，原因是什么？
   └── 输出检查结论
```

## 模式提取指南

### 什么值得提取

| 类型 | 信号 | 示例 |
|------|------|------|
| 正面模式 | 解决了反复出现的问题 | "用 Strategy 模式解耦支付渠道" |
| 陷阱 | 踩坑后修复，且可能再次遇到 | "SQLite 在并发写入时需要 WAL 模式" |
| 决策 | 有明确取舍，且理由非显而易见 | "选择 SSR 而非 SPA 因为 SEO 需求" |
| 工作流 | 发现了更高效的开发流程 | "先写集成测试再拆单元测试更高效" |
| 验证盲区 | ms-verify 未检出但后续暴露的缺陷 | "verify --impl 未发现跨模块副作用" |

### 什么不值得提取

- 项目特有且不可复用的细节
- 显而易见的最佳实践（如"要写测试"）
- 临时性的 workaround（除非标记为临时）
- 已在 AGENTS.md 或 SKILL.md 中覆盖的规则

## 模式文档结构

每个模式文档遵循统一结构，详见 [templates/pattern.md](templates/pattern.md)。

**文件命名**：`docs/devdocs/patterns/<kebab-case-pattern-name>.md`

## 验证盲区提取

每次执行 `/ms-compound` 时，额外检查验证流程的有效性——形成 **verify → 使用 → 发现遗漏 → compound 沉淀 → verify 改进** 的闭环。

### 盲区信号

| 信号 | 示例 |
|------|------|
| verify --impl 通过但后续发现 Bug | AC-003 标记满足但实际边界条件未覆盖 |
| verify --docs 通过但实现偏离 | 设计文档对齐但实际实现走了不同路径 |
| 对抗式验证未检出的代码质量问题 | 隐式依赖耦合、跨模块副作用 |
| readiness 通过但开发中发现任务定义不足 | 文件路径具体但缺少关键的中间步骤 |

### 盲区输出

发现验证盲区时，追加到 `docs/devdocs/patterns/verify-blindspots.md`：

```markdown
## [日期] 盲区描述

- **维度**: --impl / --docs / --readiness / 对抗式验证
- **遗漏内容**: 具体描述 verify 未检出的问题
- **根因**: 为什么当前检查规则无法检出
- **建议检查项**: 未来 verify 应新增的检查逻辑
- **来源**: 本次开发中如何发现的（Bug 报告/上线后反馈/code review）
```

> 此文件由 ms-verify 启动时读取，作为额外检查项补充。形成持续改进的评估者调优闭环（[参考](https://www.anthropic.com/engineering/harness-design-long-running-apps)：评估提示需要多轮迭代调优）。

## 系统学习检查

每次执行 `/ms-compound` 时，必须回答以下检查问题：

### 检查清单

1. **规则检查**：本次遇到的问题，是否已沉淀为规则（约束/检查项）？
   - 若是 → 记录在哪个 SKILL.md 或 AGENTS.md 中
   - 若否 → 是否应该沉淀？理由？

2. **模板检查**：本次的解决方案，是否应更新到某个模板中？
   - 若是 → 标记目标模板文件
   - 若否 → 理由？

3. **检查器检查**：本次的验证逻辑，是否可自动化为检查步骤？
   - 若是 → 标记目标 Skill 的约束章节
   - 若否 → 理由？

4. **验证盲区检查**：本次是否发现了 ms-verify 未能检出的问题？
   - 若是 → 追加到 `docs/devdocs/patterns/verify-blindspots.md`
   - 若否 → 记录"未发现新盲区"

### 检查输出格式

```markdown
## 系统学习检查

| 维度 | 已沉淀？ | 目标位置 | 备注 |
|------|---------|----------|------|
| 规则 | ✅/❌ | <文件路径> | <说明> |
| 模板 | ✅/❌ | <文件路径> | <说明> |
| 检查器 | ✅/❌ | <文件路径> | <说明> |
| 验证盲区 | ✅/❌ | docs/devdocs/patterns/verify-blindspots.md | <说明> |

**未沉淀原因**：<若有未沉淀项，说明原因>
```

## 输出文件

- 模式文档：`docs/devdocs/patterns/<pattern-name>.md`
- 系统学习检查结论：输出到对话（不单独生成文件）

## 约束

### 提取约束

- [ ] **必须回顾 verify-report 和任务文档**
- [ ] **必须与用户确认后再写入**（`--extract-only` 仅预览）
- [ ] **必须检查已有模式避免重复**
- [ ] 模式文档遵循模板结构
- [ ] 文件名使用 kebab-case

### 质量约束

- [ ] **模式必须包含"问题背景"和"解决方式"**（缺一不可）
- [ ] **必须包含"适用条件"和"禁忌条件"**（防止误用）
- [ ] 模式描述具体、可操作，避免泛泛而谈
- [ ] 关联 Skill/模板字段帮助 Agent 发现和复用

### 系统学习约束

- [ ] **每次执行必须完成系统学习检查**
- [ ] **检查结论必须回答四个维度（规则/模板/检查器/验证盲区）**
- [ ] 未沉淀项必须说明原因
- [ ] 验证盲区发现时必须追加到 `docs/devdocs/patterns/verify-blindspots.md`

### 安全约束

- [ ] **不修改代码文件**
- [ ] **不修改现有 DevDocs 文档**（仅新建/更新 patterns/）
- [ ] 不直接修改 AGENTS.md，需更新时建议用户运行 `/agent-memory`

## Skill 协作

| 场景 | 协作 Skill | 说明 |
|------|-----------|------|
| 前置 | `/ms-sync` | 在 sync 完成后执行 compound |
| 前置 | `/ms-verify` | 读取验证报告提取改进模式 |
| 前置 | `/ms-dev-workflow` | 在工作流末尾推荐执行（批量模式默认） |
| 知识更新 | `/agent-memory` | 大范围知识更新时可配合使用 |

## 子 Agent 摘要格式

当本 Skill 作为子 Agent 运行时，返回以下结构化摘要：

```yaml
skill: ms-compound
status: success | partial
summary:
  headline: "提取 2 个新模式，1 个模板缺口"
  details:
    patterns_extracted: 2
    patterns_updated: 1
    patterns_skipped: 0
    system_learning:
      rules_gap: false
      template_gap: true
      checker_gap: false
      verify_blindspots: 0
blockers: []
output_files:
  - docs/devdocs/patterns/strategy-payment-channels.md
  - docs/devdocs/patterns/sqlite-wal-concurrency.md
  # - docs/devdocs/patterns/verify-blindspots.md  # 当 verify_blindspots > 0 时包含
new_ids: {}
next_recommended:
  skill: ms-onboard
  args: "--update"
```

## 下一步

| 结果 | 建议下一步 |
|------|------------|
| 提取了新模式 | 在下次相关开发中参考 `docs/devdocs/patterns/` |
| 发现规则缺口 | 更新对应 SKILL.md 的约束章节 |
| 发现模板缺口 | 更新对应 templates/ 文件 |
| 无新知识 | 正常，不是每次迭代都有新模式 |
