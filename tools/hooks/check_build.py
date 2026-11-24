"""stop: 生成物（build/）が正本と食い違っていないかを検査する（設計 9.5）。

食い違っていれば、終了コード 2 で tools/build.py の実行を促す。stop_hook_active のときは止めない。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mcc import checks  # noqa: E402


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        data = {}
    if data.get("stop_hook_active"):
        return 0
    r = checks.check_build_up_to_date()
    if r.ok:
        return 0
    print("build/ が正本と食い違っている。uv run python tools/build.py を実行する。\n" + "\n".join(r.details[:10]), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
