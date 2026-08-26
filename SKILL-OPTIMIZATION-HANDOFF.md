# Skills 仓库优化评估交接

> 日期：2026-08-10  
> 状态：待 Claude 复核与决定实施范围  
> 范围：仓库 `/Users/mason/Projects/skills`、当前 Codex 会话已加载的 skill catalog、`/Users/mason/.agents/skills` 安装目录  
> 性质：只读盘点结论；本文记录问题、背景、建议方案和验收标准，不代表方案已经实施

## 1. 任务背景

本仓库是一套跨 Claude Code、Codex CLI、OpenCode 使用的 Agent Skills，当前包含 35 个 skill：

- 22 个 `ms-*` DevDocs 流程 skill；
- 13 个独立 skill；
- 规格形态为 Markdown、YAML frontmatter、references、templates；
- 当前没有仓库级 build、test 或 lint 命令；
- `SKILL.md <= 500` 行是现有硬约束；
- 跨 skill 的协议级 SSOT 位于 `skills/_shared/constraints.md`。

本轮任务是结合仓库现状和 Codex 当前已加载的 skills，判断还存在哪些优化空间。盘点后的核心判断是：

> 当前最优先的问题不是继续增加或合并 skill，而是仓库定义、安装结果、运行时工具能力和路由规则四者没有形成可验证的一致性闭环。

现有 skill 的领域拆分总体合理，22/13 数量与 README、AGENTS.md 一致，所有 `SKILL.md` 均未超过 500 行。主要风险集中在安装漂移、跨客户端工具协议、流程 owner 冲突、工具型 skill 过期和缺少回归评测。

## 2. 本轮盘点范围与方法

### 2.1 已检查内容

- 根目录 `README.md`、`AGENTS.md`、`CLAUDE.md`；
- `skills/*/SKILL.md` 的名称、frontmatter、行数和描述；
- `skills/_shared/constraints.md`；
- `docs/workflows.md` 中 superpowers 共存策略；
- 部署脚本 `scripts/deploy-skills.sh`；
- 当前 Codex 会话提供的 loaded skills catalog；
- 当前 Codex 运行时实际暴露的 IDEA、Chrome DevTools 等工具；
- `/Users/mason/.agents/skills` 中的已安装副本；
- 当前 git 工作区状态。

### 2.2 结构统计

盘点时统计结果：

| 项目 | 结果 |
|---|---:|
| skill 数量 | 35 |
| `ms-*` skill | 22 |
| 独立 skill | 13 |
| `skills/*/SKILL.md` 总行数 | 10,962 |
| `skills/` 下文件数 | 179 |
| `skills/` 下 Markdown/HTML 总行数 | 38,915 |
| 超过 500 行的 `SKILL.md` | 0 |
| 超过 20KB 的 `SKILL.md` | 6 |
| 含 `allowed-tools` frontmatter 的 skill | 32 |
| 含自定义 `metadata` frontmatter 的 skill | 24 |
| 含 `user-invocable` frontmatter 的 skill | 9 |
| `agents/openai.yaml` | 0 |

超过 20KB 的入口包括：

- `skills/dev-workflow/SKILL.md`；
- `skills/pipeline/SKILL.md`；
- `skills/verify/SKILL.md`；
- `skills/system-design/SKILL.md`；
- `skills/requirements/SKILL.md`；
- `skills/code-quality/SKILL.md`。

### 2.3 工作区保护

盘点开始前已有一个用户未跟踪文件：

```text
?? docs/superpowers/specs/2026-07-31-markdown-style-skill-design.md
```

该文件未被修改。本交接文档是本轮唯一新增文件。

## 3. P0：安装、发现和加载状态不一致

### 3.1 观察到的事实

以仓库 `skills/*/SKILL.md` 的 frontmatter `name` 为键，与 `/Users/mason/.agents/skills/<name>/SKILL.md` 比较：

- 26 个 skill 内容一致；
- 6 个已安装 skill 落后于仓库版本；
- 3 个仓库 skill 在对应安装路径下缺失。

