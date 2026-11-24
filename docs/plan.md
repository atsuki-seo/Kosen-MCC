# kosen-mcc 実装プラン

`docs/design.md` の設計をすべて実装し、`atsuki-seo/kosen-mcc` を公開リポジトリにするまでのプランである。この文書だけを読んだエージェントが、これまでの経緯を知らなくても作業できるように書く。

- 設計と決定の理由: `docs/design.md`（作業の前に必ず全文を読む）
- 試作スクリプト: `tools/prototypes/`（設計時の検証に使ったもの。参考資料であり、本実装で置き換える）

## 1. 完了の定義

次の 2 つを、同じターンの会話に出力した時点で完了とする。

1. `uv run python tools/check_all.py` の出力全体。最終行が `CHECK_ALL: PASS (<n>/<n>)` で、終了コードが 0 である
2. `gh repo view atsuki-seo/kosen-mcc --json visibility,url,defaultBranchRef` の出力。`visibility` が `PUBLIC` である

`/goal` の判定者は、会話に出た内容だけを見る。ファイルは読まず、コマンドも実行しない。そのため、検査の結果は要約せず、コマンドの出力をそのまま会話に出す。

### `/goal` に渡す文

```text
docs/plan.md のフェーズ 0〜9 をすべて実装する。完了の条件は、同じターンに次の 2 つの出力をそのまま表示すること。(1) `uv run python tools/check_all.py` の出力全体で、最終行が `CHECK_ALL: PASS (n/n)`、終了コードが 0。(2) `gh repo view atsuki-seo/kosen-mcc --json visibility,url,defaultBranchRef` の出力で、visibility が PUBLIC。制約: docs/design.md の決定を変えない。data/ と text/ の原文を手で直さない。検査を通すために検査項目を削ったり基準を緩めたりしない。公開への切り替えは、docs/plan.md のフェーズ 9 の確認をユーザーから得てから行う。docs/plan.md の「止まる条件」に当たったら、理由を報告して止まる。
```

回数や時間の上限を付ける場合は、文末に「または 300 ターンで止まる」のように足す。使うモデルは `/goal` とは別に、セッションのモデル選択で指定する。

## 2. 前提

### 2.1 すでに済んでいること

- `~/Documents/kosen-mcc` を git リポジトリとして初期化した（ブランチ `main`、コミットなし）
- リポジトリ内の設定: `user.name` は `atsuki-seo`、`user.email` は `146819854+atsuki-seo@users.noreply.github.com`
- `docs/design.md`、`docs/plan.md`、`tools/prototypes/` を置いた（未コミット）

### 2.2 実行環境（確認済み）

| ツール | 状態 |
| --- | --- |
| Python | 3.15.0。パッケージ管理は `uv` を使う |
| pdfplumber | 0.11.11 で検証した。この版に固定する |
| Node.js | v26.12.1。rulesync は `npx` で実行し、使った版を固定して記録する |
| poppler（`pdftoppm`、`pdftotext`） | あり。ページ画像の生成に使う |
| `gh` | `atsuki-seo` でログイン済み。git の通信は SSH |

### 2.3 設計時に検証済みの事実

- 全 234 ページで、文字化けと外字は 0 件
- 到達目標に数式はない。上付き・下付き文字は PDF 95 ページの 1 か所だけ
- 罫線による表抽出で、到達目標の表の列の対応が保たれる（PDF 90〜91 ページで確認）
- CDIO 対照表は、横罫線から行の帯を求める方式で 22 項目すべてがページ画像と一致した（`tools/prototypes/cdio.py`）
- ABET 対照表は 5 列で 7 行が取れる。IEA の列の空欄は結合セルではなく、原本でも空欄である
- 第 4 部の学習指導要領の対照表は、ほぼ全ページで本文の 99% 以上が 3 列の表として取れる
- rulesync は、`agentsmd`・`claudecode`・`agentsskills` の組み合わせで衝突なく生成できる。`generate --check` は、一致で終了コード 0、食い違いで 1 を返す
- Claude Code 向けには、`postToolUse` が `PostToolUse`、`stop` が `Stop`、permissions の拒否が `Edit(source/**)` の形で `.claude/settings.json` に出力される

