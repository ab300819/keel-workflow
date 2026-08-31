---
name: agent-memory
description: Manage AI agent memory files (AGENTS.md/CLAUDE.md). Supports update and restructure modes. Use when users need to sync, update, or restructure agent memory files. Triggers on keywords like "记忆文件", "memory file", "AGENTS.md", "更新记忆", "重构记忆", "memory sync", "memory restructure".
allowed-tools: Read, Write, Glob, Grep, Edit, Bash, AskUserQuestion
---

# 记忆文件管理

管理 AI Agent 记忆文件（AGENTS.md / CLAUDE.md），支持更新和重构操作。

## 核心理念

### AGENTS.md 为唯一事实源

```text
项目信息源（代码库 + 文档）
    │
    │  提取精华（distill）
    ▼
AGENTS.md（精简、稳定、跨 AI 工具通用）← 通用信息唯一编辑点
    │
    ├── CLAUDE.md（@AGENTS.md 导入 + Claude Code 专属补充）
    ├── .claude/rules/devdocs-state.md（仅 DevDocs 项目，编号状态）
    └── 未来：.cursorrules / .windsurfrules（预留，不实现）
```

**原则**：
- AGENTS.md 保持工具无关，不包含特定 AI 工具的专属语法
- CLAUDE.md 通过 `@AGENTS.md` 导入通用信息，并可追加 Claude Code 专属补充
- 工具专属信息通过各自的规则文件补充（如 `.claude/rules/`）

### 最佳实践参照

[best-practices.md](templates/best-practices.md) 为所有模式的共享规范：
- 首次创建时：作为质量基准
- `--update` 更新时：作为内容筛选依据
- `--restructure` 重组时：作为结构验证和反模式检测标准

### 与 `/init` 的协作

各 AI 工具的 `/init` 行为不同（如 Claude Code 创建 CLAUDE.md）。本 skill 不假设 `/init` 产出什么文件，而是保证 AGENTS.md 架构正确：
- AGENTS.md 不存在时：自动从项目源扫描并创建
- `/init` 已创建 AGENTS.md 时：后续 `--update` 在此基础上增量更新
- [best-practices.md](templates/best-practices.md) 作为内容质量参考
- [memory-template.md](templates/memory-template.md) 作为 AGENTS.md 输出模板

## 语言规则

- 支持中英文提问
- 统一中文回复

## 运行模式

```bash
/agent-memory                    → 智能检测（AGENTS.md 存在？需要更新？）
/agent-memory --update           → 从项目源提取信息，更新 AGENTS.md
/agent-memory --restructure      → 按最佳实践重组现有 AGENTS.md
```

| 模式 | 读取项目 | 写入文件 | 适用场景 |
|------|----------|----------|----------|
| 智能检测 | 视情况 | 视情况 | 不确定时 |
| `--update` | ✅ | AGENTS.md + CLAUDE.md（若缺失） + devdocs-state.md（仅 DevDocs） | 阶段性工作完成后同步 |
| `--restructure` | ✅ | AGENTS.md + CLAUDE.md | 记忆文件结构混乱时重组 |

### 智能检测流程

```text
检测 AGENTS.md 是否存在
        │
        ├── 不存在 → 扫描项目源，首次创建 AGENTS.md + CLAUDE.md
        │
        └── 存在 → 分析内容状态
                    ├── 信息过时 → 建议 --update
                    └── 结构混乱 → 建议 --restructure
```

## 信息提取分层

### 通用提取（所有项目）

| 来源 | 提取内容 |
|------|----------|
| package.json / go.mod / Cargo.toml | 技术栈、运行命令 |
| README.md | 项目概述 |
| git log | 提交约定 |
| 代码结构 | 关键目录、入口文件 |

### DevDocs 增强提取（有 docs/devdocs/ 时）

| 来源 | 提取内容 |
|------|----------|
| 02-system-design.md | 技术栈、架构决策 (ADR) 摘要 |
| 01-requirements.md | 领域术语 |
| 04-dev-tasks.md | 活跃任务 + 进度 |
| 所有文档 | 编号状态（max F/US/AC/T/ADR） |

**工作流路由节(幂等补节)**:`docs/devdocs/` 存在且 AGENTS.md 缺「工作流路由」节 → 按 [memory-template.md](templates/memory-template.md) 补入(带 `<!-- agent-memory:managed -->` 标记);节已存在 → 保留原文不覆盖(用户自定义优先)。