内容落后的 6 个：

| Skill | 状态 |
|---|---|
| `agent-memory` | 安装副本比仓库少 21 行 |
| `ms-bugfix` | 仓库相对安装副本约 20 行新增、1 行变化 |
| `ms-dev-workflow` | 仓库相对安装副本有 6 行新增、3 行变化 |
| `ms-onboard` | 1 行变化 |
| `ms-pipeline` | 5 行新增、1 行变化 |
| `ms-retrofit` | 3 行新增、1 行变化 |

对应安装路径缺失的 3 个：

- `/Users/mason/.agents/skills/ms-board/SKILL.md`；
- `/Users/mason/.agents/skills/e2e-test-flow/SKILL.md`；
- `/Users/mason/.agents/skills/idea-mcp-workflow/SKILL.md`。

值得注意的是，当前 Codex turn 的 loaded skills catalog 又列出了这 3 个 skill，并把路径归到 `r1`，而 `r1` 映射为 `/Users/mason/.agents/skills`。这表明 catalog 快照、磁盘安装目录或技能发现缓存之间可能存在漂移。Claude 接手时需要确认具体客户端的发现/缓存机制，不应直接假设 catalog 与磁盘总是实时一致。

### 3.2 部署脚本的命名问题

`scripts/deploy-skills.sh` 当前使用目录 basename 作为安装目录名：

```bash
skill_name=$(basename "$skill_dir")
ln -sfn "$skill_dir" ~/.agents/skills/"$skill_name"
```

但 22 个 `ms-*` skill 的目录刻意省略 `ms-` 前缀，例如：

```text
skills/bugfix/       -> frontmatter name: ms-bugfix
skills/pipeline/     -> frontmatter name: ms-pipeline
skills/requirements/ -> frontmatter name: ms-requirements
```

因此本地部署脚本会创建 `~/.agents/skills/bugfix`，而现有安装习惯和 loaded catalog 使用的是 `~/.agents/skills/ms-bugfix`。这会造成：

- 同一 skill 出现两种目录名；
- 旧安装副本无法被新部署覆盖；
- 用户以为部署成功，运行时仍加载旧版本；
- 不同客户端可能按目录名或 frontmatter 名产生不同结果。

### 3.3 README 安装命令错误

README 当前写的是：

```bash
git clone https://github.com/ab300819/skills.git && bash skills/scripts/deploy-skills.sh
```

真实脚本路径是仓库根目录下的：

```text
scripts/deploy-skills.sh
```

若用户 clone 后当前目录没有恰好满足额外的 `skills/` 层级，README 命令会失败。

### 3.4 建议修复方案

1. 部署脚本从每个 `SKILL.md` 的 frontmatter 读取 `name`，安装目标统一使用 runtime name。
2. 增加只读检查模式：

   ```bash
   scripts/deploy-skills.sh --check
   ```

3. `--check` 至少报告：

   - missing；
   - stale/content-diff；
   - wrong-directory-name；
   - duplicate；
   - broken symlink；
   - source commit/hash；
   - 可能需要迁移的旧短名目录。

4. 正常部署只创建或更新正确名称的链接，不自动删除旧目录。
5. 对旧目录的清理先提供 dry-run，再由用户确认执行。
6. 修正 README 的本地部署命令，并说明脚本使用符号链接还是复制。
7. 明确 catalog 是否需要重启客户端、刷新缓存或重新发现才能生效。

### 3.5 验收标准

- 35 个仓库 skill 均可由 frontmatter `name` 在目标目录找到；
- `--check` 返回零 missing、零 stale、零 wrong-name；
- 连续执行部署两次结果幂等；
- 不产生 `bugfix` 与 `ms-bugfix` 两套安装；
- README 命令在全新 clone 后可直接执行；
- Claude、Codex、OpenCode 至少各做一次发现结果抽查。

## 4. P0：缺少仓库自身的验证闭环

### 4.1 背景

