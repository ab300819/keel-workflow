# 任务执行流程详解

各层级任务的详细执行流程。

## 多任务编排流程

批量模式下，外层循环包裹单任务执行流程：

```
┌─ 外层编排 ────────────────────────────────────────┐
│                                                    │
│  1. 批量指定符解析                                  │
│     └── T-XX~T-YY / F-XXX / US-XXX / --all        │
│                    │                                │
│                    ▼                                │
│  2. 依赖解析 + 拓扑排序                             │
│     └── 递归收集依赖 → 已完成跳过 → DAG → 排序     │
│                    │                                │
│                    ▼                                │
│  3. 逐任务循环                                      │
│     ┌──────────────────────────────────────┐       │
│     │  a. 断点检测（5 步流水线）            │       │
│     │  b. 执行单任务流程（见下方各层级流程） │       │
│     │  c. Commit 1: 代码提交               │       │
│     │  d. 更新任务状态 + /devdocs-sync --trace │    │
│     │  e. Commit 2: 文档+追踪提交          │       │
│     └──────────────────────────────────────┘       │
│                    │                                │
│                    ▼                                │
│  4. 批量执行报告                                    │
│                                                    │
└────────────────────────────────────────────────────┘
```

> 详见 [task-orchestration.md](task-orchestration.md)

## 核心逻辑任务（强制 TDD）🔴

```
1. 开始任务
   │
   ▼
2. 生成接口骨架（Step 1）
   ├── 方法签名 + @requirement/@satisfies 标注
   └── 方法体: throw new Error('Not implemented')
   │
   ▼
3. 生成测试骨架（Step 2）
   ├── 测试结构 + @verifies/@testcase 标注
   └── 测试体: test.skip()
   │
   ▼
4. 移除 skip，编写测试断言
   │
   ▼
5. 运行测试 → 确认失败（红）
   │
   ▼
6. 实现接口细节（遵循 /code-quality）
   │
   ▼
7. 运行测试 → 确认通过（绿）
   ├── 失败 → 修复实现 → 重新测试（最多 N 次，默认 3；超限标记任务失败）
   │
   ▼
8. 重构代码（保持测试通过）
   │
   ▼
9. 检查验收标准（AC-XXX）
   ├── 全部满足 ─────────────┐
   └── 未满足 → 补充测试+实现 │
                             ▼
10. 对抗式验证（🔴 自动触发）
   ├── Phase 1: 代码质量审查（/code-quality）
   ├── Phase 2: 测试完备性审查（/testing-guide）
   ├── Phase 3: 综合报告
   ├── Blocker → 修复 → 重新验证
   └── 通过 ────────────────┐
                             ▼
11. 更新自描述（/code-self-describe --update）
   │
   ▼
12. 提交决策（--headless 自动提交 / 交互模式询问用户）
   │
   ▼
13. Commit 1: 代码提交
   │
   ▼
14. 更新任务状态 + /devdocs-sync --trace → Commit 2: 文档提交
```

## 接口层任务（推荐 TDD）🟡

```
1. 开始任务
   │
   ▼
2. 生成接口骨架（带标注）
   │
   ▼
3. 生成测试骨架（带标注）
   │
   ▼
4. [推荐] 移除 skip，编写接口测试
   │
   ▼
5. 实现接口逻辑
   │
   ▼
6. 运行测试 → 确认通过
   │
   ▼
7. 检查验收标准 → Review → Commit 1: 代码提交
   │
   ▼
8. 更新任务状态 + /devdocs-sync --trace → Commit 2: 文档提交
```

## UI 层任务（可选 TDD）🟢

```
1. 开始任务
   │
   ▼
2. 生成组件骨架（带标注）
   │
   ▼
3. 生成 E2E 测试骨架（带标注）
   │
   ▼
4. 实现 UI 组件（遵循 /ui-orchestrator）
   │
   ▼
5. 视觉验证（手动检查）
   │
   ▼
6. 移除 skip，完善 E2E 测试
   │
   ▼
7. 运行测试 → 确认通过
   │
   ▼
8. 检查验收标准 → Review → Commit 1: 代码提交
   │
   ▼
9. 更新任务状态 + /devdocs-sync --trace → Commit 2: 文档提交
```

## 基础设施任务 ⚪

```
1. 开始任务
   │
   ▼
2. 实现基础设施（DB/配置/部署）
   │
   ▼
3. 运行集成测试验证
   │
   ▼
4. 检查验收标准 → Review → 提交
```

## 任务完成流程

### TDD 任务（核心逻辑 🔴）

1. **确认测试先行**：检查是否先写了测试
2. **确认红-绿循环**：测试从失败到通过
3. **检查重构**：代码是否经过优化
4. **验证验收标准**：检查所有 AC 是否满足
5. **对抗式验证**（自动触发）：
   - Phase 1: 代码质量审查（/code-quality 视角）
   - Phase 2: 测试完备性审查（/testing-guide 视角）
   - Phase 3: 综合报告，处理 Blocker
6. **更新自描述**：运行 /code-self-describe --update
7. **提交决策**：
   - `--headless` 模式：自动提交
   - 交互模式：AskUserQuestion："是否提交代码？" → "提交" / "继续修改" / "跳过"
8. **如提交**（原子提交）：
   - Commit 1: `git add [代码文件] && git commit -m "<type>(T-XX): <名称>"`
   - 更新 04-dev-tasks*.md 状态为 `已完成`
   - 运行 /devdocs-sync --trace
   - Commit 2: `git add [文档文件] && git commit -m "docs(T-XX): 更新任务状态并同步 trace"`
9. **更新 TodoWrite**：将任务标记为已完成

### 非 TDD 任务（接口/UI/基础设施）

1. **执行测试**：运行任务定义的测试方法
2. **验证验收标准**：检查所有验收标准是否满足
3. **对抗式验证**（如 --review 触发）：同上 Phase 1-3
4. **自查 Review 要点**：检查代码审查要点
5. **提交决策**：
   - `--headless` 模式：自动提交
   - 交互模式：AskUserQuestion："是否提交代码？" → "提交" / "继续修改" / "跳过"
6. **如提交**（原子提交）：
   - Commit 1: `git add [代码文件] && git commit -m "<type>(T-XX): <名称>"`
   - 更新 04-dev-tasks*.md 状态为 `已完成`
   - 运行 /devdocs-sync --trace
   - Commit 2: `git add [文档文件] && git commit -m "docs(T-XX): 更新任务状态并同步 trace"`
7. **更新 TodoWrite**：将任务标记为已完成

## 提交信息格式

遵循 `/commit-convention` 规范，格式如下：

```
<type>(T-XX): <任务名称>

- <完成内容1>
- <完成内容2>

关联: F-XXX, AC-XXX
测试: UT-XXX, IT-XXX 通过
```

**type 类型**：feat | fix | refactor | test | docs | chore

## TodoWrite 集成

用户确认开始开发时：

```
使用 TodoWrite 添加任务：
- 每个任务成为一个 todo 项
- 保持定义的任务顺序
- todo 内容包含任务编号
- 提交后更新状态
```

### 批量模式下 TodoWrite

```
1. 初始化：将执行队列中所有任务添加为 todo 项
2. 执行中：当前任务标记为 in_progress
3. 完成时：任务标记为 completed
4. 断点续做：读取 TodoWrite 状态辅助判断进度
```
