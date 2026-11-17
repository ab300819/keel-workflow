#!/bin/bash
# devdocs-drift 的固定用例。改 hook 的路径解析后跑：bash hooks/test-devdocs-drift.sh
# 以本文件为准，⛔ 不靠审查者临时想文件名来验证。
set -u
HOOK="$(cd "$(dirname "$0")" && pwd)/devdocs-drift"
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
fail=0

# new_repo <名字>：建一个已提交 01-requirements.md 的 keel 项目
new_repo() {
  R="$TMP/$1"; mkdir -p "$R/docs/devdocs" "$R/src"
  git -C "$R" init -q; git -C "$R" config user.email t@t; git -C "$R" config user.name t
  echo x > "$R/docs/devdocs/01-requirements.md"; echo x > "$R/src/old.ts"; echo x > "$R/README.md"
  git -C "$R" add -A; git -C "$R" commit -qm init
}
run() { CLAUDE_PROJECT_DIR="$R" bash "$HOOK"; }
# expect <用例名> <应出现的子串；空串 = 应静默>
expect() {
  out=$(run)
  if [ -z "$2" ]; then [ -z "$out" ] && return; echo "FAIL $1: 应静默，实际输出 $out"
  else case "$out" in *"$2"*) return;; esac; echo "FAIL $1: 应含「$2」，实际输出 ${out:-<空>}"
  fi
  fail=1
}

new_repo code;     echo y > "$R/src/a.ts";                          expect "只改代码" "（src/a.ts）"
new_repo space;    echo y > "$R/src/my file.ts";                    expect "代码文件名带空格" "（src/my file.ts）"
new_repo arrowdoc; echo y > "$R/docs/note -> example.ts";           expect "docs 下文件名带箭头" ""
new_repo md;       echo y > "$R/notes with spaces.md";              expect "只改带空格的 Markdown" ""
new_repo intodoc;  git -C "$R" mv README.md docs/devdocs/02-system-design.md; echo y > "$R/src/a.ts"
                                                                    expect "重命名进 devdocs 且改了代码" ""
new_repo arrowmv;  git -C "$R" mv src/old.ts "src/a -> b.ts";       expect "重命名目标带箭头" "（src/a -> b.ts）"
new_repo cool;     echo y > "$R/src/a.ts"; run >/dev/null;          expect "5 分钟冷却内第二次" ""
R="$TMP/nokeel"; mkdir -p "$R"; git -C "$R" init -q; echo y > "$R/a.ts"; expect "非 keel 项目" ""

[ $fail -eq 0 ] && echo "devdocs-drift: 8 个用例全部通过"
exit $fail
