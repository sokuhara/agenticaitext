#!/usr/bin/env bash
#
# main ブランチの保護を設定する。
#
#   使い方:  ./scripts/setup_branch_protection.sh <owner>/<repo>
#
# 事前に GitHub CLI の認証が必要です:  gh auth login
#
set -euo pipefail

REPO="${1:?リポジトリを指定してください  例: myorg/vibe-order}"
RULESET="$(dirname "$0")/../.github/rulesets/main-protection.json"

echo "==> $REPO に main protection を適用します"

gh api \
  --method POST \
  -H "Accept: application/vnd.github+json" \
  "/repos/${REPO}/rulesets" \
  --input "$RULESET"

echo "==> 完了しました。次を満たさないと main にマージできません:"
echo "    - プルリクエスト経由であること"
echo "    - レビュー承認が1件以上あること"
echo "    - CI の check ジョブが成功していること"
echo "    - main への直接プッシュと強制プッシュは拒否されます"
