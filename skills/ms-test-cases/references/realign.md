# test-cases Realign 实例化

> 共享契约见 [../../ms-pipeline/references/realign.md](../../ms-pipeline/references/realign.md)。

## 当前 spec_version

**`test.v2`**（v1→v2：追溯矩阵改反向依赖，见 Migration Matrix）

## Migration Matrix（spec_version 演进）

### v1 → v2（反向依赖）

| 分级 | 变更项 | 修复动作 | 判据 |
|---|---|---|---|
| restructuring | 追溯矩阵「入口代码 / 测试代码」两列（`src/user.ts:15` 行号）合并为「变更来源」一列（`<repository>@<sha>` + 一句话描述）| AskUserQuestion 呈现 before/after；存量行号无法自动转换为 sha，逐 AC 由用户确认写入或标待补 | 表头含「入口代码」或「测试代码」列 |
| restructuring | 数据源从「扫描代码 `@satisfies`/`@verifies` 标注」改为「Commit 2 写入文档」| 存量矩阵保留原值不动，新增 AC 走新流程；⛔ 不批量回填 | §3 说明段仍写「标注扫描」|

### v1 → v2（保留字段，未来启用）

| 分级 | 变更项 | 修复动作 | 判据 |
|---|---|---|---|
| additive | （示例）测试用例模板新增"测试类型理由"字段（UT/IT/E2E 选择理由） | 追加字段；已有用例默认 `—` 待补 | 用例块缺"测试类型理由"字段 |
| additive | （示例）追溯矩阵新增"覆盖率模式"列（branch/line/statement） | 表头追加列 | 表头列数差异 |
| restructuring | （示例）AC↔测试映射从"1:N 散列"改为"矩阵块" | AskUserQuestion 逐 AC 呈现 before/after 确认 | §3 追溯矩阵格式不匹配 |

## Realign 子流程

### 入口

- 主入口：`/ms-pipeline realign` 编排调度
- 底层：`/ms-test-cases --realign[=scope]`，scope ∈ {strategy / coverage / trace / cases}

### 流程

```text
1. 加载 spec_version 常量 + Matrix
     │
     ▼
2. 扫描 03-test-*.md（含拆分文件）
     │
     ▼
3. 定位差距（additive / restructuring）
     │
     ▼
4. 差距清单展示
     │
     ▼
5. 用户确认（restructuring 逐项）
     │
     ▼
6. Edit 补齐 + 尾部 Realign Log
     │
     ▼
7. 幂等校验
```

### 输出

- 补齐后的 `03-test-*.md`
- `## Realign Log` 小节
- yaml-summary-v1（details：`{from_spec, to_spec, additive_count, restructuring_count, scope, missing_test_types}`）

### 约束

- ❌ 不补写测试实现代码（那是 ms-dev-workflow --realign 职责）
- ❌ 不重新选择 AC↔测试类型映射（除非 restructuring 且用户确认）
- ✅ **缺失的测试类型**列入差距清单，传递给 ms-dev-workflow 让 Test Agent 补写实际测试
- ✅ 保留已有追溯标注

## 与其他 skill 的协同

| 差距类型 | 本 skill 职责 | 传递给 |
|---|---|---|
| 测试用例文档字段/结构差距 | ✅ 直接补齐 | — |
| AC↔测试映射格式差距 | ✅ 结构补齐 | — |
| 缺失 UT/IT/E2E（测试类型覆盖不全） | 仅列差距清单 | ms-dev-workflow --realign（写实际测试） |
