"""postToolUse（Write|Edit）: data/・extensions/ の編集後に、スキーマ検証と ID の重複検査をする（設計 9.5）。

Claude Code の PostToolUse の入力（JSON）を標準入力から読む。失敗すれば終了コード 2 で内容を返す。
data/ は tools/extract_all.py の生成物なので、手で編集したこと自体も知らせる。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mcc import checks  # noqa: E402
from mcc.paths import ROOT  # noqa: E402


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    path = (data.get("tool_input") or {}).get("file_path", "")
    try:
        rel = Path(path).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return 0
    if not (rel.startswith("data/") or rel.startswith("extensions/")):
        return 0
    messages = []
    if rel.startswith("data/"):
        messages.append("data/ は tools/extract_all.py の生成物で、手で編集しない。抽出スクリプトか config/ を直して再実行する。")
    for fn in (checks.check_schema, checks.check_id_unique):
        r = fn()
        if not r.ok:
            messages.append(f"{r.name}: {r.summary}")
            messages += [f"  {d}" for d in r.details[:10]]
    if messages:
        print("\n".join(messages), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
