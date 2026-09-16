---
name: test-cases
description: 依据 DevDocs 需求设计可追溯的 UT/IT/E2E 用例文档。编写测试代码用 testing-guide；运行套件用 test-run。
allowed-tools: Read, Write, Glob, Grep, AskUserQuestion
metadata:
  patterns: [generator]
  interaction: multi-turn
  handoff: yaml-summary-v1
---

# 测试用例设计

> 视角：QA 分析师 — 关注边界覆盖与路径完备性，追求可测性而非实现细节。

基于需求文档设计测试用例，建立验收标准与测试用例的追溯关系。

## 快速开始

**一句话**: 设计测试用例（UT/IT/E2E/Journey），建立需求→测试追溯。

**最常见用法**: `/test-cases`（自动检测初始/增量）

**不适合?** 跑测试→`/test-run`，开发指导→`/dev-workflow`

## 语言规则

- 支持中英文提问
- 统一中文回复
- 使用中文生成文档

## 触发条件

- 用户已完成需求文档
- 用户要求设计测试用例
- 用户需要测试覆盖策略

## 前置条件

- 需求文档：`docs/devdocs/01-requirements.md`
- 系统设计文档：`docs/devdocs/02-system-design.md`（设计 UT/IT 时需要了解接口签名和模块划分）
- 如不存在，建议先运行前置阶段

## 核心理念

### 测试用例来源

```text
功能点 (F-XXX)
    │
    └── 用户故事 (US-XXX)
            │
            └── 验收标准 (AC-XXX)
                    │
                    ├── 单元测试 (UT-XXX)      ← 验证内部逻辑
                    │
                    ├── 集成测试 (IT-XXX)      ← 验证组件协作
                    │
                    ├── E2E 测试 (E2E-XXX)     ← 验证单 US 用户场景
                    │
                    └── 用户旅程 (Journey-XXX)  ← 验证跨 US 业务闭环
```

**关键原则**：
- 测试用例从需求推导，不是从代码推导
- 每个验收标准至少有一个测试用例覆盖
- 测试类型根据验收标准的性质选择

### 测试类型选择

| 验收标准类型 | 推荐测试类型 | 示例 |
|--------------|--------------|------|
| 输入验证规则 | 单元测试 | "邮箱格式校验" → UT |
| 业务逻辑规则 | 单元测试 + 集成测试 | "密码加密存储" → UT + IT |
| 用户交互流程 | E2E 测试 | "完成注册流程" → E2E |
| 跨功能用户流程 | 用户旅程测试 | "新用户从注册到首次使用" → Journey |
| 组件间协作 | 集成测试 | "发送验证邮件" → IT |

> **E2E 与 Journey 的区别**：E2E-XXX 验证单个用户故事的完整交互；Journey-XXX 串联 >= 2 个用户故事，验证跨功能的业务闭环与步骤间状态传递。

## 编号规范

>

| 类型 | 前缀 | 格式 | 示例 |
|------|------|------|------|
| 单元测试 | UT | UT-XXX | UT-001, UT-002 |
| 集成测试 | IT | IT-XXX | IT-001, IT-002 |
| E2E 测试 | E2E | E2E-XXX | E2E-001, E2E-002 |
| 用户旅程 | Journey | Journey-XXX | Journey-001, Journey-002 |

## 运行模式

- `/test-cases` → 标准模式（逐步确认）
- `/test-cases --realign[=scope]` → 规范升级回扫（结构/字段差距补齐；缺失测试类型传递给 dev-workflow）。详见 [references/realign.md](references/realign.md)；推荐 `/pipeline realign`

### 快速档（`ceremony: fast`）

- 跳过测试类型选择的逐步确认
- 自动根据 AC 性质选择最佳测试类型
- 仅保留最终写入前的 1 次确认
- **档位由编排层下传的 `ceremony` 决定**（[`task/intent-normalization`](../shared/constraints.md)）：`fast` → 本节；`standard`（缺省）/ `deep` → 标准模式。
  ⛔ 不得自行解读用户原话来判档。

## 工作流程

