---
paths:
  - tools/**
  - config/**
---
# 抽出の決まり

- そのページでしか使えない値（座標、ページ番号、続きの行の指定など）は、コードに埋めず `config/` に書く
- 解決できない参照や、種類を判定できない表は捨てない。原文のまま残し、未解決の一覧（`build/STATUS.md`）に出す
- 参照の解決は `tools/mcc/resolver.py` の共通の解決器で行う。コードと名称の両方で照合し、食い違う場合は解決しない
- 検査を通すために検査項目を削ったり基準を緩めたりしない
- 変更したら `uv run python tools/extract_all.py`、`uv run python tools/build.py`、`uv run python tools/check_all.py` の順に実行する
