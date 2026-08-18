---
name: python-spec
description: Opinionated Python toolchain spec — mise owns runtime versions, uv owns virtualenvs, dependency resolution, lockfiles and execution. Covers project layout, script classification (PEP 723 vs project env), throwaway usage, and diagnosing pip/uv env guard failures. Use when bootstrapping a Python project, changing dependencies, writing standalone scripts, or when a pip/uv command fails unexpectedly. Triggers on keywords like "uv", "mise", "venv", "pyproject.toml", "uv.lock", "PEP 723", "pip install 失败", "虚拟环境", "Python 项目初始化", "依赖管理". NOT for migrating an existing repo's toolchain (keep its poetry/conda/requirements), and NOT for ordinary Python code changes that don't touch tooling.
allowed-tools: Read, Write, Glob, Grep, Edit, Bash
---

# Python Toolchain (mise + uv)

Python 运行时、依赖和脚本的管理约定：保持系统 Python 干净、避免全局依赖污染、环境可复现。

## Language

- Accept questions in both Chinese and English
- Always respond in Chinese

## Trigger Conditions

- 新建 Python 项目 / 初始化依赖
- 增删依赖、处理 lock 文件
- 写独立脚本或临时试用某个包
- `pip` / `uv` 命令报出环境相关错误，需要判断是守卫拦截还是真故障

## 适用范围

适用于**新建**项目。已有 repo 沿用它现有的工具链（poetry / pdm / pip-tools / requirements.txt / conda 都算）——
可以建议迁移，不要擅自执行。

---

## 职责边界

**一个职责一个工具。**

| 工具 | 负责 |
|------|------|
| mise | 运行时版本（Python / Node / Go…）、项目级工具版本 |
| uv | 虚拟环境、依赖解析、lock 文件、项目执行、单文件脚本运行 |

不要在这之上再叠 pyenv / conda / 手工 venv / 全局 `pip install`。同一职责由两个工具管，
是后续所有诡异问题的根源。

---

## 项目

```
project/
├── mise.toml        # 钉运行时 —— 运行时的唯一真源
├── pyproject.toml   # 项目需要什么（PEP 621）
├── uv.lock          # 实际解析结果 —— 要提交
├── src/
└── tests/
```

运行时按项目钉，不依赖系统 Python：

```toml
# mise.toml
[tools]
python = "3.12"
```

然后 `mise install`。如果全局设了 `not_found_auto_install = false`，`cd` 进目录不会自动装，
需要显式执行。

**`uv init` 会生成 `.python-version`**，内容取自当前生效的解释器（很可能是全局那个，
不是你打算给项目钉的版本）。它和 `mise.toml` 构成两个运行时真源，一漂移就出事——
uv 按 `.python-version` 要版本，mise 提供的是另一个，再叠加 `UV_PYTHON_DOWNLOADS=never`
就是直接失败。

运行时归 mise，所以：

```bash
uv init --no-pin-python     # 不生成 .python-version
```

要保留 `.python-version` 也行，但必须和 `mise.toml` 同步改；`pyproject.toml` 的
`requires-python` 声明的是支持范围，不是开发用的具体版本。

依赖走 uv，不走裸 pip：

```bash
uv add <pkg>         # 运行依赖
uv add --dev <pkg>   # 开发依赖
uv sync              # 对齐 .venv；pyproject 与 lock 不一致时会先更新 lock

uv lock --upgrade                 # 升级全部锁定依赖
uv lock --upgrade-package <pkg>   # 只升级指定包
```

`uv sync` 不会因为上游发了新版就主动升级已锁定的版本——升级是 `uv lock --upgrade` 的事。

`pyproject.toml` + `uv.lock` 都要提交：前者描述项目需要什么，后者固定实际解析结果。
新建项目以这两个为真源，不再另维护 `requirements.txt`——
导出一份给 Docker 分层缓存之类的消费方是可以的，但那是**产物**，不是真源。

执行走 `uv run`，不手动 activate —— `.venv` 归 uv 管：

```bash
uv run python main.py
uv run pytest
uv run ruff check .
```

---

## 脚本

判断原则：**离开项目还能跑 → PEP 723；依赖项目代码 → 项目环境。**

独立脚本（运维脚本、API 探测、一次性自动化）用 inline metadata，不需要项目：

```python
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx", "rich"]
# ///
```

```bash
uv run script.py     # uv 建一个带缓存的临时环境
```

只用标准库的脚本不必强加 metadata，`uv run script.py` 直接就跑。需要第三方依赖、
或要钉 Python 版本时才加。

