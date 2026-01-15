---
name: devdocs-test-plan
description: Create comprehensive test plans including unit tests, UI automation, and manual test cases. Use when users need test strategy, test cases, or QA planning. Triggers on keywords like "test plan", "test cases", "QA", "testing strategy", "unit test", "e2e test".
allowed-tools: Read, Write, Glob, Grep, AskUserQuestion
---

# DevDocs Test Plan

Create comprehensive test plans covering unit tests, UI automation, manual tests, and release regression.

## Language

- Accept questions in both Chinese and English
- Always respond in Chinese
- Generate all documents in Chinese

## Trigger Conditions

- User has completed system design
- User asks for test plan or test cases
- User needs QA strategy or testing coverage

## Prerequisites

- Requirements document: `docs/devdocs/01-requirements.md`
- System design document: `docs/devdocs/02-system-design.md`
- If not exists, suggest running previous phases first

## Test Strategy Overview

| Test Type | Coverage Scope | Coverage Requirement |
|-----------|----------------|----------------------|
| Unit Test | Core business logic | Line coverage >= 80%, Branch coverage >= 80% |
| UI Automation | Core user scenarios | All P0 scenarios |
| Manual Test | All scenarios | All acceptance criteria |

> **编写测试时**：必须遵循 `/testing-guide` 的质量约束（断言质量、Mock 策略、变异测试）

## Workflow

1. **Read documents**: Load requirements and system design
2. **Identify test scope**: Map acceptance criteria to test types
3. **Design unit tests**: Cover core business logic
4. **Design UI automation**: Cover P0 user scenarios
5. **Design manual tests**: Cover all remaining scenarios
6. **Create regression plan**: Define pre-release checklist
7. **Confirm with user**: Get approval

## Output

**Files** in `docs/devdocs/`:

| File | Content |
|------|---------|
| `03-test-plan.md` | Test strategy overview and coverage matrix |
| `03-test-unit.md` | Unit test cases and mock strategy |
| `03-test-e2e.md` | UI automation test cases |
| `03-test-manual.md` | Manual test cases |
| `03-test-regression.md` | Pre-release regression checklist |

For detailed templates, see:
- [templates/unit-test-template.md](templates/unit-test-template.md)
- [templates/e2e-test-template.md](templates/e2e-test-template.md)
- [templates/manual-test-template.md](templates/manual-test-template.md)
- [templates/regression-template.md](templates/regression-template.md)

## Constraints

### 覆盖率约束
- [ ] **Unit tests must cover core business logic with >= 80% line and branch coverage**
- [ ] **UI automation must cover all P0 scenarios**
- [ ] Manual test cases must cover all acceptance criteria

### 用例设计约束
- [ ] Each core feature needs at least 1 positive test case
- [ ] Each user input needs at least 1 negative test case
- [ ] Must provide acceptance criteria coverage matrix
- [ ] Priority labels: P0 (blocker), P1 (major), P2 (minor)
- [ ] Test steps must be executable, not vague
- [ ] Unit tests must specify mock strategy

### 质量约束（参考 `/testing-guide`）
- [ ] **测试依据来自需求，不是代码**
- [ ] **禁止弱断言**（toBeDefined, toBeTruthy 等不能作为唯一断言）
- [ ] 测试名称必须描述预期行为
- [ ] 推荐使用变异测试验证测试有效性（变异得分 ≥ 80%）

### 发布约束
- [ ] **Must include pre-release regression checklist**
- [ ] **Must define rollback conditions and post-release verification**

## Next Step

After user confirms test plan, suggest running `/devdocs-dev-tasks` for development task breakdown.

## Related Skills

| Skill | 用途 |
|-------|------|
| `/testing-guide` | 编写测试时的质量约束（断言、Mock、变异测试） |
| `/devdocs-dev-tasks` | 将测试计划转化为开发任务 |
| `/code-quality` | 确保代码可测试性 |