AGENTS.md 明确记录本仓库“无 build/test/lint 命令”。对 Markdown skill 规格库而言不需要传统编译，但当前已经存在以下可机械发现的问题：

- README 引用了错误脚本路径；
- 部署目录名与 frontmatter `name` 不一致；
- 已安装版本与仓库版本漂移；
- 工具名和当前 runtime schema 漂移；
- internal/FUTURE skill 仍进入默认发现集；
- frontmatter 字段在不同客户端的支持范围不同。

现有 `/ms-pipeline realign --scope=health` 主要治理消费方项目的 DevDocs 产物，不等同于本 skill 仓库自身的 package validation。

### 4.2 建议修复方案

增加一个仓库原生、确定性、尽量零依赖的 validator。命名可由维护者决定，例如：

```text
scripts/validate-skills.sh
scripts/check-skills.rb
```

首版只实现高价值检查，不扩展成复杂框架：

1. YAML frontmatter 可解析；
2. `name`、`description` 存在；
3. `name` 唯一且符合命名规则；
4. 目录短名与 runtime name 满足显式映射规则；
5. `SKILL.md <= 500`；
6. README 声明数量与实际数量一致；
7. README、SKILL.md 中的仓库内文件链接存在；
8. SKILL.md 直接引用的 references/templates 存在；
9. internal skill 不应暴露为用户入口；
10. 共享协议的 status 值域、FUTURE 标记和 yaml-summary envelope 不漂移；
11. 工具依赖属于对应平台 capability manifest；
12. 可选执行 installed-state check。

链接检查需要区分：

- 真正的仓库相对链接；
- 模板中的示例路径；
- FUTURE 产物路径；
- Markdown 代码块内的伪链接；
- 带 anchor 的链接。

不要用“所有形如 `[x](y)` 都必须在仓库存在”的简单正则直接阻断 CI，否则会把模板输出路径误判为死链。

### 4.3 外部 validator 试运行结果

本轮尝试使用当前 Codex `skill-creator` 自带的 `quick_validate.py`，但环境缺少 PyYAML：

```text
ModuleNotFoundError: No module named 'yaml'
```

这进一步说明仓库 validator 最好：

- 使用系统已有的标准库；或
- 明确声明和安装依赖；或
- 提供固定容器/CI 环境。

不能把一个当前环境无法运行的外部校验器当作仓库验证闭环。

### 4.4 验收标准

- validator 在全新 clone 环境中有明确、可复现的启动方式；
- 当前 README 错误和部署命名错误能被测试用例捕获；
- 退出码能区分 pass/fail；
- 输出包含文件和规则 ID；
- 不修改仓库；
- CI 和本地使用同一入口；
- 对模板示例路径没有大量误报。

## 5. P1：跨客户端工具协议没有抽象

### 5.1 观察到的事实

`skills/_shared/constraints.md` 将委托协议直接绑定到 `Task tool`。多个 skill 的 frontmatter 或正文还直接使用：

- `Task`；
- `AskUserQuestion`；
- `TodoWrite`；
- `Read`、`Write`、`Glob`、`Grep`、`Edit`、`Bash`；
- `mcp__chrome-devtools__*`；
- `mcp__idea__*`。

这些是具体客户端或具体 runtime 的工具名，不是稳定的业务语义。当前 Codex 对应能力主要表现为：

- 子代理：`spawn_agent` 等 collaboration tools；
- 文件修改：`apply_patch`；
- shell：`exec_command`；
- 用户输入工具只在特定模式可用；
- MCP 工具可能延迟加载，也可能在本轮完全不存在。

因此当前仓库更接近“文档层跨客户端”，还没有完全做到“执行层跨客户端”。

### 5.2 建议架构

将协议拆成两层：

```text
稳定语义能力
  delegate
  ask-user
  plan
  read
  patch
  shell
  browser
  browser-devtools
  ide
  database-read
        |
        v
平台适配
  Claude Code adapter
  Codex adapter
  OpenCode adapter
```

