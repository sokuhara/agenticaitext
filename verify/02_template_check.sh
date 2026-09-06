#!/usr/bin/env bash
#
# テンプレートリポジトリが本当に動くかを確認する。
#
#   ./02_template_check.sh /path/to/vibe-order-template
#
# 確認すること:
#   1. 依存が入るか        (uv sync)
#   2. make check が通るか  (ruff format / ruff check / pytest)
#   3. 起動して応答するか   (uvicorn + curl)
#
set -uo pipefail

DIR="${1:?テンプレートのディレクトリを指定してください}"
cd "$DIR"

fail=0
step() { echo; echo "=== $* ==="; }
result() { if [ "$1" -eq 0 ]; then echo "  -> OK"; else echo "  -> 失敗 (exit $1)"; fail=1; fi; }

step "1. 依存のインストール"
make install; result $?

step "2. make check"
make check; result $?

step "3. 起動と応答"
uv run uvicorn vibe_order.app:app --port 8765 >/tmp/uvicorn.log 2>&1 &
PID=$!
sleep 4
curl -sf http://127.0.0.1:8765/api/health && echo && result 0 || result 1
curl -sf http://127.0.0.1:8765/ >/dev/null && echo "  トップ画面: OK" || { echo "  トップ画面: 失敗"; fail=1; }
kill $PID 2>/dev/null
wait $PID 2>/dev/null

step "4. PART 7 用ブランチ"
if [ -d .git ]; then
  ./scripts/make_challenge_branch.sh && make check
  if [ $? -ne 0 ]; then
    echo "  -> OK（ここは落ちるのが正解です）"
  else
    echo "  -> 失敗: 落ちるはずのテストが通っています"; fail=1
  fi
  git switch - >/dev/null 2>&1
else
  echo "  git リポジトリではないので飛ばします"
fi

echo
if [ "$fail" -eq 0 ]; then echo "==== すべて通りました ===="; else echo "==== 失敗があります ===="; fi
exit "$fail"
