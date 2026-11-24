<!-- 生成: tools/build.py。手で編集しない。 -->

# STATUS

整備の状況。件数、確認の状態の内訳、未解決の一覧を、正本から生成している。

## 件数

### 到達目標

| 大分類 | 件数 |
|---|---|
| I | 76 |
| II | 151 |
| III | 41 |
| IV | 44 |
| V | 753 |
| VI | 96 |
| VII | 15 |
| VIII | 16 |
| IX | 6 |
| 計（Ⅰ〜Ⅸ） | 1198 |
| MCC plus | 267 |

### ノード

| 種類 | 件数 |
|---|---|
| content | 627 |
| goal | 1465 |
| field | 47 |
| area | 64 |
| category | 9 |

### 関係

| 種類 | 件数 | 指し先の数 | 未解決の指し先 |
|---|---|---|---|
| common-goal | 8 | 8 | 0 |
| composite-required | 229 | 229 | 75 |
| curriculum-guideline | 223 | 336 | 0 |
| external-standard（ABET-JABEE-IEA） | 7 | 62 | 5 |
| external-standard（CDIO） | 22 | 83 | 8 |
| mccplus-correspondence | 267 | 139 | 0 |

### 散文と図

- 節: 67
- 図: 21

- 誤記・表記ゆれの記録（data/mcc2023/errata.yaml）: 11

## 確認の状態の内訳

machine は原文が該当ページの抽出テキストに含まれることを機械で確かめた状態、image はページ画像と突き合わせた状態、human は人が原本と見比べた状態（設計 7.1）。

| 対象 | machine | image | human |
|---|---|---|---|
| ノード | 2157 | 55 | 0 |
| 関係 | 584 | 172 | 0 |
| 散文・図 | 66 | 22 | 0 |
| 未分類の表 | 0 | 1 | 0 |

### 画像照合の対象（設計 7.2）

| 種類 | 件数 |
|---|---|
| page-top-row | 111 |
| committee | 1 |
| abet | 7 |
| cdio | 22 |
| unresolved | 103 |
| figure | 21 |

## 未解決の一覧

解決できなかった参照と、種類を判定できず取り込まなかった表。原文は正本に残している。キーは「レコード ID#指し先の番号」。