```text
1. 读取需求文档
   │
   ▼
2. 提取功能点、用户故事、验收标准
   │
   ▼
3. 为每个验收标准选择测试类型
   │
   ▼
4. 按功能点分批设计测试用例
   │  对每个功能点 (F-XXX)：
   │    ├── 设计该功能点的 UT
   │    ├── 设计该功能点的 IT
   │    ├── 设计该功能点的 E2E
   │    └── 质量一致性自检（与首批对比详细程度）
   │
   ▼
4.5 汇总用户旅程
   │  所有功能点的 UT/IT/E2E 完成后：
   │    ├── 回顾跨功能点的 US 串联关系
   │    ├── 筛选核心旅程（>= 2 个 US 串联）
   │    └── 设计 Journey 用例
   │
   ▼
5. 生成追溯矩阵（含 Journey）
   │
   ▼
6. 用户确认
```

## 上下文管理

### 分批原则

按功能点 (F-XXX) 分批设计，每批完成一个功能点的全部测试用例（UT + IT + E2E）。

### 质量锚点

- 首个功能点的用例作为**质量锚点**
- 每个新功能点开始前，回顾首批用例的详细程度（字段完整性、场景覆盖、输入输出具体性）
- 若当前批次详细程度明显低于锚点，立即补充

### 一致性自检

每个功能点完成后，对比检查：
- [ ] 场景覆盖是否包含正常 + 异常路径

## 输出文件

**主文件**：`docs/devdocs/03-test-cases.md`

### 文档拆分规则

**默认拆分**为主文件 + 子文件结构。每个子文件控制在合理大小内，Agent 每次只写一个子文件以减轻上下文负担。

**拆分方式**：

```text
docs/devdocs/
├── 03-test-cases.md           # 大纲：策略、覆盖率、追溯矩阵、用例索引
├── 03-test-unit.md            # UT 详情
├── 03-test-integration.md     # IT 详情
└── 03-test-e2e.md             # E2E 详情
```

**主文档保留内容**（大纲，不含具体用例）：
- 测试策略说明
- 覆盖率目标
- 完整追溯矩阵（F → US → AC → 测试）
- 各子文档的用例范围说明

**小型项目例外**：测试用例 ≤ **15 个**且文档 ≤ **200 行**时，可合并为单一文件 `03-test-cases.md`。

详细模板参见：
- [templates/test-cases-template.md](templates/test-cases-template.md)
- [templates/unit-test-template.md](templates/unit-test-template.md)
- [templates/integration-test-template.md](templates/integration-test-template.md)
- [templates/e2e-test-template.md](templates/e2e-test-template.md)

## 测试用例概览文档结构

```markdown
# 测试用例：<功能名称>

## 1. 测试策略
## 2. 覆盖率要求
## 3. 追溯矩阵
## 4. 测试用例索引
```

## 追溯矩阵

追溯矩阵是核心产出，展示需求与测试、代码的完整关联。

### 基础格式（设计阶段）

```markdown
| 功能点 | 用户故事 | 验收标准 | 单元测试 | 集成测试 | E2E/旅程测试 | 状态 |
|--------|----------|----------|----------|----------|-------------|------|
| F-001 | US-001 | AC-001 | UT-001 | - | E2E-001, Journey-001 | ⏳ |
| F-001 | US-001 | AC-002 | UT-002 | - | E2E-001, Journey-001 | ⏳ |
| F-001 | US-002 | AC-004 | UT-003, UT-004 | IT-001 | - | ⏳ |
| F-002 | US-003 | AC-006 | - | IT-002 | Journey-001 | ⏳ |
```

### 完整格式（开发阶段，含变更来源）

> 变更来源由 `/sync` 维护：⛔ **代码里不写任何 DevDocs 编号**，连接方向是**文档 → commit**（反向依赖）。

