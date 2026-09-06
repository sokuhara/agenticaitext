# Vibe Order テンプレート

Agentic Coding 教材（PART 5 〜 PART 7）で使うテンプレートリポジトリです。

`make check` が通る最小の状態から始まります。ここに PART 6 で注文管理を実装し、
PART 7 で自作 Agent にテストを直させます。

---

## 講師の準備（1回だけ）

### 1. テンプレートリポジトリとして公開する

1. このフォルダの中身をGitHubの新しいリポジトリへ push する
2. リポジトリの Settings → General → **Template repository** にチェックを入れる

学生は「Use this template」から自分のリポジトリを作ります。フォークより後の操作が楽です。

### 2. ブランチ保護を設定する

GitHub CLI の認証を済ませてから実行します。

```bash
gh auth login
./scripts/setup_branch_protection.sh <owner>/<repo>
```

これで次が有効になります。

- `main` への直接プッシュを禁止
- プルリクエストとレビュー承認1件を必須
- CI の `check` ジョブの成功を必須
- 強制プッシュとブランチ削除を禁止

画面から設定する場合は Settings → Rules → Rulesets → New ruleset で、
`.github/rulesets/main-protection.json` を Import すれば同じ状態になります。

> **注意**：学生が自分のリポジトリを作ると、保護設定は引き継がれません。
> 各自に `setup_branch_protection.sh` を実行させるか、Organization の
> ruleset で全リポジトリに一括適用してください。後者のほうが確実です。

### 3. PART 7 用のブランチを作る

```bash
./scripts/make_challenge_branch.sh
git push -u origin agent-challenge
```

テストが落ちる状態のブランチができます。PART 7 の Agent は、この失敗を直すのが目標です。

---

## 学生の手順

```bash
# 1. 取得して依存を入れる
git clone <あなたのリポジトリ>
cd vibe-order
make install

# 2. 通ることを確認する
make check

# 3. 起動して画面を見る
make run
# → http://localhost:8000
```

`make check` が通れば準備完了です。

---

## 何が入っているか

| ファイル | 役割 | 対応する節 |
|---|---|---|
| `Makefile` | 完了条件を1コマンドに一本化する | 5.1 |
| `pyproject.toml` | 依存とツール設定を1か所に集約 | 5.2 |
| `AGENTS.md` | Agentが毎回読む作業ルール | 5.3 |
| `.github/workflows/ci.yml` | 手元と同じ検査を他人の環境でも回す | 5.4 |
| `.gitignore` / `.clineignore` | 秘密情報を守る | 5.5 |
| `.github/rulesets/` | ブランチ保護の設定 | 5.4.2 |
| `src/vibe_order/` | 実装（いまはヘルスチェックだけ） | 6章で育てる |
| `tests/` | テスト（いまは起動確認だけ） | 6章で育てる |

## 道具は7つだけ

uv、Git、pytest、Ruff、`make check`、GitHub Actions、gitleaks。

mypy、pip-audit、pre-commit、Renovate、actionlint は**あえて入れていません**。
必要になった時点で足せます。最初から全部入れると、何が中心なのかが分からなくなります。

---

## PART 5 の演習（5.6）

わざと壊して、止まることを確認してください。**設定を書いただけでは、効いているか分かりません。**

```bash
git switch -c break-test

# 1. 書式を崩す
#    どれかの .py のインデントや空行を適当に変える
make check          # ruff format --check で落ちる

# 2. 必ず落ちるテストを足す
echo 'def test_broken(): assert False' >> tests/test_health.py
make check          # pytest で落ちる

# 3. .env をコミットしようとする
echo 'API_KEY=dummy' > .env
git add .
git status          # .env がステージに載らないことを確認

# 4. 壊れたままプルリクエストを出す
git commit -am "wip"
git push -u origin break-test
# → CIが赤くなり、マージできないことを確認
```

終わったらブランチを捨ててください。

```bash
git switch main
git branch -D break-test
rm -f .env
```

---

## よくあるつまずき

| 症状 | 原因 |
|---|---|
| `make: command not found` | Windowsの場合。WSL、Git Bash、またはDev Containerを使う |
| `uv: command not found` | uv が未インストール。`curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| import が解決しない | `make install` を実行していない。`pyproject.toml` の `pythonpath` も確認 |
| CIだけ落ちる | 手元と依存が違う。`uv.lock` をコミットしているか確認 |
| gitleaks が失敗する | privateリポジトリではライセンスが要る場合がある。CIのその行を外してよい |