| キー | 理由 |
|---|---|
| `mcc2023:rel:composite:1-001#0` | mcc2023:V-A-1 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:1-004#0` | mcc2023:V-A-2 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:1-006#0` | mcc2023:V-A-2 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:1-031#0` | 同じ文の到達目標が 2 件ある |
| `mcc2023:rel:composite:1-031#area` | コード VI-A の名称は「機械系分野」で、参照の名称「機械系」と食い違う |
| `mcc2023:rel:composite:1-032#0` | 同じ文の到達目標が 2 件ある |
| `mcc2023:rel:composite:1-032#area` | コード VI-A の名称は「機械系分野」で、参照の名称「機械系」と食い違う |
| `mcc2023:rel:composite:1-033#area` | コード VI-A の名称は「機械系分野」で、参照の名称「機械系」と食い違う |
| `mcc2023:rel:composite:2-019#0` | mcc2023:V-B-3 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:2-046#0` | 同じ文の到達目標が 2 件ある |
| `mcc2023:rel:composite:2-046#area` | コード VI-B の名称は「材料系分野」で、参照の名称「材料系」と食い違う |
| `mcc2023:rel:composite:2-047#area` | コード VI-B の名称は「材料系分野」で、参照の名称「材料系」と食い違う |
| `mcc2023:rel:composite:2-048#area` | コード VI-B の名称は「材料系分野」で、参照の名称「材料系」と食い違う |
| `mcc2023:rel:composite:2-049#area` | コード VI-B の名称は「材料系分野」で、参照の名称「材料系」と食い違う |
| `mcc2023:rel:composite:3-022#area` | コード VI-C の名称は「電気・電子系分野」で、参照の名称「電気・電子系」と食い違う |
| `mcc2023:rel:composite:3-023#area` | コード VI-C の名称は「電気・電子系分野」で、参照の名称「電気・電子系」と食い違う |
| `mcc2023:rel:composite:3-024#area` | コード VI-C の名称は「電気・電子系分野」で、参照の名称「電気・電子系」と食い違う |
| `mcc2023:rel:composite:4-004#0` | mcc2023:V-D-1 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:4-012#0` | mcc2023:V-D-3 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:4-021#area` | コード VI-D の名称は「情報系分野」で、参照の名称「情報系」と食い違う |
| `mcc2023:rel:composite:4-022#0` | 同じ文の到達目標がない |
| `mcc2023:rel:composite:4-022#area` | コード VI-D の名称は「情報系分野」で、参照の名称「情報系」と食い違う |
| `mcc2023:rel:composite:5-001#0` | mcc2023:V-E-1 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:5-002#0` | mcc2023:V-E-1 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:5-003#0` | mcc2023:V-E-1 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:5-004#0` | mcc2023:V-E-2 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:5-005#0` | mcc2023:V-E-2 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:5-006#0` | mcc2023:V-E-3 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:5-007#0` | mcc2023:V-E-3 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:5-008#0` | mcc2023:V-E-3 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:5-009#0` | mcc2023:V-E-4 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:5-010#0` | mcc2023:V-E-4 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:5-011#0` | mcc2023:V-E-4 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:5-012#0` | mcc2023:V-E-4 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:5-013#0` | mcc2023:V-E-4 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:5-014#0` | mcc2023:V-E-4 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:5-015#0` | mcc2023:V-E-4 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:5-016#0` | mcc2023:V-E-5 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:5-017#0` | mcc2023:V-E-5 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:5-018#0` | mcc2023:V-E-6 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:5-019#0` | mcc2023:V-E-6 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:5-020#0` | mcc2023:V-E-6 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:5-021#0` | mcc2023:V-E-7 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:5-022#0` | mcc2023:V-E-7 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:5-023#0` | mcc2023:V-E-7 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:5-024#0` | mcc2023:V-E-7 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:5-025#0` | mcc2023:V-E-7 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:5-026#0` | 同じ文の到達目標がない |
| `mcc2023:rel:composite:5-026#area` | コード VI-E の名称は「化学・生物系分野」で、参照の名称「化学・生物系」と食い違う |
| `mcc2023:rel:composite:5-027#0` | 同じ文の到達目標がない |
| `mcc2023:rel:composite:5-027#area` | コード VI-E の名称は「化学・生物系分野」で、参照の名称「化学・生物系」と食い違う |
| `mcc2023:rel:composite:5-028#0` | 同じ文の到達目標がない |
| `mcc2023:rel:composite:5-028#area` | コード VI-E の名称は「化学・生物系分野」で、参照の名称「化学・生物系」と食い違う |
| `mcc2023:rel:composite:5-029#0` | 同じ文の到達目標がない |
| `mcc2023:rel:composite:5-029#area` | コード VI-E の名称は「化学・生物系分野」で、参照の名称「化学・生物系」と食い違う |
| `mcc2023:rel:composite:6-001#0` | mcc2023:V-F-1 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:6-002#0` | mcc2023:V-F-1 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:6-003#0` | mcc2023:V-F-1 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:6-023#0` | mcc2023:V-F-3 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:6-024#0` | mcc2023:V-F-3 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:6-025#0` | mcc2023:V-F-3 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:6-026#0` | mcc2023:V-F-3 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:6-032#0` | mcc2023:V-F-5 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:6-033#0` | mcc2023:V-F-5 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:6-035#0` | mcc2023:V-F-6 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:6-036#0` | mcc2023:V-F-6 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:6-037#0` | mcc2023:V-F-6 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:6-040#0` | mcc2023:V-F-7 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:6-042#0` | mcc2023:V-F-8 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:6-043#0` | mcc2023:V-F-8 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:6-047#0` | mcc2023:V-F-9 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:6-048#0` | 同じ文の到達目標がない |
| `mcc2023:rel:composite:6-048#area` | コード VI-F の名称は「建設系分野」で、参照の名称「建設系」と食い違う |
| `mcc2023:rel:composite:6-049#0` | 同じ文の到達目標がない |
| `mcc2023:rel:composite:6-049#area` | コード VI-F の名称は「建設系分野」で、参照の名称「建設系」と食い違う |
| `mcc2023:rel:composite:6-050#0` | 同じ文の到達目標がない |
| `mcc2023:rel:composite:6-050#area` | コード VI-F の名称は「建設系分野」で、参照の名称「建設系」と食い違う |
| `mcc2023:rel:composite:7-001#0` | mcc2023:V-G-1 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:7-002#0` | mcc2023:V-G-1 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:7-003#0` | mcc2023:V-G-2 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:7-004#0` | mcc2023:V-G-2 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:7-005#0` | mcc2023:V-G-2 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:7-006#0` | mcc2023:V-G-3 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:7-007#0` | mcc2023:V-G-3 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:7-009#0` | mcc2023:V-G-4 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:7-010#0` | mcc2023:V-G-4 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:7-011#0` | mcc2023:V-G-4 の中に同じ文の到達目標が 2 件ある |
| `mcc2023:rel:composite:7-012#0` | mcc2023:V-G-5 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:7-014#0` | mcc2023:V-G-5 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:7-016#0` | mcc2023:V-G-5 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:7-017#0` | mcc2023:V-G-5 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:7-019#0` | mcc2023:V-G-6 の中に同じ文の到達目標がない |
| `mcc2023:rel:composite:7-021#0` | 同じ文の到達目標がない |
| `mcc2023:rel:composite:7-021#area` | コード VI-G の名称は「建築系分野」で、参照の名称「建築系」と食い違う |
| `mcc2023:rel:composite:7-022#0` | 同じ文の到達目標がない |
| `mcc2023:rel:composite:7-022#area` | コード VI-G の名称は「建築系分野」で、参照の名称「建築系」と食い違う |
| `mcc2023:rel:guideline:I-003#content` | mcc2023:I の下に同じ名称の学習内容がない |
| `mcc2023:rel:guideline:I-005#content` | mcc2023:I の下に同じ名称の学習内容がない |
| `mcc2023:rel:guideline:II-A-014#content` | mcc2023:II-A の下に同じ名称の学習内容がない |
| `mcc2023:rel:guideline:II-A-015#content` | mcc2023:II-A の下に同じ名称の学習内容がない |
| `mcc2023:rel:guideline:II-A-025#content` | mcc2023:II-A の下に同じ名称の学習内容がない |
| `mcc2023:rel:guideline:II-A-026#content` | mcc2023:II-A の下に同じ名称の学習内容がない |
| `mcc2023:rel:guideline:II-C-017#content` | mcc2023:II-C の下に同じ名称の学習内容がない |
| `mcc2023:rel:abet:01#7` | コード V の名称は「分野別の専門工学」で、参照の名称「分野別専門工学」と食い違う |
| `mcc2023:rel:abet:02#1` | コード IV-E のノードがない |
| `mcc2023:rel:abet:02#2` | コード V の名称は「分野別の専門工学」で、参照の名称「分野別専門工学」と食い違う |
| `mcc2023:rel:abet:04#3` | コード IV-E のノードがない |
| `mcc2023:rel:abet:07#0` | コード VIII の名称は「基盤的資質・能力」で、参照の名称「態度・志向性」と食い違う |
| `mcc2023:rel:cdio:1.2#1` | コード V の名称は「分野別の専門工学」で、参照の名称「分野別専門工学」と食い違う |
| `mcc2023:rel:cdio:1.3#0` | コード V の名称は「分野別の専門工学」で、参照の名称「分野別専門工学」と食い違う |
| `mcc2023:rel:cdio:2.4#1` | コード VIII の名称は「基盤的資質・能力」で、参照の名称「態度・志向性」と食い違う |
| `mcc2023:rel:cdio:2.5#1` | コード VIII の名称は「基盤的資質・能力」で、参照の名称「態度・志向性」と食い違う |
| `mcc2023:rel:cdio:3.3#1` | コード VIII の名称は「基盤的資質・能力」で、参照の名称「態度・志向性」と食い違う |
| `mcc2023:rel:cdio:4.1#3` | コード VIII の名称は「基盤的資質・能力」で、参照の名称「態度・志向性」と食い違う |
| `mcc2023:rel:cdio:4.2#0` | コード VIII の名称は「基盤的資質・能力」で、参照の名称「態度・志向性」と食い違う |
| `mcc2023:rel:cdio:4.4#0` | コード V の名称は「分野別の専門工学」で、参照の名称「分野別専門工学」と食い違う |
| `mcc2023:unclassified:p055-t0` | ヘッダー行のない 1 行の表で、到達目標の列に箇条書きが入っている。前ページの II-B 物理実験「分野」の到達目標の続きに見えるが、セル内の改行が折り返しではなく箇条書きであり、到達目標の 1 件として取り込めるか判定できない |

