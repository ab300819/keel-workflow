---
name: ms-retrofit
description: Retrofit existing projects to DevDocs workflow, or migrate old DevDocs to new standards. Reverse-engineer code into structured documentation. Use when users want to adapt existing projects, migrate documentation, standardize documents, or upgrade DevDocs version. Triggers on "retrofit", "改造", "适配", "迁移", "标准化", "逆向", "升级文档", "existing project", "已有项目", "从代码生成文档". NOT for initializing new projects (use ms-pipeline) or adding features to existing DevDocs (use ms-feature).
allowed-tools: Read, Write, Glob, Grep, AskUserQuestion, Bash
metadata:
  patterns: [inversion, generator]
  interaction: multi-turn
  handoff: yaml-summary-v1
---

# 项目改造

将已有工程改造为 DevDocs 流程，或将旧版 DevDocs 迁移到新规范。

## 语言规则

- 支持中英文提问
- 统一中文回复
- 使用中文生成文档

## 快速开始

**一句话**: 将已有项目适配 DevDocs 工作流，或将旧版 DevDocs 迁移到新规范。

**最常见用法**: `/ms-retrofit`（自动检测项目状态）

**不适合?** 新项目→`/ms-pipeline init`，加功能→`/ms-feature`

## 触发条件

- 用户希望将现有项目适配 DevDocs 流程
- 用户需要标准化项目文档
- 用户要迁移或升级已有 DevDocs 文档
- 项目缺少文档，需要从代码逆向生成

## 与 realign 的边界

retrofit 与 realign（规范升级回扫）**互补不重叠**，**以 frontmatter + `spec_version` 字段为主判据**：文档顶部 YAML frontmatter 存在且含有效 `spec_version` → 信任元数据，归 **realign**（`/ms-pipeline realign`），无论正文是否缺 F-XXX 编号（编号补齐由 realign 内 additive 差距处理）；反之（无 frontmatter / 无 `spec_version` / 无 DevDocs）归 **retrofit**。详见 [../pipeline/references/realign.md](../pipeline/references/realign.md) § 与 ms-retrofit 的边界。

## 工作流程

```
1. 扫描项目结构
   │
   ▼
2. 检测项目状态
   │
   ├── 无 DevDocs ──────────────────┐
   │                                │
   ├── 有 DevDocs（旧版）────┐      │
   │                         │      │
   └── 有 DevDocs（符合规范）│      │
       → 无需改造            │      │
                             ▼      ▼
3. 分析（按检测结果分支）
   │
   ├── 版本迁移：规范检查 + 生成差异清单
   └── 新项目：自动识别文档 + 结构分析
   │
   ▼
4. 呈现分析结果 + 改造策略（AskUserQuestion）
   │              让用户选择执行分支
   ▼
5. 用户确认 → 按分支执行
   │
   ├── 版本迁移：更新迁移文档 → 生成/更新 docs/devdocs/
   └── 新项目：
       ├── 确认识别/手动指定 → 生成 DevDocs 文档
       └── 代码逆向推导 → 展示推导结果 → 用户二次确认 → 生成 DevDocs 文档
   │
   ▼
6. 生成改造报告
```

---

## 方案确认规范

扫描项目结构和检测状态后，**展示改造策略并使用 AskUserQuestion 让用户选择执行分支**，确认后再生成/更新文档。

### 版本迁移场景

展示规范检查结果和迁移动作清单后，让用户选择：

> 检测到旧版 DevDocs，建议迁移策略：
> 1. **完整迁移**（推荐）- 自动完成所有文档迁移
> 2. **选择性迁移** - 选择要迁移的文档项（选择后需指定具体迁移范围）
> 3. **仅生成差异报告** - 不迁移文档，仅输出差异报告
> 请选择迁移方式。

**选择性迁移追加交互**：用户选择选项 2 后，展示差异清单并让用户勾选要迁移的文档/章节，确认范围后再执行。

### 新项目改造场景

展示项目概况（类型、技术栈、规模）和文档识别结果后，让用户选择：

> 项目结构识别结果如下，请确认或调整：
> 1. **确认识别结果**，开始生成文档
> 2. **手动指定**模块/路径
> 3. **代码逆向推导**后再确认（推导完成后会再次展示结果供确认）

### 方案必须包含

**新项目改造**：项目概况（类型、技术栈、规模）→ 文档识别结果 → 改造方式（文档转换/逆向推导/混合）→ 推导范围和粒度 → 预估产出（F/US/AC 数量）→ 风险与注意