```markdown
| AC 编号 | 验收标准 | 测试编号 | 变更来源 | 状态 |
|---------|----------|----------|----------|------|
| AC-001 | 邮箱格式校验 | UT-001 | `api@a3f9c21` 邮箱格式校验 | ✅ |
| AC-002 | 密码强度校验 | UT-002 | `api@a3f9c21` 邮箱格式校验；`api@7b2e104` 密码强度 | ✅ |
| AC-003 | 用户名唯一性 | UT-003 | `api@c81d5f0` 用户名唯一性 | ⏳ |
| AC-004 | 发送验证邮件 | IT-001 | - | ❌ |
```

### 变更来源字段说明

| 字段 | 形态 | 说明 |
|------|------|------|
| 变更来源 | `<repository>@<full-sha>` + 一句话描述 | 该 AC 由哪几次变更引入。**允许多条**（一条 AC 可跨多个 commit，一个 commit 也可满足多条 AC）|

⛔ **它是变更事件锚点，不是当前实现定位符。** commit 只能回答「这项变化当时发生在哪」；「今天由哪里实现」必须回到当前代码搜索和测试。后续重构、移动、revert 之后 commit 仍在，但已不代表现状。

**hash 失效时**（squash / rebase / 上游 force-push）：⚠️ 警告并回到**当前代码事实**重建，⛔ 不为此建机制。旁边那句描述是人工找回的唯一线索，所以必须写。

### 状态说明

| 状态 | 含义 | 条件 |
|------|------|------|
| ✅ | 完整覆盖 | 有测试用例 + 变更来源 + 测试通过 |
| ⏳ | 进行中 | 有测试用例，代码/测试部分完成 |
| ⚠️ | 部分覆盖 | 有变更来源但缺测试，或有测试但无变更来源 |
| ❌ | 未覆盖 | 无测试用例或无代码实现 |

### 矩阵维护流程

```text
设计阶段                    开发阶段                     同步阶段
    │                          │                           │
    ▼                          ▼                           ▼
生成基础矩阵          生成骨架代码（带标注）        /sync
(AC → 测试编号)       (入口 + 测试)                      │
                                                        ▼
                                                 扫描代码标注
                                                        │
                                                        ▼
                                                 填充代码位置列
                                                        │
                                                        ▼
                                                 更新状态列
```

## 测试用例格式

### 单元测试用例

```markdown
| 编号 | 验收标准 | 测试对象 | 场景 | 输入 | 预期输出 | 优先级 |
|------|----------|----------|------|------|----------|--------|
| UT-001 | AC-001 | validateEmail() | 有效邮箱 | "test@example.com" | true | P0 |
| UT-002 | AC-002 | validateEmail() | 无效格式 | "invalid" | false | P0 |
```

### 集成测试用例

```markdown
| 编号 | 验收标准 | 测试场景 | 涉及组件 | 预期结果 | 优先级 |
|------|----------|----------|----------|----------|--------|
| IT-001 | AC-004 | 密码加密存储 | UserService + DB | 密码以 bcrypt 格式存储 | P0 |
```

### E2E 测试用例

```markdown
| 编号 | 用户故事 | 验收标准 | 操作步骤 | 预期结果 | 优先级 |
|------|----------|----------|----------|----------|--------|
| E2E-001 | US-001 | AC-001~AC-003 | 1. 打开注册页<br>2. 输入邮箱密码<br>3. 点击注册 | 注册成功，收到验证邮件 | P0 |
```

### 用户旅程测试用例

```markdown
| 编号 | 角色 | 串联故事 | 旅程步骤摘要 | 优先级 |
|------|------|----------|-------------|--------|
| Journey-001 | 新用户 | US-001→US-003 | 注册→验证→登录→首页 | P0 |
```

## 覆盖率要求

