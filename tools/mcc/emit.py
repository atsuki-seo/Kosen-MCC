"""抽出結果を正本の YAML レコードに変換する。"""
from __future__ import annotations

import re

from . import pdfsrc
from .goals import RE_GOAL_NOTE, GoalExtractor, Node
from .textnorm import join_lines, split_items

GENERATED = "生成: tools/extract_all.py（原本 PDF から抽出）。手で編集しない。誤りは抽出スクリプトか config/ を直して再実行する。"


def source(pages: list[int], page_top: bool = False) -> dict:
    pages = sorted(set(pages))
    src = {"page_pdf": pages[0], "page_printed": pdfsrc.printed_page(pages[0])}
    if len(pages) > 1:
        src["pages_pdf"] = pages
    if page_top:
        src["page_top"] = True
    return src


def node_record(n: Node, status: dict[str, str]) -> dict:
    rec: dict = {"id": n.id, "type": n.type, "parent": n.parent}
    d = dict(n.data)
    for key in ("code", "code_defined_by", "name", "note", "group", "name_empty_in_source", "heading_raw",
                "heading_raw_sub", "chapter"):
        if key in d and d[key] is not None:
            rec[key] = d[key]
    if n.description:
        rec["description"] = {"lines": n.description, "pages_pdf": n.description_pages}
    if d.get("notes"):
        rec["notes"] = d["notes"]
    pages = [n.page] + list(d.get("name_pages", []))
    rec["source"] = source(pages)
    rec["verification"] = status.get(n.id, "machine")
    return rec


def goal_record(ex: GoalExtractor, row, status: dict[str, str]) -> dict:
    n = row.node
    text = join_lines("\n".join(row.goal_parts))
    note = None
    if m := RE_GOAL_NOTE.search(text):
        note = m.group(0)
        text = text[: m.start()]
    rec: dict = {"id": n.id, "type": "goal", "parent": n.parent, "text": text}
    if row.supp_parts:
        raw = join_lines("\n".join(row.supp_parts))
        rec["supplement"] = {"kind": row.supp_kind, "raw": raw, "items": split_items(raw)}
    elif row.supp_kind:
        rec["supplement"] = {"kind": row.supp_kind, "raw": "", "items": []}
    rec["note"] = note
    rec["source"] = source(row.pages, row.page_top)
    rec["verification"] = status.get(n.id, "machine")
    return rec
