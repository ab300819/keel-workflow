# UI 质量自查清单

> 适用于 🟢 UI 层 S9 对抗验证的 **Phase 2-UI**（Phase 2 之后、Phase 3 综合报告之前）。
> 与 Phase 1(/code-quality)、Phase 2(/testing-guide) 并行，不替代。
> 分级使用 Blocker/Suggestion，与 S9 闭环兼容。
> Phase 3 综合报告汇总所有 Phase（含 Phase 2-UI）的结果。

## 与 ms-verify --ui 的边界

检查维度可重叠（均关注布局/色值/交互等），区分点在于证据来源、时机和门禁强度：

| 区分点 | dev-workflow S9 Phase 2-UI | ms-verify --ui |
|--------|---------------------------|----------------|
| 时机 | 开发中自查 | 交付前验证 |
| 证据来源 | 纯代码审查（静态） | 截图对比 + 工具辅助（运行态） |
| 门禁强度 | 轻量门禁（Blocker/Suggestion） | 完整分级报告（P1-P3） |
| 设计稿 | 不要求 | 必须提供 |
| 感知类判断 | 不做（改用静态代理指标） | 做（视觉对比） |

## UI 验收清单生成规则

清单由 Test Agent 在 **S3 结束时**必须产出（🟢 层 S3 为必做■步骤）。
S4 执行时补全可运行断言；S4 跳过时清单仍作为 Phase 2-UI 输入。

生成优先级链：
1. **AC 显式描述** → 直接提取（如"按钮禁用态显示灰色"）
2. **设计 token / 设计系统** → 引用项目已有规范
3. **均无** → 色值/字体/资源项标记 N/A，仅保留交互状态和结构类检查

## Phase 2-UI 审查维度

所有检查项为**静态可判定的代理指标**。

> **适用范围限定**：仅审查 S3 UI 验收清单中列出的项。清单中标记 N/A 或未列出的项自动跳过，不产生 Blocker。
> 例如：纯展示组件无交互状态时，2-UI.2 交互完整性的检查项全部跳过。

### 2-UI.1 设计还原度（代码视角）

- [ ] 布局结构是否与 AC 描述一致 → Blocker
- [ ] 间距/尺寸是否使用设计 token 或一致的值 → Suggestion
- [ ] 色值是否引用变量/token 而非硬编码 → Suggestion
- [ ] 图标/图片资源路径是否正确且存在 → Blocker

### 2-UI.2 交互完整性

- [ ] 所有交互状态是否有对应代码分支（hover/active/disabled/error/loading）→ Blocker
- [ ] 动画是否定义了时长和缓动参数（非无限循环或缺省值）→ Suggestion
- [ ] 表单验证是否有即时反馈逻辑（onChange/onBlur 绑定）→ Blocker
- [ ] 空状态/边界状态是否有条件渲染处理 → Blocker

### 2-UI.3 基础质量

- [ ] 语义化 HTML / 正确的组件层级 → Suggestion
- [ ] 焦点管理：键盘可达、Tab 顺序合理 → Suggestion
- [ ] 触摸目标尺寸 ≥ 44pt（移动端适用时）→ Suggestion
- [ ] 可变长度文本是否应用溢出处理样式（truncate/wrap/ellipsis）→ Suggestion
- [ ] 是否使用响应式布局约束（flex/grid/constraints）→ Suggestion

> 运行态/感知类判断（"动画是否流畅""实际截图是否匹配设计稿"）统一由 `/ms-verify --ui` 或 `--live` 负责。
> 平台专属检查（SwiftUI 安全区、Android Material 规范等）由对应外部 skill 覆盖，此清单仅含跨平台通用项。