**60 行硬限处理**:补节/更新前后计行;超限 → 仅压缩带 `<!-- agent-memory:managed -->` 标记的可再生章节(未知/用户章节绝不压缩);无标记章节可压 → ⚠️ 必须确认
恢复方式:用户选择裁剪项或转 `--restructure`;无确认不写入(不得静默越界)。

## `--update` 工作流程

```text
1. 扫描项目信息源
   ├── 通用提取（包管理器、README、git、代码结构）
   └── DevDocs 增强提取（若 docs/devdocs/ 存在）
   │
   ▼
1.5 检查 AGENTS.md 是否存在
   ├── 不存在 → 使用 memory-template.md 创建
   └── 存在 → 增量更新
   │
   ▼
2. 提取精华
   ├── 技术栈
   ├── ADR 摘要（若有；无 ADR 格式则从变更记录提取关键决策）
   ├── 领域术语
   ├── 活跃任务 + 进度
   ├── 编号状态（仅 DevDocs 项目）
   └── 运行命令
   │
   ▼
2.5 按 best-practices.md 筛选
   ├── 内容筛选标准：应写入 vs 不应写入
   └── 质量守则：6 条检查
   │
   ▼
3. 更新 AGENTS.md（使用 templates/memory-template.md）
   └── 若文件首部已有 `---...---` frontmatter 块,本步骤只在该块之后的内容范围内操作,不移动/改写/吞掉该块(即使模板「首次创建时内容」首行恰好也是 HTML 注释,与真实 frontmatter 不可混淆)
   │
   ▼
3.5 devdocs frontmatter 幂等写入(可选,仅调用方传入 `devdocs_frontmatter` 时触发;详见下方「devdocs frontmatter 写入(可选)」)
   │
   ▼
4. 确保 CLAUDE.md 存在（若缺失则创建导入文件；已存在则跳过，不覆盖补充区）
   │
   ▼
5. 生成/更新 .claude/rules/devdocs-state.md（仅 DevDocs 项目）
   ├── 写入前按 [devdocs-state-template.md](templates/devdocs-state-template.md) § Forbidden 校验
   │   ├── 占位 prose ≤ 200 字符
   │   ├── 禁止内嵌 commit hash / LOC / 测试结果 / codex 分数 / 文件路径 / submodule 引用 / 工时
   │   └── 违反时改写为简洁占位 + 明细去对应资源文件
   ▼
6. 健康度自检（仅 DevDocs 项目）
   ├── Bash: wc -c .claude/rules/devdocs-state.md
   ├── 读取 .claude/rules/.health-baseline.yml（若存在）→ 拿到 baseline 大小
   ├── 计算 delta = current_size - baseline_size
   ├── delta < 0（缩小）→ 不阻断，更新 baseline
   ├── 0 ≤ delta < 2 KiB（小幅增长）→ 不阻断，更新 baseline
   ├── delta ≥ 2 KiB 且 size > 10 KiB → ⚠️ 提示 `/ms-pipeline realign --scope=health --dry-run`
   ├── size > 40 KiB AND 无 baseline → ⛔ 阻断；用户两种恢复方式：
   │     a. /ms-pipeline realign --scope=health --apply 修复后重跑 update
   │     b. /agent-memory --update --bypass-state-check="<原因>" 一次性豁免（≥10 字符）+ 自动 init baseline
   └── size > 40 KiB AND 已有 baseline AND delta < 2 KiB → ⚠️ 提示但不阻断（存量项目逐步收敛）
```

**baseline 文件**：`.claude/rules/.health-baseline.yml`（gitignore 推荐加入；首次 bypass 时自动生成）

```yaml
schema: health-baseline.v1
devdocs_state_size_bytes: <int>
created_at: <iso-ts>
created_by: /agent-memory --update --bypass-state-check
bypass_reason: <用户提供的原因>
```

设计意图：避免 mic-en 等存量项目（245k）立即被 ⛔ 卡死；首次 bypass 锚定 baseline，之后只阻断"新增膨胀"。

### devdocs frontmatter 写入(可选)

**触发条件**:调用方随 `Task: /agent-memory --update` 传入 `devdocs_frontmatter`,嵌在 [constraints.md](../_shared/constraints.md) §3 最小握手协议的 `inputs` 里:

```yaml
skill: agent-memory
mode: update
inputs:
  devdocs_frontmatter:
    initialized_at: "2026-08-07"
expected_output: yaml-summary-v1
```

**未传入此字段时(当前全部存量项目):本节全部步骤跳过,AGENTS.md 不新增 frontmatter,行为与现状完全一致。**

