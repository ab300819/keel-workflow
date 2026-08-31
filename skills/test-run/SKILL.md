---
name: ms-test-run
description: Execute test suites and generate test reports. Supports full test run, selective run by type (UT/IT/E2E), and traceability validation. Use when users need to run tests, verify test coverage, generate test reports, or validate before release. Triggers on "run tests", "test run", "execute tests", "执行测试", "跑测试", "全量测试", "回归测试", "test report", "测试报告", "覆盖率". NOT for designing test cases (use ms-test-cases) or fixing bugs (use ms-bugfix).
allowed-tools: Read, Write, Glob, Grep, Bash, AskUserQuestion
metadata:
  patterns: [tool-wrapper]
  interaction: single-turn
  handoff: yaml-summary-v1
---

# 测试执行

执行测试套件并生成测试报告，支持全量执行、按类型分层执行、按功能点关联执行和追溯验证。

## 快速开始

**一句话**: 执行测试套件，生成测试报告。

**最常见用法**: `/ms-test-run`（全量）、`/ms-test-run --ut`（仅单元测试）

**不适合?** 设计测试用例→`/ms-test-cases`

## 语言规则

- 支持中英文提问
- 统一中文回复

## 触发条件

- 用户需要执行测试
- 用户需要验证测试覆盖率
- 用户需要追溯验证（AC 是否被通过的测试覆盖）
- `/ms-dev-workflow` 批量完成后自动触发
- 关键词："执行测试"、"跑测试"、"全量测试"、"回归测试"、"run tests"

## 运行模式

### 语法

```
/ms-test-run              # 全量执行（UT + IT + E2E）
/ms-test-run --ut         # 仅单元测试
/ms-test-run --it         # 仅集成测试
/ms-test-run --e2e        # 仅 E2E 测试
/ms-test-run F-001        # 按功能点关联的测试
/ms-test-run --trace      # 全量执行 + 追溯验证
/ms-test-run --affected   # 仅运行受变更影响的测试
/ms-test-run --affected --ut  # 受影响的单元测试
```

### 模式说明

| 模式 | 说明 |
|------|------|
| 全量执行 | 按 UT → IT → E2E 顺序分层执行所有测试 |
| `--ut` | 仅执行单元测试（UT-XXX） |
| `--it` | 仅执行集成测试（IT-XXX） |
| `--e2e` | 仅执行 E2E 测试（E2E-XXX） |
| `F-XXX` | 通过追溯矩阵查找功能点关联的所有测试并执行 |
| `--trace` | 全量执行 + 追溯完整性验证 |
| `--affected` | 基于 git diff 识别变更文件，仅运行关联测试（可与 --ut/--it/--e2e 组合） |

## 前置条件

- 测试用例文档：`docs/devdocs/03-test-cases*.md`
- 项目已配置测试框架（Jest/Vitest/pytest/Go test 等）

## 执行流程

> 测试命令在 `workspace_context.code_roots` 各路径下执行（`inline` 时为单项，`path` = 仓库根绝对路径，**调用方不分支**）。代码根多于一项时逐个执行并在报告中按 root 分组。测试报告恒写 `<workspace_context.docs_dir>/devdocs/05-test-report.md`。代码根取自 握手 `workspace_context`（[_shared/constraints.md](../_shared/constraints.md) §3 `task/workspace-context`；未传入时按 `inline` 缺省）。

```text
1. 读取测试用例文档
   ├── 扫描 docs/devdocs/03-test-cases*.md
   ├── 解析测试用例清单（UT/IT/E2E 编号）
   └── 解析追溯矩阵（AC → 测试映射）
           │
           ▼
1.5 [--affected] 变更范围识别
   ├── 确定比较基线（用户指定 base / 自动检测 merge-base / 不可判定时提示全量）
   ├── 执行 git diff --name-only <base> 获取变更文件
   ├── 在 03-test-cases.md 中匹配引用这些文件的测试用例
   ├── 在 04-dev-tasks.md 中匹配关联文件的任务，反查测试用例
   └── 无匹配时提示"建议运行全量"
           │
           ▼
2. 检测测试框架
   ├── 扫描 package.json / pyproject.toml / go.mod / Makefile
   ├── 识别测试框架（Jest/Vitest/pytest/Go test 等）
   └── 确定运行命令
           │
           ▼
3. 分层执行测试
   ├── 单元测试（UT-XXX）
   │   └── 运行命令 + 收集结果
   ├── 集成测试（IT-XXX）
   │   └── 运行命令 + 收集结果
   └── E2E 测试（E2E-XXX）
       └── 运行命令 + 收集结果
           │
           ▼
4. 收集测试结果
   ├── 通过/失败/跳过 统计
   ├── 覆盖率数据（如可用）
   └── 失败详情（文件:行号 + 错误信息）
           │
           ▼
5. [--trace] 追溯验证
   ├── 扫描代码中的 @verifies/@testcase 标注
   ├── 对比追溯矩阵（03-test-cases*.md）
   ├── 标记未覆盖的 AC
   └── 标记无通过测试的 AC
           │
           ▼
6. 生成测试报告
   └── 输出到 docs/devdocs/05-test-report.md
           │
           ▼
7. 输出摘要
   ├── 通过率 + 覆盖率
   ├── 失败详情（如有）
   └── [--trace] 追溯状态
```

## 测试框架检测

### 检测优先级

```text
1. package.json → scripts.test / devDependencies
   ├── vitest → npx vitest run
   ├── jest → npx jest
   └── mocha → npx mocha
2. pyproject.toml / setup.cfg / pytest.ini
   └── pytest → python -m pytest
3. go.mod
   └── Go test → go test ./...
4. Makefile / Cargo.toml / 其他
   └── 按框架惯例检测
5. 无法检测 → AskUserQuestion 询问用户
```

