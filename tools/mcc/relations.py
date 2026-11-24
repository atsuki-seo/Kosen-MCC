"""第 2 部・第 3 部の表から作る関係（設計 5.4）。

- composite-required: 複合融合学科への配慮事項の行 → 到達目標
- mccplus-correspondence: MCC plus の到達目標 → 分野・領域
- common-goal: 「（化学実験と共通）」「（物理実験と共通）」の到達目標どうし
"""
from __future__ import annotations

import re

from .emit import source
from .goals import GoalExtractor
from .resolver import Resolver, norm_text
from .textnorm import join_lines


def composite(ex: GoalExtractor, R: Resolver, status: dict[str, str]) -> list[dict]:
    out = []
    counters: dict[int, int] = {}
    for h in ex.hairyo:
        counters[h.section_no] = counters.get(h.section_no, 0) + 1
        rid = f"mcc2023:rel:composite:{h.section_no}-{counters[h.section_no]:03d}"
        area_raw = join_lines("\n".join(h.area_parts))
        text = join_lines("\n".join(h.goal_parts))
        area = R.ref(area_raw)
        area_r = area[0] if len(area) == 1 else None
        if area_r is not None and area_r.id:
            goal = R.goal_text(text, area_r.id)
        else:
            goal = R.goal_text(text)
        rec = {
            "id": rid,
            "type": "composite-required",
            "section": h.section,
            "area": (area_r.target(area_raw) if area_r else {"raw": area_raw, "id": None, "reason": "参照が複数に分かれる"}),
            "text": text,
            "consideration": join_lines("\n".join(h.consideration_parts)),
            "consideration_shared": h.consideration_inherited,
            "targets": [goal.target(text)],
            "source": source(h.pages + h.origin_pages, h.page_top),
            "verification": status.get(rid, "machine"),
        }
        out.append(rec)
    return out


def mccplus(ex: GoalExtractor, R: Resolver, status: dict[str, str]) -> list[dict]:
    out = []
    for i, row in enumerate(r for r in ex.goal_rows if r.node.id.startswith("mccplus2023:")):
        raw = "\n".join(row.mcc_parts)
        rid = f"mcc2023:rel:mccplus:{row.node.id.split(':', 1)[1]}"
        targets = []
        for item in [x.strip() for x in re.split(r"[\n、]", raw) if x.strip()]:
            if item in ("－", "-", "―"):
                continue
            for r in R.ref(item):
                targets.append(r.target(item))
        out.append({
            "id": rid,
            "type": "mccplus-correspondence",
            "from": row.node.id,
            "raw": join_lines(raw) if "\n" not in raw else raw,
            "targets": targets,
            "source": source(row.pages, row.page_top),
            "verification": status.get(rid, "machine"),
        })
    return out


def common_goals(goal_records: list[dict], status: dict[str, str]) -> list[dict]:
    """注記「（○○と共通）」の到達目標を、相手側の分野で同じ文の到達目標に結ぶ。"""
    out = []
    noted = [g for g in goal_records if g.get("note") and g["note"].endswith("と共通）")]
    names = {"物理実験": "mcc2023:II-B", "化学実験": "mcc2023:II-D"}
    for g in noted:
        m = re.match(r"^（(.+)と共通）$", g["note"])
        other = names.get(m.group(1)) if m else None
        rid = f"mcc2023:rel:common:{g['id'].split(':', 1)[1]}"
        if other is None:
            target = {"raw": g["note"], "id": None, "reason": "注記の分野名に対応する分野がない"}
        else:
            hits = [h for h in goal_records if h["id"].startswith(other + ":") and norm_text(h["text"]) == norm_text(g["text"])]
            if len(hits) == 1:
                target = {"raw": g["note"], "id": hits[0]["id"], "method": "text-exact-in-scope"}
            else:
                target = {"raw": g["note"], "id": None, "reason": f"{other} の中に同じ文の到達目標が {len(hits)} 件ある"}
        out.append({
            "id": rid,
            "type": "common-goal",
            "from": g["id"],
            "note_raw": g["note"],
            "targets": [target],
            "source": g["source"],
            "verification": status.get(rid, "machine"),
        })
    return out
