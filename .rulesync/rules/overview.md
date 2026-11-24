---
root: true
targets: ["*"]
description: kosen-mcc の目的、層の一覧、答えるときの決まり
globs: ["**/*"]
---

# kosen-mcc

国立高等専門学校機構「モデルコアカリキュラム」（令和 5 年 4 月 28 日版、以下「原本」）を、AI エージェントが参照しやすい形式で転記したリポジトリ。知識の取り出しと確認のための SSOT（唯一の参照元）として使う。設計と決定の理由は `docs/design.md` にある。

## 層

| パス | 中身 | 位置づけ |
| --- | --- | --- |
| `data/mcc2023/` | ノード（大分類・分野・領域・学習内容・到達目標）、`relations/`、`errata.yaml`、`verification-log.yaml` | 正本 |
| `text/mcc2023/` | 散文の節（`sections/`）、図の画像と書き起こし（`figures/`） | 正本（散文） |
| `extensions/` | 原本にない付加情報 | 別層 |
| `build/` | `goals.jsonl`、`relations.jsonl`、`tree.md`、`by-field/*.md`、`STATUS.md` | 生成物 |
| `schema/`、`config/`、`tools/` | スキーマ、抽出の設定、抽出・検査・生成のスクリプト | 仕組み |
| `source/` | 原本の出典情報と取得スクリプト（PDF 本体はコミットしない） | 権威への参照 |

権威は原本である。リポジトリの内容と原本が食い違う場合は、原本が正しい。

## 答えるときの決まり

- 原本の内容を答えるときは、ID とページ（PDF のページ番号）を必ず添える
- 原本の記述と付加情報（`extensions/`）を区別して示す
- 見つからないときは推測せず「原本に記載なし」と答える
- 引き方はスキル `mcc-lookup` に従う

## 検査

```bash
uv run python tools/check_all.py
```
