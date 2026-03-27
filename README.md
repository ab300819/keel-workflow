# AI Agent Skills

面向**个人开发者**的 AI Agent Skills 模板项目。

包含 19 个 ms- 流程 skill（覆盖 PRD → 需求 → 设计 → 测试 → 开发 → 验证全链路）和 9 个独立工具 skill。

兼容 **Claude Code**、**Codex CLI**、**OpenCode** 等遵循 [Agent Skills](https://agentskills.io) 开放标准的 AI 编码工具。

## 安装

### Claude Plugin Marketplace（推荐）

```
/plugin marketplace add ab300819/skills
```

### npx（跨工具通用）

```bash
npx skills add ab300819/skills --list      # 列出所有 skill
npx skills add ab300819/skills@code-quality # 安装单个
```

### 本地部署

```bash
git clone https://github.com/ab300819/skills.git
bash skills/scripts/deploy-skills.sh
```

---

## 快速开始

**不确定用哪个？** 运行 `/ms-pipeline`，2-3 个问题自动路由到合适的流程。

### 常见场景速查

| 你的情况 | 命令 |
|----------|------|
| 有个模糊想法，想探索需求 | `/ms-prd` |
| 有明确需求，全新项目 | `/ms-pipeline init` |
| 已有项目，加新功能 | `/ms-pipeline feature` |
| 修 Bug | `/ms-pipeline bugfix` |
| 写完代码，文档没跟上 | `/ms-sync --absorb` |
| 接手项目，快速了解 | `/ms-onboard --read` |
| 已有项目，想规范化 | `/ms-retrofit` |
| 检查质量 | `/ms-verify` |
| 周期收尾 | `/ms-pipeline close` |

---

## 两大工作流

### PRD 流程（需求发现）

适用于**模糊想法**或**已有 PRD 文档**，独立于 DevDocs，通过 `--from-prd` 桥接。

```
你的想法 / PRD 文档
    │
    ▼
/ms-prd（自动检测：短想法 → 头脑风暴，大文档 → 结构化解析）
    │
    ├── /ms-prd-brainstorm（发散探索，5W1H → MoSCoW 收敛）
    │   └── 产出 FR-XX / NFR-XX 需求文件
    │
    └── /ms-prd-parser（文档分片 + 指纹追踪）
        └── 逐块调用 brainstorm 澄清
    │
    ▼
成熟度评估（idea → draft → ready）
    │
    ▼
ready 后：/ms-requirements --from-prd（进入 DevDocs）
```

### DevDocs 流程（文档驱动开发）

适用于**需求明确**的项目，从需求到代码的完整流程。

```
/ms-requirements        需求编码（F/US/AC）
    │
    ▼
/ms-system-design       技术架构设计
    │
    ▼
/ms-test-cases          测试用例设计（UT/IT/E2E）
    │
    ▼
/ms-dev-tasks           任务拆分（T-XX，≤4h/任务）
    │
    ▼
/ms-verify --readiness  就绪检查（⛔ P1 阻塞则修复）
    │
    ▼
/ms-dev-workflow        开发执行（骨架优先 + 分层 TDD）
    │                   批量模式含 /ms-test-run --trace
    ▼
/ms-verify --impl       实现验证
    │
    ▼
/ms-sync                文档同步（trace + audit）
    │
    ▼
/ms-compound            知识沉淀（提取经验模式）
```

---

## 全部 Skill

### 编排层（用户主入口）

| Skill | 命令 | 用途 |
|-------|------|------|
| 工作流编排器 | `/ms-pipeline` | 顶层入口，6 个模式（init/feature/bugfix/verify/close/insights） |
| 产品需求编排 | `/ms-prd` | 模糊想法/大型 PRD → 结构化需求 |
| 新功能 | `/ms-feature` | 已有项目追加新功能（含 lite/full 模式） |
| Bug 修复 | `/ms-bugfix` | 测试先行的 Bug 修复 |

### PRD 流程 Skill

| Skill | 命令 | 用途 |
|-------|------|------|
| 需求探索 | `/ms-prd-brainstorm` | 5W1H → 用户旅程 → MoSCoW 收敛 |
| 文档解析 | `/ms-prd-parser` | 大型 PDF/md/截图 → 结构化分片 |

### DevDocs 流程 Skill

| Skill | 命令 | 用途 | 输出 |
|-------|------|------|------|
| 需求编码 | `/ms-requirements` | 功能点/用户故事/验收标准 | `01-requirements.md` |
| 系统设计 | `/ms-system-design` | 技术架构、API、数据模型 | `02-system-design*.md` |
| 测试设计 | `/ms-test-cases` | UT/IT/E2E/Journey 测试用例 | `03-test-*.md` |
| 任务拆分 | `/ms-dev-tasks` | 可执行的开发任务 | `04-dev-tasks*.md` |
| 开发执行 | `/ms-dev-workflow` | 骨架优先 + 分层 TDD + 双 Agent 隔离 | 代码 |
| 测试执行 | `/ms-test-run` | 运行测试 + 追溯验证 | `05-test-report.md` |
| 统一验证 | `/ms-verify` | --docs / --impl / --ui / --readiness | 验证报告 |
| 文档同步 | `/ms-sync` | trace + audit + archive | 更新追溯矩阵 |
| 洞察收集 | `/ms-insights` | 审查/调研结果 → 需求 | `05-insights.md` |
| 知识沉淀 | `/ms-compound` | 提取经验模式 | `patterns/*.md` |
| 项目上下文 | `/ms-onboard` | AI 工具切换时的上下文传递 | `00-context.md` |
| 项目改造 | `/ms-retrofit` | 已有项目适配 DevDocs | 逆向生成文档 |
| 代码盘点 | `/ms-codebase-insight` | 只读分析现有代码库 | `codebase-insight.md` |

### 独立工具 Skill

| Skill | 命令 | 用途 |
|-------|------|------|
| 代码质量 | `/code-quality` | MTE 原则、重构指导、Review 清单 |
| 测试指导 | `/testing-guide` | 断言质量、Mock 规范、变异测试 |
| 重构 | `/refactor` | 系统化重构，测试驱动 |
| 提交规范 | `/commit-convention` | 提交信息格式化 |
| Git 安全 | `/git-safety` | 强制 git mv/rm 规范操作 |
| UI 调度器 | `/ui-orchestrator` | 路由到专业 UI/UX skill |
| 工作报告 | `/work-report` | 周报/月报/季报/年终总结 |
| 代码自描述 | `/code-self-describe` | 模块级 CLAUDE.md + 文件头注释 |
| 记忆管理 | `/agent-memory` | AI agent 记忆文件管理 |

---

## 开发路径选择

| 场景 | 路径 | 说明 |
|------|------|------|
| 需求明确 | `/ms-pipeline init` | requirements → design → tests → tasks → dev |
| 有模糊想法 | `/ms-prd` → `/ms-pipeline init` | 先探索需求，再走标准流程 |
| 已有项目加功能 | `/ms-pipeline feature` | 增量更新全套文档 |
| 已有代码无文档 | `/ms-retrofit` | 从代码逆向生成 DevDocs |
| 探索性原型 | 先写代码 → `/ms-retrofit` | 代码稳定后补文档 |
| Bug 修复 | `/ms-pipeline bugfix` | 写失败测试 → 修复 → 通过 |
| 小改动 | 直接提交 | 遵循 `/commit-convention` |

---

## 编号体系

DevDocs 使用统一编号实现需求到代码的全链路追溯：

```
F-001 (功能点)
  └── US-001 (用户故事)
        └── AC-001 (验收标准)
              ├── UT-001 → @verifies AC-001（代码标注）
              ├── IT-001
              └── E2E-001
                    └── T-01 (开发任务) → @satisfies AC-001（代码标注）
```

| 前缀 | 含义 | 来源 |
|------|------|------|
| FR-XX / NFR-XX | PRD 阶段需求 | `/ms-prd` |
| F-XXX | 功能点 | `/ms-requirements` |
| US-XXX | 用户故事 | `/ms-requirements` |
| AC-XXX | 验收标准 | `/ms-requirements` |
| UT/IT/E2E/Journey | 测试用例 | `/ms-test-cases` |
| T-XX | 开发任务 | `/ms-dev-tasks` |
| INS-XXX | 洞察建议 | `/ms-insights` |
| BUG-XXX | Bug 记录 | `/ms-bugfix` |

---

## 文件结构

```
docs/
├── prd/                          # PRD 流程产出
│   ├── requirements/index.md     # 需求总纲
│   ├── requirements/FR-XX-*.md   # 各功能需求
│   └── chunks/                   # PRD 原文分片
│
├── devdocs/                      # DevDocs 流程产出
│   ├── 00-context.md             # 项目上下文（/ms-onboard）
│   ├── 01-requirements.md        # 需求文档
│   ├── 02-system-design*.md      # 系统设计
│   ├── 03-test-*.md              # 测试用例
│   ├── 04-dev-tasks*.md          # 开发任务
│   ├── 05-test-report.md         # 测试报告
│   ├── 05-insights.md            # 洞察日志
│   ├── 05-bugfix-log.md          # Bug 修复日志
│   └── patterns/                 # 经验模式库（/ms-compound）
│
└── codebase-insight.md           # 代码盘点（/ms-codebase-insight）
```

---

## 大型需求最佳实践

基于 [Harness Design for Long-Running Apps](https://www.anthropic.com/engineering/harness-design-long-running-apps) 的 Generator-Evaluator 分离、Sprint Contract、最小可行 Harness 等设计模式，结合 ms- 流程的推荐使用方式：

### 1. 需求阶段拉长，开发阶段提速

用 `/ms-prd` 充分探索需求（对应文章的 Planner Agent 角色），需求清晰后一次性走完 requirements → system-design → test-cases → dev-tasks，开发用 `--headless` 或 `--auto-commit` 批量执行。

### 2. 善用 --readiness 门控

不要跳过 `/ms-verify --readiness`，它相当于文章中的 Sprint Contract 验证——在编码前确认交付规格可测试、依赖无环、路径具体。P1 问题一定修复后再开工，返工成本远大于修复成本。

### 3. 批量执行 + 断点续做

大需求拆成 10-20 个任务后，按依赖顺序用 `F-001` 或范围（`T-01~T-10`）批量执行。中断后直接续做，检查点机制会精确恢复到中断的 Agent 和步骤。每完成一个 Feature 的所有任务后运行 `/ms-sync` + `/ms-verify --impl`。

### 4. 迭代而非一步到位

文章核心经验：**多轮 QA 比一次完美实现更有效**。第一轮 dev-workflow 完成后，运行 `/ms-verify --impl` 找差距，将差距转为 bugfix 或 insight 再次进入开发循环，最后运行 `/ms-compound` 沉淀经验。

### 5. 对抗式验证不要跳过

`--review` 对抗验证对应文章中的独立 Evaluator——外部视角发现自己看不到的问题。文章指出 LLM 对自身输出有正面偏见，分离评估是最有效的质量保障手段。

---

## 语言规则

- 支持中英文提问
- 统一中文回复
- 使用中文生成文档

## 详细文档

每个 skill 的完整规范见 `skills/<dir>/SKILL.md`。架构决策和约定见 `AGENTS.md`。
