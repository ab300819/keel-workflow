---
name: devdocs-requirements
description: Expand user requirements into detailed DevDocs documents. Use when users provide feature requirements, want to clarify requirements, or need to create product requirement documents. Triggers on keywords like "requirements", "PRD", "feature request", "user story".
allowed-tools: Read, Write, Glob, Grep, AskUserQuestion
---

# DevDocs Requirements Expansion

Expand brief user requirements into comprehensive product requirement documents.

## Language

- Accept questions in both Chinese and English
- Always respond in Chinese
- Generate all documents in Chinese

## Trigger Conditions

- User provides a feature requirement or idea
- User asks to create/write a PRD
- User wants to clarify or document requirements

## Workflow

1. **Understand the requirement**: Read user's initial input
2. **Explore codebase**: If in an existing project, understand current architecture
3. **Draft requirements**: Create comprehensive requirement document
4. **Confirm with user**: Get user approval before finalizing

## Output

**File**: `docs/devdocs/01-requirements.md`

If the document exceeds 300 lines, split into:
- `docs/devdocs/01-requirements.md` - Overview and core requirements
- `docs/devdocs/01-requirements-stories.md` - Detailed user stories
- `docs/devdocs/01-requirements-nfr.md` - Non-functional requirements

## Document Template

```markdown
# Requirements: <Feature Name>

## 1. Background

<Why this feature is needed, what problem it solves>

## 2. Target Users

<Who will use this feature, user personas>

## 3. Core Features

- [ ] Feature 1: <description>
- [ ] Feature 2: <description>

## 4. User Stories

| ID | Role | Expectation | Purpose |
|----|------|-------------|---------|
| US-01 | As a <role> | I want <feature> | So that <value> |

## 5. Acceptance Criteria

- [ ] AC-01: <measurable criterion>
- [ ] AC-02: <measurable criterion>
- [ ] AC-03: <measurable criterion>

## 6. Non-functional Requirements

- **Performance**: <requirements>
- **Security**: <requirements>
- **Compatibility**: <requirements>

## 7. Scope Boundaries

### In Scope
- <included items>

### Out of Scope
- <excluded items>

## 8. Assumptions and Dependencies

- <preconditions>
```

## Constraints

- [ ] Must confirm core features with user before finalizing
- [ ] Must define at least 3 acceptance criteria
- [ ] Must list scope boundaries to prevent scope creep
- [ ] Must NOT add major features user didn't mention without confirmation
- [ ] Each user story must follow "As a... I want... So that..." format
- [ ] Acceptance criteria must be measurable and verifiable

## Next Step

After user confirms requirements, suggest running `/devdocs-system-design` for system design phase.