共享约束描述语义和失败行为，不写死工具名。例如：

```text
delegate：创建隔离上下文执行原子任务。
- Claude Code：Task
- Codex：spawn_agent
- 无子代理能力：返回 capability-missing，不得伪造 fresh-context review
```

### 5.3 frontmatter 兼容性

当前 32 个 skill 带 `allowed-tools`，24 个带自定义 `metadata`。当前 Codex `skill-creator` 的指导倾向于只在 frontmatter 保留 `name` 和 `description`，其他运行时可能允许更多字段。

不建议未经验证就删除现有字段，因为它们可能服务于 Claude 或其他工具。更稳妥的方案是：

- 源文件保留平台中立 capability 声明；
- 构建或部署时生成平台特定 frontmatter/manifest；或
- 明确记录哪些字段属于 agentskills 标准、哪些是 Claude 扩展、哪些仅供仓库治理。

### 5.4 验收标准

- 核心协议不再把 `Task` 当成唯一实现；
- 每个需要子代理/交互/浏览器的 skill 都有 capability preflight；
- 能力缺失时返回诚实的 partial/failed + recovery；
- 不把“逻辑上应该隔离”表述成“运行时已经物理隔离”；
- 同一个 skill 在三个目标客户端上都能找到合法执行路径或明确失败。

## 6. P1：工具依赖型 skill 与当前 runtime 漂移

### 6.1 `idea-mcp-workflow`

当前 skill 描述和正文包含以下假设：

- IDEA 工具约 60 个；
- `mcp__idea__*` 全是 deferred；
- 调用前必须先通过 `ToolSearch` 加载；
- 使用 `find_files_by_glob`、`search_in_files_by_regex` 等工具名；
- `build_project` 返回形态可能是结构化 JSON，也可能是文本。

本轮 Codex runtime 实际暴露约 65 个 `mcp__idea__*` 工具，其中当前可见工具名包括：

- `search_file`；
- `search_regex`；
- `search_text`；
- `build_project`；
- `get_file_problems`；
- `analyze_calls`；
- `execute_sql_query`；
- XDebug 系列。

因此至少存在这些漂移：

- 不应记录易漂移的工具总数；
- deferred/ToolSearch 机制不能视为跨运行时恒定事实；
- 部分正文工具名已过期；
- `build_project` 的当前 schema 已明确为结构化结果。

建议：

1. `SKILL.md` 只保留稳定纪律：`projectPath`、输出防爆、依赖与真 bug 区分、Maven reload 边界；
2. 工具选择表放到按 runtime/schema 更新的 reference；
3. 启动时动态检查当前工具；
4. 不记录工具数量；
5. 删除或更新不存在的旧工具名；
6. 为 schema 漂移增加 smoke prompt。

### 6.2 `ui-orchestrator`

当前 UI 路由主要围绕：

- `baseline-ui`；
- `ui-ux-pro-max`；
- `frontend-design`；
- `swiftui-expert-skill`。

它通过 shell 扫描 `~/.claude/skills`、`~/.agents/skills` 判断是否安装，未安装就提示用户安装。

但当前 loaded skills 已经包含更完整的 UI 能力：

- `baseline-ui`；
- `fixing-accessibility`；
- `fixing-metadata`；
- `fixing-motion-performance`；
- `swiftui-expert-skill`；
- 多个 Figma skill；
- Sites building/hosting；
- Figma motion、SwiftUI、design-to-code 等强制前置 skill。

当前 `ui-orchestrator` 没有反映这些能力和 mandatory prerequisite，且仍可能优先推荐当前并未加载的 `ui-ux-pro-max`、`frontend-design`。

建议二选一：

#### 方案 A：缩成薄路由层，推荐

- 按当前 catalog/capability 路由；
- 不通过 shell 目录猜测“是否可调用”；
- 只描述路由决策，不复制外部规则；
- 缺首选能力时优先选已加载的等价能力；
- 尊重 Figma、Sites 等插件 skill 的 mandatory prerequisite。

