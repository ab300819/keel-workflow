# onboard Realign 实例化

> 共享契约见 [../../pipeline/references/realign.md](../../pipeline/references/realign.md)。

## 当前 spec_version

**`context.v1`**（MVP 起点）

## Migration Matrix（保留字段）

### v1 → v2（未来启用）

| 分级 | 变更项 | 修复动作 | 判据 |
|---|---|---|---|
| additive | （示例）新增"近期变更"章节 | 追加章节占位，标注 `--update` 后自动填充 | §章节缺失 |
| restructuring | （示例）"快速开始"字段结构变更 | AskUserQuestion 呈现 before/after | 字段格式不匹配 |

## Realign 子流程

入口：`/onboard --realign`，或 `/pipeline realign` 编排调度。

流程：
1. 扫描 `docs/devdocs/00-context.md`
2. 对照 Matrix 定位结构差距
3. additive → Edit 补齐（需扫描项目的章节标记 "待 --update 填充"，不自动执行扫描）
4. restructuring → AskUserQuestion
5. 尾部追加 Realign Log

## 约束

- ❌ 不触发项目扫描（那是 `--update` 职责）
- ❌ 不修改已填充的项目信息内容
- ✅ 结构差距补齐后，如用户要新数据 → 提示运行 `/onboard --update`
