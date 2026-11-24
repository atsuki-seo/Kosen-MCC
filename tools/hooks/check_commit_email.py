"""preToolUse（Bash）: git commit の前に、コミットのメールアドレスが決めた noreply アドレスかを検査する（設計 9.5）。

Claude Code の PreToolUse の入力（JSON）を標準入力から読む。食い違えば終了コード 2 で止める。
"""
from __future__ import annotations

import json
import re
import subprocess
import sys

EMAIL = "146819854+atsuki-seo@users.noreply.github.com"


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    command = (data.get("tool_input") or {}).get("command", "")
    if not re.search(r"\bgit\b[^|;&]*\bcommit\b", command):
        return 0
    r = subprocess.run(["git", "config", "user.email"], capture_output=True, text=True)
    email = r.stdout.strip()
    if email != EMAIL:
        print("git の user.email がこのリポジトリで決めた noreply アドレスではない。"
              "docs/development.md の「コミットの設定」に従って設定し直してからコミットする。", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