### 2.4 設計時に確認できていないこと

実装の中で確かめ、結果を `docs/development.md` か `build/STATUS.md` に記録する。

| 項目 | 確かめるフェーズ |
| --- | --- |
| 原本の利用条件 | 0 |
| ページをまたぐ行の分断が、全部で何か所あるか | 2 |
| 再掲された到達目標が、元の文と一字一句同じか | 4 |
| `Edit(...)` の拒否が、新規作成の Write にも効くか | 7 |
| `rulesync fetch` で `mcc-lookup` を実際に取り込めるか | 9（公開後） |

## 3. 作業の決まり

- `docs/design.md` の決定を変えない。設計と実態が合わない点を見つけたら、設計を黙って変えず、「止まる条件」に従う
- 転記はすべて抽出スクリプトで行う。`data/` と `text/` の原文を手で直さない。抽出結果が誤っている場合は、抽出スクリプトか `config/` を直して再実行する
- 検査を通すために、検査項目を削ったり基準を緩めたりしない
- 解決できない参照や、種類を判定できない表は、捨てずに未解決の一覧へ出す
- コミットはフェーズごとに行う。コミットの前に、`git config user.email` が 2.1 の値であることを確かめる
- リポジトリ内のファイルに、手元の絶対パス（`/Users/` で始まるもの）と、メールアドレスを書かない
- 説明や報告には根拠を添える。確認できていないことを確定した事実として書かない

### 止まる条件

次のどれかに当たったら、作業を止めて理由を報告する。

- 原本の利用条件に、転載や再配布を禁じる記述が見つかった
- 取得した PDF の SHA-256 が `source/SOURCE.yaml` の値と一致しない
- 設計のデータモデルで表現できない構造が原本に見つかった
- 同じ検査が、原因を変えずに 3 回続けて失敗した
- 公開への切り替えの確認を求めた（フェーズ 9）

## 4. フェーズ

各フェーズの「確認」は、その出力を会話に出してから次へ進む。

### フェーズ 0: 土台

1. `source/SOURCE.yaml`（名称、発行者、発行日、URL、SHA-256、ページ数）と取得スクリプトを作る。PDF を取得し、ハッシュ値を照合する
2. `.gitignore`、`pyproject.toml`（`uv`、pdfplumber 0.11.11）、`LICENSE`（MIT）を作る
3. 原本の利用条件を確認する。発行者のサイト（`www.kosen-k.go.jp`）のサイトポリシーや著作権の記載を読み、該当する記述と URL を `docs/development.md` に記録する
4. `docs/development.md` に、環境の準備、コミット設定のやり直し方、検査の実行方法を書く

確認: 取得スクリプトの実行結果（ハッシュ値の一致）と、利用条件について見つけた記述の引用。

### フェーズ 1: スキーマとページ対応表

1. `schema/` に、ノード、到達目標、関係、誤記、画像照合の記録、付加情報の JSON Schema を作る
2. `config/pages.yaml` に、全 234 ページについて、どの抽出器を当てるかを書く。1 ページに複数の抽出器が当たってよい
3. ページ対応表から、どの抽出器にも当たっていないページを出す検査を作る

確認: 抽出器が当たっていないページが 0 であること。

### フェーズ 2: 到達目標の抽出（第 2 部）

1. 到達目標の抽出器と、共通の後処理（設計 6.2）を実装する
2. 情報系（V-D）で先に通し、`data/mcc2023/V-D.yaml` を出力して形を確かめる
3. Ⅰ〜Ⅸ の全分野に広げる。ID を振る
4. 注記（「（化学実験と共通）」など）を `note` に分け、共通の到達目標の関係を出力する
5. ページをまたぐ行の分断を、ページ先頭の行の一覧として出す

確認: 大分類ごとの到達目標の件数と、設計 6.4 の概算との差。種類を判定できなかった表の一覧。

### フェーズ 3: MCC plus と配慮事項

