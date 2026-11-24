"""すべての検査を順に実行し、1 項目 1 行で結果を出す（plan 5 節）。

使い方:
  uv run python tools/check_all.py                 # 手元。SKIP を認めない
  uv run python tools/check_all.py --ci            # CI。原本 PDF を使う項目は SKIP を認める
  uv run python tools/check_all.py --only schema,id-unique

1 つでも失敗したら終了コード 1 を返す。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mcc import checks  # noqa: E402

CHECKS = [
    ("source-hash", checks.check_source_hash),
    ("page-coverage", checks.check_page_coverage),
    ("schema", checks.check_schema),
    ("id-unique", checks.check_id_unique),
    ("text-in-source", checks.check_text_in_source),
    ("relations-target", checks.check_relations_target),
    ("unresolved-listed", checks.check_unresolved_listed),
    ("image-verification", checks.check_image_verification),
    ("build-up-to-date", checks.check_build_up_to_date),
    ("rulesync-check", checks.check_rulesync),
    ("no-absolute-path", checks.check_no_absolute_path),
    ("commit-identity", checks.check_commit_identity),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ci", action="store_true", help="原本 PDF のない環境。PDF を使う項目の SKIP を認める")
    ap.add_argument("--only", help="実行する項目（カンマ区切り）")
    args = ap.parse_args()
    selected = [c for c in CHECKS if not args.only or c[0] in args.only.split(",")]
    passed = 0
    for name, fn in selected:
        try:
            r = fn()
        except Exception as e:  # 検査そのものが落ちたら FAIL として扱う
            r = checks.Result(name, False, f"検査の実行に失敗: {type(e).__name__}: {e}")
        if r.ok is None:
            status = "SKIP"
            ok = args.ci
        else:
            status = "PASS" if r.ok else "FAIL"
            ok = bool(r.ok)
        passed += ok
        print(f"{status} {name:<20} {r.summary}".rstrip())
        if not ok or status == "SKIP":
            for d in r.details:
                print(f"     {d}")
    total = len(selected)
    print(f"CHECK_ALL: {'PASS' if passed == total else 'FAIL'} ({passed}/{total})")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
