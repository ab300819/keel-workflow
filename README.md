# AI Agent Skills

面向**个人开发者**的 AI Agent Skills 模板项目——一套给 AI 编码工具用的可复用指令集。

兼容 **Claude Code**、**Codex CLI**、**OpenCode** 等遵循 [Agent Skills](https://agentskills.io) 开放标准的工具。

> 共 37 个 skill，分两类：`ms-` 前缀 = DevDocs 文档驱动流程（需求→设计→测试→开发→验证全链路）；非 `ms-` = 独立工具（代码质量、测试、通用开发流程等）。

---

## 安装

```bash
# Claude Plugin Marketplace（推荐）
/plugin marketplace add ab300819/skills

# npx（跨工具通用）
npx skills add ab300819/skills --list          # 列出所有 skill
npx skills add ab300819/skills@code-quality     # 安装单个

# 本地部署
git clone https://github.com/ab300819/skills.git && bash skills/scripts/deploy-skills.sh
```

---

## 我该用哪个？

**拿不准就运行 `/ms-pipeline`**，它问 2-3 个问题自动路由。或按下表自己选：

| 你的情况 | 用这个 |
|----------|--------|
| **新项目开工前，想知道别人做过没有** | `/prior-art-scan` |
| 模糊想法，想先探索需求 | `/ms-prd` |
| 明确需求，全新项目，走完整文档流程 | `/ms-pipeline init` |
| 已有 DevDocs 项目，加新功能 | `/ms-pipeline feature` |
| 修 Bug | `/ms-pipeline bugfix` |
| **没有 DevDocs 文档，只想按计划/任务直接开发** | `/dev-flow` |
| 接手项目，快速了解 | `/ms-onboard --read` |
| 已有代码无文档，想规范化 | `/ms-retrofit` |
| 写完代码，文档没跟上 | `/ms-sync` |
| 检查质量 / 周期收尾 | `/ms-verify` / `/ms-pipeline close` |

> **两条开发主线**：重型 `DevDocs`（文档驱动，编号追溯，适合大需求）走 `/ms-pipeline`；轻量 `/dev-flow`（计划/任务直接驱动，三道质量门控）适合小项目或无文档场景。各流程的逐步走查见 **[docs/workflows.md](docs/workflows.md)**。

---

## 4 个上手例子

**例 1 — 全新项目，需求已明确**
```
/ms-pipeline init        # 引导走 requirements → design → test-cases → dev-tasks
/ms-dev-workflow --all   # 按依赖批量开发，骨架优先 + 分层 TDD
```

**例 2 — 没有文档，直接做个小功能**
```
/dev-flow                # 给它任务描述或计划文档，自动走 契约 → 红绿 → 验证
```

**例 3 — 接手别人的项目**
```
/ms-onboard --read       # 只读生成项目上下文摘要
/ms-retrofit             # 需要规范化时，从代码逆向生成 DevDocs
```

**例 4 — 已有用例文档，要对运行中系统跑一遍黑盒实测**
```
/e2e-test-flow           # 给它用例文档，自动走 分类 → 变更影响排序 → 接口实测 → UI 实测 → 面板报告
```

---

## 全部 Skill

### 主入口（用户直接调用）

| Skill | 命令 | 用途 |
|-------|------|------|
| 工作流编排器 | `/ms-pipeline` | 顶层入口，8 个模式（init/feature/bugfix/verify/close/insights/design/realign） |
| 通用开发流程 | `/dev-flow` | 非 DevDocs 开发执行器：契约先行 + 红绿 + 质量地板 + fresh-context 审查 |
| 产品需求编排 | `/ms-prd` | 模糊想法/大型 PRD → 结构化需求 |
| 项目上下文 | `/ms-onboard` | 接手项目 / AI 工具切换时的上下文传递 |

### DevDocs 流程 Skill（多数由 `/ms-pipeline` 自动调度）

| Skill | 命令 | 用途 |
|-------|------|------|
| 需求编码 | `/ms-requirements` | 功能点/用户故事/验收标准 → `01-requirements.md` |
| 系统设计 | `/ms-system-design` | 技术架构、API、数据模型 → `02-system-design*.md` |
| 测试设计 | `/ms-test-cases` | UT/IT/E2E/Journey 用例 → `03-test-*.md` |
| 任务拆分 | `/ms-dev-tasks` | 可执行开发任务 → `04-dev-tasks*.md` |
| 开发执行 | `/ms-dev-workflow` | 骨架优先 + 分层 TDD + 双 Agent 隔离 → 代码 |
| 测试执行 | `/ms-test-run` | 运行测试 + 追溯验证 → `05-test-report.md` |
| 统一验证 | `/ms-verify` | --docs / --impl / --ui / --readiness |
| 可视化评审 | `/ms-board` | 01/02 → 交互评审页面（浏览器桥双向），意见回流为文档修订 |
| 文档同步 | `/ms-sync` | trace + audit + archive |
| 新功能 / Bug | `/ms-feature` / `/ms-bugfix` | 增量功能 / 测试先行修复 |
| 洞察 / 沉淀 / 暂缓 | `/ms-insights` / `/ms-compound` / `/ms-backlog` | 改进项 / 经验模式 / 暂缓池 |
| 改造 / 盘点 | `/ms-retrofit` / `/ms-codebase-insight` | 适配 DevDocs / 只读代码分析 |
| PRD 子流程 | `/ms-prd-brainstorm` / `/ms-prd-parser` | 需求探索 / 大文档解析 |

### 独立工具 Skill

| Skill | 命令 | 用途 |
|-------|------|------|
| 代码质量 | `/code-quality` | MTE 原则、核心阈值表、命名/注释规范、Review 清单 |
| 测试指导 | `/testing-guide` | 断言质量、Mock、覆盖率/变异得分阈值 |
| 重构 | `/refactor` | 系统化重构，测试驱动 |
| 对抗审查 | `/adversarial-review` | 外部 LLM 独立审查计划/设计/代码 |
| JetBrains MCP 操作 | `/idea-mcp-workflow` | 通过 `idea` MCP 编译/调试/查库的决策与踩坑（projectPath 纪律、build 输出防爆、依赖 vs bug、Maven reload 提示） |
| E2E 实测 | `/e2e-test-flow` | 已有用例文档 → 对运行中系统黑盒实测（接口+UI，只读观测 DB），产出 HTML 评审面板 |
| Markdown 规范 | `/markdown-style` | 标记与排版审查（markdownlint + GB/T 15834 中文排版 + LLM 排版毛病），只报告不改语意 |
| Python 工具链 | `/python-spec` | 本机 mise+uv 规范：项目 / 脚本 / 临时使用 + 三道护栏诊断（已有 repo 沿用其工具链） |
| 文档信息组织 | `/doc-organization` | 五条指导原则：当前状态与变更历史分离、编号先定义、引言职责、结论单一出处、写给缺上下文的读者 |
| 先例扫描 | `/prior-art-scan` | 开工前查 GitHub 同类项目 → 维护度评估 → 缺口分类 → 六路径决策（只读，产出单文件 md）|
| UI 调度 / 自描述 / 记忆 / 报告 | `/ui-orchestrator` / `/code-self-describe` / `/agent-memory` / `/work-report` | 专项工具 |

> `commit-convention`、`git-safety`、`iteration-policy` 由其他 skill 自动调用，不需用户直接运行。

---

## 语言规则

支持中英文提问；统一中文回复；文档用中文生成。

## 详细文档

- **[docs/workflows.md](docs/workflows.md)** — 各流程逐步走查 + 大型需求最佳实践
- **[docs/architecture.md](docs/architecture.md)** — 治理体系、编号规则（F/US/AC/UT/IT/T/INS/BUG）、文件结构（维护者参考）
- 每个 skill 的完整规范见 `skills/<dir>/SKILL.md`；架构决策与约定见 [AGENTS.md](AGENTS.md)
