# 多任务编排

批量执行、依赖解析、断点续做的完整规范。

## 1. 批量指定符解析

### 语法

```
/ms-dev-workflow T-03                # 单任务（现有行为）
/ms-dev-workflow T-01~T-05           # 范围
/ms-dev-workflow T-01,T-03,T-07      # 枚举
/ms-dev-workflow F-001               # 按功能点（通过 关联需求 字段反查）
/ms-dev-workflow US-001              # 按用户故事（同上）
/ms-dev-workflow --all               # 所有待开发任务
```

### 解析流程

```
1. 读取 docs/devdocs/04-dev-tasks*.md
2. 识别指定符类型
   ├── T-XX          → 直接使用
   ├── T-XX~T-YY     → 展开范围内所有任务 ID
   ├── T-XX,T-YY,... → 拆分为任务 ID 列表
   ├── F-XXX         → 扫描所有任务的 关联需求 字段，匹配 F-XXX
   ├── US-XXX        → 扫描所有任务的 关联需求 字段，匹配 US-XXX
   └── --all         → 收集所有 状态≠已完成 的任务
3. 返回去重后的任务 ID 列表
```

### 验证规则

- 任务 ID 不存在 → 报错，列出无效 ID
- 范围 `T-XX~T-YY` 中 XX > YY → 报错
- F-XXX / US-XXX 无匹配任务 → 警告，确认是否继续
- 结果为空 → 报错终止

## 2. 依赖解析

### 拓扑排序算法

```
输入：目标任务 ID 列表
输出：按依赖顺序排列的执行队列

1. 从目标任务列表出发，递归收集所有 依赖 字段引用的任务
2. 对每个依赖任务：
   ├── 状态=已完成 → 跳过，不加入执行队列
   ├── 状态=进行中 → 标记为警告
   └── 状态=待开发 → 加入执行队列
3. 构建 DAG（有向无环图）
4. 拓扑排序得到执行顺序
5. 检测循环 → 有循环则报错终止
```

### 错误处理

| 情况 | 处理 |
|------|------|
| 循环依赖 | 报错，列出循环路径（如 T-03 → T-05 → T-03），终止 |
| 依赖任务不存在 | 报错，列出缺失任务 ID，终止 |
| 依赖任务"进行中" | 交互模式：AskUserQuestion："任务 T-XX 状态为进行中，选择：先完成该依赖 / 跳过 / 终止"；`--headless` 模式：fail-fast，报告阻塞链 |
| 依赖任务"已完成" | 跳过，不加入执行队列 |

### 自动补充前置依赖

用户指定 `T-05` 但 T-05 依赖 T-03、T-04 且未完成时：

```
用户请求: T-05
依赖分析: T-05 → T-03（待开发）、T-04（待开发）
实际执行队列: [T-03, T-04, T-05]
提示用户: "T-05 依赖 T-03、T-04（未完成），已自动加入执行队列"
```

## 3. 断点续做状态机

每个任务开始前执行以下 5 步检测流水线：

