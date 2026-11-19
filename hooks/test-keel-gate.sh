#!/bin/bash
# keel-gate 的固定用例（Claude Code / Codex 两种输入形状）：bash hooks/test-keel-gate.sh
set -u
for v in $(env | grep -o "^GIT_[A-Z_]*"); do unset "$v"; done   # 夹具 git 不能落到外层仓库
HOOK="$(cd "$(dirname "$0")" && pwd)/keel-gate"
KEEL="$(dirname "$HOOK")/../skills/shared/scripts/keel.py"
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
fail=0

# new_proj <名字>：已初始化 keel 状态、含任务 T-1 并已提交的项目
new_proj() {
  R="$TMP/$1"; mkdir -p "$R/docs/devdocs"
  git -C "$R" init -q; git -C "$R" config user.email t@t; git -C "$R" config user.name t
  echo x > "$R/docs/devdocs/01-requirements.md"
  python3 "$KEEL" --root "$R" init >/dev/null && python3 "$KEEL" --root "$R" task add --title x --source dev-tasks >/dev/null
  git -C "$R" add -A; git -C "$R" commit -qm init
}
# expect <用例名> <pre|post> <payload> <应出现的子串；空串 = 应静默>
expect() {
  out=$(printf '%s' "$3" | CLAUDE_PROJECT_DIR="$R" ${ENVX:-} /bin/bash "$HOOK" "$2" 2>&1)
  if [ -z "$4" ]; then [ -z "$out" ] && return; echo "FAIL $1: 应静默，实际输出 $out"
  else case "$out" in *"$4"*) return;; esac; echo "FAIL $1: 应含「$4」，实际输出 ${out:-<空>}"
  fi
  fail=1
}

new_proj claude
expect "Claude Pre 拒绝写状态文件" pre \
  '{"tool_name":"Edit","tool_input":{"file_path":"'"$R"'/docs/devdocs/state/tasks/T-1.json"}}' '"permissionDecision": "deny"'
new_proj codex
expect "Codex Pre 拒绝补丁改 backlog.md" pre \
  '{"tool_name":"apply_patch","tool_input":{"command":"*** Begin Patch\n*** Update File: docs/devdocs/backlog.md\n@@\n-a\n+b\n*** End Patch"}}' \
  '"permissionDecision": "deny"'
expect "Pre 拦模型代人 state accept" pre \
  '{"tool_name":"Bash","tool_input":{"command":".keel/bin/keel state accept"}}' '! .keel/bin/keel'
new_proj bash; echo '{"hand":1}' > "$R/docs/devdocs/state/tasks/T-1.json"
expect "Post 发现 Bash 改过的状态文件" post '{"tool_name":"Bash","tool_input":{"command":"echo"}}' '"decision": "block"'
new_proj long; printf '%0600d\n' 0 >> "$R/docs/devdocs/04-dev-tasks.md"
expect "Post 拦新增超长行" post '{"tool_name":"Write","tool_input":{"file_path":"docs/devdocs/04-dev-tasks.md"}}' 'K3'
R="$TMP/nokeel"; mkdir -p "$R"
expect "非 keel 项目静默" pre '{"tool_name":"Bash","tool_input":{"command":"keel state accept"}}' ""
new_proj nopy
ENVX="env PATH=/nonexistent" expect "PATH 里无 python3 时静默" pre \
  '{"tool_name":"Edit","tool_input":{"file_path":"'"$R"'/docs/devdocs/state/tasks/T-1.json"}}' ""

new_proj shimerr; rm -rf "$R/.keel"; mkdir -p "$TMP/elsewhere"; ln -s "$TMP/elsewhere" "$R/.keel"
out=$(CLAUDE_PROJECT_DIR="$R" bash "$(dirname "$HOOK")/keel-shim" 2>&1); rc=$?
[ -z "$out" ] && [ $rc -eq 0 ] || { echo "FAIL keel-shim 出错须静默: rc=$rc 输出 $out"; fail=1; }

[ $fail -eq 0 ] && echo "keel-gate: 8 个用例全部通过"
exit $fail
