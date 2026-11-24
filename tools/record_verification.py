"""画像照合の結果を data/mcc2023/verification-log.yaml に追記する（設計 7.1）。

使い方:
  uv run python tools/record_verification.py <results.yaml> --batch <name> --date YYYY-MM-DD [--verifier ...]

results.yaml は page-verifier の返答（results: [{record_id, result, findings}]）。
照合の対象の種類とページは、同じバッチの work/verify/<batch>/targets.yaml から取る。
match は result: match、mismatch は result: mismatch-open として記録する（状態は上がらない）。
食い違いを抽出スクリプトか config/ の修正で直し、照合し直して一致したら、--fixed <ID,...> を付けて記録する
（result: mismatch-fixed、findings に直した内容を残す）。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mcc import emit, yamlio  # noqa: E402
from mcc.paths import DATA, WORK  # noqa: E402

LOG = DATA / "verification-log.yaml"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("results", type=Path)
    ap.add_argument("--batch", required=True)
    ap.add_argument("--date", required=True)
    ap.add_argument("--verifier", default="page-verifier（Claude エージェント。ページ画像と抽出結果だけを受け取って照合）")
    ap.add_argument("--fixed", default="", help="食い違いを直したあとの照合で一致したレコード ID（カンマ区切り）")
    ap.add_argument("--fix-note", default="")
    args = ap.parse_args()

    targets = yamlio.load(WORK / "verify" / args.batch / "targets.yaml")["targets"]
    by_id: dict[str, list[dict]] = {}
    for t in targets:  # 同じレコードが複数の種類の対象になることがある（ABET の行が未解決も持つなど）
        by_id.setdefault(t["record_id"], []).append(t)
    results = list({r["record_id"]: r for r in yamlio.load(args.results)["results"]}.values())
    missing = set(by_id) - {r["record_id"] for r in results}
    if missing:
        raise SystemExit(f"結果のない対象があります: {sorted(missing)[:5]}")
    log = yamlio.load(LOG) if LOG.exists() else {"meta": {"source": "mcc2023", "note": "画像照合と人の確認の記録。tools/record_verification.py で追記する"}, "entries": []}
    n = len(log["entries"])

    groups: dict[tuple[str, str], list[dict]] = {}
    for r in results:
        ts = by_id.get(r["record_id"])
        if ts is None:
            raise SystemExit(f"targets.yaml にない record_id: {r['record_id']}")
        res = "match" if r["result"] == "match" else "mismatch-open"
        if r["record_id"] in set(args.fixed.split(",")) and res == "match":
            res = "mismatch-fixed"
        for t in ts:
            groups.setdefault((t["kind"], res), []).append({**r, "pages": t["pages"]})
    for (kind, res), rs in sorted(groups.items()):
        n += 1
        findings = [f"{r['record_id']}: {r['findings']}" for r in rs if r.get("findings")]
        entry = {
            "id": f"vlog-{n:04d}",
            "date": args.date,
            "status": "image",
            "verifier": args.verifier,
            "target": kind,
            "pages_pdf": sorted({p for r in rs for p in r["pages"]}),
            "scope": f"バッチ {args.batch} の {kind} の対象 {len(rs)} 件。抽出結果の文字列と、行の境目の判断をページ画像と突き合わせた",
            "result": res,
            "record_ids": [r["record_id"] for r in rs],
        }
        if findings or args.fix_note:
            entry["findings"] = "\n".join(([args.fix_note] if args.fix_note else []) + findings)
        log["entries"].append(entry)
        print(f"{entry['id']}: {kind} {res} {len(rs)} 件")
    yamlio.write(LOG, log, header="画像照合と人の確認の記録（設計 7.1）。tools/record_verification.py で追記する。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
