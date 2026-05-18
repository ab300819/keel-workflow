# 代码分支覆盖分析详解

> ℹ️ 本文件提及的 `@verifies` 等标注属于 **layout.v1 legacy**（v2 起改读 traceability.yml，[FUTURE 状态](../../pipeline/references/layout/docs-layout-migration.md#-执行接口落地状态future)）。

## 理念

### 为什么需要分支分析？

需求驱动测试（AC → 测试）覆盖的是**业务规则**，但代码实现中常包含需求文档未明确描述的逻辑：

- 防御性编程：null 检查、参数校验、类型保护
- 错误处理路径：try/catch、错误重抛、降级策略
- 隐式分支：if 无 else、switch 无 default
- 边界条件：空集合、溢出、并发竞争

这些逻辑不对应任何 AC，但如果出错同样会导致系统故障。

### 双向测试保障

```
AC 驱动测试   → 验证"系统应该做什么"（业务正确性）
分支覆盖分析  → 验证"系统不应该崩溃"（健壮性）
变异测试     → 验证"测试能否发现 bug"（测试质量）
```

三者互补，不是替代关系。

> **⚠️ 回溯规则**：BCA 分析发现的**业务逻辑分支**应回溯到对应 AC，转为正式测试（UT/IT/E2E 编号）；仅**防御性逻辑**（null 检查、类型保护、异常兜底等）保留 BCA 编号。断言必须来自 03-test-\*.md 中对应 AC 的测试用例，禁止从实现代码反推测试。业务分支回溯时，应先在需求/测试文档中补齐 AC 和测试编号，再编写正式测试。

---

## 分支类型清单

### 条件分支

| 代码模式 | 需要测试的路径 | 示例 |
|----------|---------------|------|
| `if/else` | true 分支 + false 分支 | `if (user.isAdmin)` |
| `if` (无 else) | true + 隐式 false（跳过） | `if (!valid) return;` |
| `switch/case` | 每个 case + default | `switch (status)` |
| 三元表达式 | 两个分支 | `isAdmin ? admin() : user()` |
| `&&` 短路 | 左假 + 左真右假 + 全真 | `a && b()` |
| `||` 短路 | 左真 + 左假右真 + 全假 | `a || fallback()` |
| `??` 空值合并 | 非空 + 空值 | `name ?? 'default'` |

### 异常路径

| 代码模式 | 需要测试的路径 |
|----------|---------------|
| `try/catch` | 正常路径 + 各类异常触发 |
| `throw` | 触发条件 |
| `Promise.reject` | 拒绝场景 |
| 错误重抛 | catch 中 `throw error` 的条件 |
| 降级策略 | catch 中返回默认值的路径 |

### 循环边界

| 代码模式 | 需要测试的路径 |
|----------|---------------|
| `for/while` | 零次执行、一次执行、多次执行 |
| `for...of` | 空集合、单元素、多元素 |
| `break/continue` | 触发条件 |
| 提前终止 | 循环内 return 的条件 |

### 早返回（Guard Clause）

```typescript
function processOrder(order: Order) {
  if (!order) throw new Error('required');        // Guard 1
  if (order.items.length === 0) return empty();   // Guard 2
  if (order.cancelled) return cancelled();         // Guard 3
  // 主逻辑...
}
```

每个 guard clause 都需要独立测试。

---

## 完整分析示例

### 示例代码

```typescript
async function processOrder(order: Order): Promise<OrderResult> {
  // Guard 1: null 检查
  if (!order) {
    throw new Error('Order is required');
  }

  // Guard 2: 空订单
  if (order.items.length === 0) {
    return { status: 'empty', total: 0 };
  }

  // 业务逻辑分支
  const total = calculateTotal(order.items);

  if (total > 1000) {
    // 高价值订单路径
    order.discount = 0.1;
    await notifyManager(order);
  } else if (total > 500) {
    // 中价值订单路径
    order.discount = 0.05;
  }
  // else: 无折扣路径（隐式）

  // 异常处理
  try {
    await saveOrder(order);
  } catch (error) {
    if (error instanceof DatabaseError) {
      throw new OrderProcessingError('Failed to save', error);
    }
    throw error; // 未知错误重抛
  }

  return { status: 'completed', total };
}
```

### 分支分析表

| # | 分支描述 | 类型 | AC 已覆盖 | 需补充 |
|---|---------|------|----------|--------|
| B1 | order 为 null/undefined | 早返回 | ❌ | ✅ |
| B2 | order.items 为空 | 早返回 | ❌ | ✅ |
| B3 | total > 1000（高价值） | 条件 | ✅ AC-003 | ❌ |
| B4 | 500 < total ≤ 1000（中价值） | 条件 | ❌ | → 回溯 AC（业务逻辑，应归入 AC） |
| B5 | total ≤ 500（无折扣，隐式） | 隐式 | ❌ | → 回溯 AC（业务逻辑，应归入 AC） |
| B6 | saveOrder 成功 | 正常路径 | ✅ AC-001 | ❌ |
| B7 | saveOrder 抛 DatabaseError | 异常 | ❌ | ✅ |
| B8 | saveOrder 抛其他 Error | 异常 | ❌ | ✅ |

### 生成的补充测试

```typescript
/**
 * @covers-branch processOrder:null-order-guard
 * @testcase BCA-001
 */
test('processOrder 应该抛出错误当 order 为 null', async () => {
  await expect(processOrder(null)).rejects.toThrow('Order is required');
});

/**
 * @covers-branch processOrder:empty-items-guard
 * @testcase BCA-002
 */
test('processOrder 应该返回 empty 状态当订单无商品', async () => {
  const order = { items: [], cancelled: false };
  const result = await processOrder(order);
  expect(result.status).toBe('empty');
  expect(result.total).toBe(0);
});

// ⚠️ 以下 AC-???/UT-??? 为占位符，不可直接落盘；须先在 03-test-*.md 分配正式编号后替换

/**
 * ↓ BCA 发现业务逻辑分支：需先在 03-test-*.md 补齐 AC 和测试编号，再写正式测试
 * @verifies AC-??? - 中价值订单折扣（待需求/测试文档补齐）
 * @testcase UT-???
 */
test('processOrder 应该应用 5% 折扣当总额在 500-1000 之间', async () => {
  const order = { items: [{ price: 600, quantity: 1 }], cancelled: false };
  const result = await processOrder(order);
  expect(order.discount).toBe(0.05);
});

/**
 * ↓ BCA 发现业务逻辑分支：需先在 03-test-*.md 补齐 AC 和测试编号，再写正式测试
 * @verifies AC-??? - 无折扣路径（待需求/测试文档补齐）
 * @testcase UT-???
 */
test('processOrder 应该无折扣当总额 ≤ 500', async () => {
  const order = { items: [{ price: 100, quantity: 1 }], cancelled: false };
  const result = await processOrder(order);
  expect(order.discount).toBeUndefined();
});

/**
 * @covers-branch processOrder:database-error-handling
 * @testcase BCA-003
 */
test('processOrder 应该抛出 OrderProcessingError 当数据库错误', async () => {
  mockSaveOrder.mockRejectedValue(new DatabaseError('connection failed'));
  const order = { items: [{ price: 100, quantity: 1 }] };
  await expect(processOrder(order)).rejects.toThrow(OrderProcessingError);
});

/**
 * @covers-branch processOrder:unknown-error-rethrow
 * @testcase BCA-004
 */
test('processOrder 应该重抛未知错误', async () => {
  const unknownError = new Error('unknown');
  mockSaveOrder.mockRejectedValue(unknownError);
  const order = { items: [{ price: 100, quantity: 1 }] };
  await expect(processOrder(order)).rejects.toThrow('unknown');
});
```

---

## 分析报告模板

分支覆盖分析完成后，在终端输出报告：

```
📊 分支覆盖分析报告

分析范围: src/services/order.service.ts → processOrder()

分支统计:
  总分支数:      8
  AC 测试已覆盖:  2 (25%)
  需补充:        6 (75%)
  补充后覆盖率:   100%

未覆盖分支（防御性逻辑 → BCA）:
  #B1 null-order-guard        → BCA-001
  #B2 empty-items-guard       → BCA-002
  #B7 database-error-handling → BCA-003
  #B8 unknown-error-rethrow   → BCA-004

回溯到 AC（业务逻辑 → 先补齐需求文档再写正式测试）:
  #B4 medium-value-discount   → 待补齐 AC/UT（需更新 03-test-*.md）
  #B5 no-discount-path        → 待补齐 AC/UT（需更新 03-test-*.md）

生成补充测试: 4 个 BCA + 2 个待回溯（需补齐 AC）
```

---

## 编号规范

BCA 编号独立于主追溯矩阵（不对应 AC），但记录在分支覆盖分析报告中：

| 类型 | 前缀 | 说明 |
|------|------|------|
| 分支补充测试 | BCA | Branch Coverage Analysis，代码分支覆盖补充测试 |

BCA 编号从 BCA-001 开始，按文件/模块范围独立编号。

---

## 与覆盖率工具的协作

分支覆盖分析可结合覆盖率工具的报告辅助 AI 分析：

```bash
# 生成覆盖率报告（含分支覆盖）
npm test -- --coverage --coverageReporters=json   # Jest
pytest --cov=src --cov-branch --cov-report=json   # pytest
go test -cover -coverprofile=coverage.out ./...    # Go
```

覆盖率工具提供**哪些行/分支未覆盖**的定量数据，AI 分析提供**为什么未覆盖、如何测试**的定性洞察。两者结合效果最佳。