项目内脚本（`scripts/migrate.py` 要 import `src/`）不写 PEP 723 块，用项目环境：

```bash
uv run python scripts/migrate.py
```

---

## 临时使用

试一次的东西不要装成全局包。

```bash
uv run --with rich python              # 叠加在当前项目环境之上，rich 只对这次生效
uv run --no-project --with rich python # 与当前项目完全无关的临时试用
uvx <cli>                              # 一次性跑某个 CLI
uv tool install <cli>                  # 常驻 CLI，隔离安装
```

注意 `--with` 在项目目录里**不是隔离沙箱**：项目本身仍会被发现并同步，额外依赖只是加一层。
要完全撇开当前项目，加 `--no-project`。

---

## 环境守卫

推荐在 mise 全局配置（`~/.config/mise/config.toml`）里设这三项。**撞上报错先判断是不是守卫
故意拦的**，再决定动作——它们的存在就是为了让错误提前、响亮地暴露：

```toml
[env]
UV_PYTHON_DOWNLOADS = "never"
PIP_REQUIRE_VIRTUALENV = "true"

[settings]
python.uv_venv_auto = "source"
```

| 守卫 | 拦住什么 | 撞上了怎么办 |
|------|---------|-------------|
| `PIP_REQUIRE_VIRTUALENV=true` | 裸 `pip install` 报 `Could not find an activated virtualenv (required)` | 进虚拟环境，或改用 `uv add`。**它管不到 `uv pip install`**——不过 uv 自己默认也拒绝写非虚拟环境（报 `No virtual environment found`），真正要当心的是 `--system`、错激活的 `VIRTUAL_ENV`，以及下面那个 `UV_PYTHON` |
| `UV_PYTHON_DOWNLOADS=never` | uv 自己再下一个解释器；改为用 mise 提供的 | 项目钉的版本没装 → `mise install`，**不是**放宽这个变量 |
| `python.uv_venv_auto="source"` | 只激活已存在的 `.venv`，不自动创建 | 新 clone 没有 `.venv` → 先 `uv sync` |

`uv_venv_auto` 的两个前提：当前目录或父目录得有 `uv.lock`（否则不生效），且 shell 里
执行过 `mise activate`（或用 `mise exec` 跑）——只把 shims 放进 PATH 不会激活 venv。

为什么 `PIP_REQUIRE_VIRTUALENV` 有必要：mise 装的 Python **没有** PEP 668 的
`EXTERNALLY-MANAGED` 标记，不拦就会把包写进 `installs/python/<ver>/lib/.../site-packages`，
污染所有项目。

### 两个不要设的变量

- **`UV_PYTHON`（不要在全局配置里钉死解释器）** —— 它是官方支持的覆盖项，作用域应该限于
  单次命令、某个项目或 CI 矩阵。一旦全局钉死：它的优先级高于 `.python-version`，项目里的
  版本声明就失效了（钉 3.12 照样建出全局那个版本，没有警告）；而且它会改写 `uv pip` 的
  环境发现，项目里有 `.venv` 时 `uv pip install` 仍打进那个全局解释器，显式 `VIRTUAL_ENV`
  都盖不过。uv 本来就能从 PATH 找到 mise 的 Python，全局设它没有收益。
- **全局 `_.python.venv`** —— 相对路径会被钉死成 `$HOME/.venv` 并盖过 `uv_venv_auto`。
  裸 venv 项目请写进该项目自己的 `mise.toml`。

`uv` 本身可以由 mise 管，也可以由系统包管理器提供。如果不由 mise 管，就不要在项目
`mise.toml` 里假设它存在；只在某个项目确实需要特定 uv 版本时才钉进去。

---

## 禁止

- `sudo pip install`，或往系统 / mise 的 Python 里 `pip install`。
- 绕过 PEP 668 的 `EXTERNALLY-MANAGED` 保护。
- mise + pyenv + conda + 手工 venv 混用。

---

## 快速决策

| 场景 | 用什么 |
|---|---|
| 新建服务 / 应用 / 数据项目 | `mise.toml` + `pyproject.toml` + `uv.lock` |
| 新建库 | `pyproject.toml` + `uv.lock` |
| 独立辅助脚本（有第三方依赖） | PEP 723 + `uv run script.py` |
| 独立辅助脚本（纯标准库） | 直接 `uv run script.py` |
| 项目内脚本（import 项目代码） | `uv run python scripts/x.py` |
| 试用一次某个包 | `uv run --with <pkg>` |
| 常驻 CLI 工具 | `uv tool install` |
| 已有 repo 用别的工具链 | 沿用它的，别擅自迁移 |
| 系统 Python | 不碰 |