> ⛔ **`workspace:` 块不受本 skill 管理。** 工作区拓扑（`mode` / `code_roots`）是**仓库级事实**,由 [/workspace-topology](../workspace-topology/SKILL.md) 自己写自己的块。本 skill 遇到 `workspace:` 块一律**原样保留**——不解析、不比较、不覆写、不删除,连键序和缩进都不动。历史上这两个字段曾在本 skill 的受管白名单里(经 `devdocs.workspace_mode` / `devdocs.code_roots`),现已移除。

**受管字段白名单**(按字段而非块标记界定受管边界 —— YAML frontmatter 不支持 HTML 注释,不能沿用正文的 `<!-- agent-memory:managed -->` 体例):当前仅 `initialized_at`。白名单外的字段**不写**。下方写入算法本身是通用的,未来新增受管字段时只需把字段名加入白名单即可复用。本节只定义"怎么写"。

**写入步骤**:

1. **定位/插入 frontmatter 块**:
   - AGENTS.md 首行已是 `---` → 已有 frontmatter,解析到下一个 `---` 为止的 `devdocs:` YAML 段
   - AGENTS.md 不存在 → 先完成本次 `--update` 首次创建流程,再在生成结果最前面插入 frontmatter
   - AGENTS.md 存在但无 frontmatter(包括首行是 HTML 注释等正文内容)→ 在**文件最前面**插入新 frontmatter 块,原有全部内容整体下移,不改写原内容一个字符(schema 硬规则:frontmatter 必须紧贴文件起始,无 leading 空行 / heading)
2. **合并白名单字段**:
   - 传入值与已有值相同 → no-op(幂等)
   - `initialized_at` 已存在 → 不可修改;调用方传入不同值 → ⛔ 不写入,报告冲突
   - `initialized_at` 不存在 → 首次写入补当天 ISO 日期
   - 白名单外字段(含整个 `workspace:` 块):原样保留 key/value/原始顺序,不比较、不改动
3. **写入前校验**:校验规则逐条检查;任一不通过 → ⛔ 本步骤不写入,`blockers` 报告具体规则 + 冲突值,frontmatter 保持原状(**不回滚已完成的 AGENTS.md 正文更新,也不阻塞后续步骤**;整体 `status` 按 `partial` 处理,`summary.details.devdocs_frontmatter: blocked`)

   **明确(避免 fail-closed 惯性误判为阻塞)**:`devdocs:` 段首次创建时,白名单外的字段本就不存在。这种"缺失"**不是** ⛔ 判据——devdocs 段不完整只 ⚠️ 警告 + 建议补全,不阻塞。
4. 校验通过 → 写入 frontmatter,其余 AGENTS.md 正文流程照常继续

**示例**(`workspace:` 块由 workspace-topology 写入,本 skill 原样保留;本 skill 只补 `devdocs.initialized_at`):

```markdown
---
workspace:
  mode: shell
  code_roots: [web]
devdocs:
  initialized_at: "2026-08-07"
---
<!-- 由 /agent-memory 生成，请通过该命令更新 -->
```

### 分流规则

| 信息类型 | 目标位置 | 理由 |
|----------|----------|------|
| 技术栈、运行命令 | AGENTS.md | 跨工具通用，每次会话都需要 |
| 架构决策 (ADR) 摘要 | AGENTS.md | 防止重复询问 |
| 活跃任务 + 进度 | AGENTS.md | 即时行动上下文 |
| 领域术语、业务边界 | AGENTS.md | 高频稳定，防止误解 |
| 代码约定、提交格式 | AGENTS.md | 跨工具一致 |
| 编号状态 (max F/US/AC/T/ADR) | `.claude/rules/devdocs-state.md` | Claude 专属运行态 |
| 完整需求/设计/测试详情 | 留在 `docs/devdocs/` | 太详细，不适合记忆文件 |
| `initialized_at` | AGENTS.md devdocs frontmatter | 治理字段，仅调用方显式传入 `devdocs_frontmatter` 时写入 §1 |

## `--restructure` 工作流程

```text
1. 读取现有 AGENTS.md
   │
   ▼
2. 按 best-practices.md 检测不规范项
   ├── 行数限制（≤ 60 行）
   ├── 工具无关性
   ├── 章节顺序（对照结构规范）
   ├── 反模式检测
   └── 缺失章节
   │
   ▼
3. 按 templates/memory-template.md 重组
   │
   ▼
4. 展示重组方案，确认后写入
   │
   ▼
5. 确保 CLAUDE.md 存在（若缺失则创建导入文件；已存在则跳过）
```