#### 方案 B：退役

如果目标客户端已经能稳定依据 description 自动路由，`ui-orchestrator` 可能只是在重复平台能力。此时可把少量路由知识迁入 README 或 AGENTS.md，避免再维护一个容易过期的 dispatcher。

需要用实际 prompt eval 决定 A/B，不应仅凭主观判断。

### 6.3 `ms-board` 与 `e2e-test-flow`

二者 hard-code 多个 `mcp__chrome-devtools__*` 工具。本轮 Codex runtime 中该前缀工具数量为 0，但 loaded skills 中存在：

- Chrome 控制 skill；
- in-app Browser skill；
- Playwright skill；
- Computer Use skill。

建议：

- S0 增加浏览器 capability preflight；
- 明确哪些能力必须是 DevTools 网络层，哪些可以由 Chrome/Playwright 替代；
- 不能等流程中段才发现工具不存在；
- 若网络请求捕获等关键能力不可替代，直接返回 partial/blocked 和 recovery；
- 不要为了“能跑”而悄悄降低黑盒隔离或证据标准。

## 7. P1：process skill 多重触发和 owner 冲突

### 7.1 背景

仓库已经设计了与 superpowers 的单向兼容策略：DevDocs 项目中由 `ms-*` 让外部 process skill 退居辅助位置，原则是“可选增强、单一路径归一化”。

但当前加载环境中仍存在以下重叠：

| 用户意图 | 可能同时触发 |
|---|---|
| 模糊想法/需求探索 | `ms-prd`、`ms-prd-brainstorm`、`superpowers:brainstorming` |
| Bug 修复 | `ms-bugfix`、`dev-flow`、`superpowers:systematic-debugging` |
| 按计划开发 | `ms-dev-workflow`、`dev-flow`、`executing-plans`、`test-driven-development` |
| 审查/验证 | `ms-verify`、`code-quality`、`adversarial-review`、`requesting-code-review` |
| “优化一下” | `ms-insights`、`refactor`、`code-quality`、UI 专项 skill |
| 测试 | `testing-guide`、`ms-test-cases`、`ms-test-run`、`e2e-test-flow` |

`dev-flow` 自己已经包含 Contract、Red-Green、Verify、fresh-context review，却又写明 `executing-plans` 可以作上层计划执行器。若两个流程同时拥有阶段控制权，就会出现：

- 重复询问；
- 重复建计划；
- 重复 TDD 门；
- 两套完成标准；
- 谁负责提交、push、结束分支不清楚；
- 外部 skill 输出不符合 yaml-summary-v1。

### 7.2 建议规则：一个任务只能有一个 process owner

建议将路由优先级固化为：

1. 用户显式指定的 skill；
2. 项目体系标记；
3. 工具/产物专属 skill；
4. 通用流程 skill；
5. 原则型/质量型 skill 只能作为约束或参考，不得开启第二条流程。

具体建议：

- 存在 DevDocs 且任务属于主链：owner 为对应 `ms-*`；
- DevDocs 内轻量任务：`ms-dev-workflow --inline`；
- 非 DevDocs 的执行任务：`dev-flow`；
- superpowers writing-plans 的计划可以作为 `dev-flow` 输入产物；
- `executing-plans` 不应再作为与 `dev-flow` 并行的上层 owner；
- 系统化调试纪律可以被 owner 内化，但不再启动第二套 bugfix 状态机；
- `code-quality`、`testing-guide` 是约束 SSOT，不拥有开发生命周期；
- `adversarial-review` 只在 owner 明确请求独立审查时运行。

### 7.3 根仓库自身的路由缺口

`docs/workflows.md` 说明下游 DevDocs 项目会由 `agent-memory` 写入“工作流路由”节，但本仓库根 `AGENTS.md` 当前主要记录共存决策，没有一个实际生效、明确覆盖 skill 元开发场景的路由块。

