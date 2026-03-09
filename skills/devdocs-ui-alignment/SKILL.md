---
name: devdocs-ui-alignment
description: Verify alignment between UI design and implementation. Compare design specs with requirements and actual rendered output. Triggers on keywords like "UI alignment", "UI 对齐", "设计稿对比", "design review", "视觉一致性", "UI verification".
allowed-tools: Read, Glob, Grep, Bash, AskUserQuestion
---

# UI 设计对齐验证

验证"UI 设计和实现是否对齐"——两阶段验证，确保设计稿↔需求↔实现三方一致。

## 语言规则

- 支持中英文提问
- 统一中文回复
- 使用中文生成报告

## 定位

```
ui-orchestrator：路由到合适的 UI Skill 执行开发
devdocs-ui-alignment：验证 UI 设计和实现的对齐关系（不替代路由功能）
```

**互补关系**：ui-orchestrator 负责"用什么工具做"，本 Skill 负责"做对了没"。

## 触发条件

- UI 相关任务开发完成后
- 用户要求对比设计稿和实现
- 设计稿更新后需要验证实现是否同步

## 运行模式

```bash
/devdocs-ui-alignment                → 完整验证（两阶段）
/devdocs-ui-alignment --design       → 仅阶段 1：设计稿 ↔ 需求对齐
/devdocs-ui-alignment --impl         → 仅阶段 2：设计稿 ↔ 实现对齐
```

## 工作流程

```text
1. 确定设计稿来源
   ├── Pencil .pen 文件
   ├── 截图/图片文件
   └── Figma（通过截图或 MCP）
   │
   ▼
2. 阶段 1：设计稿 ↔ 需求对齐
   ├── 读取设计稿
   ├── 读取 01-requirements.md 中 UI 相关 AC
   └── 逐条检查 AC 覆盖
   │
   ▼
3. 阶段 2：设计稿 ↔ 实现对齐
   ├── 获取实现截图
   ├── 与设计稿视觉对比
   └── 检查各维度差异
   │
   ▼
4. 生成对齐报告
```

## 阶段 1：设计稿 ↔ 需求对齐

### 设计稿读取

支持三种来源：

| 来源 | 读取方式 | 说明 |
|------|----------|------|
| Pencil .pen 文件 | `mcp__pencil__batch_get` + `mcp__pencil__get_screenshot` | 获取结构 + 视觉截图 |
| 截图/图片 | Read 工具直接查看 | 支持 PNG/JPG 等 |
| Figma | 用户提供截图，或 Figma MCP | 需用户配合 |

### 检查步骤

1. 询问用户设计稿来源和位置
2. 读取设计稿内容/截图
3. 读取 `01-requirements.md`，提取 UI 相关 AC（通常包含"显示""界面""布局""交互"等关键词的 AC）
4. 逐条检查设计稿是否覆盖 AC 描述的 UI 行为

### 输出

AC 覆盖矩阵：

```markdown
| AC 编号 | AC 描述 | 设计稿体现 | 状态 |
|---------|---------|-----------|------|
| AC-001 | 登录页显示邮箱输入框 | 设计稿第 1 页 | ✅ 覆盖 |
| AC-002 | 错误时显示红色提示 | 未见错误状态设计 | ❌ 缺失 |
```

## 阶段 2：设计稿 ↔ 实现对齐

### 实现截图获取

通过浏览器工具获取实现截图：

| 工具 | 使用方式 |
|------|----------|
| Playwright MCP | `mcp__playwright__browser_take_screenshot` |
| Chrome DevTools MCP | `mcp__chrome-devtools__take_screenshot` |
| 用户提供截图 | Read 工具查看 |

### 检查维度

| 维度 | 检查内容 | 严重程度 |
|------|----------|----------|
| 布局结构 | 元素排列、层级关系、区域划分 | Blocker |
| 间距 | 元素间距、内外边距 | Warning |
| 颜色 | 主色、辅色、文字色、背景色 | Warning |
| 字体 | 字族、字号、字重 | Warning |
| 交互状态 | hover/active/disabled/error 状态 | Blocker |
| 响应式 | 不同断点下的布局变化 | Warning |

### 检查步骤

1. 获取实现截图（与设计稿相同页面/状态）
2. 视觉对比两张截图
3. 逐维度检查差异
4. 对显著差异标记严重程度

### 输出

差异列表 + 截图对比。

## 问题分级

### Blocker

- 布局结构与设计稿不符（元素缺失、位置错误）
- 关键交互状态未实现（错误提示、加载状态）
- AC 描述的 UI 行为在设计稿中缺失

### Warning

- 间距/颜色/字体的轻微偏差
- 响应式断点处理差异
- 非关键状态的视觉差异

## 输出文件

生成 `docs/devdocs/ui-alignment-report.md`

详细模板参见 [templates/ui-alignment-report.md](templates/ui-alignment-report.md)

## 降级策略

本 Skill 依赖外部 MCP 工具获取设计稿和实现截图。当工具不可用时，按以下策略降级：

| 条件 | 降级行为 |
|------|----------|
| 无设计稿输入（无截图、无 .pen 文件、无 Figma） | **不可运行**——提示用户提供设计稿后再执行 |
| 有设计稿截图，无浏览器 MCP | 阶段 1 正常执行；阶段 2 要求用户提供实现截图（人工对比模式） |
| 有 Pencil MCP 但无浏览器 MCP | 阶段 1 通过 Pencil 工具读取；阶段 2 要求用户提供实现截图 |
| 有浏览器 MCP 但无设计稿 MCP | 要求用户提供设计稿截图；阶段 2 通过浏览器工具获取实现截图 |

**工具使用说明**：本 Skill 的 `allowed-tools` 仅包含基础工具。Pencil MCP（`mcp__pencil__*`）、Playwright MCP（`mcp__playwright__*`）、Chrome DevTools MCP（`mcp__chrome-devtools__*`）为可选依赖，运行时按可用性自动选择。

## 约束

### 检查约束

- [ ] **阶段 1 必须读取需求文档中的 UI 相关 AC**
- [ ] **阶段 2 必须获取实现截图进行视觉对比**（浏览器 MCP 或用户提供）
- [ ] **必须明确设计稿来源和版本**
- [ ] **必须生成对齐报告**
- [ ] **无设计稿输入时不可运行，必须提示用户提供**

### 工具约束

- [ ] Pencil 文件必须通过 `mcp__pencil__*` 工具访问，不直接 Read
- [ ] 截图获取优先使用 Playwright/Chrome DevTools MCP
- [ ] 无浏览器工具时，要求用户提供实现截图（人工对比模式）
- [ ] MCP 工具为可选依赖，不可用时按降级策略执行

### 安全约束

- [ ] **不修改设计稿**
- [ ] **不修改代码**
- [ ] **不修改 DevDocs 文档**

## Skill 协作

| 场景 | 协作 Skill | 说明 |
|------|-----------|------|
| UI 开发 | `/ui-orchestrator` | 互补：路由开发 vs 验证对齐 |
| UI 任务完成 | `/devdocs-dev-workflow` | 被调用：UI 任务完成后触发验证 |
| 需求参考 | `/devdocs-requirements` | 读取：获取 UI 相关 AC |
| 设计偏差 | `/devdocs-system-design` | 路由：设计文档需更新时 |

## 下一步

| 结果 | 建议下一步 |
|------|------------|
| 阶段 1 有缺失 | 补充设计稿，覆盖缺失的 AC |
| 阶段 2 有 Blocker | 修复实现后重新验证 |
| 阶段 2 仅 Warning | 评估是否需要修复，或更新设计稿 |
| 全部通过 | 进入对抗式验证 |
