# 付加情報の決まり

- 原本にない情報は `extensions/` に置き、正本と混ぜない
- すべてのレコードに、作成者（`author`）、作成根拠（`basis`）、対象の ID（`targets`）を必須にする（`schema/extension.schema.json`）
- 付加情報から正本への参照は ID だけにする。正本は付加情報を参照しない