```
Step 1: 文档状态检测
        ├── 读取 04-dev-tasks*.md 中该任务的 状态 字段
        ├── 已完成 → Step 1.5（验证证据复核）
        └── 进行中 / 待开发 → Step 2

Step 1.5: 证据复核（存在完成痕迹的任务均进入此步：Step 1 判为"已完成"或 Step 2 检出 code+doc 双提交）
        ├── [A] AC 完备性表可复核（S8 产物，存于任务记录或 Commit 1 附加信息）
        ├── [B] 关联测试存在且 skipped/todo=0（除显式豁免）
        ├── [C] trace 矩阵已同步（ms-sync 产物 04-trace-matrix.md 存在并覆盖该任务）
        ├── [D] 对抗式验证证据：🔴 任务须有 Phase 3 综合报告落地；若 Commit 1 带 `Skip-Review-Reason:` 尾注且补跑审查未完成 → review_pending
        ├── [E] 后置测试证据（任一即可）：单任务为 `/ms-test-run --affected` 执行记录（affected 无匹配时回退 `--trace`）；批量为批次级 `/ms-test-run --trace` 执行记录；若 Commit 1 带 `Skip-Trace-Reason:` 尾注且补跑未完成 → postcheck_pending
        ├── A~E 全部可复核 → 跳过该任务
        └── 任一不可复核 → 进入"复核续做"（续做信号表对应 pending 之一）
            └── 旧任务迁移（Fix 4 前完成，A/D/E 产物不存在）→ AskUserQuestion：复核续做 / 豁免（登记原因） / 终止

Step 2: Git 历史检测（任务状态非"已完成"时的兜底）
        ├── git log --grep="(T-XX)" --oneline
        ├── 有代码提交 + 有文档提交 → ⚠️ 不再直接跳过，改为进入 Step 1.5 证据复核路径
        ├── 有代码提交 + 无文档提交 → 标 docs_only_pending，仅执行文档同步（/ms-sync + Commit 2）
        └── 无提交 → Step 3

Step 3: 工作区检测
        ├── git status --porcelain + git diff --name-only
        ├── 无变更 → 全新任务，正常开始
        └── 有变更 → Step 4

Step 4: 变更归属判定
        ├── 对比任务 涉及文件 字段与 git status 文件列表
        ├── 变更属于当前任务 → 续做模式（见下方信号表）
        └── 变更不属于当前任务 → Step 5

Step 5: 工作区决策
        ├── --headless 模式：fail-fast（无人值守要求洁净工作区）
        └── 交互模式：AskUserQuestion:
            "检测到不相关未提交变更：[文件列表]"
            选项："暂存(stash)后继续" / "忽略继续" / "终止"
```

### 续做模式信号表

| 检测信号 | 已完成步骤 | 续做起点 | 续做 Agent |
|----------|-----------|---------|-----------|
| 无骨架、无测试文件 | — | S2 骨架生成 | Test Agent |
| 骨架文件存在 + 测试 skip/todo | 骨架生成 | S4 编写断言 | Test Agent |
| 测试有断言且全部失败 + 无实现 | Test Agent 完成 | S5 红色验证 | 编排器 |
| 测试失败 + 有部分实现 | 红色验证完成 | S6 实现 | Impl Agent |
| 测试通过 + 未通过完成检查 | Impl Agent 完成 | S8 AC 验证 | 编排器 |
| 验证 Blocker 未修（实现类） | 验证完成 | 修复 Blocker | Impl Agent |
| 验证 Blocker 未修（测试类：测试文件被修改/测试缺陷） | 验证完成 | 修复测试 | 编排器→AskUserQuestion→Test Agent |
| 代码提交完成 + 无文档提交（`docs_only_pending`） | 代码提交 | 文档同步 | 编排器 |
| 任务状态=已完成但 AC 表不可复核（`verification_pending`） | 代码/文档均已提交 | S8 重跑 AC 完备性 | 编排器 |
| 任务状态=已完成但 trace 未同步（`trace_pending`） | 代码/文档均已提交 | `/ms-sync` 重跑 + trace 校验 | 编排器 |
| 🔴 任务跳过 S9 后未补跑对抗式验证（`review_pending`，Skip-Review-Reason 已登记但审查窗未闭） | 代码/文档均已提交 | 对抗式验证 Phase 1~3 补跑 | 编排器 |
| 单任务 `--skip-trace` 后未补跑后置测试（`postcheck_pending`） | 代码/文档均已提交 | `/ms-test-run --affected` 或 `--trace` 补跑 | 编排器 |
| 旧任务（AC 表不存在，Fix 4 前完成） | 全量历史 | AskUserQuestion：复核 / 豁免 / 终止 | 编排器 |

### 续做模式行为

进入续做模式后：

```
1. 输出续做报告：
   "任务 T-XX 检测到中断点：[已完成步骤]，将从 [续做起点] 继续"
2. 跳过已完成的步骤
3. 从续做起点开始执行标准工作流
4. 后续步骤与正常流程一致
```

## 4. 多任务执行循环

### 主循环流程

