<!-- 由 /agent-memory 生成，请通过该命令更新 -->

# AI Agent Skills

## Project Overview

This is an **AI Agent Skills template collection** for **solo developers** - a set of reusable SKILL.md files that extend AI coding agents' capabilities for software development workflows. This is NOT a traditional codebase - it's a specification library of Markdown + YAML skill definitions. There are **no build, test, or lint commands** to run.

## Language Rules

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
| Branch Coverage Test | BCA | BCA-001 | Code branch coverage supplement test |

**Traceability**: `F -> US -> AC -> (UT/IT/E2E)` and `INS -> F` and `BCA` (branch coverage supplement)

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

**Discovery**: Read `skills/*/SKILL.md` description fields to find available skills.

**Templates**: Each skill's output document format is defined by templates in its `templates/` subdirectory.

## Context Management Pattern

Skills that generate repetitive structured content across multiple batches are prone to attention decay — later batches may have less detail or completeness than earlier ones. These skills MUST implement three elements:

1. **Batch Unit** — Natural boundary for splitting work (e.g., feature point F-XXX, test layer UT/IT/E2E)
2. **Quality Anchor** — First batch output serves as the quality reference; for data-driven skills, use completeness verification instead (reported count == actual count)
3. **Consistency Self-Check** — After each batch, compare against the anchor on key dimensions specific to that skill

## DevDocs Skill Architecture

### Orchestration Layer (user-facing entry points)

| Skill | Command | Purpose |
|-------|---------|---------|
| devdocs-pipeline | `/devdocs-pipeline` | Top-level orchestrator — 5 entry points (init/feature/bugfix/verify/close) |
| devdocs-feature | `/devdocs-feature` | Add new features — routes to atomic skills, auto-chains to dev-workflow |
| devdocs-bugfix | `/devdocs-bugfix` | Test-first bug fixing |

### Atomic Skills (called by orchestrators or directly)

| Skill | Command | Purpose |
|-------|---------|---------|
| devdocs-requirements | `/devdocs-requirements` | Expand requirements into F/US/AC |
| devdocs-system-design | `/devdocs-system-design` | Create/update system design (searches patterns/) |
| devdocs-test-cases | `/devdocs-test-cases` | Design test cases (UT/IT/E2E) |
| devdocs-dev-tasks | `/devdocs-dev-tasks` | Break down into executable tasks |
| devdocs-dev-workflow | `/devdocs-dev-workflow` | Execute development (skeleton-first + layered TDD) |
| devdocs-verify | `/devdocs-verify` | Unified verification: --docs / --impl / --ui |
| devdocs-sync | `/devdocs-sync` | Sync docs with implementation (trace+audit auto-serial) |
| devdocs-insights | `/devdocs-insights` | Collect improvement insights → requirements |
| devdocs-test-run | `/devdocs-test-run` | Execute test suites |
| devdocs-onboard | `/devdocs-onboard` | Generate project context for handover |
| devdocs-compound | `/devdocs-compound` | Extract experience patterns (recommended after sync) |
| devdocs-retrofit | `/devdocs-retrofit` | Migrate existing projects to DevDocs |

### Key Collaboration Chains

- **Init**: pipeline → requirements → system-design → test-cases → dev-tasks → dev-workflow → verify → sync
- **Feature**: pipeline → feature(→requirements→design→tests→tasks→dev-workflow) → verify → sync
- **Bugfix**: pipeline → bugfix(→dev-tasks→dev-workflow) → verify → sync
- **Close**: pipeline → sync → compound → onboard --update

### Sub-Agent Architecture

- Pipeline orchestrates via Task tool — each stage skill runs as independent sub-agent
- Sub-agents return structured YAML summaries (new IDs, status, blockers, output paths)
- Cross-stage data passes through filesystem (devdocs docs = source of truth)
- Main agent retains only: pipeline definition + stage summaries (~10K tokens)

## Pattern Library

DevDocs 工作流通过 `/devdocs-compound` 沉淀的经验模式存放在 `docs/devdocs/patterns/` 目录下。

- 每个模式文档遵循统一结构（问题背景、解决方式、适用条件、禁忌条件）
- 模式文档由 `/devdocs-compound` 在开发周期结束后自动生成
- Agent 在设计和开发阶段应检索此目录，复用已有经验
- 模式模板：`skills/devdocs-compound/templates/pattern.md`

## Conventions

- Commit format: Conventional Commits — `feat/fix/refactor/docs(scope): description`
- Keep SKILL.md under 500 lines — use `templates/` for detailed reference material
- Description field is critical for agent auto-discovery — must be accurate