## 输出文件

### AGENTS.md

- 位置：项目根目录
- 模板：[templates/memory-template.md](templates/memory-template.md)
- 约束：不超过 60 行，工具无关
- 可选 devdocs frontmatter（`initialized_at`）：仅调用方传入 `devdocs_frontmatter` 时写入；`workspace:` 块原样保留不动，见 [devdocs frontmatter 写入(可选)](#devdocs-frontmatter-写入可选)

### CLAUDE.md

- 位置：项目根目录
- 结构：`@AGENTS.md` 导入 + Claude Code 专属补充区
- 创建时机：AGENTS.md 首次生成时一并创建；已存在则不覆盖
- 补充区由用户手动维护，`/agent-memory` 不修改

### .claude/rules/devdocs-state.md

- 位置：`.claude/rules/devdocs-state.md`
- 模板：[templates/devdocs-state-template.md](templates/devdocs-state-template.md)
- 条件：仅 DevDocs 项目（docs/devdocs/ 存在时）

## 约束

### 内容约束

- [ ] **AGENTS.md 不超过 60 行**
- [ ] **AGENTS.md 不包含特定 AI 工具的专属语法**
- [ ] **CLAUDE.md 通过 @AGENTS.md 导入通用信息**（首次创建后不覆盖）
- [ ] **编号状态仅写入 `.claude/rules/devdocs-state.md`**
- [ ] **devdocs-state.md 占位 prose ≤ 200 字符 / 单行 ≤ 500 字符 / 文件 ≤ 40 KiB**（违反由 health-lint 检测）
- [ ] **devdocs-state.md 禁止内嵌 commit hash / LOC / 测试结果 / codex 分数 / 文件路径 / 工时统计**（明细去资源文件）
- [ ] **devdocs frontmatter 仅在调用方显式传入 `devdocs_frontmatter` 时写入**；未传入不新增、不检查，inline 路径零影响
- [ ] **`initialized_at` 一旦写入不可修改**；传入冲突值 ⛔ 不写入并报告
- [ ] **devdocs frontmatter 白名单外字段原样保留**，不读不改（按字段而非块标记界定受管边界）

### 质量守则

写入 AGENTS.md 前按 [best-practices.md](templates/best-practices.md) 检查：
- 6 条守则（短而稳定 / 广泛适用 / 可执行 / 避免重复 / 详情留原地 / 工具无关）
- 内容筛选标准（应写入 vs 不应写入）
- 反模式清单

### 操作约束

- [ ] 不生成/不修改 `00-context.md`
- [ ] 可删则删，优先命令、约束、检查点
- [ ] `--restructure` 重组前必须确认

## Skill 协作

| 场景 | 协作 Skill | 说明 |
|------|-----------|------|
| 首次创建 | `/agent-memory` 自行完成 | 从项目源扫描创建；若 `/init` 已创建则增量更新 |
| 阶段性文档变更 | `/ms-onboard` | onboard 完成后建议运行 /agent-memory |
| 任务完成轻量更新 | `/ms-dev-workflow` | dev-workflow 步骤 6.5 内联更新"当前状态" |
| 上下文摘要 | `/ms-onboard` | onboard 生成 00-context.md，不涉及记忆文件 |

## 子 Agent 摘要格式（yaml-summary-v1）

被编排层(如 `/ms-pipeline` init / `/ms-retrofit`)以 Task 委托时,返回统一信封;字段语义以 [constraints.md §2](../_shared/constraints.md) 为权威,不扩展 status、不私有化保留字段,私有统计入 `summary.details`:

```yaml
skill: agent-memory
status: success | failed | interrupted | partial   # 四值,语义见共享 SSOT
summary:
  headline: "AGENTS.md 已更新,含工作流路由节"
  details: {routing_section: added | kept | skipped, lines: 58, devdocs_frontmatter: written | unchanged | skipped | blocked}
blockers: []          # 如 60 行超限待确认,或 devdocs frontmatter 校验失败(均 partial 时必填)
output_files: [AGENTS.md]
new_ids: {}
next_recommended: {skill: "", args: ""}
```

## 模板引用

- AGENTS.md 模板：[templates/memory-template.md](templates/memory-template.md)
- 编号状态模板：[templates/devdocs-state-template.md](templates/devdocs-state-template.md)
- 最佳实践：[templates/best-practices.md](templates/best-practices.md)