**版本迁移**：规范检查结果 → 迁移动作清单（含影响范围和风险）→ 迁移方式（完整/选择性/仅报告）

### 约束
- **符合当前规范的项目**：直接告知用户无需改造并退出，不进入分支选择
- 用户选择前：只展示方案，不写入任何文件
- 用户选择后：按分支生成 `docs/devdocs/` 下的文档
- **选择性迁移**：必须在用户指定迁移范围后才能执行，不可猜测范围
- **代码逆向推导**：推导完成后必须再次展示结果供用户确认，确认后才能写入文档

## 项目状态检测

### 检测逻辑

```
1. 检查 docs/devdocs/ 目录是否存在
   │
   ├── 不存在 → 新项目改造流程
   │
   └── 存在 → 检查规范符合性
       │
       ├── 符合当前规范 → 无需改造
       │
       └── 不符合 → 版本迁移流程
```

### 规范符合性检查清单

| 检查项 | 检查内容 | 规范要求 |
|--------|----------|----------|
| **编号体系** | F-XXX, US-XXX, AC-XXX | 必须 |
| **测试编号** | UT-XXX, IT-XXX, E2E-XXX | 必须 |
| **追溯矩阵** | F → US → AC → 测试 映射 | 必须 |
| **文件命名** | 01-requirements.md, 03-test-cases.md 等 | 必须 |
| **章节完整性** | 各文档必要章节 | 必须 |
| **Skill 协作** | 标注协作 Skill | 建议 |

---

## 版本迁移流程（已有 DevDocs 但不符合规范）

当检测到已有 DevDocs 文档但不符合当前规范时执行。完整 Step M1-M4 详细规范（规范检查报告 / 差异清单格式 / 用户确认话术 / 编号迁移示例 / 文件重命名 / 追溯矩阵生成）见 [references/version-migration.md](references/version-migration.md)。

要点：
- M1 规范检查：生成"检测结果"表（文件 / 状态 / 问题）
- M2 生成差异清单：编号体系 + 文件结构 + 追溯矩阵 + 章节补充
- M3 用户确认：AskUserQuestion 三选项（完整迁移 / 选择性 / 仅报告）
- M4 迁移执行：编号 + 重命名（git mv 保留历史）+ 追溯矩阵

---

## 新项目改造流程（无 DevDocs）

当项目没有 DevDocs 文档时执行。完整 Step 1-5 详细规范（扫描位置 / 识别规则 / 用户确认 / 代码逆向推导示例 / 测试用例推导 / 输出文件结构）见 [references/new-project-retrofit.md](references/new-project-retrofit.md)。

要点：
- Step 1 扫描常见文档位置（docs/ / README / design/ / tests/）
- Step 2 自动识别（按关键词匹配文档类型）
- Step 3 用户确认三选项（确认识别 / 手动指定 / 代码逆向）
- Step 4 代码逆向推导（路由→F、API→US、测试→AC/UT/IT/E2E）
- Step 5 生成 DevDocs 完整目录结构

---

## 改造报告

改造完成后必须生成 `00-retrofit-report.md`，包含改造概览、文档状态、编号分配、待完善项、下一步建议。

详细模板参见 [templates/retrofit-report-template.md](templates/retrofit-report-template.md)。

**关键规则**：改造不是终点，必须通过后续 Skill 进入正常开发循环。推荐先用 `/ms-requirements --context` 补充背景信息。

