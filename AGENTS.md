# AI Agent Skills

This file provides guidance to AI coding agents when working with code in this repository.

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

## When Modifying Skills

1. Keep `SKILL.md` under 500 lines - use `templates/` for detailed reference material
2. Description field is critical - agents use it for auto-discovery
