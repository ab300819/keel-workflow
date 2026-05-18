# Skill Layout Compatibility Matrix

> 全部 skill 与 docs_layout_version / id_scheme / traceability_version 三层版本号的兼容关系总表。
>
> 本文件是 [layout-versioning-policy.md](layout-versioning-policy.md) skill 兼容性声明的实例化。各 skill SKILL.md 的 frontmatter 必须与本表一致。
>
> ⚠️ **执行接口当前状态**：本文件提及的 `/ms-verify --layout-drift` 等命令落地状态见 [docs-layout-migration.md § 执行接口落地状态（FUTURE）](docs-layout-migration.md#-执行接口落地状态future)。

## 兼容性矩阵

### ⚠️ Transitional State（v2 接口 [FUTURE] 落地前的过渡策略）

**当前所有 A/B skill 的 `writes_*` 字段声明为 v1**，反映 SKILL.md 正文的实际行为（v1 输出 `01-requirements.md` / `F-XXX` / 代码注释追溯）。`reads_*` 保留 `[v1, v2]` 允许前向读取 v2 产物。

**升级时序**：
1. **当前**（治理框架就绪）：所有 skill `writes_layout: v1`，正文 v1 行为，layout drift 检测不会误报
2. **#1 编号体系交付后**：所有 skill **保持 `writes_id_scheme: id.v1`**（仅 SKILL.md/模板加双轨说明，runtime 未实现）；待 runtime 检测层 [FUTURE] 落地 + 至少 1 个 v2 项目验证通过后，再升级到 `id.v2`。详见 [id-scheme-implementation.md § frontmatter 升级规则](id-scheme-implementation.md#frontmatter-升级规则条件性)。
3. **#2 文件夹组织交付后**：同 #1 模式，先保持 `writes_layout: v1` + 双轨说明，runtime + 验证后再升 v2
4. **#4 代码解耦交付后**：同上，traceability.yml runtime 落地后才升 `writes_traceability: trace.v1`
5. **所有阶段完成**：全 skill 的 `writes_*` 升级到 v2，治理框架"声明 == 行为"对齐

**单一升级原则**：任何 skill 的 `writes_*` 字段升级到 v2 时，**SKILL.md 正文必须同步升级**到 v2 行为（输出新目录 / 新编号 / 新追溯机制），不允许"声明先行"。

### A 类 skill（DevDocs 主链路产物）

| Skill | reads_layout | writes_layout | reads_id | writes_id | reads_trace | writes_trace | on_incompatible |
|-------|------------|---------------|----------|-----------|-------------|--------------|-----------------|
| `ms-requirements` | [v1, v2] | **v1** | [v1, v2] | **v1** | [v0, v1] | **v0** | block |
| `ms-system-design` | [v1, v2] | **v1** | [v1, v2] | **v1** | [v0, v1] | **v0** | block |
| `ms-test-cases` | [v1, v2] | **v1** | [v1, v2] | **v1** | [v0, v1] | **v0** | block |
| `ms-dev-tasks` | [v1, v2] | **v1** | [v1, v2] | **v1** | [v0, v1] | **v0** | block |
| `ms-dev-workflow` | [v1, v2] | **v1** | [v1, v2] | **v1** | [v0, v1] | **v0** | block |

### B 类 skill（辅助产物）

| Skill | reads_layout | writes_layout | reads_id | writes_id | reads_trace | writes_trace | on_incompatible |
|-------|------------|---------------|----------|-----------|-------------|--------------|-----------------|
| `ms-prd-parser` | [v1, v2] | **v1** | [v1, v2] | **v1** | [v0, v1] | **v0** | block |
| `ms-prd-brainstorm` | [v1, v2] | **v1** | [v1, v2] | **v1** | [v0, v1] | **v0** | block |
| `ms-insights` | [v1, v2] | **v1** | [v1, v2] | **v1** | [v0, v1] | **v0** | block |
| `ms-onboard` | [v1, v2] | **v1** | [v1, v2] | **v1** | [v0, v1] | **v0** | warn |

注：`ms-onboard` 使用 `warn` 而非 `block`，因为 onboarding 是只读报告，不应阻塞用户了解项目状态。

### 编排层 skill

| Skill | reads_layout | writes_layout | 说明 |
|-------|------------|---------------|------|
| `ms-pipeline` | [v1, v2] | **v1** | 编排所有 A/B skill，自身不写产物（只协调）|
| `ms-feature` | [v1, v2] | **v1** | 编排，与 pipeline 同 |
| `ms-bugfix` | [v1, v2] | **v1** | 编排，与 pipeline 同 |
| `ms-prd` | [v1, v2] | **v1** | 编排 prd-parser + prd-brainstorm |

### 验证 / 同步 / 知识沉淀 skill

| Skill | reads_layout | writes_layout | 说明 |
|-------|------------|---------------|------|
| `ms-verify` | [v1, v2] | n/a | 只读校验，无 write |
| `ms-sync` | [v1, v2] | **v1** | 写 traceability.yml 等 v2 产物为 [FUTURE]，当前写 v1 形态 |
| `ms-compound` | [v1, v2] | **v1** | 写 patterns/ 文件，PATTERN-NNN 编号化为 [FUTURE] |
| `ms-codebase-insight` | [v1, v2] | n/a | 只读分析，无 write |
| `ms-retrofit` | [v1, v2] | **v1** | 改造已有项目，目标 v2 但当前产出 v1 形态 |

### 独立工具 skill（不参与 layout 治理）

以下 skill **不需要** layout 兼容性字段（独立于 DevDocs 治理体系）：

- `commit-convention`（git 提交规范）
- `git-safety`（git 操作安全）
- `code-quality`（代码质量约束）
- `code-self-describe`（代码自描述）
- `testing-guide`（测试规范）
- `refactor`（重构）
- `adversarial-review`（对抗审查）
- `ui-orchestrator`（UI 调度）
- `agent-memory`（memory 治理）
- `work-report`（工作报告）

## 不兼容场景示例

### 场景 1：项目 layout.v1，调用 `writes_layout: v2` 的 skill

```text
项目 AGENTS.md:
  devdocs:
    docs_layout_version: layout.v1

调用 /ms-requirements 时（当前 transitional state writes_layout: v1）：
  reads_layout: [v1, v2] → 包含 v1 → 允许读取
  writes_layout: v1 → 与项目一致 → 正常运行
  
（v2 写入能力 [FUTURE]：待 #2 文件夹组织阶段升级 writes_layout: v2 + SKILL.md 正文 v2 行为后激活）
```

### 场景 2：项目 layout.v2，调用 `reads_layout: [v1]` 的旧 skill

```text
项目: layout.v2
旧 skill: reads_layout: [v1]
  → 旧 skill 无法读取 v2 的目录结构
  → on_incompatible: block，要求升级 skill 而非降级项目
```

### 场景 3：layout.v2 + id.v1（依赖冲突）

```text
AGENTS.md:
  docs_layout_version: layout.v2
  id_scheme: id.v1                  # ❌ 强依赖冲突

skill 检测：layout.v2 必须配 id.v2 + trace.v1
  → 直接阻塞，建议运行 /ms-pipeline realign --docs-layout 同步升级三层
```

## 矩阵的维护责任

| 维护时机 | 触发动作 | 责任人 |
|---------|--------|--------|
| 新增 skill | 本表追加一行 + skill SKILL.md frontmatter 同步声明 | skill 作者 |
| 升级 layout.vN → vN+1 | 本表所有 `writes_layout` 更新 | layout 升级负责人 |
| skill 弃用某个 layout 兼容 | 本表 `reads_layout` 删除对应版本 | skill 作者 |
| 新 skill 不参与 layout 治理 | 本表"独立工具"清单追加 | skill 作者 |

## 与 SKILL.md frontmatter 的一致性

本表是**single source of truth**。各 skill SKILL.md frontmatter 必须与本表一致：

```yaml
# skills/requirements/SKILL.md 顶部（Transitional State：writes_* 当前为 v1）
---
name: ms-requirements
...
reads_layout: [layout.v1, layout.v2]    # 必须与本表 ms-requirements 行一致
writes_layout: layout.v1                # 当前 transitional；v2 接口 [FUTURE] 落地后升级
reads_id_scheme: [id.v1, id.v2]
writes_id_scheme: id.v1
reads_traceability: [trace.v0, trace.v1]
writes_traceability: trace.v0
on_incompatible: block
migration: /ms-pipeline realign --docs-layout
---
```

**漂移检测**：`/ms-verify --layout-drift` 比对本表 vs 各 skill frontmatter，发现差异 surface 报告。

## 引用关系

| 引用本文件的位置 | 引用目的 |
|---------|----|
| `skills/pipeline/SKILL.md` § realign | layout 升级时批量更新 skill frontmatter 的总表 |
| `skills/verify/SKILL.md` § `--layout-drift` | 检测 skill frontmatter 与本表是否一致 |
| `layout-versioning-policy.md` | 兼容性声明的具体实例化 |

## 变更日志

| 日期 | 变更 | 触发 |
|------|------|------|
| 2026-05-15 | 初始版本 | DevDocs 治理体系升级（6 大支柱 #6）|