**工作区模式探测（`retrofit` 路径）**：改造成功、`docs/devdocs/` 生成后、`agent-memory --update` 之前，执行一次工作区模式探测，步骤见 [../pipeline/references/layout/workspace-shell.md § 探测](../pipeline/references/layout/workspace-shell.md#探测)（本文不重复算法）。无 `.gitmodules` 时静默判定 `inline`，不打扰用户；有条目则 AskUserQuestion 后，将探测结果通过 `devdocs_frontmatter` 输入（`workspace_mode` / `code_roots`）随下一步 `Task: /agent-memory --update` 一并传入，字段契约见 [agent-memory/SKILL.md](../agent-memory/SKILL.md) § devdocs frontmatter 写入(可选)。

**记忆同步(成功路径必做)**:改造成功、`docs/devdocs/` 生成后,执行 `Task: /agent-memory --update` 同步 AGENTS.md(DevDocs 项目会包含工作流路由节;若上一步探测到工作区模式,一并写入 `devdocs:` frontmatter)。写 AGENTS.md 走 agent-memory 的窄例外(见下方约束「Write 工具仅用于写入 docs/devdocs/」),本 Skill 不直接 Write 该文件。失败语义:ℹ️ 不阻塞改造交付,blockers 记入报告。

---

## Skill 协作

| 场景 | 协作 Skill | 说明 |
|------|-----------|------|
| 需求审查 | `/ms-requirements` | 审查改造后的需求文档 |
| 设计审查 | `/ms-system-design` | 审查系统设计 |
| 测试用例 | `/ms-test-cases` | 完善测试用例设计 |
| 新增功能 | `/ms-feature` | 改造后添加新功能 |
| Bug 修复 | `/ms-bugfix` | 改造后修复问题 |
| 测试质量 | `/testing-guide` | 检查测试有效性 |
| 文件操作 | `/git-safety` | 重命名文件时使用 git mv |

---

## 约束

### 阶段边界约束（最高优先级）
- [ ] **⛔ 禁止继续：文档阶段不得产出实现代码**（恢复方式：使用 /ms-dev-workflow 执行编码）
- [ ] Write 工具仅用于写入 `docs/devdocs/` 下的 Markdown 文档;窄例外:改造成功后委托 `agent-memory` 写其受管记忆文件(`AGENTS.md`/`CLAUDE.md` 导入行/`.claude/rules/devdocs-state.md`),其余业务文件仍禁止
- [ ] 编码实现由 `/ms-dev-workflow` 负责，本 Skill 不涉及

### 方案确认约束

- [ ] **扫描项目 + 检测状态后，必须展示方案并等待用户选择执行分支**
- [ ] **方案必须包含改造策略和预估产出（新项目）或迁移动作清单（版本迁移）**
- [ ] **用户确认方案后才能开始文档改造**
- [ ] 用户要求调整时，更新方案后重新确认

### 检测约束

- [ ] **必须先检测项目状态（无 DevDocs / 旧版 / 符合规范）**
- [ ] 必须扫描常见文档目录
- [ ] 识别结果必须让用户确认

### 迁移约束

- [ ] **迁移前必须生成差异清单**
- [ ] **迁移前必须用户确认**
- [ ] 文件重命名必须使用 `git mv`
- [ ] 不得删除原有文档的有效内容

### 编号约束

- [ ] **必须为所有功能点分配 F-XXX 编号**
- [ ] **必须为所有用户故事分配 US-XXX 编号**
- [ ] **必须为所有验收标准分配 AC-XXX 编号**
- [ ] **必须为所有测试用例分配 UT/IT/E2E-XXX 编号**
- [ ] 编号必须连续，不得跳号

### 输出约束

- [ ] 输出目录统一为 `docs/devdocs/`
- [ ] 文件命名遵循 DevDocs 规范
- [ ] 必须生成改造报告
- [ ] 逆向推导内容必须标注 `[从代码推导]`

---

## 错误处理

详见 [references/error-handling.md](references/error-handling.md)（无法识别文档、项目无文档、迁移冲突）

---

## 子 Agent 摘要格式

当本 Skill 作为子 Agent 运行时，返回以下结构化摘要：

```yaml
skill: ms-retrofit
status: success | failed | partial
summary:
  headline: "项目改造完成，逆向提取 3 功能点"
  details:
    docs_generated:
      - docs/devdocs/01-requirements.md
      - docs/devdocs/02-system-design.md
    features_extracted: X
    apis_extracted: X
    coverage:
      requirements: "XX%"
      design: "XX%"
      tests: "XX%"
blockers: []
output_files:
  - docs/devdocs/00-retrofit-report.md
new_ids:
  features: [F-001~F-003]
  stories: [US-001~US-006]
  acceptance: [AC-001~AC-012]
next_recommended:
  skill: ms-requirements
  args: "--context"
```

## 输出文件

```
docs/devdocs/
├── 00-retrofit-report.md    # 改造报告
├── 01-requirements.md       # 需求文档（含编号）
├── 02-system-design.md      # 系统设计
├── 02-system-design-api.md  # API 设计（如需要）
├── 03-test-cases.md         # 测试用例概览 + 追溯矩阵
├── 03-test-unit.md          # 单元测试（含 UT-XXX）
├── 03-test-integration.md   # 集成测试（含 IT-XXX）
├── 03-test-e2e.md           # E2E 测试（含 E2E-XXX）
└── 04-dev-tasks.md          # 开发任务（含 T-XX）
```
