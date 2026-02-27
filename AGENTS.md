<!-- 由 /agent-memory 生成，请通过该命令更新 -->

# AI Agent Skills

## Project Overview

This is an **AI Agent Skills template collection** for **solo developers** - a set of reusable SKILL.md files that extend AI coding agents' capabilities for software development workflows. This is NOT a traditional codebase - it's a specification library of Markdown + YAML skill definitions. There are **no build, test, or lint commands** to run.

## Language Rules

- Accept questions in both Chinese and English
- Always respond in Chinese
- Generate all documents in Chinese

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

## 约定

- 提交格式：Conventional Commits — `feat/fix/refactor/docs(scope): description`
- SKILL.md 不超过 500 行，用 `templates/` 存放详细参考材料
- Description 字段是 agents 自动发现的关键，务必准确
