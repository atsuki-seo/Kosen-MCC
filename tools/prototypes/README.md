# 試作スクリプト

設計時の検証に使ったスクリプトである。参考資料であり、本実装で置き換える。
`docs/plan.md` のフェーズ 8 で削除する。

実行例（引数は原本 PDF のパス）:

```bash
uv run --with pdfplumber==0.11.11 python tools/prototypes/cdio.py source/mcc-2023.pdf
```
