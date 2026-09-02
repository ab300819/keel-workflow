# 测试报告模板

> 由 `/ms-test-run` 自动生成，输出到 `docs/devdocs/05-test-report.md`

```markdown
# 测试报告

> 生成时间: {{timestamp}}
> 执行模式: {{mode}} (全量 / --ut / --it / --e2e / F-XXX / --trace / --affected)

## 执行摘要

| 指标 | 值 |
|------|-----|
| 总测试数 | {{total}} |
| 通过 | {{passed}} |
| 失败 | {{failed}} |
| 跳过 | {{skipped}} |
| 通过率 | {{pass_rate}}% |
| 覆盖率 | {{coverage}}%（如可用） |
| 执行时间 | {{duration}} |

## 分层结果

### 单元测试 (UT)

| 编号 | 描述 | 状态 | 耗时 |
|------|------|------|------|
| UT-001 | {{description}} | ✅/❌ | {{duration}} |

**统计**: {{ut_passed}}/{{ut_total}} 通过

### 集成测试 (IT)

| 编号 | 描述 | 状态 | 耗时 |
|------|------|------|------|
| IT-001 | {{description}} | ✅/❌ | {{duration}} |

**统计**: {{it_passed}}/{{it_total}} 通过

### E2E 测试 (E2E)

| 编号 | 描述 | 状态 | 耗时 |
|------|------|------|------|
| E2E-001 | {{description}} | ✅/❌ | {{duration}} |

**统计**: {{e2e_passed}}/{{e2e_total}} 通过

## 失败详情

### {{test_id}}: {{test_description}}

- **文件**: {{file_path}}:{{line_number}}
- **关联**: {{ac_id}}
- **错误信息**:
  ```
  {{error_message}}
  ```
- **建议**: {{suggestion}}

<!-- 重复上述格式，每个失败测试一个章节 -->

## 追溯验证结果

> 仅在 --trace 模式下生成

### 覆盖状态

| AC 编号 | 描述 | 关联测试 | 测试状态 | 覆盖状态 |
|---------|------|----------|----------|----------|
| AC-001 | {{description}} | UT-001, IT-001 | ✅ 全部通过 | ✅ 已覆盖 |
| AC-002 | {{description}} | UT-002 | ❌ 1/1 失败 | ⚠️ 测试失败 |
| AC-003 | {{description}} | — | — | ❌ 未覆盖 |

### 追溯统计

| 指标 | 值 |
|------|-----|
| AC 总数 | {{ac_total}} |
| 已覆盖（测试通过） | {{ac_covered}} |
| 测试失败 | {{ac_test_failed}} |
| 未覆盖 | {{ac_uncovered}} |
| 覆盖率 | {{ac_coverage}}% |

### 标注一致性

| 类型 | 数量 | 详情 |
|------|------|------|
| ⚠️ 标注不一致 | {{inconsistent_count}} | {{details}} |
| ℹ️ 孤立测试 | {{orphan_count}} | {{details}} |

## 覆盖范围

> 仅 --affected 模式时填写，全量模式可省略。

- 模式：{{run_mode}}
- 比较基线：{{base_ref}}
- 变更文件：{{changed_files}}
- 匹配测试：{{matched_tests}}
- 未覆盖变更：{{uncovered_files}}

## 建议

<!-- 根据测试结果自动生成建议 -->

- [ ] **未覆盖 AC**: 为 {{ac_ids}} 补充测试用例
- [ ] **失败测试**: 修复 {{test_ids}} 中的断言错误
- [ ] **标注不一致**: 同步 {{files}} 中的追溯标注
```

## 模板使用说明

### 占位符

- `{{xxx}}` 格式的占位符由 `/ms-test-run` 在生成报告时替换为实际值
- 章节根据实际执行结果动态增减（无失败则省略失败详情，非 --trace 则省略追溯验证，非 --affected 则省略覆盖范围）

### 输出规则

- 文件路径: `docs/devdocs/05-test-report.md`
- 每次执行覆盖之前的报告（保留最新一份）
- 报告生成后输出摘要到终端
