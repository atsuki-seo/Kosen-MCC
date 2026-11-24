---
paths:
  - data/**
  - text/**
---
# 正本の扱い

- `data/` と `text/` は `tools/extract_all.py` の生成物であり、手で編集しない。原文を変えない（要約、言い換え、誤記の修正をしない）
- 抽出結果が誤っている場合は、抽出スクリプト（`tools/`）か `config/` を直して `uv run python tools/extract_all.py` を再実行する
- ID は公開の約束事である。一度振った ID を振り直さない
- 原本の表記ゆれと誤記は `config/errata.yaml` に記録し、抽出で `data/mcc2023/errata.yaml` に書き出す。正本の原文は直さない
- 画像照合の記録は `tools/record_verification.py` で `data/mcc2023/verification-log.yaml` に追記する
