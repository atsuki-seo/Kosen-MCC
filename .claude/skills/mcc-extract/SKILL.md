---
name: mcc-extract
description: 原本 PDF から正本（data/、text/）を作り直す、抽出の誤りを直す、表の種類を判定する、未解決の一覧を処理するときに使う。
---
# mcc-extract

## 手順

1. 原本を取得し、ハッシュを照合する: `uv run python source/fetch.py`
2. 抽出する: `uv run python tools/extract_all.py`
3. 生成物を作り直す: `uv run python tools/build.py --with-local-checks`
4. 検査する: `uv run python tools/check_all.py`

## 抽出器とページ

どのページにどの抽出器を当てるかは `config/pages.yaml` にある。ページ固有の値（続きの行、未分類の表、図の領域、CDIO の境界など）は `config/extract.yaml`、`config/figures.yaml`、`config/prose.yaml` に書く。

| 抽出器 | モジュール |
| --- | --- |
| 到達目標・配慮事項・MCC plus | `tools/mcc/goals.py`、`tools/mcc/relations.py` |
| 学習指導要領・ABET・CDIO | `tools/mcc/part4.py` |
| 散文・図 | `tools/mcc/prose.py` |
| 参照の解決 | `tools/mcc/resolver.py` |

## 表の種類の判定

- 表の種類はヘッダー行（「学習内容／到達目標／…」「学習領域／…」など）で判定する。ヘッダーのない表は、前の表の続きとして列の x 座標で割り当てる
- ヘッダー行で種類を判定できず、続きとしても扱えない表は、自動で取り込まない。`config/extract.yaml` の `unclassified_tables` に理由を書き、`data/mcc2023/unclassified.yaml` に原文のまま残す

## 未解決の一覧の処理

- `build/STATUS.md` の「未解決の一覧」に、解決できなかった参照と未分類の表が出る
- 解決の規則（コードと名称の両方で照合し、食い違えば解決しない）を緩めて解決しない。原本の表記ゆれが原因なら `config/errata.yaml` に記録する
- 抽出の誤りが原因なら、抽出器か `config/` を直して再実行する。`data/` と `text/` を手で直さない
