"""画像照合（設計 7.2）のパックを作る。

照合する側（page-verifier）には抽出ロジックを渡さず、ページ画像と抽出結果だけを渡す。
このスクリプトは work/verify/<batch>/ に、ページ画像（pages/pNNN.png）と照合の対象（targets.yaml）を置く。
work/ は .gitignore の対象で、コミットしない。

使い方:
  uv run python tools/verify_pack.py --list                 # バッチの一覧
  uv run python tools/verify_pack.py <batch> [<batch> ...]  # パックを作る
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mcc import checks, pdfsrc, yamlio  # noqa: E402
from mcc.paths import WORK  # noqa: E402

INSTRUCTIONS = """\
あなたは page-verifier。原本のページ画像と、そこから抽出した結果（targets.yaml）を突き合わせる。
抽出の方法は知らなくてよい。画像に見える原本と、抽出結果の文字列だけを比べる。

各対象について:
- 抽出結果の文字列が、画像の該当箇所と一字一句同じかを確かめる。改行と空白の違いは無視する。
  全角・半角、句読点、括弧、記号、送り仮名、漢字の違いは食い違いとして扱う
- boundary がある対象は、その行が「前の行とは別の新しい行」か「前のページ最後の行の続き」かの判断が、
  画像の表の罫線と合っているかも確かめる
- 判読できない箇所は mismatch にせず、findings に「判読できない」と書く

返答の最後に、次の形の YAML だけを出す:
results:
  - record_id: <targets.yaml の record_id>
    result: match | mismatch
    findings: <mismatch のときは食い違いの内容を具体的に。match なら空でよい>
