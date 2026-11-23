#!/usr/bin/env bash
# 开发期门禁：ruff + mypy + python3 ≥ 3.9 下自测。不随插件分发。
# 清掉 git hook 注入的 GIT_*，否则自测的临时 git 夹具会误操作外层仓库
for v in $(env | grep -o "^GIT_[A-Z_]*"); do unset "$v"; done
cd "$(dirname "$0")/.." || exit 3
S=skills/shared/scripts
step() { echo "== $1"; }
fail() { echo "check-python 失败于：$1" >&2; exit 1; }

step "ruff"
uvx ruff check --target-version py39 --select E4,E7,E9,F,B,UP $S skills/pipeline/scripts || fail ruff

step "mypy --strict（钉 1.18.2：新版不再支持 --python-version 3.9）"
if [ -d $S/keellib ] && [ -f $S/keel.py ]; then
  uvx mypy==1.18.2 --strict --python-version 3.9 $S/keel.py $S/keellib || fail mypy
else
  echo "keellib 尚不存在，跳过 mypy"
fi

step "自测（python3 ≥ 3.9，用 PATH 上的 python3；下限兼容由上面 ruff / mypy 的 3.9 目标保证）"
PY=python3
"$PY" -c 'import sys; sys.exit(sys.version_info < (3, 9))' 2>/dev/null \
  || { echo "python3 不可用或低于 3.9：$("$PY" --version 2>&1)" >&2; fail "python3 版本"; }
"$PY" --version
if [ -f $S/keel.py ]; then
  "$PY" $S/keel.py --self-test || fail "keel.py --self-test"
fi
"$PY" skills/pipeline/scripts/health-lint.py --selftest || fail "health-lint --selftest"
echo "check-python OK"