### 测试文件定位

通过测试用例文档中的路径信息定位测试文件：

```text
1. 03-test-cases*.md 中的测试文件路径
2. 代码中的 @testcase 标注（反向查找）
3. 测试框架约定路径（__tests__/、*.test.ts、*_test.go）
```

## 分层执行策略

### 执行顺序

```text
UT（单元测试）→ IT（集成测试）→ E2E（端到端测试）
```

**UT 全失败提示**：UT 全部失败时，按调用上下文决定：
- 独立调用（用户直接使用）：AskUserQuestion 是否继续 IT/E2E
- 被 dev-workflow 调用（--trace）：继续执行，收集全部结果

### 按功能点执行

```text
/ms-test-run F-001

1. 读取追溯矩阵
2. 查找 F-001 关联的所有 AC
3. 查找每个 AC 关联的测试用例（UT/IT/E2E）
4. 仅执行这些测试
5. 生成功能点维度的报告
```

## 上下文管理

### 分段写入

按测试层分段处理：完成 UT 结果 → 写入报告 UT 章节 → 再处理 IT → 写入 IT 章节 → 再处理 E2E。避免一次性处理全部结果。

### 完整性校验

每层写入后验证：
- [ ] 报告中的测试条目数 == 测试框架输出的实际条目数

### 失败详情一致性

- 首个失败用例的详情作为**格式锚点**
- 每个后续失败用例必须包含相同字段：文件路径、行号、关联 AC、错误信息、建议
- 不因失败数量多而省略任何字段

## 追溯验证（--trace）

### 验证规则

| 检查项 | 通过条件 | 失败标记 |
|--------|----------|----------|
| AC 测试覆盖 | 每个 AC 至少有 1 个关联测试 | ❌ 未覆盖 |
| 测试通过 | AC 关联的所有测试全部通过 | ⚠️ 测试失败 |
| 标注一致性 | 代码 @verifies 与文档追溯矩阵一致 | ⚠️ 标注不一致 |
| 孤立测试 | 测试用例有对应的 AC 关联 | ℹ️ 孤立测试（信息） |

### 追溯报告格式

```markdown
## 追溯验证结果

| AC 编号 | 描述 | 关联测试 | 测试状态 | 覆盖状态 |
|---------|------|----------|----------|----------|
| AC-001 | 邮箱格式校验 | UT-001, IT-001 | ✅ 全部通过 | ✅ 已覆盖 |
| AC-002 | 密码强度校验 | UT-002 | ❌ 1/1 失败 | ⚠️ 测试失败 |
| AC-003 | 重复注册检测 | — | — | ❌ 未覆盖 |
```

## 测试报告

### 输出路径

`docs/devdocs/05-test-report.md`

### 报告内容

> 详见 [templates/test-report-template.md](templates/test-report-template.md)

报告包含：
- 执行摘要（通过率、覆盖率、执行时间）
- 分层结果（UT/IT/E2E 各自统计）
- 失败详情（文件路径、行号、错误信息、关联 AC）
- [--trace] 追溯验证结果
- 建议（未覆盖 AC 的处理建议）
- [--affected] 覆盖范围（模式、比较基线、变更文件、匹配测试、未覆盖变更）

## Skill 协作

| 场景 | 协作 Skill | 说明 |
|------|-----------|------|
| 测试用例来源 | `/ms-test-cases` | 前置：提供 UT/IT/E2E 用例清单和追溯矩阵 |
| 测试质量标准 | `/testing-guide` | 协作：覆盖率和断言质量判定标准 |
| 开发完成后调用 | `/ms-dev-workflow` | 被调用：批量开发完成后自动触发全量测试 |
| 追溯更新 | `/ms-sync` | 后续：测试结果可触发追溯矩阵状态更新 |

## 约束

### 执行约束

- [ ] **执行前必须检测到测试框架**（无法检测时询问用户）
- [ ] **分层执行顺序：UT → IT → E2E**（不可打乱）
- [ ] **单个测试失败不终止后续测试**（收集全部结果后汇总）
- [ ] UT 全部失败时，独立调用可提示用户，被调用时继续执行
- [ ] **超时保护**：单个测试套件超时 5 分钟（可配置）

### 报告约束

- [ ] **必须生成测试报告**（输出到 05-test-report.md）
- [ ] **失败详情必须包含文件路径和行号**
- [ ] **--trace 模式必须包含追溯验证结果**
- [ ] 所有失败详情字段完整度一致（不因数量多而省略）

### 追溯约束

- [ ] **追溯验证必须覆盖所有 AC**
- [ ] **未覆盖的 AC 必须明确标记**
- [ ] **标注不一致必须警告**（代码 vs 文档）
- [ ] **追溯结果不修改源文件**（仅报告，修改由 /ms-sync 负责）

## 子 Agent 摘要格式

当本 Skill 作为子 Agent 运行时，返回以下结构化摘要：

```yaml
skill: ms-test-run
status: success | failed
summary:
  headline: "全量测试通过，覆盖率 85%"
  details:
    tests_run:
      unit: { passed: X, failed: 0, total: X }
      integration: { passed: X, failed: 0, total: X }
      e2e: { passed: X, failed: 0, total: X }
    coverage: "XX%"
    trace_verified: true
blockers: []
output_files:
  - docs/devdocs/05-test-report.md
new_ids: {}
next_recommended:
  skill: ms-verify
  args: "--impl"
```

## 参考资料

- [templates/test-report-template.md](templates/test-report-template.md) - 测试报告模板
