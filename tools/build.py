"""正本（data/、text/）から build/ を作り直す（設計 8）。

使い方:
  uv run python tools/build.py                       # build/ を作り直す
  uv run python tools/build.py --with-local-checks   # 原本 PDF を使う検査も実行し、結果を STATUS.md に残す
  uv run python tools/build.py --out <dir>           # 別の場所に出力する（検査用）

build/ は手で編集しない。PDF を使う検査の結果は build/local-checks.json に記録され、
--with-local-checks を付けたときだけ更新される。
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mcc import checks, yamlio  # noqa: E402
from mcc.paths import BUILD, DATA, ROOT, TEXT  # noqa: E402

HEADER = "<!-- 生成: tools/build.py。手で編集しない。 -->\n"


def jdump(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=False, separators=(",", ":"))


def fingerprint() -> str:
    """正本（data/ と text/ の Markdown・YAML）の内容のハッシュ。"""
    h = hashlib.sha256()
    files = sorted(list(DATA.rglob("*.yaml")) + list(TEXT.rglob("*.md")))
    for p in files:
        h.update(p.relative_to(ROOT).as_posix().encode())
        h.update(p.read_bytes())
    return h.hexdigest()


def load():
    nodes = checks.all_nodes()
    by_id = {n["id"]: n for n in nodes}
    rels = checks.all_relations()
    return nodes, by_id, rels


def ancestors(n: dict, by_id: dict) -> list[dict]:
    out = []
    p = n["parent"]
    while p:
        out.append(by_id[p])
        p = by_id[p]["parent"]
    return list(reversed(out))


def goals_jsonl(nodes, by_id) -> str:
    lines = []
    for n in nodes:
        if n["type"] != "goal":
            continue
        anc = ancestors(n, by_id)
        rec = {"id": n["id"], "text": n["text"]}
        for a in anc:
            key = {"category": "category", "field": "field", "area": "area", "content": "content"}[a["type"]]
            d = {"id": a["id"], "name": a["name"]}
            if a.get("code"):
                d["code"] = a["code"]
            if a["type"] == "content" and a.get("group"):
                d["group"] = a["group"]["raw"]
            rec[key] = d
        if n.get("supplement"):
            rec["supplement"] = n["supplement"]
        rec["note"] = n.get("note")
        rec["page_pdf"] = n["source"]["page_pdf"]
        rec["page_printed"] = n["source"]["page_printed"]
        rec["verification"] = n["verification"]
        lines.append(jdump(rec))
    return "\n".join(lines) + "\n"


def relations_jsonl(rels) -> str:
    return "\n".join(jdump(r) for r in rels) + "\n"


def tree_md(nodes) -> str:
    out = [HEADER, "# 目次（全ノード）", "",
           "ID と名称を階層で並べたもの。到達目標は本文を示す。ページは PDF のページ番号（括弧内は紙面のページ番号）。", ""]
    depth: dict[str, int] = {}
    for n in nodes:
        d = depth[n["parent"]] + 1 if n["parent"] in depth else 0
        depth[n["id"]] = d
        src = n["source"]
        page = f"p{src['page_pdf']}" + (f"（{src['page_printed']}）" if src.get("page_printed") else "")
        label = n["text"] if n["type"] == "goal" else (n["name"] or "（名称なし）")
        if n["type"] in ("category", "field", "area"):
            label = f"{n['code']} {label}"
        out.append(f"{'  ' * d}- `{n['id']}` {label} — {page}")
    return "\n".join(out) + "\n"


def md_escape(s: str) -> str:
    return (s or "").replace("|", "\\|").replace("\n", " ")


def by_field(nodes, by_id, rels) -> dict[str, str]:
    """分野（大分類 I は大分類）ごとの Markdown。"""
    mcc_of = {r["from"]: r for r in rels if r["type"] == "mccplus-correspondence"}
    groups: dict[str, list[dict]] = collections.OrderedDict()
    for n in nodes:
        if n["type"] == "category" and n["code"] != "I":
            continue
        anc = ancestors(n, by_id) + [n]
        key_node = next((a for a in anc if a["type"] == "field"), None) or anc[0]
        groups.setdefault(key_node["id"], []).append(n)
    out = {}
    for key, ns in groups.items():
        head = by_id[key]
        prefix = "mccplus-" if key.startswith("mccplus2023:") else ""
        fname = f"{prefix}{head['code']}.md"
        lines = [HEADER]
        cat = by_id[head["parent"]] if head.get("parent") else None
        title = f"{head['code']} {head['name']}" if not cat else f"{cat['code']} {cat['name']} ／ {head['code']} {head['name']}"
        if prefix:
            title = f"MCC plus {head['name']}（分野コード {head['code']} はこのリポジトリで定めたもの）"
        lines += [f"# {title}", "", f"- ID: `{head['id']}`", f"- 原本: PDF {head['source']['page_pdf']} ページ", ""]
        table_open = False
        for n in ns:
            if n["type"] in ("category", "field", "area"):
                if n["type"] == "area":
                    lines += ["", f"## {n['code']} {n['name']}", "", f"- ID: `{n['id']}`", ""]
                    table_open = False
                if n.get("description"):
                    lines += ["<details><summary>説明（原文）</summary>", "", *[f"{ln}  " for ln in n["description"]["lines"]], "", "</details>", ""]
                for note in n.get("notes", []):
                    lines += [f"- {note['label']}: {note['text']}"]
                continue
            if n["type"] == "content":
                continue
            if not table_open:
                kind = (n.get("supplement") or {}).get("kind")
                cols = ["ID", "学習内容", "到達目標"] + ([kind] if kind else []) + (["MCC対応"] if prefix else []) + ["ページ"]
                lines += ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
                table_open = True
            content = by_id[n["parent"]]
            cname = content["name"] or "（空欄）"
            if content.get("group"):
                cname = f"{content['group']['raw']} {cname}"
            row = [f"`{n['id']}`", md_escape(cname), md_escape(n["text"] + (n["note"] or ""))]
            if n.get("supplement"):
                row.append(md_escape(n["supplement"]["raw"]))
            if prefix:
                row.append(md_escape(mcc_of[n["id"]]["raw"]) if n["id"] in mcc_of else "")
            row.append(str(n["source"]["page_pdf"]))
            lines.append("| " + " | ".join(row) + " |")
        out[fname] = "\n".join(lines) + "\n"
    return out


def status_md(nodes, rels, local: dict | None) -> str:
    out = [HEADER, "# STATUS", "", "整備の状況。件数、確認の状態の内訳、未解決の一覧を、正本から生成している。", ""]
    # 件数
    c = collections.Counter()
    for n in nodes:
        key = "mccplus2023" if n["id"].startswith("mccplus2023:") else n["id"].split(":")[1].split("-")[0]
        if n["type"] == "goal":
            c[key] += 1
    out += ["## 件数", "", "### 到達目標", "", "| 大分類 | 件数 |", "|---|---|"]
    for k in ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"]:
        out.append(f"| {k} | {c[k]} |")
    out.append(f"| 計（Ⅰ〜Ⅸ） | {sum(c[k] for k in ['I','II','III','IV','V','VI','VII','VIII','IX'])} |")
    out.append(f"| MCC plus | {c['mccplus2023']} |")
    out += ["", "### ノード", "", "| 種類 | 件数 |", "|---|---|"]
    for t, cnt in collections.Counter(n["type"] for n in nodes).items():
        out.append(f"| {t} | {cnt} |")
    out += ["", "### 関係", "", "| 種類 | 件数 | 指し先の数 | 未解決の指し先 |", "|---|---|---|---|"]
    rc = collections.defaultdict(lambda: [0, 0, 0])
    for r in rels:
        k = r["type"] + (f"（{r['standard']}）" if r.get("standard") else "")
        rc[k][0] += 1
        rc[k][1] += len(r["targets"])
        rc[k][2] += sum(1 for t in r["targets"] if t["id"] is None)
    for k, (a, b, u) in rc.items():
        out.append(f"| {k} | {a} | {b} | {u} |")
    prose = checks.prose_files()
    kinds = collections.Counter(checks.front_matter(p)[0]["kind"] for p in prose)
    out += ["", "### 散文と図", "", f"- 節: {kinds['section']}", f"- 図: {kinds['figure']}", ""]
    errata = (yamlio.load(DATA / "errata.yaml") or {}).get("entries", []) if (DATA / "errata.yaml").exists() else []
    out += [f"- 誤記・表記ゆれの記録（data/mcc2023/errata.yaml）: {len(errata)}", ""]

    # 確認の状態
    vs = collections.Counter(n["verification"] for n in nodes)
    vr = collections.Counter(r["verification"] for r in rels)
    vp = collections.Counter(checks.front_matter(p)[0]["verification"] for p in prose)
    vu = collections.Counter(t["verification"] for t in checks.unclassified())
    out += ["## 確認の状態の内訳", "",
            "machine は原文が該当ページの抽出テキストに含まれることを機械で確かめた状態、image はページ画像と突き合わせた状態、human は人が原本と見比べた状態（設計 7.1）。", "",
            "| 対象 | machine | image | human |", "|---|---|---|---|"]
    for label, cnt in (("ノード", vs), ("関係", vr), ("散文・図", vp), ("未分類の表", vu)):
        out.append(f"| {label} | {cnt['machine']} | {cnt['image']} | {cnt['human']} |")
    targets = checks.image_targets()
    out += ["", "### 画像照合の対象（設計 7.2）", "", "| 種類 | 件数 |", "|---|---|"]
    for k, ids in targets.items():
        out.append(f"| {k} | {len(ids)} |")

    # 未解決
    unresolved = checks.unresolved_entries()
    out += ["", "## 未解決の一覧", "",
            "解決できなかった参照と、種類を判定できず取り込まなかった表。原文は正本に残している。キーは「レコード ID#指し先の番号」。", "",
            "| キー | 理由 |", "|---|---|"]
    for k, reason in unresolved:
        out.append(f"| `{k}` | {md_escape(reason)} |")

    # ページ先頭の行
    tops = [n for n in nodes if n["source"].get("page_top")] + [r for r in rels if r["source"].get("page_top")]
    out += ["", "## ページ先頭の行", "",
            "前のページから続く表の 1 行目（設計 6.2）。前の行の続きとして結合したものは、source.pages_pdf に 2 ページ以上を持つ。", "",
            "| レコード ID | ページ | 前の行の続きか |", "|---|---|---|"]
    for r in tops:
        src = r["source"]
        out.append(f"| `{r['id']}` | {src['page_pdf']} | {'はい' if 'pages_pdf' in src else 'いいえ'} |")

    # 手元の検査
    fp = fingerprint()
    out += ["", "## 原本 PDF を使う検査（手元で実行）", "",
            "CI は原本の PDF を取得しないので、PDF を使う検査は手元で `uv run python tools/build.py --with-local-checks` を実行して結果を残す。", ""]
    if local is None:
        out.append("記録なし。")
    else:
        current = "現在の正本と一致する" if local["fingerprint"] == fp else "記録の後に正本が変わっている（再実行が必要）"
        out += [f"- 対象の正本: {current}", f"- 原本: {local['source_sha256']}", ""]
        out += ["| 検査 | 結果 | 内容 |", "|---|---|---|"]
        for r in local["results"]:
            out.append(f"| {r['name']} | {'PASS' if r['ok'] else 'FAIL'} | {md_escape(r['summary'])} |")
    return "\n".join(out) + "\n"


def run_local_checks() -> dict:
    from mcc import pdfsrc

    if not pdfsrc.available():
        raise SystemExit("原本の PDF がないため、--with-local-checks を実行できない（uv run python source/fetch.py）")
    results = [checks.check_source_hash(), checks.check_page_coverage(), checks.check_text_in_source()]
    return {"fingerprint": fingerprint(), "source_sha256": pdfsrc.meta()["sha256"],
            "results": [{"name": r.name, "ok": bool(r.ok), "summary": r.summary} for r in results]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=BUILD)
    ap.add_argument("--with-local-checks", action="store_true")
    args = ap.parse_args()
    out: Path = args.out
    local_path = BUILD / "local-checks.json"
    if args.with_local_checks:
        local = run_local_checks()
        BUILD.mkdir(exist_ok=True)
        local_path.write_text(json.dumps(local, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    local = json.loads(local_path.read_text(encoding="utf-8")) if local_path.exists() else None

    nodes, by_id, rels = load()
    files = {
        "goals.jsonl": goals_jsonl(nodes, by_id),
        "relations.jsonl": relations_jsonl(rels),
        "tree.md": tree_md(nodes),
        "STATUS.md": status_md(nodes, rels, local),
    }
    for name, text in by_field(nodes, by_id, rels).items():
        files[f"by-field/{name}"] = text
    if local is not None:
        files["local-checks.json"] = json.dumps(local, ensure_ascii=False, indent=2) + "\n"
    if out.exists() and out != BUILD:
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    keep = set()
    for name, text in files.items():
        p = out / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        keep.add(p)
    for p in out.rglob("*"):
        if p.is_file() and p not in keep:
            p.unlink()
    print(f"build: {len(files)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