1. MCC plus（4 分野）の到達目標を抽出する。分野コードを定め、`MCC対応` の列を関係として出力する
2. 複合融合学科への配慮事項を抽出する。再掲された文を到達目標の ID に解決する

確認: MCC plus と配慮事項の件数。解決できなかった再掲の件数と一覧。

### フェーズ 4: 第 4 部の対照表

1. 参照の解決器（設計 5.4）を実装する。コードと名称の両方で照合する
2. 学習指導要領の対照表を抽出する。箇条書きを分割し、到達目標の ID に解決する
3. ABET・JABEE・IEA の対照表を抽出する。セル内をラベル（`1.`、`(c)`、`WK1:`、`WA1:`）で分割する
4. CDIO の対照表を抽出する。ページ固有の値は `config/` に書く
5. 見つかった誤記を `errata.yaml` に記録する

確認: 関係の種類ごとの件数。未解決の参照の一覧。ABET が 7 行、CDIO が 22 項目であること。

### フェーズ 5: 散文と図

1. 第 1 部、各章の説明文、第 4 部第 2 章、審議過程・委員名簿を、節ごとの Markdown として `text/mcc2023/` に出力する
2. 表の上にある説明文（「【教育領域の到達目標】」など）を、該当するノードに持たせる
3. 図を画像として切り出し、書き起こしを添える
4. 目次と表紙も対象にする

確認: 全ページの対応検査の結果（234/234）。

### フェーズ 6: 検査、生成、画像照合

1. 機械検査（設計 7.3）をすべて実装する
2. `build/` の生成スクリプトを実装し、`goals.jsonl`、`relations.jsonl`、`tree.md`、`by-field/*.md`、`STATUS.md` を出力する
3. `tools/check_all.py` を実装する（5 節）
4. 画像照合（設計 7.2 の対象すべて）を、`page-verifier` の役割で行う。照合する側には、抽出ロジックを渡さず、ページ画像と抽出結果だけを渡す
5. 照合で見つかった誤りは、抽出スクリプトか `config/` を直して再実行し、照合し直す
6. 照合の記録を `verification-log.yaml` に残し、対象レコードの状態を `image` に上げる

確認: `tools/check_all.py` のうち、rulesync と GitHub に関わらない項目がすべて PASS であること。

### フェーズ 7: エージェント向け設定

1. `rulesync.jsonc` と `.rulesync/`（設計 9）を作る。`skills/mcc-lookup/` を実体にし、`.rulesync/skills/mcc-lookup` からシンボリックリンクを張る
2. hooks のスクリプトを `tools/hooks/` に作る
3. `rulesync generate` を実行し、生成物をコミットの対象にする
4. `mcc-lookup` を使って、設計 8 の表にある 5 種類の問いに実際に答え、ID とページが添えられることを確かめる
5. `source/` への Write と Edit を試し、拒否されることを確かめる。Write が拒否されない場合は、拒否の設定を足す

確認: `rulesync generate --check` の終了コード 0。5 種類の問いへの答え。拒否の試験の結果。

### フェーズ 8: README と CI

1. `README.md` を、設計 10 の 5 節で書く。件数や進み具合を書かない
2. `.github/workflows/ci.yml` を作る。実行するのは、スキーマ検証、ID の重複検査、関係の指し先の検査、生成物の食い違いの検査、`rulesync generate --check`、絶対パスの検査である
3. CI では原本の PDF を取得しない。PDF を使う検査（ページの対応、原文の照合）は手元で実行し、結果を `build/STATUS.md` に残す
4. `docs/plan.md` と `tools/prototypes/` を削除する

確認: `uv run python tools/check_all.py` が、GitHub に関わる項目を除いてすべて PASS であること。

### フェーズ 9: GitHub への作成と公開

外部への送信と公開を伴う。対象、影響、実行内容は次のとおりである。