因此维护这个 skills 仓库本身时，仍可能被 superpowers 的强制 process skill 接管。Claude 应评估是否在根 AGENTS.md 中增加本仓专用规则，例如：

- 对 skill 元设计、协议调整、DevDocs skill 开发，哪个流程是 owner；
- 何时允许 superpowers brainstorming/writing-plans；
- 何时只把 superpowers 产物当输入；
- 明确禁止双重门控。

### 7.4 验收标准

建立 should-trigger/should-not-trigger prompt 集，至少覆盖：

- “帮我分析现有代码”；
- “优化一下这个 skill”；
- “修这个 DevDocs 项目的 bug”；
- “修一个没有 DevDocs 的小 bug”；
- “根据这份计划开发”；
- “设计 E2E 测试用例”；
- “执行已有 E2E 用例”；
- “审查代码”；
- “审查 01/02 文档”；
- “做一个 Figma 设计并落代码”。

每条 case 应声明：

- 唯一 process owner；
- 可叠加的约束 skill；
- 不应触发的近邻 skill；
- 预期工具前置检查；
- 是否需要用户确认。

## 8. P2：上下文成本与渐进披露仍可优化

### 8.1 当前状态

全部 `SKILL.md` 都满足 500 行硬约束，说明已有拆分治理有效。问题不是“文件违规”，而是多个高频入口在触发后一次性加载 20KB 到 35KB 内容。

当前正文中常见的可压缩内容：

- frontmatter 已写过的触发条件在正文再次完整出现；
- 快速开始、触发条件、边界表重复描述同一信息；
- yaml-summary schema 在多个 skill 中重复；
- 共享门控、Recovery、FUTURE 规则仍有局部复制；
- 大段输出模板和示例可放入 templates/references；
- checklist 同时出现在流程正文和末尾约束清单。

### 8.2 建议修复方案

优先处理高频且体积最大的 6 个入口，不做全仓机械拆分：

1. `ms-dev-workflow`；
2. `ms-pipeline`；
3. `ms-verify`；
4. `ms-system-design`；
5. `ms-requirements`；
6. `code-quality`。

目标结构：

```text
SKILL.md
  - 身份和边界
  - 核心决策树
  - 硬门控
  - 何时读取哪个 reference
  - 最小输出约定

references/
  - 详细算法
  - schema
  - rubric
  - 变体流程

templates/
  - 可直接生成或复制的产物模板
```

不建议：

- 仅为了减少行数而深层嵌套 references；
- 把必须先知道的安全门控移出 SKILL.md；
- 为单次使用内容创建新抽象；
- 合并边界已经清楚的独立 skill。

建议以真实触发任务做前后对比，而不是只看 LOC：

- 首次加载 token；
- 是否还会漏读必要 reference；
- 完成率；
- 误触发率；
- 规则遗漏率。

## 9. P2：internal/FUTURE skill 的发现面治理

`ms-iteration-policy` 当前具备这些特征：

- `user-invocable: false`；
- 声明为 internal；
- 由 `ms-pipeline realign --scope=layout` 调度；
- 对应 runtime 仍在 FUTURE 状态矩阵中；
- 自身 `SKILL.md` 约 330 行。

如果一个组件当前不能独立执行，而且只服务于另一个编排 skill，它作为默认可发现 skill 的收益有限，却会：

- 增加 metadata 上下文；
- 产生潜在误触发；
- 让用户看到声明了但不能真正执行的入口；
- 增加跨客户端 frontmatter 兼容负担。

建议评估：

1. 暂时迁为 `pipeline/references/` 内部规则；或
2. 在发行 manifest 中排除，仅允许 pipeline 按路径读取；或
3. 保留 skill，但必须保证所有目标客户端都能识别 `user-invocable: false` 且不会自动触发。

layout.v2、trace.v1 等 FUTURE references 不建议删除。它们是已审查的设计资产，并且 references 默认不进入上下文；重点是不要把未实现能力呈现成当前可调用 runtime。

## 10. P2：Codex UI metadata 与发布形态