```
┌─ 初始化 ──────────────────────────────────────┐
│  1. 解析批量指定符 → 任务 ID 列表             │
│  2. 依赖解析 + 拓扑排序 → 执行队列            │
│  3. TodoWrite 初始化全部任务                   │
└──────────────────────────────────────────────┘
          │
          ▼
┌─ 逐任务循环（双 Agent 模型）────────────────────┐
│  1. 断点检测 → 跳过 / 续做 / 全新              │
│  2. 启动 Test Agent（Task tool）                │
│     ├── 输入：系统设计+测试用例+需求            │
│     └── 产出：接口骨架 + 测试文件               │
│  3. 红色验证（编排器执行）                      │
│     ├── 运行测试 → 确认全部失败                 │
│     └── 意外通过 → ⛔ 检查测试有效性            │
│  4. 启动 Impl Agent（Task tool）                │
│     ├── 输入：系统设计+测试文件+骨架            │
│     ├── 实现代码使测试通过                      │
│     └── 退出条件：所有测试通过                   │
│  5. 编排器处理 Impl Agent 结果                  │
│     ├── 成功 → 继续                            │
│     ├── 测试缺陷 → AskUserQuestion 确认        │
│     └── 失败 → 交互：询问 / headless：终止      │
│  6. 完成检查 + 对抗式验证 + Commit 1            │
│  7. 更新 04-dev-tasks*.md 状态为 已完成         │
│  8. /ms-sync                                │
│  9. Commit 2: docs(T-XX): 更新任务状态+追踪      │
│     └── git add [文档文件] && git commit        │
│ 10. 洁净校验 + 写检查点                         │
│     └── git status --porcelain 非空 → 报错      │
│ 11. TodoWrite 标记任务完成                       │
│ 12. → 下一任务                                  │
└──────────────────────────────────────────────────┘
          │
          ▼
┌─ 后置测试校验 ──────────────────────────────────┐
│  触发条件：至少 1 个任务成功完成                  │
│  执行：                                          │
│  ├── 批量模式：/ms-test-run --trace（全量+追溯） │
│  ├── 单任务模式：/ms-test-run --affected         │
│  │    └── affected 无匹配 → 回退 /ms-test-run --trace │
│  └── --skip-trace="<原因>" → 跳过并登记尾注      │
│  结果处理：                                      │
│  ├── 全部通过 → 记录到执行报告                   │
│  └── 有失败 →                                    │
│      ├── 交互模式：AskUserQuestion 询问修复/跳过  │
│      └── --headless：记录警告到交付报告           │
│  注意：不回滚已提交任务（已原子提交）             │
└──────────────────────────────────────────────────┘
          │
          ▼
┌─ 完成汇总 ──────────────────────────────────┐
│  输出批量执行报告：                          │
│  - 已完成任务列表                            │
│  - 跳过任务列表（已完成 / 用户跳过）         │
│  - 失败任务列表（如有）                      │
│  - 全量测试结果                              │
└──────────────────────────────────────────────┘
```

### 上下文压缩策略（批量模式）

批量执行大量任务时，编排器主动管理上下文避免衰减：

```text
每完成 N 个任务后（N=3，可调整）：
    │
    ├── 输出当前批次进度摘要（已完成/失败/剩余）
    ├── 重新加载 04-dev-tasks.md 获取最新状态（覆盖内存中的旧状态）
    ├── 清理已完成任务的详细日志（仅保留 commit hash + 状态）
    └── 继续执行下一批次
```

**策略参数**：
- `N=3`：默认每 3 个任务重置一次（可通过 `--context-reset N` 调整）
- 重置时不影响检查点文件和 TodoWrite 状态
- --headless 模式下自动启用；交互模式下可选

