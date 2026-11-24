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

| 項目 | 結果 |
| --- | --- |
| 原本の利用条件 | 4 節のとおり |
