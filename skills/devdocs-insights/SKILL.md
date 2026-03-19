---
name: devdocs-insights
description: Collect improvement insights from UI/UX reviews, document research, or external references, convert confirmed items into development requirements. Use when users have optimization suggestions, research findings, competitor analysis, or want to improve based on external references. Triggers on "insights", "improvements", "optimize", "review findings", "research", "借鉴", "优化建议", "审查结果", "调研", "竞品", "可以借鉴". NOT for bug fixes (use devdocs-bugfix) or adding new features directly (use devdocs-feature).
allowed-tools: Read, Write, Glob, Grep, AskUserQuestion, WebFetch
metadata:
  patterns: [inversion, generator]
  interaction: multi-turn
  handoff: yaml-summary-v1
---

# 洞察收集

收集来自 UI/UX 审查、文档调研、外部参考等来源的改进建议，经用户确认后转化为开发需求。

## 语言规则

- 支持中英文提问
- 统一中文回复
- 使用中文生成文档

## 触发条件

- 用户完成 UI/UX 审查，有优化建议
- 用户调研了文档/方案，发现可借鉴点
- 用户发现外部参考（竞品、最佳实践）可借鉴
- 用户有改进想法需要转化为需求

## 核心理念

### 洞察来源

```
┌─────────────────────────────────────────────────────────────┐
│                      洞察来源                                │
├─────────────────────────────────────────────────────────────┤
│  🎨 UI/UX 审查     │ 界面问题、交互优化、视觉改进            │
├─────────────────────────────────────────────────────────────┤
│  📄 文档调研       │ 技术方案、设计模式、架构参考            │
├─────────────────────────────────────────────────────────────┤
│  🔍 外部参考       │ 竞品分析、行业最佳实践、开源项目        │
├─────────────────────────────────────────────────────────────┤
│  💡 内部反馈       │ 用户反馈、团队建议、性能监控            │
└─────────────────────────────────────────────────────────────┘
```

### 转化流程

```
洞察来源                确认阶段                 输出阶段
    │                      │                        │
    ▼                      ▼                        ▼
┌─────────┐          ┌─────────┐            ┌─────────────┐
│ 收集    │    →     │ 用户    │      →     │ 追加到      │
│ 建议    │          │ 确认    │            │ 需求文档    │
└─────────┘          └─────────┘            └─────────────┘
                          │
                          ▼
                    部分确认 / 全部确认 / 拒绝
```

**核心原则**：
- 建议必须经过用户确认才能转化为需求
- 保留建议来源的追溯性
- 区分优先级，避免需求膨胀

## 工作流程

```
1. 识别洞察来源
   │
   ▼
2. 收集/整理建议
   ├── UI/UX 审查结果
   ├── 文档调研发现
   ├── 外部参考借鉴
   └── 内部反馈汇总
   │
   ▼
3. 结构化建议列表
   ├── 分类整理
   ├── 评估影响范围
   └── 建议优先级
   │
   ▼
4. 用户确认（AskUserQuestion）
   ├── 逐条确认
   ├── 批量确认
   └── 调整优先级
   │
   ▼
5. 转化为需求
   ├── 生成功能点 (F-XXX)
   ├── 生成验收标准 (AC-XXX)
   └── 追加到 01-requirements.md
   │
   ▼
6. 建议后续流程
   └── 运行 /devdocs-system-design 或 /devdocs-dev-tasks
```

## 输出文件

### 需求追加（唯一源）

确认的建议将追加到：`docs/devdocs/01-requirements.md`（**唯一内容源**）

### 洞察变更日志

**文件**：`docs/devdocs/05-insights.md`

降级为**变更日志**——仅记录 INS 编号、来源、确认时间和转化目标，不重复需求内容。避免 `05-insights.md` 与 `01-requirements.md` 之间的双写不同步风险。

```markdown
## 洞察变更日志

| INS 编号 | 来源 | 确认时间 | 状态 | 转化目标 |
|----------|------|----------|------|----------|
| INS-001 | 🎨 UI/UX 审查 | 2024-01-15 | 🔄 已转化 | F-015, AC-030~031 |
| INS-002 | 📄 文档调研 | 2024-01-15 | ❌ 已拒绝 | -（原因：优先级不足） |
```