"""


def node_fields(n: dict) -> dict:
    if n["type"] == "goal":
        d = {"到達目標": n["text"]}
        if n.get("note"):
            d["注記"] = n["note"]
        if n.get("supplement"):
            d[n["supplement"]["kind"]] = n["supplement"]["raw"]
        return d
    if n["type"] == "content":
        return {"学習内容": n["name"]}
    return {"見出し": n.get("heading_raw"), "名称": n.get("name")}


def rel_fields(r: dict) -> dict:
    t = r["type"]
    if t == "composite-required":
        return {"学習領域": r["area"]["raw"], "必須となる到達目標": r["text"], "履修上の配慮": r["consideration"]}
    if t == "mccplus-correspondence":
        return {"MCC対応": r["raw"]}
    if t == "curriculum-guideline":
        d = {"学習内容": (r["content"] or {}).get("raw") or r.get("content_raw", ""), "MCC側": r["mcc_raw"],
             "高等学校学習指導要領": r["guideline_raw"]}
        return d
    if t == "external-standard":
        d = {k: [f"{i.get('title', '') + ' ' if i.get('title') else ''}{i['text']}" for i in v] for k, v in r["items"].items()}
        d["MCC"] = r["mcc_raw"]
        return d
    if t == "common-goal":
        return {"注記": r["note_raw"]}
    return {}


def goal_context(nodes_by_id, n):
    """到達目標のレコードに、学習内容の名称を添える。"""
    out = node_fields(n)
    if n["type"] == "goal":
        c = nodes_by_id[n["parent"]]
        out = {"学習内容": c["name"] or "（空欄）", **out}
    return out


def batches() -> dict[str, list[dict]]:
    nodes = checks.all_nodes()
    by_id = {n["id"]: n for n in nodes}
    rels = checks.all_relations()
    rel_by_id = {r["id"]: r for r in rels}
    uncl = {t["id"]: t for t in checks.unclassified()}
    targets = checks.image_targets()
    unresolved = dict(checks.unresolved_entries())
    goals = [n for n in nodes if n["type"] == "goal"]
    prev_goal = {g["id"]: goals[i - 1] for i, g in enumerate(goals) if i > 0}

    items: list[dict] = []
    for rid in sorted(targets["page-top-row"]):
        if rid in by_id:
            n = by_id[rid]
            pages = n["source"].get("pages_pdf") or [n["source"]["page_pdf"]]
            split = "pages_pdf" in n["source"]
            top_page = pages[-1] if split else pages[0]
            prev = prev_goal.get(rid)
            items.append({"kind": "page-top-row", "record_id": rid, "pages": sorted({top_page - 1, top_page}),
                          "boundary": ("この行はページをまたいで続く 1 行として、両ページの断片をつないで抽出した"
                                       if split else f"PDF {top_page} ページ先頭の行は、前ページ最後の行とは別の新しい行として抽出した"),
                          "previous_row": goal_context(by_id, prev) if prev and not split else None,
                          "extracted": goal_context(by_id, n)})
        else:
            r = rel_by_id[rid]
            pages = r["source"].get("pages_pdf") or [r["source"]["page_pdf"]]
            items.append({"kind": "page-top-row", "record_id": rid, "pages": sorted(set(pages) | {pages[-1] - 1}),
                          "boundary": "ページ先頭の行。前ページから続く行は、両ページの断片をつないで 1 行として抽出した",
                          "extracted": rel_fields(r)})
    for rid in sorted({k.split("#")[0] for k in unresolved}):
        if rid in uncl:
            t = uncl[rid]
            items.append({"kind": "unresolved", "record_id": rid, "pages": [t["source"]["page_pdf"] - 1, t["source"]["page_pdf"]],
                          "extracted": {"表の行": t["rows"]}, "note": "取り込まなかった表。セルの文字列が原本どおりかを確かめる"})
            continue
        r = rel_by_id[rid]
        pages = r["source"].get("pages_pdf") or [r["source"]["page_pdf"]]
        items.append({"kind": "unresolved", "record_id": rid, "pages": pages, "extracted": rel_fields(r),
                      "note": "参照を解決できなかった行。文字列が原本どおりかを確かめる"})
    for kind in ("abet", "cdio"):
        for rid in sorted(targets[kind]):
            r = rel_by_id[rid]
            items.append({"kind": kind, "record_id": rid, "pages": [r["source"]["page_pdf"]], "extracted": rel_fields(r)})

    for path in checks.prose_files():
        fm, body = checks.front_matter(path)
        if fm["kind"] == "figure" and fm["id"] in targets["figure"]:
            text = body.split("## 書き起こし（原文ではない）")[-1].strip()
            items.append({"kind": "figure", "record_id": fm["id"], "pages": fm["pages_pdf"], "figure_image": fm["image"],
                          "extracted": {"図の題": fm["title"], "書き起こし": text},
                          "note": "書き起こしは原文ではなく、図の構成の説明。図にないことを書いていないか、"
                                  "位置・矢印の向き・つながりの説明が図と合っているか、引用した文字が図の表記どおりかを確かめる"})
        elif fm["id"] in targets["committee"]:
            items.append({"kind": "committee", "record_id": fm["id"], "pages": fm["pages_pdf"],
                          "extracted": {"本文": body.strip()},
                          "note": "審議過程と委員名簿。行の配置は全角空白で近似している。氏名・所属・役職・期間・日付の文字を一字一句確かめる"})

    def pick(f):
        return [i for i in items if f(i)]

    out = {
        "b1-top-49-100": pick(lambda i: i["kind"] == "page-top-row" and max(i["pages"]) <= 100),
        "b2-top-101-149": pick(lambda i: i["kind"] == "page-top-row" and 100 < max(i["pages"]) <= 149),
        "b3-composite-unresolved": pick(lambda i: i["kind"] == "unresolved" and ":composite:" in i["record_id"]),
        "b4-top-158-178": pick(lambda i: i["kind"] == "page-top-row" and 149 < max(i["pages"]) <= 178),
        "b6-top-186-221": pick(lambda i: i["kind"] == "page-top-row" and max(i["pages"]) > 178),
        "b7-committee": pick(lambda i: i["kind"] == "committee"),
        "b8-figures": pick(lambda i: i["kind"] == "figure"),
        "b5-part4-tables": pick(lambda i: i["kind"] in ("abet", "cdio") or (i["kind"] == "unresolved" and ":composite:" not in i["record_id"])),
    }
    return out


RESOLUTION = 100


def render(pages: set[int], dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for p in sorted(pages):
        path = dest / f"p{p:03d}.png"
        if path.exists():
            continue
        page = pdfsrc.page(p)
        res = max(RESOLUTION, 130) if page.width > page.height else RESOLUTION
        page.to_image(resolution=res).save(path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("batches", nargs="*")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--only", help="照合し直すレコード ID（カンマ区切り）。--name のバッチに入れる")
    ap.add_argument("--name", help="--only で作るバッチの名前")
    ap.add_argument("--resolution", type=int, default=100, help="ページ画像の解像度（dpi）")
    args = ap.parse_args()
    global RESOLUTION
    RESOLUTION = args.resolution
    all_b = batches()
    if args.only:
        ids = set(args.only.split(","))
        all_b[args.name] = [i for b in list(all_b.values()) for i in b if i["record_id"] in ids]
        args.batches = [args.name]
    if args.list or not args.batches:
        for k, v in all_b.items():
            pages = sorted({p for i in v for p in i["pages"]})
            print(f"{k}: {len(v)} targets, {len(pages)} pages")
        return 0
    for name in args.batches:
        items = all_b[name]
        d = WORK / "verify" / name
        render({p for i in items for p in i["pages"]}, d / "pages")
        for i in items:
            if i.get("figure_image"):
                import shutil

                from mcc.paths import TEXT
                shutil.copy(TEXT / "figures" / i["figure_image"], d / "pages" / i["figure_image"])
        (d / "INSTRUCTIONS.md").write_text(INSTRUCTIONS, encoding="utf-8")
        yamlio.write(d / "targets.yaml", {"batch": name, "targets": items})
        print(f"{name}: {len(items)} targets -> {d.relative_to(WORK.parent)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
