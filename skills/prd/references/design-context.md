# 设计上下文契约（跨 Skill 共享）

> 本文件定义 design_context 的 schema、探测协议和迟到协议。
> 虽放在 prd/references/ 下，但作为跨 skill 共享定义，被 ms-prd、ms-requirements、ms-system-design、ms-dev-tasks、ms-dev-workflow、ms-verify 共同消费。

## Schema

```yaml
design_context:
  design_files:
    available: true | false
    source_type: mastergo | figma | pencil | screenshots | none
    references:
      - id: D-01                  # 设计稿标识，递增编号
        type: mastergo | figma | pencil | screenshot
        location: "<链接/路径>"    # MasterGo 短链接、Figma URL、.pen 文件路径、截图路径
        pages: ["登录", "注册"]    # 该设计稿覆盖的页面/功能
        access_method: structured_dsl | node_tree | vision | manual
  component_library:
    available: true | false
    name: "<包名或路径>"           # 如 @company/ui-kit 或 src/components
    location: "<node_modules/xxx | src/components/>"
    docs_url: "<可选 Storybook/文档站 URL>"
    access_method: read_source | read_types | docs
```

## access_method 语义与工具映射

| access_method | 语义 | MCP 工具 | 适用来源 |
|--------------|------|---------|---------|
| `structured_dsl` | 结构化 DSL 提取（组件层级、属性、样式） | `mastergo-magic-mcp → getDsl / getComponentLink` | MasterGo |
| `node_tree` | 节点树读取（设计节点结构） | `pencil → batch_get` | Pencil .pen |
| `vision` | AI 视觉分析 | `Read` 工具读取图片 | Figma 截图、标注图 |
| `manual` | 人工输入（无法自动提取） | AskUserQuestion | 无工具支持时的兜底 |
| `read_source` | 读取组件源码和类型定义 | `Read` / `Grep` | 代码包（本地） |
| `read_types` | 仅读取 .d.ts 类型定义 | `Read` / `Grep` | 代码包（node_modules） |
| `docs` | 读取在线文档 | `WebFetch` / `context7` | Storybook / 文档站 |

## 探测协议

ms-prd Step 0 和 ms-requirements 步骤 0.5 调用此协议，通过 AskUserQuestion 收集设计资产信息。

### 询问脚本

**问题 1：设计稿**
> 是否有 UI/UX 设计稿？
> - MasterGo（提供短链接或文件 ID）
> - Figma（提供链接或截图）
> - Pencil .pen 文件（提供文件路径）
> - 截图/标注图（提供图片路径）
> - 暂无

**问题 2：UI 组件库**
> 是否有 UI 组件库？
> - 代码包（提供包名和项目内路径，如 node_modules/@company/ui-kit）
> - 本地组件目录（提供路径，如 src/components/ui/）
> - 有在线文档/Storybook（提供 URL）
> - 暂无

### 探测结果处理

- 有设计稿 → 构造 design_context YAML，写入目标文档的 `## 设计资产` 章节
- 无设计稿 → 标记 `design_files.available: false`，写入文档，后续 skill 自动跳过
- 有组件库 → 填充 component_library 字段
- 无组件库 → 标记 `component_library.available: false`

## 迟到协议

设计稿可在任意阶段到达。按"到达时已完成到哪个阶段"，由对应 skill 负责回填：

| 设计稿到达时 | 回填动作 | 负责 skill |
|-------------|---------|------------|
| PRD 完成后、requirements 之前 | 追加 design_context 到 prd index.md `## 设计资产` | ms-requirements（步骤 0.5 询问） |
| requirements 完成后、system-design 之前 | 用户补充到 01-requirements.md `## 设计资产`；检查 UI 相关 AC 是否需要补充交互状态 | ms-system-design 步骤 2（询问偏好）时顺带确认设计稿 |
| system-design 完成后、dev-tasks 之前 | 追加到 01-requirements.md；已完成的 API 设计可能需要局部调整 | ms-dev-tasks（启动时检查并回填） |
| dev-tasks 已拆后 | 追加到 01-requirements.md；对已拆的 🟢 UI 任务补充 design_ref 和组件库映射 | ms-dev-workflow（🟢 任务 S1 触发回填） |
| 开发进行中 | 追加到 01-requirements.md；生成差异报告（设计稿 vs 已有实现） | ms-verify --ui（显式调用） |

### 设计稿更新

已有 design_context 但设计稿内容变更时：由用户主动声明，不做自动检测。声明后按当前所处阶段对应的回填动作执行。

## 设计源能力矩阵

各设计源能自动提供的信息级别：

| 需要的信息 | MasterGo | Pencil .pen | Figma | 截图 |
|-----------|----------|-------------|-------|------|
| 页面/组件结构（布局、层级） | ✅ getDsl | ✅ batch_get | ⚠️ 手动 | ⚠️ AI 视觉 |
| 交互状态清单 | ✅ getDsl | ✅ batch_get | ⚠️ 手动 | ⚠️ AI 视觉 |
| 组件映射（设计→代码） | ✅ getComponentLink | ⚠️ 手动 | ⚠️ 手动 | ❌ |
| 样式 token（颜色、字号、间距） | ✅ getDsl | ✅ batch_get | ⚠️ 手动 | ❌ |
| 设计转代码 | ✅ getD2c | ❌ | ❌ | ❌ |