> 原理：长上下文中模型一致性会退化（[参考](https://www.anthropic.com/engineering/harness-design-long-running-apps)："context anxiety"）。通过主动摘要重置，每个任务都在相对干净的上下文中执行。子 Agent 已天然隔离，此策略针对编排器层的上下文累积。

### 原子提交规则

| 规则 | 说明 |
|------|------|
| 每任务独立提交 | 不跨任务合并代码变更 |
| 代码/文档分离 | Commit 1 = 代码，Commit 2 = 文档状态更新 + trace 同步结果 |
| 提交前检查 | 必须通过完成检查后才能提交 |
| `--single-commit` | 可选参数，将代码+文档合并为单次提交 |

### Commit 消息格式

**Commit 1（代码）**：

```
<type>(T-XX): <任务名称>

- <完成内容1>
- <完成内容2>

关联: F-XXX, AC-XXX
测试: UT-XXX, IT-XXX 通过
```

**Commit 2（文档）**：

```
docs(T-XX): 更新任务状态并同步 trace
```

### 单任务模式编排

单任务模式（`/ms-dev-workflow T-03`）复用同一编排器-执行器架构：

- 跳过批量解析，直接进入依赖解析
- 依赖解析仍然执行（自动补充前置依赖）
- **依赖扩展后 >1 任务时，自动升级为批量编排**（逐任务子 Agent + 拓扑排序）
- 仅 1 任务时，同样使用双 Agent 模型（Test Agent → 红色验证 → Impl Agent），复用下方子 Agent 协议
- 断点检测由编排器执行，根据续做信号表判定从哪个 Agent 的哪个步骤续做
- **完成后必须调用 `/ms-test-run --affected`** 做受影响测试校验（见上方"后置测试校验"块）；affected 无匹配时回退 `/ms-test-run --trace`；显式关闭须 `--skip-trace="<原因>"` 并登记尾注

### 批量模式中断处理

| 情况 | 交互模式 | `--headless` 模式 |
|------|----------|-------------------|
| 某任务完成检查失败 | AskUserQuestion：修复/跳过/终止 | 重试 ≤N 次，耗尽则 fail-fast 终止批量 |
| 某任务测试失败 | AskUserQuestion：修复/跳过/终止 | 重试 ≤N 次，耗尽则 fail-fast 终止批量 |
| 用户中断（Ctrl+C） | 保留已提交，变更留在工作区 | 同左 |
| 依赖任务被跳过 | 后续依赖也跳过，警告用户 | N/A（headless 不跳过，直接终止） |

### TodoWrite 集成

批量模式下 TodoWrite 的使用：

```
1. 初始化：将执行队列中所有任务添加为 todo 项
2. 执行中：当前任务标记为 in_progress
3. 完成时：任务标记为 completed
4. 断点续做：读取 TodoWrite 状态辅助判断进度
```

### 检查点文件

批量模式下每任务完成后写入 `docs/devdocs/.batch-checkpoint.json`：

```json
{
  "batch_id": "<ISO-8601 时间戳>",
  "mode": "--headless",
  "total_tasks": 5,
  "completed": [
    {"task": "T-01", "status": "success", "commit1": "abc1234", "commit2": "def5678"},
    {"task": "T-02", "status": "success", "commit1": "111aaaa", "commit2": "222bbbb"}
  ],
  "current": "T-03",
  "remaining": ["T-03", "T-04", "T-05"],
  "resume_command": "/ms-dev-workflow T-03~T-05 --headless"
}
```

> `mode` 字段记录原始调用模式（`"--headless"` 或 `"interactive"`），`resume_command` 据此生成——
> 交互批量的续做命令不带 `--headless`，避免意外切换到无人值守模式。

用途：
- 上下文压缩后恢复批量状态（交互和 headless 均受益）
- fail-fast / 会话中断后提供精确续做信息
- 批量完成后生成执行报告的数据源

### 批量执行报告

成功时输出完整报告（commit 表 + 统计 + 全量测试结果），失败时输出中断详情 + 续做命令。

> `--headless` 模式下输出交付报告，详见 [auto-mode.md](auto-mode.md)
> 全量测试报告详见 `docs/devdocs/05-test-report.md`

### 子 Agent 协议（双 Agent 模型）

所有模式（含单任务）统一使用编排器-执行器架构。每个任务产生两个子 Agent 调用，严格按顺序执行：

#### Test Agent 协议

**输入**（编排器 → Test Agent）：

| 字段 | 说明 |
|------|------|
| 任务编号 | T-XX |
| 任务定义 | 从 04-dev-tasks*.md 提取的完整任务块 |
| 关联编号 | F-XXX, AC-XXX, UT-XXX |
| 系统设计 | 02-system-design*.md（接口签名 + 行为契约） |
| 测试用例 | 03-test-*.md（对应 AC 的测试用例定义） |
| 需求文档 | 01-requirements.md |
| 涉及文件 | src/xxx.ts（骨架目标）, tests/xxx.test.ts |
| 决策模式 | `交互` 或 `--headless` |
| 续做起点 | `null` 或 `skeleton_interface`/`skeleton_test`/`red_assertions` |

> ⛔ 信息屏障：Test Agent 禁止读取任何 src/ 下的已有实现文件（骨架除外）

**输出**（Test Agent → 编排器）：

```yaml
skill: ms-dev-workflow:test-agent
status: success | failed
summary:
  headline: "T-XX 测试代码编写完成，N 个测试用例"
  details:
    task: T-XX
    skeleton_files: [src/services/xxx.ts]
    test_files: [tests/xxx.test.ts]
    test_count: 12
    assertion_sources: [AC-001, AC-002]
blockers: []
output_files: [src/services/xxx.ts, tests/xxx.test.ts]
new_ids: {}
```

#### 红色验证（编排器执行）

Test Agent 成功后，编排器运行测试验证红色状态：

```
1. 记录测试基线（Task 开始前运行一次测试，记录已有失败集合）
2. 运行项目测试命令
3. 验证 Test Agent 新产出的测试全部失败（骨架抛出 Not implemented）
4. 新测试全部失败 + 已有测试无新增失败（相比基线）→ 进入 Impl Agent
5. 新测试意外通过 → ⛔ 异常，测试无效（恢复方式：回到 Test Agent 修复测试）
6. 已有测试出现基线外的新失败 → ⛔ 骨架破坏已有功能（恢复方式：回到 Test Agent 修复骨架）
```

#### Impl Agent 协议

**输入**（编排器 → Impl Agent）：

| 字段 | 说明 |
|------|------|
| 任务编号 | T-XX |
| 任务定义 | 从 04-dev-tasks*.md 提取的完整任务块（不含测试用例细节） |
| 关联编号 | F-XXX, AC-XXX |
| 系统设计 | 02-system-design*.md（接口签名 + 行为契约） |
| 骨架文件 | Test Agent 产出的接口骨架文件路径 |
| 测试文件 | Test Agent 产出的测试文件路径 |
| 决策模式 | `交互` 或 `--headless` |
| 续做起点 | `null` 或 `green_impl`/`refactored` |
| max_retries | N（默认 3，仅 headless 生效） |

> ⛔ 信息屏障：Impl Agent 禁止读取 03-test-*.md 和 01-requirements.md
> 允许读取：系统设计文档、Test Agent 产出的代码文件、项目现有源码

**输出**（Impl Agent → 编排器）：

```yaml
skill: ms-dev-workflow:impl-agent
status: success | failed
summary:
  headline: "T-XX 实现完成，N/N 测试通过"
  details:
    task: T-XX
    test_summary:
      passed: 12
      failed: 0
      coverage: "92%"
    impl_files: [src/services/xxx.ts]
    refactored: true
    test_defects: []  # 疑似测试缺陷列表，非空时触发用户确认
blockers: []
output_files: [src/services/xxx.ts]
new_ids: {}
```

#### 测试代码不可变原则

> ⛔ 禁止继续：Impl Agent 严禁修改 Test Agent 产出的测试代码。测试失败只能通过修改实现代码解决。

**例外 — 疑似测试缺陷**：

若 Impl Agent 判断测试代码存在逻辑错误（断言值与行为契约矛盾、测试 setup 不正确等）：

1. Impl Agent 停止实现，在摘要 `test_defects` 中报告缺陷（含测试编号和问题描述）
2. 编排器通过 AskUserQuestion 向用户确认：
   - 选项 A：确认测试有误 → 回退 Test Agent 修复 → 重新红色验证 → 重启 Impl Agent
   - 选项 B：测试正确 → Impl Agent 继续调整实现
   - 选项 C：终止当前任务
3. `--headless` 模式：直接 fail-fast 终止，不自动修改测试

**安全网**：编排器在 Impl Agent 完成后对比测试文件 diff，若测试文件有任何变更 → ⛔ Blocker。

> 交互模式下子 Agent 可通过 AskUserQuestion 与用户交互；headless 模式下由策略自动决策。
> 架构相同，决策方式不同。
