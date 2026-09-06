# 動作確認ガイド

教材に載せたコードのうち、**この環境では確認できなかったもの**を、
実際に動かして確かめるためのスクリプト集です。

作成した環境はネットワークが無効で、`fastapi`、`pytest`、`ruff`、`ollama`、
`langchain`、`langgraph`、`mcp` をインストールできませんでした。
そのため、これらを使うコードは**構文チェックまでしか行えていません。**

このフォルダのスクリプトを上から順に実行すれば、どこが動いてどこが動かないかが分かります。

---

## 実行の順番

```
python3 01_check_env.py                        # まずこれ
./02_template_check.sh <テンプレートのパス>     # PART 5-6
python3 03_ollama_shape.py                     # PART 7.1 の前提
python3 04_agent_min.py                        # PART 7.1
python3 05_langchain_agent.py                  # PART 7.2
python3 06_langgraph_flow.py                   # PART 7.3-7.4
python3 07_mcp_server.py --selftest            # PART 7.5
python3 08_mcp_client.py                       # PART 7.5
python3 09_video_pipeline.py                   # PART 8
```

先に進む前に、各スクリプトの最後の行（`=>` で始まる行）を確認してください。

---

## ファイルごとの説明

### `01_check_env.py`

**何をするか**　Python のバージョン、コマンド（uv / git / make / ollama / ffmpeg / gh）、
パッケージ（fastapi / pytest / langgraph / mcp など）の有無を一覧にします。

**この環境での結果**　実行済み。jinja2 と PIL 以外はすべて「なし」でした。
それが、以下の多くを確認できなかった理由です。

**確認してほしいこと**　「足りないもの」に何が並ぶか。ここが埋まらないと他は動きません。

---

### `02_template_check.sh`

**何をするか**　`vibe-order-template` に対して、依存のインストール、`make check`、
サーバ起動と応答、PART 7 用ブランチの作成までを通しで実行します。

**この環境での結果**　**未実行。**`uv sync` がネットワークを必要とするためです。

**確認してほしいこと**

| 段階 | 期待 |
|---|---|
| 1. `make install` | 依存が入る。`uv.lock` が生成される |
| 2. `make check` | **通る。**ruff format / ruff check / pytest がすべて成功 |
| 3. 起動と応答 | `/api/health` が `{"status":"ok"}` を返し、トップ画面が開く |
| 4. challenge ブランチ | **落ちる。**ここだけは失敗が正解です |

**ここが通れば、PART 5 と PART 6 の土台は確定します。**逆に、ここが通らないまま
授業を始めると、全員が同じ場所で止まります。

**つまずきやすい点**

- Windows で `make` がない。WSL、Git Bash、Dev Container のいずれかを使う
- `pyproject.toml` の `pythonpath = ["src"]` が効かず import が解決しない
- 3の段階でポート 8765 が使用中

---

### `03_ollama_shape.py`

**何をするか**　`ollama.chat()` の応答が、どんな型で、どのキーに
ツール呼び出しが入っているかを表示します。

**なぜ必要か**　**教材で唯一、ライブラリのバージョン差で壊れうる箇所です。**
`ollama` パッケージは、応答が辞書だったり Pydantic オブジェクトだったりします。
教材のコードは `dict()` で包んで揃えていますが、それが効くかは実物で見ないと分かりません。

**この環境での結果**　**未実行。**`ollama` パッケージがなく、モデルも動いていません。

**確認してほしいこと**

- `dict(msg)` が成功するか
- `tool_calls` が 1 件以上返るか
- `function` の `name` と `arguments` が取り出せるか

**ツール呼び出しが 0 件だった場合**、モデルが tools に対応していません。
Ollama のライブラリ一覧で対応を確認し、対応しているモデルに変えてください。
これは教材の誤りではなく、モデル選択の問題です。

---

### `04_agent_min.py`

**何をするか**　PART 7.1 の最小 Agent を、単体で動かします。
`/tmp` に使い捨てのプロジェクト（わざと壊した `add` 関数と、そのテスト）を作り、
Agent に直させます。**教材のリポジトリには触りません。**

**この環境での結果**　**部分的に実行。**Agent 本体は動かせていませんが、
安全策の 2 つは確認済みです。

- `_safe_path` がプロジェクト外（`../../etc/passwd`）を弾く … **確認済み**
- `write_file` が `.py` 以外を弾く … **確認済み**

**確認してほしいこと**

- ループが回り、`read_file` → `write_file` → `run_tests` の順にツールが呼ばれるか
- 最後に `add` が直り、テストが通るか

**通らなかった場合**、モデルを大きくして再試行してください。4B では厳しいはずです。
27B でも数回に 1 回は失敗します。**それ自体が PART 7.3 の「停止条件」の必要性を示します。**

---

### `05_langchain_agent.py`

**何をするか**　使える Agent 生成関数を自動で探し、見つかった名前を報告します。
そのうえで、`bind_tools` だけの場合（ループが回らない）と、
Agent を作った場合（ループが回る）の違いを実際に見せます。

**なぜ必要か**　**LangChain の Agent API は名前が変わり続けている部分です。**
教材には `create_agent` と書いていますが、バージョンによっては存在しません。

探す順番は次のとおりです。

1. `from langchain.agents import create_agent`
2. `from langgraph.prebuilt import create_react_agent`
3. `from langchain.agents import create_tool_calling_agent`

