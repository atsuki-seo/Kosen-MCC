# 開発の手引き

設計は `docs/design.md` にある。この文書には、手元で作業するための準備と手順を書く。

## 1. 環境の準備

| ツール | 用途 |
| --- | --- |
| Python 3.12 以上と `uv` | 抽出・検査・生成のスクリプト |
| poppler（`pdftoppm`） | 画像照合用のページ画像の生成 |
| Node.js（`npx`） | rulesync の実行 |
| `gh` | GitHub の操作（任意） |

```bash
uv sync
```

```bash
uv run python source/fetch.py
```

`source/fetch.py` は、`source/SOURCE.yaml` の URL から原本の PDF を `source/mcc-2023.pdf` に取得し、SHA-256 を照合する。一致しなければ終了コード 1 で止まる。PDF はコミットしない（`.gitignore`）。

## 2. コミットの設定

コミットの名前とメールアドレスはリポジトリ内の設定で持つ。clone し直すと消えるので、clone のたびに設定し直す。

```bash
git config user.name atsuki-seo
```

```bash
git config user.email 146819854+atsuki-seo@users.noreply.github.com
```

Claude Code では、`git commit` の前に hooks（`tools/hooks/check_commit_email.py`）がこの値を検査する。

## 3. 抽出・生成・検査

```bash
uv run python tools/extract_all.py
```

```bash
uv run python tools/build.py
```

```bash
uv run python tools/check_all.py
```

- `tools/extract_all.py` は、原本の PDF から `data/mcc2023/` と `text/mcc2023/` を作り直す。`data/` と `text/` は手で直さない。誤りは抽出スクリプトか `config/` を直して再実行する
- `tools/build.py` は、正本から `build/` を作り直す
- `tools/check_all.py` は、すべての検査を 1 項目 1 行で出し、1 つでも失敗すれば終了コード 1 を返す。PDF がない環境（CI）では PDF を使う項目を `SKIP` にする。手元では `SKIP` を認めない

画像照合用のページ画像は `work/pages/` に作る（`.gitignore`）。

```bash
uv run python tools/render_pages.py 90 91
```

## 4. 原本の利用条件（フェーズ 0 で確認、2026-11-25）

確認した範囲と、見つかった記述:

| 確認先 | 結果 |
| --- | --- |
| 発行者サイトのトップ、サイトマップ（https://www.kosen-k.go.jp/sitemap）、WordPress のページ一覧（https://www.kosen-k.go.jp/page-sitemap.xml） | 「サイトポリシー」「著作権」「利用規約」に当たるページは見つからなかった。`/sitepolicy`、`/site_policy`、`/policy`、`/copyright`、`/terms` は 404 |
| 各ページのフッター（トップ、サイトマップ、モデルコアカリキュラムのページ https://www.kosen-k.go.jp/nationwide/main_super_kosen） | `Copyright © National Institute of Technology. All rights reserved.` |
| モデルコアカリキュラムのページ本文 | 策定の経緯と PDF へのリンクのみ。転載・再配布の可否についての記述はない |
| 原本 PDF の全 234 ページの抽出テキスト | 「著作」「転載」「複製」「無断」「Copyright」を検索した。原本自身の利用条件についての記述はない（到達目標の中の「著作権法」などの語のみ） |

- 転載や再配布を明示的に禁じる記述は見つからなかった
- 見つかったのは、サイト全体のフッターにある `All rights reserved.` の著作権表示である。これは権利の留保の表示であり、転載や再配布の許諾を与えるものではない
- 以上から、このリポジトリは原本の PDF を再配布せず（取得元の URL とハッシュだけを持つ）、転記したデータにはライセンスを付けず、原本の権利に従うと明記する。転記の公開が許されるかどうかを発行者に確認したわけではない

## 5. 設計時に確認できていなかったことの結果

