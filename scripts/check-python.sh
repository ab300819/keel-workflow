#!/usr/bin/env bash
# 开发期门禁：ruff + mypy + 真实 Python 3.9 下自测。不随插件分发。
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

step "python 3.9 自测"
PY39="$(mise where python@3.9 2>/dev/null)/bin/python3"
if [ ! -x "$PY39" ]; then
  echo "缺 Python 3.9：请执行 mise install python@3.9（不要改用别的版本）" >&2
  fail "python3.9"
fi
if [ -f $S/keel.py ]; then
  "$PY39" $S/keel.py --self-test || fail "keel.py --self-test"
fi
"$PY39" skills/pipeline/scripts/health-lint.py --selftest || fail "health-lint --selftest"
echo "check-python OK"
