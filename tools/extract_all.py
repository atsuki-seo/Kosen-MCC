"""原本 PDF から正本（data/mcc2023/、text/mcc2023/）を作り直す。

使い方: uv run python tools/extract_all.py
data/ と text/ は手で直さない。誤りはこのスクリプトが呼ぶ抽出器か config/ を直して再実行する。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mcc import categories, emit, errata, part4, prose, relations, yamlio  # noqa: E402
from mcc.goals import GoalExtractor  # noqa: E402
from mcc.paths import CONFIG, DATA, TEXT  # noqa: E402
from mcc.resolver import Resolver  # noqa: E402


def load_status() -> dict[str, str]:
    """verification-log.yaml から、画像照合・人の確認を済ませたレコードの状態を引く。"""
    path = DATA / "verification-log.yaml"
    if not path.exists():
        return {}
    log = yamlio.load(path) or {}
    rank = {"machine": 0, "image": 1, "human": 2}
    status: dict[str, str] = {}
    for entry in log.get("entries", []):
        if entry.get("result") == "mismatch-open":
            continue
        for rid in entry.get("record_ids", []):
            if rank[entry["status"]] > rank[status.get(rid, "machine")]:
                status[rid] = entry["status"]
    return status


def file_key(node_id: str, node_type: str) -> str:
    prefix, code = node_id.split(":")[:2]
    if prefix == "mccplus2023":
        return f"mccplus/{code}"
    if node_type == "category":
        return "categories"
    parts = code.split("-")
    return "-".join(parts[:2])


def write_meta(extractor: str, key: str, **extra) -> dict:
    return {"source": "mcc2023", "extractor": extractor, "file": key, **extra}


def goal_records(ex: GoalExtractor, status: dict[str, str], catcfg: dict) -> dict[str, list[dict]]:
    goal_by_id = {r.node.id: r for r in ex.goal_rows}
    divisions = categories.divisions(catcfg["division_table"]["page_pdf"])
    levels = categories.levels(catcfg)
    files: dict[str, list[dict]] = {}
    for n in ex.nodes:
        rec = emit.goal_record(ex, goal_by_id[n.id], status) if n.type == "goal" else emit.node_record(n, status)
        if n.type == "category":
            code = n.data["code"]
            div = divisions[code]
            rec = {**{k: v for k, v in rec.items() if k not in ("source", "verification")},
                   "division": {"mcc": div["mcc"], "group": div["group"], "page_pdf": div["page_pdf"]},
                   "level": levels[code], "source": rec["source"], "verification": rec["verification"]}
        files.setdefault(file_key(n.id, n.type), []).append(rec)
    return files


def clean(directory: Path, pattern: str, keep: set[Path]) -> None:
    """前回の生成物のうち、今回作らなかったファイルを消す。"""
    for p in directory.glob(pattern):
        if p not in keep:
            p.unlink()


def main() -> int:
    cfg = yamlio.load(CONFIG / "extract.yaml")
    status = load_status()
    gcfg = cfg["goals"]

    # 到達目標（第 2 部、第 3 部）
    ex = GoalExtractor(gcfg)
    ex.run_pages(*gcfg["part2_pages"], "goals")
    ex.run_pages(*gcfg["plus_pages"], "plus")
    files = goal_records(ex, status, yamlio.load(CONFIG / "categories.yaml"))
    written: set[Path] = set()
    for key, records in files.items():
        path = DATA / f"{key}.yaml"
        extra = {}
        if key.startswith("mccplus/"):
            extra["note"] = ("MCC plus の分野コード（AI、SEC、ROBOT、IOT）は原本にないため、このリポジトリで定めた"
                             "（config/extract.yaml の plus_fields）。原本の見出しは分野ノードの heading_raw にある")
        yamlio.write(path, {"meta": write_meta("goals", key, **extra), "nodes": records}, header=emit.GENERATED)
        written.add(path)
    clean(DATA, "*.yaml", written | {DATA / n for n in ("errata.yaml", "verification-log.yaml", "unclassified.yaml")})
    clean(DATA / "mccplus", "*.yaml", written)
    all_records = [r for recs in files.values() for r in recs]
    goals_only = [r for r in all_records if r["type"] == "goal"]
    print(f"goals: {len(files)} files, {len(goals_only)} goals")

    # 関係（第 2 部・第 3 部）
    R = Resolver(all_records)
    rel_files = {
        "composite-required": relations.composite(ex, R, status),
        "mccplus-correspondence": relations.mccplus(ex, R, status),
        "common-goals": relations.common_goals(goals_only, status),
    }

    # 未分類の表
    unclassified = []
    for u in ex.unclassified:
        uid = f"mcc2023:unclassified:p{u.page:03d}-t{u.table}"
        unclassified.append({"id": uid, "reason": u.reason, "context": u.context, "rows": u.rows,
                             "source": emit.source([u.page]), "verification": status.get(uid, "machine")})
    yamlio.write(DATA / "unclassified.yaml", {"meta": write_meta("goals", "unclassified"), "tables": unclassified},
                 header=emit.GENERATED)

    # 第 4 部の対照表
    gl, gl_notes, gl_title = part4.guideline(cfg["guideline"], R, status)
    rel_files["curriculum-guideline"] = gl
    abet_rows, abet_header = part4.abet(cfg["abet"], R, status)
    rel_files["external-abet-jabee-iea"] = abet_rows
    rel_files["external-cdio"] = part4.cdio(cfg["cdio"], R, status)
    rel_meta = {
        "curriculum-guideline": {"title": gl_title, "notes": gl_notes},
        "external-abet-jabee-iea": {"column_headers": abet_header},
    }

    rel_written = set()
    for key, recs in rel_files.items():
        path = DATA / "relations" / f"{key}.yaml"
        meta = write_meta("relations", f"relations/{key}", **rel_meta.get(key, {}))
        yamlio.write(path, {"meta": meta, "relations": recs}, header=emit.GENERATED)
        rel_written.add(path)
        unresolved = sum(1 for r in recs for t in r["targets"] if t["id"] is None)
        print(f"relations/{key}: {len(recs)} relations, {unresolved} unresolved targets")
    clean(DATA / "relations", "*.yaml", rel_written)

    # 誤記の記録
    entries = errata.build(yamlio.load(CONFIG / "errata.yaml"))
    yamlio.write(DATA / "errata.yaml", {"meta": write_meta("errata", "errata", note="config/errata.yaml の引用を照合して書き出す"),
                                        "entries": entries}, header=emit.GENERATED)
    print(f"errata: {len(entries)} entries")

    # 散文と図
    pcfg = yamlio.load(CONFIG / "prose.yaml")
    fcfg = yamlio.load(CONFIG / "figures.yaml")["figures"]
    sections = prose.ProseExtractor(pcfg, fcfg).run()
    sec_paths, fig_paths = prose.write_all(sections, TEXT, status)
    clean(TEXT / "sections", "*.md", set(sec_paths))
    clean(TEXT / "figures", "*.md", set(fig_paths))
    clean(TEXT / "figures", "*.png", {p.with_suffix(".png") for p in fig_paths})
    print(f"text: {len(sec_paths)} sections, {len(fig_paths)} figures")
    return 0


if __name__ == "__main__":
    sys.exit(main())
