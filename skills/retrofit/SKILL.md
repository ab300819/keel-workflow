---
name: ms-retrofit
description: Retrofit existing projects to DevDocs workflow, or migrate old DevDocs to new standards. For projects without docs, establish a project baseline recording what code cannot answer. Use when users want to adapt existing projects, take over legacy code, migrate documentation, standardize documents, or upgrade DevDocs version. Triggers on "retrofit", "改造", "适配", "迁移", "标准化", "基线", "摸底", "接手项目", "升级文档", "existing project", "已有项目". NOT for initializing new projects (use ms-pipeline), adding features to existing DevDocs (use ms-feature), or code inventory (use ms-codebase-insight).
allowed-tools: Read, Write, Glob, Grep, AskUserQuestion, Bash, Task
metadata:
  patterns: [inversion, generator]
  interaction: multi-turn
  handoff: yaml-summary-v1
---

# 项目改造

将已有工程改造为 DevDocs 流程，或将旧版 DevDocs 迁移到新规范。

## 语言规则

- 支持中英文提问
- 统一中文回复
- 使用中文生成文档

## 快速开始

**一句话**: 将已有项目适配 DevDocs 工作流，或将旧版 DevDocs 迁移到新规范。

**最常见用法**: `/ms-retrofit`（自动检测项目状态）

`/ms-retrofit --realign`   → 规范升级回扫：00-baseline.md 按当前 baseline.v1 查漏补缺（⛔ 只补结构，不改带来源标注的正文）。推荐用户入口 /ms-pipeline realign

**不适合?** 新项目→`/ms-pipeline init`，加功能→`/ms-feature`

## 触发条件

- 用户希望将现有项目适配 DevDocs 流程
- 用户需要标准化项目文档
- 用户要迁移或升级已有 DevDocs 文档
- 项目缺少文档，需要建立可维护的基线

## 与 realign 的边界

retrofit 与 realign（规范升级回扫）**互补不重叠**，**以 frontmatter + `spec_version` 字段为主判据**：文档顶部 YAML frontmatter 存在且含有效 `spec_version` → 信任元数据，归 **realign**（`/ms-pipeline realign`），无论正文是否缺 F-XXX 编号（编号补齐由 realign 内 additive 差距处理）；反之（无 frontmatter / 无 `spec_version` / 无 DevDocs）归 **retrofit**。详见 [../pipeline/references/realign.md](../pipeline/references/realign.md) § 与 ms-retrofit 的边界。

## 工作流程

```text
1. 扫描项目结构
   │
   ▼
2. 检测项目状态
   │
   ├── 无 docs/devdocs/ ──────────────────► 建立项目基线
   │
   ├── 有 00-baseline.md 且无 01~04 ────► 基线已建，终态，无需改造
   │
   ├── 有 DevDocs（符合规范）────────────► 无需改造
   │
   └── 有 DevDocs（旧版）────────────────► 版本迁移
   │
   ▼
3. 呈现方案 + AskUserQuestion 确认
   │
   ▼
4. 执行
   │
   ├── 建立基线：调查 → 校验 → 推导 → 提问 → 落盘 00-baseline.md
   └── 版本迁移：更新迁移文档 → 生成/更新 docs/devdocs/
   │
   ▼
5. 收尾
   │
   ├── 基线路径：不产报告（建立记录已在基线内）
   └── 版本迁移：生成 00-retrofit-report.md
```

---

## 方案确认规范

扫描项目结构和检测状态后，**展示改造策略并使用 AskUserQuestion 让用户选择执行分支**，确认后再生成/更新文档。

### 版本迁移场景

展示规范检查结果和迁移动作清单后，让用户选择：

> 检测到旧版 DevDocs，建议迁移策略：
> 1. **完整迁移**（推荐）- 自动完成所有文档迁移
> 2. **选择性迁移** - 选择要迁移的文档项（选择后需指定具体迁移范围）
> 3. **仅生成差异报告** - 不迁移文档，仅输出差异报告
> 请选择迁移方式。

