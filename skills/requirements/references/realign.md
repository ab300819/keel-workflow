# requirements Realign 实例化

> 共享契约见 [../../pipeline/references/realign.md](../../pipeline/references/realign.md)。

## 当前 spec_version

**`req.v1`**（MVP 起点，未发生首次 bump）

## Migration Matrix（spec_version 演进）

### v1 → v2（保留字段，未来启用）

| 分级 | 变更项 | 修复动作 | 判据 |
|---|---|---|---|
| additive | （示例）AC 表新增"验收来源"列（PRD/Brainstorm/Insights） | 在 AC 表追加列，已有行默认 `—` 待人工补 | AC 表列数 < 当前模板 |
| additive | （示例）追溯矩阵新增"设计 ref"列 | 在 §5 追溯矩阵追加列 | 表头列数差异 |
| restructuring | （示例）US 模板字段重排（角色/动机/价值三分） | AskUserQuestion 呈现 before/after，逐 US 确认后改写 | US 段落缺字段标签 |

## Realign 子流程

### 入口

- 主入口：由 `/ms-pipeline realign` 编排层调度
- 底层直用：`/ms-requirements --realign[=scope]`，scope ∈ {features / stories / ac / trace / nfr}

### 流程

```text
1. 加载当前 spec_version 常量 + Migration Matrix
     │
     ▼
2. 扫描 01-requirements.md（含拆分文件）
     │
     ▼
3. 按 Matrix 定位差距
     ├── additive：章节/字段缺失
     └── restructuring：结构不兼容
     │
     ▼
4. 差距清单展示（按章节分组）
     │
     ▼
5. 用户确认（restructuring 逐项）
     │
     ▼
6. Edit 补齐 + 尾部追加 Realign Log
     │
     ▼
7. 幂等校验
```

### 输出

- 补齐后的 `01-requirements.md`
- `## Realign Log` 小节（格式见共享契约）
- yaml-summary-v1 信封（details：`{from_spec, to_spec, additive_count, restructuring_count, scope}`）

### 约束

- ❌ 不触发新一轮 Inversion gate（需求假设挑战）— 那是初始模式职责
- ❌ 不修改已确认的 F/US/AC 编号
- ❌ 不重算追溯矩阵语义（仅补齐列结构）
- ✅ 已有内容一律保留；realign 只做"按新规范的结构/字段差距"补齐

## 与其他模式边界

| 模式 | 触发 | realign 职责 |
|---|---|---|
| 初始 | 无 01-requirements.md | 不适用 |
| 增量 | 新增 F/US/AC | 不适用（由增量模式处理） |
| `--context` | 补充背景 | 不适用 |
| `--from-prd` | 消费 PRD 包 | 不适用（PRD 自有映射机制） |
| **Realign** | spec_version 落后 | 按规范结构差距补齐，**不新增/修改业务内容** |
