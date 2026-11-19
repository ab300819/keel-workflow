# hcom 窗口实例（外部审查方的首选送达方式）

> 2026-11 本机实测：hcom 0.7.31、agy 1.5.12、tmux。只在 skill multi-turn 模式使用，embedded-headless ⛔ 不用。

审查方不再每轮起一个一次性进程，而是在一个 tmux 窗口里的 hcom 实例中连续对话：复审接着上一轮说，审查方能自己跑命令。本文件是实例方式的**唯一出处**；询问、对齐、一方失败见 [cross-validation.md](cross-validation.md)，命令行通道见 [external-reviewer-integration.md](external-reviewer-integration.md)。

⛔ 不替用户处理实例里的弹框，唯一允许的界面注入是 § 发消息与等回复的「推一下」。⛔ 不碰用户自己的 tmux 窗口与 hcom 实例（含 `hmux` 起的），也不复用它们。⛔ 实例不跨审查会话保留。

## 通道顺序与探测

| 审查方 | 顺序 |
|---|---|
| codex | 窗口实例 → T1 → T1b → T2（后三级规则不变）|
| agy | 窗口实例 → `agy` CLI |

S2.5 探测分两层，**任一层可用该方就算可用**：

- **窗口实例**（前置条件，三条同时成立）：`$TMUX` 非空；`hcom` 在 PATH 上；`hcom hooks status <codex|antigravity>` 不含 `not installed`。登录与工具调用是否正常，到 § 启动才见分晓。
- **命令行**：集成文档的现行探测原样执行（它同时是落回通道）。命令行探测失败但窗口实例前置条件满足 → 该方仍可用，记下「无落回通道」。

**额度类失败不走 T1**：codex 实例与 T1 共用同一订阅。实例屏幕或回复里出现额度用尽信号（含「是否换模型」弹框）→ 照抄原文与重置时间，直接按集成文档 § T1b 处理。

## 启动与关闭

- **标签**：`<目录名>-rv<4 位随机>-codex` / `…-agy`；目录名只留字母、数字、连字符。随机段每个审查会话生成一次，复审沿用。窗口名用同一后缀（如 `rv7k2q-codex`）。
- **建窗口**：`tmux new-window -d -t "=<协调方所在会话>:" -n <窗口名> -c <仓库>`，等它回到 shell 提示符再打命令（否则命令会丢）。
- **打入启动命令**（`tmux send-keys … Enter`）：

  ```bash
  hcom codex --tag <标签> --terminal here --sandbox read-only
  hcom agy   --tag <标签> --terminal here --sandbox --model <id> --settings <放行文件>
  ```

  - `<id>` 按集成文档 § agy CLI「模型选取」。
  - 放行文件写在临时目录，只对本次会话生效、不落盘：

    ```json
    {"permissions":{"allow":["command(git show)","command(git diff)","command(git log)","command(git status)","command(git blame)","command(git ls-files)","command(hcom send)"]}}
    ```

  - ⛔ 不用 `hcom <工具> --terminal "<命令> {script}"` 让 hcom 自己开窗口——实测参数被并成一个，两方都秒退。`--terminal here` 未写进 hcom 帮助，失效时该方按起不来处理。
- **就绪**：`hcom list` 里出现该标签的实例且状态为 `listening`，记下它的**完整名字**（等回复、推一下、查事件都用名字；标签只用于发消息和关闭）。`blocked` → 把屏幕上的弹框原文报给用户并等其处理。约 2 分钟仍未就绪 → 落回。不另发握手消息。
- **关闭**（会话结束、失败、用户中止都要做）：`hcom kill tag:<标签>`，再 `tmux kill-window`（窗口已不在则忽略——`hcom kill` 有时会连窗口一起关）。

## 发消息与等回复

- **发**：先记下当前最新事件号（`hcom events --last 1`），再

  ```bash
  hcom send @<标签>- -b --intent request --file <brief 文件>
  ```

  两方 brief 内容相同。实例能自己跑命令，不必为 agy 把 diff 存成文件。brief 末尾写明三件事：只读、不修改任何文件；不读取其他实例的对话与消息；用 `hcom send @bigboss` 回复，内容是与现行 schema 同形的 JSON（代码审查）或带约定末尾标记的文本（方案 / 文档审查），回复后停下等下一条。
- **推一下**：发完约 30 秒该实例仍有未读 →

  ```bash
  hcom term inject <名字> "有新的 hcom 消息，请处理。" --enter
  ```

  只对自己起的审查实例做，只推这一句，每条消息最多一次。推过仍未送达 → 落回。原因见 § 已知问题 1；实测 agy 首条必须推，之后的不一定，codex 不需要。