**选择性迁移追加交互**：用户选择选项 2 后，展示差异清单并让用户勾选要迁移的文档/章节，确认范围后再执行。

### 建立基线场景

展示调查覆盖面和校验结果后，让用户选择：

> 调查与校验结果如下，请确认或调整：
> 1. **确认调查结果**，开始建立基线
> 2. **补充材料**（指定被漏掉的文档 / issue / 历史资料）后再调查
> 3. **调整基线范围**（哪些节先建、哪些标未知）

### 方案必须包含

**建立基线**：调查覆盖面（已挖的材料来源）→ 校验结果（已佐证 / 未可验 / 与代码矛盾 各几条）→ 待提问项清单 → 预估「未知」比例 → 风险与注意

**版本迁移**：规范检查结果 → 迁移动作清单（含影响范围和风险）→ 迁移方式（完整/选择性/仅报告）

### 约束
- **符合当前规范的项目**：直接告知用户无需改造并退出，不进入分支选择
- 用户选择前：只展示方案，不写入任何文件
- 用户选择后：按分支生成 `docs/devdocs/` 下的文档
- **选择性迁移**：必须在用户指定迁移范围后才能执行，不可猜测范围
- **基线草案**：落盘前必须展示带来源标注的草案供用户确认；用户未表态的条目保持 `推导待确认`，不得升格

## 项目状态检测

### 检测逻辑

```text
0. 带 --realign 标志？
   │
   ├── 是 → 直接进 realign 子流程（见 references/realign.md），跳过下方全部检测
   │        ⛔ 只补结构（缺失章节 / frontmatter 字段），不改带来源标注的正文
   │
   └── 否 → 继续
   │
   ▼
1. docs/devdocs/ 是否存在？
   │
   ├── 不存在 → 建立项目基线
   │
   └── 存在 → 有 00-baseline.md 且无 01~04？
       │
       ├── 是 → 基线已建（第三终态）→ 无需改造，提示下一步 /ms-feature
       │
       └── 否 → 规范符合性检查
           │
           ├── 符合当前规范 → 无需改造
           │
           └── 不符合 → 版本迁移流程
```

⛔ **「基线已建」是与「符合规范」并列的第三种终态，不是「旧版待迁移」。**

基线项目一项编号都没有，若直接进规范符合性检查，会被判成「缺少 F/US/AC 编号 ⚠️ 需迁移」，
于是版本迁移流程**试图把刚建好的基线项目迁回旧的编号形态**——用户第二次跑 `/ms-retrofit`
就会撞上这个死循环。判据必须在规范检查**之前**短路。

判据是**存在性**不是排他性：基线项目允许有 05-bugfix-log.md、00-context.md 等其他产物，它们不影响「基线已建」的判定。只看 01~04 在不在。

### 规范符合性检查清单

| 检查项 | 检查内容 | 规范要求 |
|--------|----------|----------|
| **编号体系** | F-XXX, US-XXX, AC-XXX | 必须 |
| **测试编号** | UT-XXX, IT-XXX, E2E-XXX | 必须 |
| **追溯矩阵** | F → US → AC → 测试 映射 | 必须 |
| **文件命名** | 01-requirements.md, 03-test-cases.md 等 | 必须 |
| **章节完整性** | 各文档必要章节 | 必须 |
| **Skill 协作** | 标注协作 Skill | 建议 |

---

## 版本迁移流程（已有 DevDocs 但不符合规范）

当检测到已有 DevDocs 文档但不符合当前规范时执行。完整 Step M1-M4 详细规范（规范检查报告 / 差异清单格式 / 用户确认话术 / 编号迁移示例 / 文件重命名 / 追溯矩阵生成）见 [references/version-migration.md](references/version-migration.md)。

要点：
- M1 规范检查：生成"检测结果"表（文件 / 状态 / 问题）
- M2 生成差异清单：编号体系 + 文件结构 + 追溯矩阵 + 章节补充
- M3 用户确认：AskUserQuestion 三选项（完整迁移 / 选择性 / 仅报告）
- M4 迁移执行：编号 + 重命名（git mv 保留历史）+ 追溯矩阵