## 建议结构

### 单条建议格式

```markdown
### INS-001: <建议标题>

| 属性 | 内容 |
|------|------|
| **来源** | 🎨 UI/UX 审查 / 📄 文档调研 / 🔍 外部参考 / 💡 内部反馈 |
| **参考** | <来源链接或描述> |
| **现状** | <当前问题或不足> |
| **建议** | <改进建议> |
| **影响范围** | <涉及模块/功能> |
| **优先级** | P0 / P1 / P2 |
| **状态** | ⏳ 待确认 / ✅ 已确认 / ❌ 已拒绝 / 🔄 已转化 |

**预期收益**：
- <收益1>
- <收益2>
```

### 建议列表格式

```markdown
# 洞察收集：<主题>

**收集时间**：YYYY-MM-DD
**来源类型**：UI/UX 审查 / 文档调研 / 外部参考

## 建议汇总

| 编号 | 标题 | 来源 | 优先级 | 状态 |
|------|------|------|--------|------|
| INS-001 | <标题> | 🎨 | P1 | ⏳ |
| INS-002 | <标题> | 📄 | P0 | ⏳ |

## 详细建议

### INS-001: <标题>
...

---

## 确认结果

- [x] INS-001: 已确认 → F-XXX
- [ ] INS-002: 待确认
- [x] INS-003: 已拒绝（原因：...）
```

## 来源类型处理

| 来源 | 输入 | 关注点 |
|------|------|--------|
| 🎨 UI/UX 审查 | 截图/原型/审查结果 | 可用性、视觉一致性、无障碍性 |
| 📄 文档调研 | 技术文档/设计方案 | 架构模式、实现方案、性能优化 |
| 🔍 外部参考 | 竞品/开源项目/行业报告 | 竞品优势、行业模式、用户期望 |
| 💡 内部反馈 | 用户反馈/团队建议/监控数据 | 用户痛点、团队共识、性能瓶颈 |

> **收集建议时，必须读取 [source-types.md](source-types.md) 获取各来源类型的输入方式、关注点和示例。**

## 用户确认流程

使用 **AskUserQuestion** 进行交互式确认：

### 单条确认

```
建议 INS-001: 按钮对比度不足，影响可读性

来源：🎨 UI/UX 审查
优先级：P1
影响范围：全局按钮组件

是否确认转化为需求？
- 确认（转化为 F-XXX）
- 调整优先级后确认
- 拒绝（请说明原因）
- 稍后决定
```

### 批量确认

```
以下建议待确认：

| 编号 | 标题 | 优先级 |
|------|------|--------|
| INS-001 | 按钮对比度不足 | P1 |
| INS-002 | 缺少加载状态 | P1 |
| INS-003 | 移动端导航问题 | P2 |

请选择：
- 全部确认
- 选择性确认（输入编号，如：1,2）
- 全部拒绝
- 逐条审查
```

## 需求转化规则

### 转化映射

| 建议类型 | 转化为 | 说明 |
|----------|--------|------|
| 新功能建议 | F-XXX (新功能点) | 创建新的功能点 |
| 优化建议 | F-XXX (优化标记) | 标记为优化类型 |
| Bug 修复 | 直接触发 /devdocs-bugfix | 走 Bug 修复流程 |
| 技术改进 | F-XXX (技术债务) | 标记为技术改进 |

### 功能点格式

```markdown
### F-XXX: <功能名称> [优化]

**来源**：INS-XXX (<来源类型>)
**优先级**：P0 / P1 / P2

**描述**：
<从建议转化的功能描述>

**验收标准**：
- AC-XXX: <可验证的标准1>
- AC-XXX: <可验证的标准2>
```

### 编号规则

- 功能点编号：延续 `01-requirements.md` 中的编号
- 验收标准编号：延续现有 AC 编号
- 建议编号：INS-XXX（仅在洞察文档中使用）

## 约束

### 收集约束

- [ ] **必须标明建议来源**
- [ ] **必须评估影响范围**
- [ ] 每条建议必须有明确的现状和改进点
- [ ] 外部参考必须提供来源链接