- **等**：分段等（每段约 60 秒），每段结束看一次 `hcom list <名字>`：

  ```bash
  hcom events --wait 60 --type message --from <名字> --sql "id><发送前的事件号>"
  ```

  | 状态 | 处置 |
  |---|---|
  | 收到回复 | 进入解析 |
  | `active` | 继续等；单轮累计约 15 分钟仍无回复按失败 |
  | `blocked` | 报弹框原文并等用户；超时落回 |
  | `listening` 且无回复 | 发一条提醒「用 hcom send @bigboss 回复结果」，只提醒一次；仍无回复按失败 |
  | 实例已退出 | 按失败 |

- **复审**：发给同一个实例，只说这一轮改了什么、要复核哪几条。
- **解析**：解析、截断判定、校验优先级**完全沿用** SKILL.md § S3–S4 与集成文档 § 输出解析，本文不另立判据。「原通道重跑一次」在实例方式下 = 给同一实例发「上一条回复不完整，请完整重发」；仍不完整 → 落回。

## 落回

以下任一情况：关掉该实例，落到下一级通道，结论里写明「<某方> 本轮起改用 <通道>，原因：<原文>」。

- 窗口实例起不来，或等用户处理弹框超时
- 推过仍未送达；回复两次不完整；实例退出；单轮等待超限
- § 事后检查不通过

规则：

- **落回的当轮就重建完整 brief**。实例收到的可能只是增量（复审轮），或依赖它自己跑命令。落到命令行时按集成文档重新准备：完整材料、上一轮的发现清单、agy 的 diff 文件。
- 落回后本次会话该方不再重起实例（上下文已丢，重起拿不回连续性）。SKILL.md 的「连续 2 轮失败才永久降级」管命令行各级之间，原样保留。
- 所有通道都失败 → [cross-validation.md § 一方失败](cross-validation.md)。

## 事后检查（每轮收到回复后、对齐前）

1. **只读**：调度前后各算一次工作区指纹，必须相同。

   ```bash
   { git status --porcelain; git diff --binary HEAD; \
     git ls-files -o --exclude-standard -z | xargs -0 shasum 2>/dev/null; } | shasum
   ```

   ⛔ 不能只比 `git status`——被审的工作区本来就有未提交改动，再改一次状态行不变。不一致 → 列出差异报告用户，由用户决定是否回退，⛔ 协调方不自行回退。责任记在 agy（codex 有系统沙箱）：agy 本轮结果无效并落回；codex 本轮结果保留，但标注「审查期间工作区被改动」，由用户决定是否采用。
2. **独立**：`hcom events --agent <名字> --cmd "<模式>"` 对 `hcom transcript`、`hcom term` 无结果，对 `hcom events` / `hcom listen` 的结果里没有查别的实例；并且另一方回复里的一段原文没有出现在它的会话记录里（会话记录路径见 `hcom list <名字>`）。命中 → 该方本轮结果无效并落回。

两点局限照实告诉用户：agy 的只读**不是事前保证**（实测 `--sandbox` 加放行清单都挡不住 `touch`）；hcom 启动时会把在线实例的名字写进每个实例的初始上下文，**对方的名字藏不住**，独立性只靠上面的检查。审查方直接读 `~/.codex/sessions/`、`~/.hcom/` 下的文件，这两项检查发现不了。

## 已知问题

1. **agy 空闲时收不到消息**。输入框的模式提示行（`Auto mode: …`，三种 `--mode` 都有）被 hcom 读成未提交的草稿：`hcom term <名字> --json` 显示 `ready: true`、`prompt_empty: false`。上游 [aannoo/hcom#114](https://github.com/aannoo/hcom/issues/114) 关闭时未修。绕法即「推一下」。
2. **弹框会挡住消息**，`hcom list` 标 `blocked`。遇到过：codex「额度快用完，是否换模型」；agy「是否信任此目录」（`~/.gemini/antigravity-cli/settings.json` 的 `trustedWorkspaces` 要写完整路径，hcom 的 `auto_trust_workspace` 对 agy 无效）；agy「是否执行此命令」（不在放行文件里的命令）。
3. agy 需一次性安装常驻接入：`hcom hooks add antigravity`。
4. 实测耗时（审一份约 170 行的设计稿）：两方启动到就绪约 30 秒；codex 首轮约 1 分钟、复审 8 秒；agy 首轮约 7 分钟、复审约 1 分钟。