---

## 建立项目基线（无 DevDocs）

当项目没有 DevDocs 文档时执行。完整流程（调查范围 / 校验规则 / 来源标注 / 提问纪律 / 落盘）见 [references/new-project-retrofit.md](references/new-project-retrofit.md)，产物形状见 [templates/baseline-template.md](templates/baseline-template.md)。

**基线只记录重扫代码无法重建的信息。** 模块 / 接口 / 数据对象 / 技术栈归 `docs/codebase-insight.md`；当前进度 / 待办归 `docs/devdocs/00-context.md`。

要点：

- Step 1 调查：委托 `ms-codebase-insight` 摸排 + README / CHANGELOG / git 提交信息 / issue·PR / 实跑构建测试
- Step 2 校验：拿代码检验文档里每条可验证陈述 → `已佐证` / `未可验` / `与代码矛盾`
- Step 3 推导：起草带依据标注的草案，每条写清「据什么」
- Step 4 提问：只问推不出、依据薄弱、或校验出矛盾的项；⛔ 每题必须有「我也不清楚」出口
- Step 5 落盘：`docs/devdocs/00-baseline.md`，不产 `01`~`04`

**存量代码不编号。** `01-requirements.md` 由首次 `/ms-feature` 创建，`F-001` 从新需求起。
改造完成到首个需求之间，`/ms-board`、`/ms-test-cases`、`/ms-verify` 会拒绝运行——**这是正确行为**，还没有需求，当然不能评审需求。

---

## 改造报告

**仅版本迁移路径生成** `00-retrofit-report.md`，包含迁移动作清单（改了哪些编号、重命名了哪些文件）。详细模板参见 [templates/retrofit-report-template.md](templates/retrofit-report-template.md)。

**基线路径不产报告**：原报告的「编号分配」表整张作废（不再产编号）、「文档状态」表塌成一行（只产一份基线），剩下的「待完善项」与「下一步建议」已并入基线的「建立记录」节——它跟着基线走，下次读基线的人才看得到这份基线的局限。

**关键规则**：基线不是终点。有新需求 → `/ms-feature`；补充项目背景或把 `推导待确认` 升为 `用户确认` → `/ms-requirements --context`（写入 `00-baseline.md`）。

**工作区拓扑（`retrofit` 路径）**：改造成功、`docs/devdocs/` 生成后，执行 `Task: /workspace-topology reconcile`。该 skill 自己写 `AGENTS.md` 的 `workspace:` 块，无声明时问一次 mode 与代码根并落声明。见 [../workspace-topology/SKILL.md](../workspace-topology/SKILL.md)。

**记忆同步(成功路径必做)**:改造成功、`docs/devdocs/` 生成后,执行 `Task: /agent-memory --update` 同步 AGENTS.md(DevDocs 项目会包含工作流路由节)。写 AGENTS.md 走 agent-memory 的窄例外(见下方约束「Write 工具仅用于写入 docs/devdocs/」),本 Skill 不直接 Write 该文件。失败语义:ℹ️ 不阻塞改造交付,blockers 记入报告。

---

## Skill 协作

| 场景 | 协作 Skill | 说明 |
|------|-----------|------|
| 代码盘点 | `/ms-codebase-insight` | 建立基线 Step 1 委托，产出清单层供提问出候选 |
| 基线增量补全 | `/ms-requirements --context` | 把 `未知` / `推导待确认` 升为 `用户确认` |
| 需求审查 | `/ms-requirements` | 审查需求文档（基线项目须先有 `01`，由首次 `/ms-feature` 创建） |
| 设计审查 | `/ms-system-design` | 审查系统设计（同上，须先有需求文档） |
| 测试用例 | `/ms-test-cases` | 完善测试用例设计（同上，须先有需求文档） |
| 新增功能 | `/ms-feature` | 改造后添加新功能 |
| Bug 修复 | `/ms-bugfix` | 改造后修复问题 |
| 测试质量 | `/testing-guide` | 检查测试有效性 |
| 文件操作 | `/git-safety` | 重命名文件时使用 git mv |