### 确认约束

- [ ] **所有建议必须经过用户确认才能转化**
- [ ] **拒绝的建议必须记录原因**
- [ ] 批量确认前必须展示完整列表
- [ ] 用户可以调整建议优先级

### 转化约束

- [ ] **转化后的需求必须可追溯到原始建议**
- [ ] **必须生成可验证的验收标准**
- [ ] 优化类需求必须标记 [优化] 标签
- [ ] 转化后更新建议状态为 🔄 已转化

### 避免需求膨胀

- [ ] 单次收集建议不超过 **10 条**
- [ ] 低优先级建议可标记为"待定"
- [ ] 鼓励用户聚焦核心改进
- [ ] 定期清理过期的待确认建议

## Skill 协作

| 场景 | 协作 Skill | 说明 |
|------|-----------|------|
| UI/UX 审查来源 | `/ui-orchestrator` | 审查结果可作为洞察来源 |
| 需求转化 | `/devdocs-requirements` | 被调用：洞察转化为需求 |
| 设计变更 | `/devdocs-system-design` | 触发：复杂改进需要设计调整 |
| 测试补充 | `/devdocs-test-cases` | 触发：改进建议需要测试覆盖 |
| 简单改进 | `/devdocs-dev-tasks` | 无架构变更，直接拆分任务 |
| 复杂改进 | `/devdocs-feature` | 有架构变更，走完整流程 |
| Bug 类建议 | `/devdocs-bugfix` | 走 Bug 修复流程 |
| 需求更新 | `/devdocs-sync` | 同步文档状态 |

## 使用示例

> 详见 [examples.md](examples.md)

## 子 Agent 摘要格式

当本 Skill 作为子 Agent 运行时，返回以下结构化摘要：

```yaml
skill: devdocs-insights
status: success | failed | partial
summary:
  headline: "收集 3 条洞察，2 条已转化为需求"
  details:
    source_type: ui_review | doc_research | external_ref | internal_feedback
    insights_collected: 3
    insights_confirmed: 2
    insights_rejected: 1
blockers: []
output_files:
  - docs/devdocs/01-requirements.md
  - docs/devdocs/05-insights.md
new_ids:
  features: [F-015, F-016]
  acceptance: [AC-030~AC-033]
  insights: [INS-001~INS-003]
next_recommended:
  skill: devdocs-feature
```

## 命令选项

```bash
# 标准模式：交互式收集和确认
/devdocs-insights

# 从 URL 提取建议
/devdocs-insights --url <url>

# 从文件提取（如审查报告）
/devdocs-insights --file <path>

# 快速模式：直接输入建议列表
/devdocs-insights --quick
```

## 下一步

确认建议并转化为需求后，根据改进复杂度选择路径：

### 路径选择

```
确认的改进建议
      │
      ▼
评估是否涉及架构变更
      │
      ├── 无架构变更（简单改进）
      │   ├── UI 微调、配置修改、小功能
      │   └── → /devdocs-dev-tasks 直接拆分任务
      │
      └── 有架构变更（复杂改进）
          ├── 新接口、数据模型变更、新模块
          └── → /devdocs-feature 完整流程
                  └── system-design → test-cases → dev-tasks
```

### 架构变更判断

| 条件 | 是否架构变更 | 推荐路径 |
|------|-------------|----------|
| 仅 UI/样式调整 | 否 | `/devdocs-dev-tasks` |
| 仅配置项修改 | 否 | `/devdocs-dev-tasks` |
| 新增 API 接口 | **是** | `/devdocs-feature` |
| 数据模型变更 | **是** | `/devdocs-feature` |
| 新增独立模块 | **是** | `/devdocs-feature` |
| 第三方服务集成 | **是** | `/devdocs-feature` |

### 使用 AskUserQuestion 确认

```
已确认 X 条改进建议，转化为需求。

检测到以下情况：
- INS-001: UI 按钮样式调整 → 无架构变更
- INS-003: 新增导出 API → 涉及架构变更

建议路径：
- INS-001 → /devdocs-dev-tasks（直接拆分任务）
- INS-003 → /devdocs-feature（完整流程）

是否按建议执行？[是/调整]
```
