<!-- Keep in sync with CLAUDE.md -->

# AI Agent Skills

This file provides guidance to AI coding agents when working with code in this repository.

## Project Overview

This is an **AI Agent Skills template collection** for **solo developers** - a set of reusable SKILL.md files that extend AI coding agents' capabilities for software development workflows. This is NOT a traditional codebase with build/test processes - it's a specification library of Markdown + YAML skill definitions.

## Language Rules

All skills follow consistent language rules:
- Accept questions in both Chinese and English
- Always respond in Chinese
- Generate all documents in Chinese

## Numbering System

DevDocs workflow uses a unified numbering system for traceability:

| Type | Prefix | Example | Description |
|------|--------|---------|-------------|
| Feature | F | F-001 | User-perceivable function |
| User Story | US | US-001 | User scenario |
| Acceptance Criteria | AC | AC-001 | Measurable completion condition |
| Unit Test | UT | UT-001 | Verify internal logic |
| Integration Test | IT | IT-001 | Verify component collaboration |
| E2E Test | E2E | E2E-001 | Verify user scenario |
| Insight | INS | INS-001 | Improvement suggestion from review/research |
| Bug | BUG | BUG-001 | Bug fix record |
| Task | T | T-01 | Development task (2-digit exception) |

**Traceability**: `F → US → AC → (UT/IT/E2E)` and `INS → F`

## Skill Structure

Each skill lives in `skills/<skill-name>/` with a `SKILL.md` file:

```yaml
---
name: skill-name
description: What the skill does (used by agents for auto-discovery)
allowed-tools: Read, Write, Glob, Grep, Edit, Bash, AskUserQuestion
user-invocable: true  # (optional, defaults to true)
---

# Skill instructions in Markdown...
```

Some skills have a `templates/` subdirectory for additional reference files.

## Core Skills

### DevDocs Workflow (Document Generation)
- `devdocs-requirements` → `devdocs-system-design` → `devdocs-test-cases` → `devdocs-dev-tasks`
- Output location: `docs/devdocs/0X-[document-type].md`
- `devdocs-retrofit` adapts existing projects to the DevDocs flow

### Development Guidance (No Output Files)
- `code-quality` - MTE principles (Maintainability, Testability, Extensibility)
- `testing-guide` - Test quality constraints, mutation testing (≥80% mutation score)
- `ui-orchestrator` - UI/UX constraints for frontend development
- `refactor` - Test-driven refactoring (requires ≥80% coverage before refactoring)
- `git-safety` - Enforce `git mv`/`git rm` for tracked files
- `commit-convention` - Learn from `git log` then apply Conventional Commits

### Utility
- `work-report` - Generate weekly/monthly/quarterly/annual reports

## Key Principles

**MTE (Code Quality)**:
- Maintainability: Single responsibility, clear dependencies
- Testability: Core logic unit-testable, dependencies mockable (≥80% coverage)
- Extensibility: Reasonable extension points, no over-engineering

**TAR (Dev Tasks)**:
- Testable: Has test method and expected results
- Acceptable: Has quantifiable completion criteria
- Reviewable: Has code review checkpoints

## Commit Convention

Follow Conventional Commits style observed in git history:
```
type(scope): subject

Examples:
feat(testing-guide): add mutation testing support
refactor(skill-name): reorganize templates
```

## When Modifying Skills

1. Keep `SKILL.md` under 500 lines - use `templates/` for detailed reference material
2. Description field is critical - agents use it for auto-discovery
3. Use `allowed-tools` to restrict tool access when appropriate
4. Test skill triggering by asking questions that match the description
5. All test cases must reference AC (Acceptance Criteria) numbers for traceability