当前 35 个 skill 都没有 `agents/openai.yaml`。当前 Codex `skill-creator` 将其视为推荐的 UI metadata，可用于：

- `display_name`；
- `short_description`；
- `default_prompt`；
- skill list/chip 的用户展示。

这不是 P0，因为当前 skill 已经能够通过 name/description 被发现。但在解决安装和路由一致性后，可以考虑：

- 由仓库 SSOT 生成 OpenAI/Codex metadata；
- 不手工维护第二份容易漂移的 description；
- 将平台特定文件作为生成产物或受验证的发布文件。

## 11. 新增 Markdown style skill 的处理建议

当前存在未跟踪设计稿：

```text
docs/superpowers/specs/2026-07-31-markdown-style-skill-design.md
```

从已阅读部分看，该设计强调：

- 它是 Markdown 审查策略，不是自动格式化器；
- 默认只报告；
- 保护语义承载标记；
- 明确 markdownlint、中文排版和 LLM 输出问题的边界；
- 对自动修复风险有较完整的反证记录。

这个方向本身有独立价值，但建议在以下前置完成后再作为第 36 个 skill 落地：

1. 安装命名和加载漂移修复；
2. 仓库 validator 建立；
3. frontmatter/平台 capability 策略明确；
4. 与 `code-quality`、`work-report`、`lark-markdown`、Obsidian Markdown 等近邻 skill 的触发边界完成测试。

否则新 skill 会继续扩大当前安装和路由问题。

## 12. 推荐实施顺序

### Phase A：恢复基础可信度

1. 修 README 安装路径；
2. 修部署脚本 runtime name；
3. 增加 `deploy --check`；
4. 设计旧短名目录迁移策略；
5. 在三个客户端抽查发现结果。

完成定义：仓库、安装目录、loaded catalog 可以解释为同一个版本集合。

### Phase B：建立自动验证

1. 实现最小 validator；
2. 添加针对已发现问题的回归 fixture；
3. 接入 CI；
4. 将 README 数量、链接、名称映射、行数纳入阻断；
5. tool/capability 检查先作为 warning，稳定后再决定是否阻断。

完成定义：本轮发现的 README 和命名问题不能再次进入主分支。

### Phase C：跨客户端执行协议

1. 定义 capability vocabulary；
2. 为 Claude、Codex、OpenCode 建适配矩阵；
3. 更新 shared constraints；
4. 更新依赖子代理和用户确认的核心入口；
5. 明确无能力时的 partial/failed recovery。

完成定义：核心流程不再把某个客户端工具名当成唯一事实。

### Phase D：工具型 skill 对齐

1. `idea-mcp-workflow`；
2. `ui-orchestrator`；
3. `ms-board`；
4. `e2e-test-flow`。

完成定义：每个 skill 都先检查当前能力，并且只引用存在的工具或明确适配路径。

### Phase E：路由和评测

1. 定义 process owner 规则；
2. 补根 AGENTS.md 的元开发路由；
3. 建 should/should-not-trigger prompt corpus；
4. 在 Claude/Codex/OpenCode 前向测试；
5. 记录误触发和双重门控案例。

完成定义：同一任务只存在一个生命周期 owner。

### Phase F：瘦身与新能力

1. 压缩 6 个高频大入口；
2. 处理 internal/FUTURE 发现面；
3. 评估 `agents/openai.yaml`；
4. 再决定 Markdown style skill 是否落地。

## 13. 不建议做的事情

- 不建议现在大规模合并 35 个 skill；现有领域边界总体清晰。
- 不建议为了满足某个客户端，直接删除所有扩展 frontmatter。
- 不建议部署脚本自动删除旧安装目录。
- 不建议把所有 FUTURE 设计资产删除；应治理发现面和执行声明。
- 不建议仅靠 NOT-for 文案解决路由冲突；需要实际 prompt eval。
- 不建议用正则一次性重写全部 SKILL.md frontmatter。
- 不建议在 capability 缺失时假装完成了子代理隔离、浏览器网络观测或 fresh-context review。
- 不建议在 P0/P1 未处理前继续扩大 skill 数量。

