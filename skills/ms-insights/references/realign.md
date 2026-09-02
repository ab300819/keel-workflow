# insights Realign 实例化

> 共享契约见 [../../ms-pipeline/references/realign.md](../../ms-pipeline/references/realign.md)。

## 当前 spec_version

**`ins.v1`**（MVP 起点）

## Migration Matrix（保留字段）

### v1 → v2（未来启用）

| 分级 | 变更项 | 修复动作 | 判据 |
|---|---|---|---|
| additive | （示例）INS 条目新增"转化优先级"字段 | 追加字段；已有条目默认 `—` | INS 块缺字段 |
| restructuring | （示例）"来源类型"枚举变化 | AskUserQuestion 逐条确认映射 | 现有值不在新枚举内 |

## Realign 子流程

入口：`/ms-insights --realign`，或通过 `/ms-pipeline realign` 编排调度。

流程（简化版，遵循共享契约骨架）：
1. 扫描 `docs/devdocs/05-insights.md`
2. 对照 Matrix 定位差距
3. additive → Edit 补齐；restructuring → AskUserQuestion 逐条确认
4. 尾部追加 Realign Log

## 约束

- ❌ 不新增/修改 INS 条目的业务内容（realign 只补规范缺字段）
- ❌ 不触发"确认→转化为需求"流程（那是标准模式职责）
- ✅ 保留已转化状态标记