---

## 约束

### 阶段边界约束（最高优先级）
- [ ] **⛔ 禁止继续：文档阶段不得产出实现代码**（恢复方式：使用 /ms-dev-workflow 执行编码）
- [ ] Write 工具仅用于写入 `docs/devdocs/` 下的 Markdown 文档;窄例外:改造成功后委托 `agent-memory` 写其受管记忆文件(`AGENTS.md`/`CLAUDE.md` 导入行/`.claude/rules/devdocs-state.md`),其余业务文件仍禁止

### 方案确认约束

- [ ] **扫描项目 + 检测状态后，必须展示方案并等待用户选择执行分支**
- [ ] **方案必须包含改造策略和调查覆盖面与预估未知比例（建立基线）或迁移动作清单（版本迁移）**

### 检测约束

- [ ] **必须先检测项目状态（无 DevDocs / 基线已建 / 旧版 / 符合规范）**
- [ ] 必须扫描常见文档目录

### 迁移约束

- [ ] **迁移前必须生成差异清单**
- [ ] **迁移前必须用户确认**
- [ ] 文件重命名必须使用 `git mv`
- [ ] 不得删除原有文档的有效内容

### 基线内容约束

- [ ] **⛔ `00-baseline.md` 不得出现模块表 / 接口表 / 数据对象表 / 依赖图 / 技术栈清单 / 目录结构树**（→ `codebase-insight.md`）
- [ ] **⛔ 不得出现当前分支 / 未提交改动 / 完成率 / 待办**（→ `00-context.md`）
- [ ] **⛔ 不得从实现细节推导出「必须保持此行为」**——最大的危害不是过时，是把实现偶然性写成设计意图
- [ ] **⛔ 不得出现没有来源标注的断言**；推不出就标 `未知`
- [ ] **⛔ `推导待确认` 不得因用户沉默而升格为 `用户确认`**
- [ ] **⛔ 每次提问必须提供「我也不清楚」出口**，且选它不算失败——不给出口，用户被迫瞎选产生的假信息比标 `未知` 更糟
- [ ] 护栏节三要素（决定 / 约束哪些改动 / 依据）**缺一不写**
- [ ] 「已知未知」每条必须写出「确认前的安全默认动作」

### 输出约束

- [ ] 基线路径只产 `00-baseline.md`，不产 `01`~`04`

---

## 错误处理

详见 [references/error-handling.md](references/error-handling.md)（调查材料不足、项目无任何文档、迁移冲突）

---

## 子 Agent 摘要格式

当本 Skill 作为子 Agent 运行时，返回以下结构化摘要：

```yaml
skill: ms-retrofit
status: success | failed | partial
summary:
  headline: "项目基线已建立，5 项未知待补"
  details:
    path: baseline | version-migration
    baseline_established: true
    adoption_commit: "a1b2c3d"
    counts:
      用户确认: X
      已有文档: X
      推导待确认: X
      未知: X
    evidence_conflicts: X
    build: "pass | fail | none"
    tests: "pass | fail | none"
blockers: []
output_files:
  - docs/devdocs/00-baseline.md
new_ids: {}
next_recommended:
  skill: ms-feature
  args: ""
```

## 输出文件

**基线路径**：

```text
docs/devdocs/
└── 00-baseline.md          # 项目基线（唯一产物）
```

附带（由委托的 skill 各自产出，不由本 skill 写）：`docs/codebase-insight.md`（`ms-codebase-insight`）、`AGENTS.md` 的领域术语与架构决策节（`agent-memory`）。

**版本迁移路径**：

```text
docs/devdocs/
├── 00-retrofit-report.md    # 迁移报告
└── <按迁移范围更新的既有 01~04 文档>
```