| 手順 | 実行内容 | 対象と影響 |
| --- | --- | --- |
| 9-1 | `gh repo create atsuki-seo/kosen-mcc --private --source . --remote origin` | GitHub に非公開のリポジトリを作る。この時点では本人にしか見えない |
| 9-2 | `git push -u origin main` | 全コミットを GitHub へ送る。通信は SSH |
| 9-3 | CI の結果を待つ | 送信なし |
| 9-4 | 公開前の検査と報告 | 送信なし |
| 9-5 | ユーザーの確認を待つ | 送信なし |
| 9-6 | `gh repo edit atsuki-seo/kosen-mcc --visibility public --accept-visibility-change-consequences` | リポジトリを公開する。全コミットの履歴が誰からでも見えるようになる。公開した内容は、非公開に戻しても第三者の手元に残りうる |
| 9-7 | 公開後の確認 | 取得のみ |

9-4 で報告する内容:

- 全コミットの作成者とコミッターのメールアドレスの一覧（重複を除く）。2.1 の値だけであること
- リポジトリ内に `/Users/` で始まる絶対パスがないこと
- 追跡しているファイルの一覧に、原本の PDF と照合用の画像が含まれないこと
- 原本の利用条件について、フェーズ 0 で確認した内容
- `build/STATUS.md` の内容（件数、確認の状態の内訳、未解決の一覧）
- CI の結果

9-5 では、上の報告を示したうえで、公開してよいかをユーザーに尋ねて止まる。ユーザーが明示的に了承するまで、9-6 を実行しない。

9-7 で行うこと:

- `gh repo view atsuki-seo/kosen-mcc --json visibility,url,defaultBranchRef` を実行する
- 一時ディレクトリで `rulesync fetch atsuki-seo/kosen-mcc --skills mcc-lookup` を実行し、スキルを取り込めることを確かめる。取り込めない場合は、原因と対処を報告する
- 最後に、1 節の 2 つの出力を同じターンに出す

## 5. `tools/check_all.py`

すべての検査を順に実行し、1 項目 1 行で結果を出す。1 つでも失敗したら終了コード 1 を返す。

```text
PASS source-hash          sha256 一致
PASS page-coverage        234/234
PASS schema               <ファイル数> files
PASS id-unique            <件数> ids
PASS text-in-source       <件数>/<件数> records
PASS relations-target     未解決の指し先 0
PASS unresolved-listed    未解決 <件数> 件はすべて STATUS.md に記載
PASS image-verification   対象 <件数> 件はすべて記録あり
PASS build-up-to-date
PASS rulesync-check
PASS no-absolute-path
PASS commit-identity      <コミット数> commits
CHECK_ALL: PASS (12/12)
```

| 項目 | 合格の条件 |
| --- | --- |
| `source-hash` | 取得した PDF の SHA-256 が `SOURCE.yaml` と一致する |
| `page-coverage` | 全 234 ページが、いずれかのレコードか散文ファイルに対応する |
| `schema` | `data/` と `extensions/` の全ファイルがスキーマに適合する |
| `id-unique` | ID が重複していない |
| `text-in-source` | 全レコードの原文が、該当ページの抽出テキストに含まれる |
| `relations-target` | 関係の指し先の ID がすべて存在する |
| `unresolved-listed` | 未解決の参照が、すべて `build/STATUS.md` に載っている |
| `image-verification` | 設計 7.2 の対象が、すべて `verification-log.yaml` に記録されている |
| `build-up-to-date` | `build/` を作り直しても差分が出ない |
| `rulesync-check` | `rulesync generate --check` が終了コード 0 を返す |
| `no-absolute-path` | 追跡しているファイルに、正規表現 `/Users/[A-Za-z0-9._-]+/` に一致する文字列がない（ユーザー名を含むパスだけを検出し、文書中の「`/Users/` で始まる」という説明には反応しない） |
| `commit-identity` | 全コミットの作成者とコミッターのメールアドレスが 2.1 の値である |

`commit-identity` は公開前に手元で 1 回確かめるための項目であり、CI には入れない。PDF がない環境（CI）では、`source-hash`、`page-coverage`、`text-in-source` を `SKIP` として出し、手元の実行では `SKIP` を認めない。