**この環境での結果**　**未実行。**

**確認してほしいこと**

- どれが使えたか。教材の 7.2 のコードを、その名前に合わせて直してください
- `17 + 25` の答えとして `42` が返るか
- 3 つとも見つからなかった場合は、使用中のバージョンのドキュメントを確認

---

### `06_langgraph_flow.py`

**何をするか**　PART 7.3〜7.4 のグラフを、**LLM なしで**検証します。
`implement` を偽物に差し替え、状態、分岐、再試行の上限、`interrupt`、
`Command(resume=...)` による再開だけを見ます。

**なぜLLMを外すか**　モデルの出来不出来と、LangGraph の API の問題を切り分けるためです。
ここが通れば、あとはモデルを繋ぐだけです。

**この環境での結果**　**未実行。**`langgraph` がありません。

**確認してほしいこと**

| 項目 | 期待 |
|---|---|
| `interrupt` で止まるか | 戻り値に `__interrupt__` が入る |
| `revise` で `implement` に戻るか | ログに `implement#2` が出る |
| 指摘が次に渡るか | ログに「指摘を受け取った」が出る |
| 3 回失敗で `give_up` に落ちるか | ログに `give_up` が出る |

4 つすべてが期待どおりなら、教材の 7.3〜7.4 はそのまま使えます。

---

### `07_mcp_server.py` と `data/kitchen_board.json`

**何をするか**　PART 7.5 の厨房ボード MCP サーバです。教材と同じものです。
`--selftest` を付けると、MCP を使わずにデータが読めるかだけ確認します。

**この環境での結果**　`--selftest` は**実行済み。**3 件のデータが読め、
アレルギー警告の付いた注文（#31 Prawn Curry）も正しく表示されました。
MCP サーバとしての起動は**未実行**（`mcp` パッケージがないため）。

---

### `08_mcp_client.py`

**何をするか**　`07_mcp_server.py` を子プロセスとして起動し、
**Cline を使わずに** ツール一覧の取得と `get_kitchen_board` の呼び出しを行います。

**なぜ必要か**　Cline で見えないとき、サーバ側の問題なのか Cline 側の設定なのかを
切り分けられます。**これが通ればサーバは正しく作れています。**

**この環境での結果**　**未実行。**

**確認してほしいこと**

- ツール一覧に `get_kitchen_board` が出るか
- 呼び出しで 3 件の注文が返るか
- `data/kitchen_board.json` を書き換えて再実行し、**返る内容が変わるか**

最後の項目が PART 7.5 の要点です。変われば、Agent は「いまの状況」を
取りに行けています。

---

### `09_video_pipeline.py`

**何をするか**　PART 8 のスターター Notebook の動画部分を、Colab の外で動かします。
スライド生成、字幕、ffmpeg での組み立て、ffprobe での検査まで。

**この環境での結果**　**実行済み。すべて動きました。**

```
フォント: NotoSansCJK-Regular.ttc
字幕の焼き込み: OK
尺       : 70.5 秒
解像度   : 1280
音声     : なし
duration_ok: False
=> 仕込みどおり落ちました
```

日本語のスライド文字と焼き込み字幕が両方出ること、
初期設定で 70.5 秒になって検査に落ちることを、フレーム画像で確認しています。

**確認してほしいこと**　配布先の環境で日本語フォントがあるか。
なければ豆腐（□□□）になります。`apt-get install fonts-noto-cjk` で入ります。

**Notebook 側で未確認なのは LangGraph の部分だけです。**そこは
`06_langgraph_flow.py` で先に確かめてください。同じ API を使っています。

---

## まとめ：確認状況の一覧

| 対象 | 状態 |
|---|---|
| 動画パイプライン（PART 8） | **動作確認済み** |
| 仕込みバグ（PART 7 の金額計算） | **動作確認済み** |
| `_safe_path` / `write_file` の安全策 | **動作確認済み** |
| テンプレートの `repository.py` | **動作確認済み** |
| `.gitignore` が `.env` を弾くか | **動作確認済み** |
| MCP サーバのデータ読み込み | **動作確認済み** |
| ruleset JSON、シェルスクリプト | 構文チェックのみ |
| テンプレートの `make check` | **未確認** → `02` |
| `ollama.chat` の応答形式 | **未確認** → `03` |
| PART 7.1 の Agent ループ | **未確認** → `04` |
| LangChain の `create_agent` | **未確認** → `05` |
| LangGraph の interrupt / resume | **未確認** → `06` |
| MCP の接続 | **未確認** → `07`, `08` |

---

## 見つかったら教材のどこを直すか

| 症状 | 直す場所 |
|---|---|
| `dict(msg)` が失敗する | PART 7.1.2 のループ。`print(reply)` の結果に合わせる |
| `create_agent` が無い | PART 7.2 のimport行と、`agent_executor` の作り方 |
| `interrupt` が止まらない | PART 7.4。LangGraph のバージョンを上げる |
| `Command(resume=...)` の形が違う | PART 7.4 の再開のコード |
| MCP のツールが見えない | PART 7.5.1 の設定 JSON。パスを絶対パスにする |
| `make check` が落ちる | テンプレートの `pyproject.toml`。`pythonpath` と依存を確認 |

どれも**Agent の設計ではなく、ライブラリの都合です。**
教材の本文には、その旨の注記を入れてあります。学生が詰まったときは、
「設計の問題ではない」と先に伝えてください。
