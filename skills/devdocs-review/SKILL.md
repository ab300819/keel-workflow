---
name: devdocs-review
description: Review implementation correctness against requirements and design. Verify AC satisfaction, design conformance, and traceability completeness. Use after development and before adversarial verification. Triggers on keywords like "review", "AC check", "design check", "实现审查", "需求验证", "设计一致性".
allowed-tools: Read, Glob, Grep, Bash, AskUserQuestion
---

# 实现正确性审查

验证"实现是否正确"——与对抗式验证（验证"代码质量是否合格"）互补。

## 语言规则

- 支持中英文提问
- 统一中文回复
- 使用中文生成报告

## 定位

```
对抗式验证 Phase 1：MTE 原则、安全检查       → 代码质量
对抗式验证 Phase 2：覆盖率、断言质量          → 测试完备性
devdocs-review：AC 满足度、设计一致性、追溯完整性 → 实现正确性
```

**互补关系**：对抗式验证检查"代码写得好不好"，本 Skill 检查"代码做对了没"。

## 触发条件

- 任务开发完成后、对抗式验证之前
- 用户要求检查实现是否符合需求
- 通过 `--review` 集成到对抗式验证流程

## 运行模式

```bash
/devdocs-review                    → 完整审查（三个维度）
/devdocs-review --ac               → 仅 AC 满足度审查
/devdocs-review --design           → 仅设计符合度审查
/devdocs-review --trace            → 仅追溯完整性审查
/devdocs-review T-01 T-02          → 指定任务范围审查
```

## 工作流程

```text
1. 读取 DevDocs 文档
   ├── 01-requirements.md（AC 列表）
   ├── 02-system-design.md（设计规范）
   └── 03-test-cases.md（追溯矩阵）
   │
   ▼
2. 扫描代码实现
   ├── @satisfies 标注定位实现代码
   ├── @verifies 标注定位测试代码
   └── 未标注的核心逻辑检测
   │
   ▼
3. 三维度审查
   ├── AC 满足度审查
   ├── 设计符合度审查
   └── 追溯完整性审查
   │
   ▼
4. 生成审查报告
   │
   ▼
5. Blocker 修复建议
```

## 审查维度

### 维度 1：AC 满足度审查

逐条验证实现是否匹配验收标准。

**检查步骤**：

1. 读取 `01-requirements.md` 中所有 AC
2. 通过 `@satisfies` 标注 + 代码搜索定位实现
3. **语义判断**实现是否匹配 AC 描述（不仅检查标注存在性，还检查实现逻辑）
4. 对每条 AC 给出判定

**判定标准**：

| 判定 | 含义 | 示例 |
|------|------|------|
| ✅ 满足 | 实现完整匹配 AC 描述 | AC 要求"密码至少8位"，代码有长度校验且阈值为8 |
| ⚠️ 部分满足 | 实现覆盖部分场景 | AC 要求"支持中英文"，代码只处理了英文 |
| ❌ 未满足 | 无实现或实现不匹配 | AC 要求"30分钟过期"，代码无过期逻辑 |

### 维度 2：设计符合度审查

对照系统设计文档检查实现偏离。

**检查项**：

| 检查项 | 说明 | 严重程度 |
|--------|------|----------|
| 接口签名一致性 | 实际参数/返回值与设计文档不符 | Blocker |
| 模块职责偏离 | 模块承担了设计中未分配的职责 | Blocker |
| 数据流符合度 | 数据流转路径与设计不符 | Warning |
| 组件边界 | 组件间依赖关系与设计不符 | Warning |

**检查步骤**：

1. 读取 `02-system-design.md` 中的接口定义、模块职责、数据流
2. 扫描对应代码文件，提取实际接口签名和模块结构
3. 逐项对比，标记偏离

### 维度 3：追溯完整性审查

检查代码标注的覆盖率，确保可追溯性。

**检查项**：

| 检查项 | 说明 |
|--------|------|
| `@satisfies` 覆盖率 | 有多少 AC 在代码中有对应 @satisfies 标注 |
| `@verifies` 覆盖率 | 有多少 AC 在测试中有对应 @verifies 标注 |
| 未标注核心逻辑 | 业务逻辑代码无任何追溯标注 |

**复用 devdocs-sync --trace 的扫描能力**：使用相同的标注搜索模式（`@satisfies`/`@verifies`/`@testcase`）。

## 问题分级

### Blocker（必须修复）

- AC 未满足（❌）
- 接口签名与设计不符
- 模块职责严重偏离
- 核心 AC 无 @satisfies 标注

### Warning（建议修复）

- AC 部分满足（⚠️）
- 数据流与设计有轻微偏离
- 非核心代码缺少追溯标注
- @satisfies 覆盖率 < 80%

## 输出文件

生成 `docs/devdocs/review-report.md`

详细模板参见 [templates/review-report.md](templates/review-report.md)

## 上下文管理

### 分批原则

按任务 (T-XX) 或功能点 (F-XXX) 分批审查，每批完成一个功能点的全部三个维度检查。

### 质量锚点

首个功能点的审查结果作为**质量锚点**——后续功能点的审查深度（AC 语义判断的细致程度、设计偏离检查的全面性）不低于首批。

### 一致性自检

每个功能点审查完成后，对比检查：
- [ ] AC 语义判断是否与首批同等深度（非仅检查标注存在性）
- [ ] 设计偏离检查是否覆盖全部检查项（接口、职责、数据流、边界）
- [ ] 追溯标注统计口径是否一致

## 约束

### 审查约束

- [ ] **必须读取所有相关 DevDocs 文档后再审查**
- [ ] **AC 满足度必须语义判断，不仅检查标注存在性**
- [ ] **设计符合度必须对照设计文档原文，不凭记忆**
- [ ] **必须生成审查报告**

### 分级约束

- [ ] Blocker 必须列出修复建议
- [ ] Warning 标注建议修复方向
- [ ] 不将 Warning 升级为 Blocker（除非用户要求严格模式）

### 安全约束

- [ ] **不修改代码，只生成报告**
- [ ] **不修改 DevDocs 文档**
- [ ] 发现设计偏离时建议更新设计文档，而非直接修改

### 上下文管理约束

- [ ] 后批次审查深度不低于首批次
- [ ] 每个功能点完成后执行一致性自检

## Skill 协作

| 场景 | 协作 Skill | 说明 |
|------|-----------|------|
| 开发完成 | `/devdocs-dev-workflow` | 被调用：任务完成后触发审查 |
| 对抗式验证 | `/devdocs-dev-workflow` | 协作：作为验证流程的前置步骤 |
| 追溯扫描 | `/devdocs-sync --trace` | 复用：标注扫描能力 |
| AC 缺失 | `/devdocs-requirements` | 路由：发现 AC 不完整时 |
| 设计偏离 | `/devdocs-system-design` | 路由：发现设计文档需更新时 |
| 代码质量 | `/code-quality` | 互补：code-quality 关注代码质量约束 |

## 下一步

审查完成后：

| 结果 | 建议下一步 |
|------|------------|
| 有 Blocker | 修复后重新运行 `/devdocs-review` |
| 仅 Warning | 进入对抗式验证（`/devdocs-dev-workflow` 验证流程） |
| 全部通过 | 进入对抗式验证 |
| 设计偏离 | `/devdocs-system-design` 更新设计文档 |
| AC 缺失 | `/devdocs-requirements --incremental` 补充 AC |
