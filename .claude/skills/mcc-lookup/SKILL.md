---
name: mcc-lookup
description: >-
  国立高専機構「モデルコアカリキュラム」（令和5年版、MCC）の内容を、このリポジトリの正本と生成物から引いて答える。
  到達目標・学習内容・分野の検索、コードから ID を探す、複合融合学科への配慮事項・MCC
  plus・他基準（ABET、JABEE、IEA、CDIO、学習指導要領）との対応、 分野の到達目標の一覧、考え方や定義（散文）を問われたときに使う。
---
# mcc-lookup

モデルコアカリキュラム（令和 5 年 4 月 28 日版、以下「原本」）の内容を引いて答える。専用の検索サーバーはない。ファイルと `rg` で引く。

## 答えの書式

- 原本の記述には、ID と PDF のページ番号を必ず添える。例: `mcc2023:V-D-1:02.03`（PDF 90 ページ）
- 原文はそのまま引用する。要約するときは要約であることを明記する
- 原本の記述と付加情報（`extensions/`）を区別する
- 見つからないときは推測せず「原本に記載なし」と答える
- 確認の状態（`verification`: machine / image / human）を、必要に応じて添える

## 問いの種類ごとの引き方

| 問い | 引く場所 | 例 |
| --- | --- | --- |
| 1. 語で到達目標を探す | `build/goals.jsonl` | `rg '暗号' build/goals.jsonl` |
| 2. コードや名称から ID・階層を探す | `build/tree.md` | `rg 'V-D-1 ' build/tree.md` |
| 3. 関係を引く（配慮事項、MCC plus の対応、他基準、学習指導要領、共通の到達目標） | `build/relations.jsonl` | `rg '"to":|mcc2023:IV-C' build/relations.jsonl` |
| 4. 分野の到達目標を丸ごと読む | `build/by-field/<コード>.md` | `build/by-field/V-D.md` |
| 5. 考え方や定義（散文、図） | `text/mcc2023/sections/*.md`、`text/mcc2023/figures/*.md` | `rg -l '到達水準' text/mcc2023/sections` |

整備の状況（件数、未解決の一覧、確認の状態）は `build/STATUS.md` にある。

### 1. 語で到達目標を探す

`build/goals.jsonl` は到達目標を 1 行 1 件にしたもの。各行に `id`、`text`、上位の階層（`category`、`field`、`area`、`content` の ID と名称）、`supplement`（学習の目安となる項目／キーワード）、`page_pdf` がある。

```bash
rg '暗号' build/goals.jsonl
```

3 列目（`supplement`）は参考で、到達目標そのものは `text`。`supplement.kind` が「キーワード」のものは「必ずしも包含する必要はない」参考である（原本 PDF 48 ページ）。

### 2. コードや名称から ID を探す

`build/tree.md` は全ノードを階層で並べた目次。原本のコードは全角・半角が混在する（`Ⅴ-D`、`V-D`）が、ID は半角に正規化している（`mcc2023:V-D`）。

```bash
rg -n '情報リテラシー' build/tree.md
```

MCC plus の分野コード（`AI`、`SEC`、`ROBOT`、`IOT`）は原本にないので、このリポジトリで定めた（ID は `mccplus2023:AI:01.02` の形）。

### 3. 関係を引く

`build/relations.jsonl` の `type` で種類を区別する。

| `type` | 中身 |
| --- | --- |
| `composite-required` | 複合融合学科/コースにおいて必須となる到達目標（`section` は分野名、`text` は再掲された原文、`consideration` は履修上の配慮） |
| `mccplus-correspondence` | MCC plus の到達目標 → MCC の分野・領域（`raw` が「－」なら対応なし） |
| `external-standard` | ABET・JABEE・IEA（`standard: ABET-JABEE-IEA`）、CDIO（`standard: CDIO`） |
| `curriculum-guideline` | 高等学校学習指導要領（平成 30 年告示）との対照 |
| `common-goal` | 物理実験と化学実験で共通の到達目標 |

指し先は `targets[].id`。`id` が `null` のものは解決できなかった参照で、理由が `reason` にある。解決できなかったものを推測で補わない。

```bash
rg '"type":"composite-required"' build/relations.jsonl | rg '情報系'
```

### 4. 分野を丸ごと読む

`build/by-field/<コード>.md`（例 `V-D.md`、`I.md`、`mccplus-AI.md`）。各分野の説明（【教育領域の到達目標】など）と、学習内容・到達目標・3 列目・ページの表がある。

### 5. 考え方や定義

散文は `text/mcc2023/sections/NNN.md`（先頭に `id`、`title`、`pages_pdf`）。図は `text/mcc2023/figures/fig-PPP-N.md` で、「図の中の文字」は原文、「書き起こし」は原文ではない（このリポジトリで書いた説明）。

```bash
rg -l 'ディプロマポリシー' text/mcc2023/sections
```

## 注意

- 原本の表記ゆれ・誤記は `data/mcc2023/errata.yaml` にある。原文は直していない
- 権威は原本（PDF）である。原本の URL と SHA-256 は `source/SOURCE.yaml` にある
