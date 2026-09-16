# --impl 完成度判定标准（IT 断言完备性 + DoD 粒度）

verify `--impl` 维度的一组增强约束详细判定。SKILL.md「检查约束」节列出短规则条目，本文件展开判定逻辑。

## 为什么需要（根因）

`--impl` 默认只看 IT 用例是否通过，不比对断言数量与 spec 的量化期望；DoD checkbox 是文本级标记，无机器校验。二者叠加会产生**"测试全绿 + DoD 全勾，但完成度远低于 spec 期望"**的静默缺口——`--impl` / `--readiness` / `--sync --check` 三个维度都不会检出。

## 检测触发条件

下列任一为真时启用本组检查：

1. 任务 spec / `03-test-cases.md` / `04-dev-tasks.md` 中 IT-XXX 条目显式提及"N 类断言 / N 项校验 / 期望覆盖 N 个 case"等量化期望。
2. 任务 commit 引入新测试方法，但 IT 用例所属测试类与 spec 期望断言类型集存在 diff。
3. 用户在 sprint closure 阶段调用 `--impl` 或 `--readiness`。

## 判定规则

| 情形 | 判定 | 行为 |
|------|------|------|
| 期望 N 类断言，实际落地 N 类（测试方法数 ≥ N 且类级断言粒度覆盖全部类型） | ✅ 满足 | 允许 DoD ✅ |
| 期望 N 类断言，实际落地 K 类（K < N），DoD 整项 ✅ 且无拆分 | ❌ P1 | ⛔ 阻断 DoD；必须拆分子任务或更新 spec 期望 |
| 期望 N 类断言，实际落地 K 类，DoD 显式标 `[完成 K/N 类]` 并把剩余转下版本 candidate | ⚠️ 部分满足（P2） | 允许通过但记录 deferred |
| spec 未量化期望（无 N 类描述） | ⏭️ 跳过 | 不触发本检查（依赖 B1 AC 语义判断） |

## 恢复方式

- 补齐缺失断言并重新跑测试用例 → 重新执行 `--impl --ac` 转 ✅ 满足。
- 拆分子任务：把剩余 (N - K) 类断言转为新任务（如 T-XXX-followup-1），DoD 标 `[完成 K/N 类，剩余 (N-K) 类转 T-XXX-followup-1]`。
- 更新 spec：若 N 期望本身过高，更新 `03-test-cases.md` 中 IT-XXX 期望数量并附调整理由（建议 cross-link 设计 trade-off 决策）。

## 边界：项目专有检查不写在这里

本文件只保留**语言与领域中立**的判定。项目特有的完成度盲区（某语言分层契约的字段透传、某框架的断言 API、某业务域的字段映射矩阵等）属**项目级知识**，写入该项目的 `docs/devdocs/patterns/verify-blindspots.md`——SKILL.md 检查约束节已声明会自动加载该文件作为额外检查项，插件位本来就在。

**不得**把项目实战发现提拔为本 skill 的默认强制约束；理由与边界见 [`shared/constraints.md`](../../shared/constraints.md) § `doc/project-rule-boundary`。
