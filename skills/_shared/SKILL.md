---
name: _shared
description: ms-* 流程 skill 与部分独立 skill 共用的约束 SSOT，被它们以 `../_shared/constraints.md` 引用。这不是一个可调用的流程——不要为了完成任务而触发它；需要查约束时直接读 constraints.md。
---

# _shared

跨 skill 共享约束的载体。本目录不提供流程，只提供被其他 skill 引用的权威文件。

| 文件 | 内容 |
|------|------|
| [constraints.md](constraints.md) | 门控标记 / yaml-summary-v1 / Task 委托 / 用户确认 / Recovery 格式 / 只读 · dry-run / FUTURE 三态 / realign · spec_version / 分层记忆原则 / 作用域匹配 |
| [runlog.md](runlog.md) | 规则触发遥测的 append-only 运行日志格式 |

## 为什么它是一个 skill

安装器（`npx skills`）只搬运带 `SKILL.md` 的目录，且每个目录整个拷成自足单元——目录以外的文件不跟着走。没有这个文件，本目录不会被安装，装出去的各 skill 里 `../_shared/constraints.md` 全部指空。