## ページ先頭の行

前のページから続く表の 1 行目（設計 6.2）。前の行の続きとして結合したものは、source.pages_pdf に 2 ページ以上を持つ。

| レコード ID | ページ | 前の行の続きか |
|---|---|---|
| `mcc2023:I:06.03` | 50 | いいえ |
| `mcc2023:I:16.01` | 51 | いいえ |
| `mcc2023:II-A:06.05` | 53 | いいえ |
| `mcc2023:II-A:17.04` | 54 | いいえ |
| `mcc2023:II-C:09.02` | 56 | いいえ |
| `mcc2023:II-E:02.03` | 58 | いいえ |
| `mcc2023:III-A:03.02` | 60 | いいえ |
| `mcc2023:III-B:04.01` | 61 | いいえ |
| `mcc2023:IV-B:03.01` | 65 | いいえ |
| `mcc2023:IV-C:01.05` | 67 | いいえ |
| `mcc2023:IV-C:05.02` | 68 | いいえ |
| `mcc2023:V-A-2:05.01` | 71 | いいえ |
| `mcc2023:V-A-3:11.02` | 72 | いいえ |
| `mcc2023:V-A-4:06.01` | 73 | いいえ |
| `mcc2023:V-B-2:08.02` | 77 | いいえ |
| `mcc2023:V-B-7:05.03` | 82 | いいえ |
| `mcc2023:V-B-8:06.01` | 83 | いいえ |
| `mcc2023:V-C-3:02.01` | 86 | いいえ |
| `mcc2023:V-C-7:02.01` | 89 | いいえ |
| `mcc2023:V-D-2:02.01` | 91 | いいえ |
| `mcc2023:V-E-1:06.01` | 96 | いいえ |
| `mcc2023:V-E-4:04.05` | 99 | いいえ |
| `mcc2023:V-E-6:06.03` | 101 | いいえ |
| `mcc2023:V-F-3:11.02` | 105 | いいえ |
| `mcc2023:V-G-2:03.01` | 111 | いいえ |
| `mcc2023:V-G-4:12.01` | 114 | いいえ |
| `mcc2023:V-G-5:03.03` | 115 | いいえ |
| `mcc2023:V-H-1:06.01` | 118 | いいえ |
| `mcc2023:V-H-2:01.05` | 119 | いいえ |
| `mcc2023:V-I-2:01.02` | 121 | はい |
| `mcc2023:V-I-6:02.02` | 125 | いいえ |
| `mcc2023:V-I-7:05.03` | 126 | いいえ |
| `mcc2023:VI-B:04.01` | 128 | いいえ |
| `mcc2023:VI-E:03.03` | 130 | いいえ |
| `mcc2023:VI-F:04.04` | 131 | いいえ |
| `mcc2023:VI-I:07.02` | 134 | いいえ |
| `mcc2023:VII-B:01.03` | 144 | はい |
| `mcc2023:VIII-C:01.01` | 146 | はい |
| `mccplus2023:AI:02.03` | 159 | いいえ |
| `mccplus2023:AI:10.02` | 160 | いいえ |
| `mccplus2023:AI:12.04` | 161 | いいえ |
| `mccplus2023:AI:13.12` | 162 | いいえ |
| `mccplus2023:IOT:02.04` | 175 | いいえ |
| `mccplus2023:IOT:10.02` | 176 | いいえ |
| `mccplus2023:IOT:12.04` | 177 | いいえ |
| `mccplus2023:IOT:20.01` | 178 | いいえ |
| `mccplus2023:ROBOT:02.04` | 169 | いいえ |
| `mccplus2023:ROBOT:10.02` | 170 | いいえ |
| `mccplus2023:ROBOT:19.01` | 171 | いいえ |
| `mccplus2023:ROBOT:33.01` | 172 | いいえ |
| `mccplus2023:ROBOT:41.01` | 173 | いいえ |
| `mccplus2023:SEC:02.02` | 164 | いいえ |
| `mccplus2023:SEC:10.01` | 165 | いいえ |
| `mccplus2023:SEC:11.07` | 166 | いいえ |
| `mccplus2023:SEC:11.19` | 167 | いいえ |
| `mcc2023:rel:composite:1-029` | 136 | いいえ |
| `mcc2023:rel:composite:2-024` | 137 | いいえ |
| `mcc2023:rel:composite:4-003` | 138 | はい |
| `mcc2023:rel:composite:5-005` | 139 | はい |
| `mcc2023:rel:composite:6-004` | 141 | いいえ |
| `mcc2023:rel:composite:6-033` | 141 | はい |
| `mcc2023:rel:composite:7-007` | 142 | はい |
| `mcc2023:rel:guideline:I-008` | 187 | いいえ |
| `mcc2023:rel:guideline:I-018` | 187 | はい |
| `mcc2023:rel:guideline:II-A-010` | 190 | いいえ |
| `mcc2023:rel:guideline:II-A-021` | 190 | はい |
| `mcc2023:rel:guideline:II-C-002` | 191 | はい |
| `mcc2023:rel:guideline:II-C-014` | 192 | はい |
| `mcc2023:rel:guideline:II-C-021` | 193 | はい |
| `mcc2023:rel:guideline:II-E-007` | 194 | はい |
| `mcc2023:rel:guideline:III-A-002` | 195 | はい |
| `mcc2023:rel:guideline:III-A-006` | 196 | はい |
| `mcc2023:rel:guideline:III-A-011` | 197 | はい |
| `mcc2023:rel:guideline:III-A-013` | 197 | はい |
| `mcc2023:rel:guideline:III-A-016` | 197 | はい |
| `mcc2023:rel:guideline:III-B-002` | 200 | はい |
| `mcc2023:rel:guideline:III-B-010` | 201 | はい |
| `mcc2023:rel:guideline:III-B-018` | 201 | はい |
| `mcc2023:rel:guideline:III-B-026` | 203 | はい |
| `mcc2023:rel:guideline:III-C-006` | 205 | はい |
| `mcc2023:rel:guideline:III-C-013` | 205 | はい |
| `mcc2023:rel:guideline:III-C-019` | 205 | はい |
| `mcc2023:rel:guideline:III-C-025` | 205 | はい |
| `mcc2023:rel:guideline:III-C-032` | 205 | はい |
| `mcc2023:rel:guideline:III-C-038` | 205 | はい |
| `mcc2023:rel:guideline:III-C-043` | 211 | はい |
| `mcc2023:rel:guideline:III-C-049` | 212 | はい |
| `mcc2023:rel:guideline:III-C-055` | 212 | はい |
| `mcc2023:rel:guideline:III-C-061` | 214 | はい |
| `mcc2023:rel:guideline:III-C-068` | 214 | はい |
| `mcc2023:rel:guideline:III-C-076` | 214 | はい |
| `mcc2023:rel:guideline:III-C-083` | 214 | はい |
| `mcc2023:rel:guideline:IV-C-002` | 219 | はい |
| `mcc2023:rel:guideline:IV-C-005` | 220 | はい |
| `mcc2023:rel:mccplus:AI:02.03` | 159 | いいえ |
| `mcc2023:rel:mccplus:AI:10.02` | 160 | いいえ |
| `mcc2023:rel:mccplus:AI:12.04` | 161 | いいえ |
| `mcc2023:rel:mccplus:AI:13.12` | 162 | いいえ |
| `mcc2023:rel:mccplus:SEC:02.02` | 164 | いいえ |
| `mcc2023:rel:mccplus:SEC:10.01` | 165 | いいえ |
| `mcc2023:rel:mccplus:SEC:11.07` | 166 | いいえ |
| `mcc2023:rel:mccplus:SEC:11.19` | 167 | いいえ |
| `mcc2023:rel:mccplus:ROBOT:02.04` | 169 | いいえ |
| `mcc2023:rel:mccplus:ROBOT:10.02` | 170 | いいえ |
| `mcc2023:rel:mccplus:ROBOT:19.01` | 171 | いいえ |
| `mcc2023:rel:mccplus:ROBOT:33.01` | 172 | いいえ |
| `mcc2023:rel:mccplus:ROBOT:41.01` | 173 | いいえ |
| `mcc2023:rel:mccplus:IOT:02.04` | 175 | いいえ |
| `mcc2023:rel:mccplus:IOT:10.02` | 176 | いいえ |
| `mcc2023:rel:mccplus:IOT:12.04` | 177 | いいえ |
| `mcc2023:rel:mccplus:IOT:20.01` | 178 | いいえ |

## 原本 PDF を使う検査（手元で実行）

CI は原本の PDF を取得しないので、PDF を使う検査は手元で `uv run python tools/build.py --with-local-checks` を実行して結果を残す。

- 対象の正本: 現在の正本と一致する
- 原本: 7810bf3a68110f2be0336b3cc83dcbcafda698b86abbd34c5bffc237e6cde965

| 検査 | 結果 | 内容 |
|---|---|---|
| source-hash | PASS | sha256 一致 |
| page-coverage | PASS | 234/234 |
| text-in-source | PASS | 3055/3055 records |
