# keel

**keel（龙骨）**——贯穿全船的主承重结构。一套 DevDocs 文档驱动开发流程（需求 → 设计 → 测试 → 开发 → 验证）
加配套的质量 / 测试 / 重构 skill，以**插件**形式分发。

兼容 **Claude Code**、**Codex CLI**、**OpenCode**（遵循 [Agent Skills](https://agentskills.io) 开放标准）。

> 共 33 个 skill：21 个 DevDocs 流程 skill（由 `/pipeline` 编排）+ 12 个被流程依赖的通用 skill。
> 与本仓无依赖的零散独立 skill 在另一个仓（`skills-local`），两者互不阻塞。

---

## 安装

**Claude Code**

```
/plugin marketplace add ab300819/keel
/plugin install keel@ab300819-keel
```

**Codex CLI** —— 在 `~/.agents/plugins/marketplace.json` 注册，插件目录放 `~/.agents/plugins/keel/`：

```bash
git clone git@github.com:ab300819/keel.git ~/.agents/plugins/keel
```

**OpenCode** —— 直接扫描 skill 目录，软链进去即可：

```bash
ln -s <keel 仓路径>/skills/<name> ~/.config/opencode/skills/<name>
```

### 调用形式按端不同

| 端 | 形式 | 说明 |
|---|---|---|
| Claude Code | `/keel:pipeline` | 插件命名空间；裸名 `/pipeline` 同样可解析 |
| Codex CLI | `/keel:pipeline` | 同上 |
| OpenCode | `/pipeline` | **该端无命名空间**，只能裸名 |

> 本文其余部分一律用**裸名**书写（三端通用）。Claude Code / Codex 上想显式标归属时加 `keel:` 前缀。
>
> ⚠️ `hooks/` 只在插件安装路径下生效；OpenCode 走 `plugins/*.js`。

---


## 我该用哪个？

**拿不准就运行 `/pipeline`**，它问 2-3 个问题自动路由。或按下表自己选：

| 你的情况 | 用这个 |
|----------|--------|
| **想让文档和代码分仓（维护开源项目 / 项目待公开）** | `/workspace-topology` |
| 模糊想法，想先探索需求 | `/prd` |
| 明确需求，全新项目，走完整文档流程 | `/pipeline init` |
| 已有 DevDocs 项目，加新功能 | `/pipeline feature` |
| 修 Bug | `/pipeline bugfix` |
| **没有 DevDocs 文档，只想按计划/任务直接开发** | `/dev-flow` |
| 接手项目，快速了解 | `/onboard --read` |
| 已有代码无文档，想规范化 | `/retrofit` |
| 写完代码，文档没跟上 | `/sync` |
| 检查质量 / 周期收尾 | `/verify` / `/pipeline close` |

> **两条开发主线**：重型 `DevDocs`（文档驱动，编号追溯，适合大需求）走 `/pipeline`；轻量 `/dev-flow`（计划/任务直接驱动，三道质量门控）适合小项目或无文档场景。各流程的逐步走查见 **[docs/workflows.md](docs/workflows.md)**。

---

## 4 个上手例子

**例 1 — 全新项目，需求已明确**
```
/pipeline init        # 引导走 requirements → design → test-cases → dev-tasks
/dev-workflow --all   # 按依赖批量开发，骨架优先 + 分层 TDD
```

**例 2 — 没有文档，直接做个小功能**
```
/dev-flow                # 给它任务描述或计划文档，自动走 契约 → 红绿 → 验证
```

**例 3 — 接手别人的项目**
```
/onboard --read       # 只读生成项目上下文摘要
/retrofit             # 需要规范化时，建立项目基线（00-baseline.md）
```

**例 4 — 代码写完了，文档没跟上**
```
/sync                 # trace 回填 + 漂移审计 + 归档
/verify --docs        # 文档与实现一致性检查
```

---

## 全部 Skill

### 主入口（用户直接调用）

| Skill | 命令 | 用途 |
|-------|------|------|
| 工作流编排器 | `/pipeline` | 顶层入口，8 个模式（init/feature/bugfix/verify/close/insights/design/realign） |
| 通用开发流程 | `/dev-flow` | 非 DevDocs 开发执行器：契约先行 + 红绿 + 质量地板 + fresh-context 审查 |
| 产品需求编排 | `/prd` | 模糊想法/大型 PRD → 结构化需求 |
| 项目上下文 | `/onboard` | 接手项目 / AI 工具切换时的上下文传递 |

### DevDocs 流程 Skill（多数由 `/pipeline` 自动调度）

| Skill | 命令 | 用途 |
|-------|------|------|
| 需求编码 | `/requirements` | 功能点/用户故事/验收标准 → `01-requirements.md` |
| 系统设计 | `/system-design` | 技术架构、API、数据模型 → `02-system-design*.md` |
| 测试设计 | `/test-cases` | UT/IT/E2E/Journey 用例 → `03-test-*.md` |
| 任务拆分 | `/dev-tasks` | 可执行开发任务 → `04-dev-tasks*.md` |
| 开发执行 | `/dev-workflow` | 骨架优先 + 分层 TDD + 双 Agent 隔离 → 代码 |
| 测试执行 | `/test-run` | 运行测试 + 追溯验证 → `05-test-report.md` |
| 统一验证 | `/verify` | --docs / --impl / --ui / --readiness |
| 可视化评审 | `/board` | 01/02 → 交互评审页面（浏览器桥双向），意见回流为文档修订 |
| 文档同步 | `/sync` | trace + audit + archive |
| 新功能 / Bug | `/feature` / `/bugfix` | 增量功能 / 测试先行修复 |
| 洞察 / 沉淀 / 暂缓 | `/insights` / `/compound` / `/backlog` | 改进项 / 经验模式 / 暂缓池 |
| 改造 / 盘点 | `/retrofit` / `/codebase-insight` | 适配 DevDocs / 只读代码分析 |
| PRD 子流程 | `/prd-brainstorm` / `/prd-parser` | 需求探索 / 大文档解析 |

### 独立工具 Skill

| Skill | 命令 | 用途 |
|-------|------|------|
| 代码质量 | `/code-quality` | MTE 原则、核心阈值表、命名/注释规范、Review 清单 |
| 测试指导 | `/testing-guide` | 断言质量、Mock、覆盖率/变异得分阈值 |
| 重构 | `/refactor` | 系统化重构，测试驱动 |
| 对抗审查 | `/adversarial-review` | 外部 LLM 独立审查计划/设计/代码 |
| 仓库拓扑 | `/workspace-topology` | 声明代码与文档同仓（inline）、代码作子模块（shell），还是代码根在本仓之外只持有引用（linked）；幂等可重入，含单仓→外壳布局的双模式迁移 |
| 文档信息组织 | `/doc-organization` | 五条指导原则：当前状态与变更历史分离、编号先定义、引言职责、结论单一出处、写给缺上下文的读者 |
| UI 调度 / 自描述 / 记忆 | `/ui-orchestrator` / `/code-self-describe` / `/agent-memory` | 专项工具 |

> `commit-convention`、`git-safety` 由其他 skill 自动调用，不需用户直接运行。

---

## 语言规则

支持中英文提问；统一中文回复；文档用中文生成。

## 详细文档

- **[docs/workflows.md](docs/workflows.md)** — 各流程逐步走查 + 大型需求最佳实践
- **[docs/architecture.md](docs/architecture.md)** — 治理体系、编号规则（F/US/AC/UT/IT/T/INS/BUG）、文件结构（维护者参考）
- 每个 skill 的完整规范见 `skills/<dir>/SKILL.md`；跨 skill 共享约束见 [skills/shared/constraints.md](skills/shared/constraints.md)；架构决策与约定见 [AGENTS.md](AGENTS.md)
