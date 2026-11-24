---
name: mcc-verify-page
description: >-
  正本のレコードを原本のページ画像と突き合わせる（画像照合）。設計 7.2
  の対象（ページ先頭の行、委員名簿、ABET・CDIO、未解決、図の書き起こし）を照合し、 verification-log.yaml に記録するときに使う。
---
# mcc-verify-page

画像照合は、抽出ロジックを見ない照合者（サブエージェント `page-verifier`）に、ページ画像と抽出結果だけを渡して行う。

## 手順

1. 照合のパックを作る（`work/` はコミットしない）

   ```bash
   uv run python tools/verify_pack.py --list
   ```

   ```bash
   uv run python tools/verify_pack.py <バッチ名>
   ```

   `work/verify/<バッチ名>/` に `INSTRUCTIONS.md`、`targets.yaml`、`pages/pNNN.png` ができる。

2. `page-verifier` に、そのディレクトリだけを読ませて照合させる。返答の YAML を `work/verify/<バッチ名>/results.yaml` に保存する
3. 記録する

   ```bash
   uv run python tools/record_verification.py work/verify/<バッチ名>/results.yaml --batch <バッチ名> --date YYYY-MM-DD
   ```

4. 食い違い（mismatch）があれば、抽出器か `config/` を直して `tools/extract_all.py` を再実行し、そのレコードだけを照合し直す

   ```bash
   uv run python tools/verify_pack.py --only <ID,...> --name <新しいバッチ名>
   ```

   一致したら `--fixed <ID,...>` と `--fix-note` を付けて記録する

5. `uv run python tools/extract_all.py` と `uv run python tools/build.py` を実行し、レコードの `verification` を `image` に上げる

## 決まり

- 照合者に抽出ロジック（`tools/`、`config/`）を読ませない
- 判読できない箇所は mismatch にせず、findings に残す
- `image` はエージェントの読み取りに依存する。人が原本と見比べた `human` とは別の状態として扱う