> 行 / 分支覆盖率数值以 [`/testing-guide` 核心阈值表](../testing-guide/SKILL.md#核心阈值表) 为权威，本节不镜像（agent 侧改指针；产物模板允许内联，见该表「镜像边界」）。下表只定义 test-cases 私有的**覆盖单位**要求。

| 测试类型 | 覆盖目标 | 覆盖要求 |
|----------|----------|----------|
| 单元测试 | 核心业务逻辑 | 行 / 分支覆盖率见 `/testing-guide` 核心阈值表 |
| 集成测试 | 组件协作场景 | 每个功能点至少 1 个 IT |
| E2E 测试 | 用户故事 | 按风险与成本决定；核心路径优先 |
| 用户旅程 | 核心用户路径 | 至少 1 条核心旅程；中大型产品 2-3 条 |

## 约束

### 阶段边界约束（最高优先级）
- [ ] **⛔ 禁止继续：文档阶段不得产出实现代码或测试代码文件**（恢复方式：使用 /dev-workflow 执行编码）
- [ ] **⛔ 禁止继续：生成/更新文档未在顶部写入 `generated_by / spec_version / generated_at` 三字段 YAML frontmatter**（恢复方式：按 [templates/test-cases-template.md](templates/test-cases-template.md) 顶部示例补齐；spec_version 常量见 [references/realign.md](references/realign.md)）

### 追溯约束
- [ ] 每个验收标准至少有 1 个测试用例覆盖
- [ ] 必须生成追溯矩阵

### 用例设计约束
- [ ] 每个用例必须有明确的预期结果
- [ ] 优先级必须标注 (P0/P1/P2)
- [ ] 后批次用例详细程度不低于首批次（字段完整性、具体值、场景覆盖）

### 覆盖约束

AC 质量评估标准详见 [../requirements/references/ac-quality-rubric.md](../requirements/references/ac-quality-rubric.md)，验证 AC→测试覆盖时参照。

- [ ] P0 验收标准必须 100% 测试覆盖（本 skill P0-P2 为**用例优先级**，与 verify 问题严重度 P 级同名不同义）
- [ ] 单元测试覆盖率目标按 [`/testing-guide` 核心阈值表](../testing-guide/SKILL.md#核心阈值表) 执行

### Generator 自检（用户确认前自动执行）

在呈现给用户确认前，加载 [../requirements/references/ac-quality-rubric.md](../requirements/references/ac-quality-rubric.md) 并自动验证：

- [ ] 测试用例的输入/输出有具体值（非"正常输入"等模糊描述）

自检不通过项自动修复后再呈现用户，不增加用户交互步骤。

### 质量约束

断言质量判据（测试命名 / 禁弱断言 / Mock 边界）以 [`/testing-guide`](../testing-guide/SKILL.md) 为权威，本文不镜像。

## Skill 协作

| 场景 | 协作 Skill | 说明 |
|------|-----------|------|
| 需求输入 | `/requirements` | 前置：提供 F/US/AC 作为测试设计依据 |
| 新功能测试 | `/feature` | 被调用：新功能需要新增测试用例 |
| Bug 回归测试 | `/bugfix` | 被调用：Bug 修复需要补充回归测试 |
| 改进测试 | `/insights` | 被调用：改进建议可能需要测试覆盖 |
| 追溯更新 | `/sync` | 协作：trace 模式更新追溯矩阵代码位置 |
| 测试质量 | `/testing-guide` | 协作：编写测试代码时的质量约束 |
| 任务拆分 | `/dev-tasks` | 后续：测试用例转化为开发任务 |

## 子 Agent 摘要格式

当本 Skill 作为子 Agent 运行时，返回以下结构化摘要：

> envelope 字段定义（status 枚举 / blockers / output_files / new_ids 等保留字段）见 [shared/constraints.md §yaml-summary-v1](../shared/constraints.md)；下例重点为 `summary.details` 私有字段。

```yaml
skill: test-cases
status: success | failed | partial
summary:
  headline: "测试设计完成，12 UT + 3 IT + 2 E2E + 1 Journey"
  details:
    mode: initial | incremental
    traceability_matrix_updated: true
blockers: []
output_files:
  - docs/devdocs/03-test-cases.md
new_ids:
  unit_tests: [UT-001~UT-012]
  integration_tests: [IT-001~IT-003]
  e2e_tests: [E2E-001~E2E-002]
  journeys: [Journey-001]
next_recommended:
  skill: dev-tasks
```

## 下一步

完成后建议运行 `/dev-tasks` 进行开发任务拆分。

> **提示**：文档变更较大时，建议运行 `/agent-memory` 同步记忆文件。