| 項目 | 結果 | 確かめた方法 |
| --- | --- | --- |
| 原本の利用条件 | 4 節のとおり。転載・再配布を禁じる記述は見つからなかった | 発行者サイトと PDF の本文を確認（2026-11-25） |
| ページをまたぐ行の分断 | 到達目標の表で 3 か所（PDF 122、145、147 ページの先頭。3 列目だけが続く）、学習内容の名称の分断が 2 か所（60、126 ページ）、配慮事項の表で 1 か所（143 ページ。結合セルの続き）、学習指導要領の対照表で 29 ページの先頭（多くは指導要領側の結合セルの続き）と学習内容の名称の分断 1 か所（195 ページ） | 抽出器の続きの処理の回数を数え、ページ先頭の行は画像照合した（verification-log.yaml の page-top-row） |
| 再掲された到達目標が元の文と一字一句同じか | 学習指導要領の対照表の再掲 336 件は、空白と行頭の「･」を除いてすべて元の文と同じ。複合融合学科への配慮事項の再掲 229 件のうち 154 件は同じで、75 件は元の文を縮めた別の文であり、到達目標の ID に解決していない（build/STATUS.md の未解決の一覧） | 参照の解決器の照合結果 |
| `Edit(...)` の拒否が新規作成の Write にも効くか | 効く。`Edit(source/**)` だけの設定で、`source/` への新規作成の Write は「権限設定で拒否されたディレクトリ」として拒否された。既存ファイルの Edit と、`build/` への Edit も拒否された。Write 用の設定は足していない | Claude Code で Write と Edit を試した（2026-11-25、rulesync 43.13.0 の生成物） |
| `rulesync fetch` で `mcc-lookup` を取り込めるか | フェーズ 9（公開後）で確かめる | — |

## 6. 原文の照合（text-in-source）の規則

`tools/check_all.py` の `text-in-source` は、正本の各レコードの原文が、該当ページの抽出テキストに含まれることを確かめる（設計 7.3）。

- 空白と改行を除いて比べる。原文は、抽出テキストに**連続して**含まれなければならない
- 「抽出テキスト」は、同じページを 3 通りに読んだもの（`tools/mcc/pdfsrc.py` の `views`）のいずれかとする
  1. 文字を PDF に書かれた順（コンテンツストリームの順）に並べたもの
  2. 行単位の抽出（上から下、左から右）
  3. 表の列ごとの抽出（表を列の幅で切り出し、上から下に読む）
- 3 通りにする理由: PDF は、1 つのセルの中の複数の行を別々の文字列として書き、ほかの列の文字列と交互に並べることがある（例: PDF 190 ページの「温度と熱（熱分野）仕事と熱（熱分野）エネルギー（熱分野）」は 1 つのセルだが、書かれた順では到達目標の列の文と交互に並ぶ）。この場合、書かれた順では連続しないが、列ごとの抽出では連続する
- ページをまたぐ行は、ページごとに連続した 1 つの断片に分かれ、各断片がそのページの抽出テキストに含まれ、ページの順に並ぶことを求める
- フッターのページ番号（ノンブル）は抽出テキストから除く
- 行の配置を保つ範囲（目次、扉、審議過程・委員名簿）と図の中の文字は、行（図は書かれた順の文字のまとまり）ごとに照合する

## 7. 画像照合

手順はスキル `mcc-verify-page`（`.rulesync/skills/mcc-verify-page/SKILL.md`）にある。照合のパックは `tools/verify_pack.py` で `work/verify/` に作り、結果は `tools/record_verification.py` で `data/mcc2023/verification-log.yaml` に記録する。

## 8. rulesync

AI エージェント向け設定のソースは `.rulesync/` にある。生成物（`AGENTS.md`、`CLAUDE.md`、`.claude/`、`.agents/`）は手で編集しない。使う版は `.rulesync-version` に固定している（43.13.0）。

```bash
npx rulesync@43.13.0 generate
```

```bash
npx rulesync@43.13.0 generate --check
```

`.rulesync/skills/mcc-lookup` は、外部へ配布するスキルの実体 `skills/mcc-lookup/` へのシンボリックリンクである。
