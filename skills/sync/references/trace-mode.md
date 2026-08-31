# 代码追溯扫描 (--trace)

> 扫描代码中的 `@requirement`/`@satisfies`/`@verifies` 标注，与文档进行交叉验证，自动更新追溯矩阵的代码位置列。

## 扫描流程

```
1. 读取 03-test-cases.md 追溯矩阵
   ├── 03 不存在且 AC 标 `来源: inline` → 跳过该 AC 的 trace 写入,提示"inline 条目待回填"(见 [dev-workflow inline-entry.md](../../dev-workflow/references/inline-entry.md))
   │
   ▼
2. 扫描代码文件
   ├── 搜索 @satisfies AC-XXX 标注 → 提取入口代码位置
   ├── 搜索 @verifies AC-XXX 标注 → 提取测试代码位置
   └── 搜索 @verifies BUG-XXX 标注 → 通过 Bug 文档的 关联功能 字段映射到 AC，更新对应行
   │
   ▼
3. 交叉验证
   ├── 文档有 AC，代码无标注 → ⚠️ 缺失实现标注
   └── 代码有标注，文档无 AC → ⚠️ 孤立标注
   │
   ▼
4. 更新追溯矩阵
   └── 填充"入口代码"和"测试代码"列
```

## 扫描规则

| 标注 | 搜索模式 | 提取内容 |
|------|----------|----------|
| `@satisfies AC-XXX` | 方法/函数上方注释 | 文件路径:行号 |
| `@verifies AC-XXX` | 测试用例上方注释 | 文件路径:行号 |
| `@verifies BUG-XXX` | 测试用例上方注释 | 通过 Bug 关联功能 映射到 AC 行 |
| `@requirement F-XXX` | 类/模块上方注释 | 文件路径 |
| `@testcase UT/IT/E2E-XXX` | 测试用例上方注释 | 文件路径:行号 |

## 扫描输出格式

```markdown
# 代码追溯扫描报告

**扫描时间**：2024-XX-XX
**扫描范围**：src/, tests/

## 文档 → 代码 验证

| AC 编号 | 入口代码 | 测试代码 | 状态 |
|---------|----------|----------|------|
| AC-001 | `src/user.ts:15` | `tests/user.test.ts:20` | ✅ |
| AC-002 | `src/user.ts:15` | `tests/user.test.ts:35` | ✅ |
| AC-003 | `src/user.ts:42` | - | ⚠️ 缺测试 |
| AC-004 | - | - | ❌ 无标注 |

## 代码 → 文档 验证

| 代码位置 | 标注 | 文档存在 | 状态 |
|----------|------|----------|------|
| `src/cache.ts:10` | @satisfies AC-099 | ❌ | ⚠️ 孤立标注 |
| `tests/helper.test.ts:5` | @verifies AC-005 | ✅ | ✅ |

## 矩阵更新

已更新 03-test-cases.md 追溯矩阵：
- 填充 3 个入口代码位置
- 填充 2 个测试代码位置
- 标记 1 个缺失实现
```

## 使用场景

```bash
# 任务完成后更新矩阵
/ms-sync              # trace 已合并到默认模式

# 结合完整同步
/ms-sync
# → 自动包含 trace 结果

# 仅查看不更新
/ms-sync --check
# → 显示追溯状态但不修改文件
```

## 约束

- [ ] **扫描基于标注，不解析代码逻辑**
- [ ] **只更新矩阵的代码位置列和状态列**
- [ ] **不自动创建或删除矩阵行**
- [ ] 发现孤立标注时提示用户处理
