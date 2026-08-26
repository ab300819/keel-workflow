# retrofit Realign 实例化

> 共享契约见 [../../pipeline/references/realign.md](../../pipeline/references/realign.md)。

## 当前 spec_version

**`baseline.v1`**（MVP 起点）

适用产物：`docs/devdocs/00-baseline.md`（`ms-retrofit` 基线路径产出）。

版本迁移路径的 `00-retrofit-report.md` 是一次性报告、非持久 A/B 类产物，不纳入 `spec_version` 体系。

## Migration Matrix（保留字段）

### v1 → v2（未来启用）

| 分级 | 变更项 | 修复动作 | 判据 |
|---|---|---|---|
| additive | （示例）新增章节 | 追加章节占位，标注待人工填写 | §章节缺失 |
| restructuring | （示例）来源标注枚举扩展 | AskUserQuestion 呈现 before/after | 标注值不在枚举内 |

## Realign 子流程

入口：`/ms-pipeline realign --scope=spec` 编排调度。

⛔ **基线不得被自动覆盖重生成。** realign 只做**结构性**查漏补缺（缺失章节追加占位、frontmatter 字段补齐），**不得改写任何带 `用户确认` / `已有文档` / `推导待确认` 标注的正文内容**——那些是问人和挖证据得来的，重生成产不出来。

判据见 [spec §2 派生 vs 原生](../../../docs/superpowers/specs/2026-08-25-retrofit-baseline-design.md)：`codebase-insight.md` 与 `00-context.md` 可被扫描重建，基线不可。把基线当可重生成产物处理，等于把它降级成前两者的副本。
