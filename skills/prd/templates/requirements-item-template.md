---
id: FR-XX
title: {{功能名称}}
type: FR                    # FR | NFR
source_prd: ""              # 所属 PRD 的 prd_id（multi-PRD 必填，legacy 省略）
source_chunk: FR-XX         # 对应 chunks/ 中的文件 ID
moscow: Must                # Must | Should | Could | Won't
maturity: draft             # idea | draft | ready
status: clarified           # clarified（brainstorm 产出即为已澄清）→ outdated
relation: new               # new | extend | modify（与已有系统的关系）
related_module: ""          # extend/modify 时标注关联的已有模块名
---

## 来源追溯

- 原始 chunk: `../chunks/{{source_chunk}}-{{主题}}.md`
- 初判分类: {{FR/NFR}}
- 终判分类: {{FR/NFR}}（一致 / 复判自 FR-XX）

## 用户角色与场景

| 用户角色 | 使用场景 | 目标 |
|----------|----------|------|
| {{角色}} | {{场景}} | {{目标}} |

## 功能描述

{{结构化的功能需求描述，由 brainstorm 澄清后产出}}

## 验收意图

> 非正式验收标准，供 ms-requirements 转化为正式 AC。

1. {{当...时，应该...}}
2. {{当...时，应该...}}

## 约束与依赖

- {{与其他 FR/NFR 的依赖关系}}

## 开放问题

- [ ] {{待澄清的问题}}