## 14. Claude 接手时建议重点复核的问题

1. Claude Code、Codex、OpenCode 分别以目录名还是 frontmatter name 作为安装和发现主键？
2. `npx skills add` 与本仓 `deploy-skills.sh` 是否采用不同命名规则？
3. Codex catalog 显示 skill、但 `r1` 对应文件缺失的具体原因是什么：缓存、插件快照、复制安装还是路径映射？
4. `allowed-tools`、`metadata`、`user-invocable` 在三个客户端中的实际支持矩阵是什么？
5. 能否保留一个平台中立源，再生成各客户端发布形态？
6. `ui-orchestrator` 在当前平台自动路由能力下是否仍有独立价值？
7. `ms-iteration-policy` 是否应继续作为可发现 skill？
8. superpowers 的强制 process skill 与本仓 owner 规则如何做到真正单一路径，而不是只在文档里声明？
9. validator 应使用何种零依赖实现，避免当前 PyYAML 缺失问题？
10. 哪些检查应立即阻断 CI，哪些应先以 warning 观察误报？

## 15. 建议的最小首批改动范围

如果 Claude 评估后决定实施，建议首批严格限定在：

```text
README.md
scripts/deploy-skills.sh
scripts/<new-validator>
tests/fixtures/ 或 scripts/fixtures/（仅在 validator 确实需要时）
AGENTS.md（只补命令/验证说明，不顺手重构）
```

首批不要同时修改 35 个 `SKILL.md`。先把安装和验证基础打牢，再用独立后续任务处理 capability adapter、路由和正文瘦身。

## 16. 可复现检查命令

以下命令均为只读，可帮助 Claude 复核本交接记录。

### 数量与行数

```bash
find skills -mindepth 2 -maxdepth 2 -name SKILL.md | wc -l
rg '^name: ms-' skills/*/SKILL.md | wc -l
rg '^name:' skills/*/SKILL.md | rg -v 'name: ms-' | wc -l
wc -l skills/*/SKILL.md | sort -n
```

### 目录名与 runtime name

```bash
find skills -mindepth 2 -maxdepth 2 -name SKILL.md -exec sh -c '
  d=${1%/SKILL.md}
  n=$(sed -n "s/^name:[[:space:]]*//p" "$1" | head -1)
  b=${d##*/}
  [ "$b" = "$n" ] || printf "%s -> %s\n" "$b" "$n"
' sh {} \;
```

### 仓库与安装目录比较

```bash
for f in skills/*/SKILL.md; do
  n=$(sed -n 's/^name:[[:space:]]*//p' "$f" | head -1)
  inst="/Users/mason/.agents/skills/$n/SKILL.md"
  if [ ! -f "$inst" ]; then
    printf 'MISSING %s repo=%s\n' "$n" "$f"
  elif cmp -s "$f" "$inst"; then
    printf 'SAME %s\n' "$n"
  else
    printf 'DIFF %s repo=%s installed=%s\n' "$n" "$f" "$inst"
  fi
done
```

### frontmatter 扩展字段统计

```bash
rg -n '^allowed-tools:' skills/*/SKILL.md | wc -l
rg -n '^metadata:' skills/*/SKILL.md | wc -l
rg -n '^user-invocable:' skills/*/SKILL.md | wc -l
```

### 工作区状态

```bash
git status --short
```

## 17. 最终判断

仓库当前不是“skill 划分失控”，而是已经从一组文档成长为跨客户端 skill 产品后，发布与运行治理没有同步升级。

最值得投入的方向依次是：

1. 安装和发现一致性；
2. 仓库级验证；
3. 平台 capability adapter；
4. 单一 process owner 路由；
5. 工具型 skill 的 runtime 对齐；
6. 上下文瘦身和新增能力。

先完成前三项，后续对任何单个 skill 的优化才会稳定地到达真实运行环境，并且能够被自动验证。
