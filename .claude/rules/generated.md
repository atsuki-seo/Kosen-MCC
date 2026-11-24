---
paths:
  - build/**
---
# 生成物の決まり

- `build/` は `uv run python tools/build.py` の生成物であり、手で編集しない
- 正本を変えたら `tools/build.py` を実行し、生成物をコミットする
- 原本の PDF を使う検査の結果は `uv run python tools/build.py --with-local-checks` で `build/STATUS.md` に残す
