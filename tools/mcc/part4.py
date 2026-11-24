"""第 4 部の対照表の抽出器（学習指導要領、ABET・JABEE・IEA、CDIO）。設計 6.1。"""
from __future__ import annotations

import re

from . import pdfsrc
from .emit import source
from .pdfsrc import Line
from .resolver import Resolver, split_refs
from .textnorm import ROMAN, join_lines, roman

RE_SECTION = re.compile(rf"^({ROMAN}(?:\s*-\s*[A-I])?)\s+\S")
RE_NOTE_START = re.compile(r"^(\*\d|注）)")
NONE_MARKS = ("（該当なし）", "該当なし")


def _col(x0: float, cols: list[float]) -> int:
    return min(range(len(cols)), key=lambda i: abs(cols[i] - x0))


def assign(row, cols: list[float]) -> list[str | None]:
    out: list[str | None] = [None] * len(cols)
    prev = -1
    for c in row:
        idx = _col(c.x0, cols) if c.x0 is not None else prev + 1
        prev = idx
        if idx < len(cols) and c.text is not None:
            out[idx] = c.text if out[idx] is None else out[idx] + "\n" + c.text
    return out


def split_bullets(raw: str) -> list[str]:
    """「･ 」で始まる箇条書きを分ける。箇条書きでなければ全体を 1 件とする。"""
    lines = [ln.strip() for ln in raw.split("\n") if ln.strip()]
    if not any(ln.startswith(("･", "・")) for ln in lines):
        return [join_lines(raw)] if lines else []
    items: list[list[str]] = []
    for ln in lines:
        if ln.startswith(("･", "・")):
            items.append([ln.lstrip("･・").strip()])
        elif items:
            items[-1].append(ln)
        else:
            items.append([ln])
    return [join_lines("\n".join(it)) for it in items]


class GuidelineExtractor:
    def __init__(self, cfg: dict, R: Resolver, status: dict[str, str]):
        self.cfg, self.R, self.status = cfg, R, status
        self.relations: list[dict] = []
        self.notes: list[dict] = []
        self.title: str | None = None
        self.section_raw: str | None = None
        self.section_code: str | None = None
        self.section: dict | None = None
        self.mode: str | None = None
        self.cols: list[float] = []
        self.group: str | None = None
        self.counter: dict[str, int] = {}
        self.cur_content: dict | None = None  # {"raw_parts": [...], "pages": [...]}
        self.cur_goals: str | None = None
        self.cur_guideline: str | None = None
        self.last: dict | None = None
        self.in_note = False

    def new_id(self) -> str:
        n = self.counter.get(self.section_code, 0) + 1
        self.counter[self.section_code] = n
        return f"mcc2023:rel:guideline:{self.section_code}-{n:03d}"

    def line(self, ln: Line) -> None:
        t = ln.text
        if t.startswith("1-2 "):
            self.title = t
            return
        if RE_SECTION.match(roman(t)) and not RE_NOTE_START.match(t):
            self.section_raw = t
            code = re.sub(r"\s*-\s*", "-", RE_SECTION.match(roman(t)).group(1))
            self.section_code = code
            res = self.R.ref(t)
            self.section = res[0].target(t) if len(res) == 1 else {"raw": t, "id": None, "reason": "参照が複数に分かれる"}
            self.group = None
            self.in_note = False
            return
        if t in self.cfg.get("group_labels", []):
            self.group = t
            self.in_note = False
            return
        if RE_NOTE_START.match(t):
            self.notes.append({"section": self.section_raw, "text": t, "page": ln.page})
            self.in_note = True
            return
        if self.in_note:
            self.notes[-1]["text"] += "\n" + t
            return
        raise ValueError(f"p{ln.page}: 扱えない行: {t}")

    def table(self, tb, first_on_page: bool) -> None:
        self.in_note = False
        for ri, row in enumerate(tb.rows):
            texts = [join_lines(c.text) if c.text else "" for c in row]
            if texts[0] == "" and len(texts) > 1 and texts[1] == "モデルコアカリキュラム":
                self.mode = "objective"
                self.cols = [c.x0 for c in row]
                continue
            if texts[0] == "学習内容":
                self.mode = "content"
                self.cols = [c.x0 for c in row]
                continue
            cells = assign(row, self.cols)
            page_top = first_on_page and ri == 0
            if self.mode == "objective":
                self.objective_row(tb.page, cells)
            else:
                self.content_row(tb.page, cells, page_top)

    def _rec(self, page: int, **kw) -> dict:
        rid = self.new_id()
        rec = {"id": rid, "type": "curriculum-guideline", "section": self.section_raw, **kw}
        rec["_pages"] = [page]
        self.relations.append(rec)
        self.last = rec
        return rec

    def objective_row(self, page: int, cells) -> None:
        _label, mcc, gl = cells
        shared = mcc is None
        if mcc is not None:
            self.cur_goals = mcc
        rec = self._rec(page, row_kind="objective")
        rec["_goals"] = self.cur_goals or ""
        rec["goals_shared"] = shared
        rec["guideline_raw_parts"] = [gl or ""]
        rec["guideline_shared"] = False

    def content_row(self, page: int, cells, page_top: bool) -> None:
        content, goals, gl = cells
        # ページ先頭で、学習内容と到達目標が空、指導要領だけがある行は前の行の続き
        if page_top and not content and not goals and gl:
            self.last["guideline_raw_parts"].append(gl)
            if page not in self.last["_pages"]:
                self.last["_pages"].append(page)
            self.last["_page_top"] = True
            return
        # ページ先頭で、学習内容が空、到達目標が箇条記号で始まらず、前の行が箇条書きなら、
        # 前の行の到達目標（と指導要領）の続き。ページをまたいで 1 行が分断されている
        prev_bulleted = self.last is not None and str(self.last.get("_goals", "")).lstrip().startswith(("･", "・"))
        first_goal_line = (goals or "").strip().split("\n")[0]
        if (page_top and not content and goals and prev_bulleted
                and not first_goal_line.startswith(("･", "・")) and first_goal_line not in NONE_MARKS) \
                or (page_top and page in self.cfg.get("row_continues", [])):
            self.last["_goals"] = self.last["_goals"] + "\n" + goals
            self.cur_goals = self.last["_goals"]
            if gl:
                self.last["guideline_raw_parts"].append(gl)
                self.cur_guideline = "\n".join(self.last["guideline_raw_parts"])
            if page not in self.last["_pages"]:
                self.last["_pages"].append(page)
            self.last["_page_top"] = True
            return
        if content and page_top and page in self.cfg.get("content_name_continues", []):
            self.cur_content["raw_parts"].append(content)
            self.cur_content["pages"].append(page)
            for r in self.relations:
                if r.get("_content_obj") is self.cur_content:
                    r["_pages"] = sorted(set(r["_pages"]) | {page})
        elif content:
            self.cur_content = {"raw_parts": [content], "pages": [page]}
        goals_shared = goals is None
        if goals is not None:
            self.cur_goals = goals
        gl_shared = gl is None
        if gl is not None:
            self.cur_guideline = gl
        rec = self._rec(page, row_kind="content")
        rec["_content_obj"] = self.cur_content
        rec["_goals"] = self.cur_goals or ""
        rec["goals_shared"] = goals_shared
        rec["guideline_raw_parts"] = [self.cur_guideline or ""]
        rec["guideline_shared"] = gl_shared
        if self.group:
            rec["group"] = self.group
        if page_top:
            rec["_page_top"] = True

    def finish(self) -> list[dict]:
        out = []
        for r in self.relations:
            scope = self.section_scope(r["section"])
            rec = {"id": r["id"], "type": r["type"], "row_kind": r["row_kind"], "section": r["section"]}
            if r.get("group"):
                rec["group"] = r["group"]
            if r["row_kind"] == "objective":
                res = self.R.ref(r["section"])
                rec["content"] = res[0].target(r["section"]) if len(res) == 1 else {
                    "raw": r["section"], "id": None, "reason": "参照が複数に分かれる"}
                rec["targets"] = []
            else:
                craw = join_lines("\n".join(r["_content_obj"]["raw_parts"])) if r["_content_obj"] else ""
                if not craw or craw in NONE_MARKS:
                    rec["content"] = None
                    rec["content_raw"] = craw
                else:
                    rec["content"] = self.content_ref(craw, scope)
            rec["mcc_raw"] = join_lines(r["_goals"])
            rec["goals_shared"] = r["goals_shared"]
            rec["guideline_raw"] = join_lines("\n".join(r["guideline_raw_parts"]))
            rec["guideline_shared"] = r["guideline_shared"]
            if r["row_kind"] == "content":
                rec["targets"] = self.goal_targets(r["_goals"], rec["content"], scope_section=scope)
            rec["source"] = source(r["_pages"], r.get("_page_top", False))
            rec["verification"] = self.status.get(r["id"], "machine")
            out.append(rec)
        return out

    def section_scope(self, section_raw: str) -> str | None:
        res = self.R.ref(section_raw)
        return res[0].id if len(res) == 1 else None

    def content_ref(self, raw: str, scope: str | None) -> dict:
        if scope is None:
            return {"raw": raw, "id": None, "reason": "節の見出しを解決できない"}
        from .resolver import norm_name

        hits = [c for c in self.R.descendants(scope, "content") if norm_name(c["name"]) == norm_name(raw)]
        if len(hits) == 1:
            return {"raw": raw, "id": hits[0]["id"], "method": "content-name-in-section"}
        if not hits:
            return {"raw": raw, "id": None, "reason": f"{scope} の下に同じ名称の学習内容がない"}
        return {"raw": raw, "id": None, "reason": f"{scope} の下に同じ名称の学習内容が {len(hits)} 件ある"}

    def goal_targets(self, goals_raw: str, content: dict | None, scope_section: str | None) -> list[dict]:
        lines = [ln.strip() for ln in goals_raw.split("\n") if ln.strip()]
        if not lines or lines[0] in NONE_MARKS:
            return []
        scope = content["id"] if content and content.get("id") else scope_section
        out = []
        for item in split_bullets(goals_raw):
            out.append(self.R.goal_text(item, scope).target(item))
        return out


def guideline(cfg: dict, R: Resolver, status: dict[str, str]) -> tuple[list[dict], list[dict], str | None]:
    ex = GuidelineExtractor(cfg, R, status)
    first, last = cfg["pages"]
    for no in range(first, last + 1):
        first_table = True
        for ev in pdfsrc.events(no):
            if isinstance(ev, Line):
                ex.line(ev)
            else:
                ex.table(ev, first_table and ev.top < 110)
                first_table = False
    return ex.finish(), ex.notes, ex.title


# ---------- ABET・JABEE・IEA ----------

ITEM_PATTERNS = {
    "ABET": re.compile(r"^\d+\.\s"),
    "JABEE": re.compile(r"^\([a-z]\)\s"),
    "IEA-WK": re.compile(r"^WK\d+:"),
    "IEA-WA": re.compile(r"^WA\d+:"),
}
LABEL = re.compile(r"^(\d+\.|\([a-z]\)|WK\d+:|WA\d+:)")


def split_items(kind: str, raw: str) -> list[dict]:
    lines = [ln.strip() for ln in (raw or "").split("\n") if ln.strip()]
    pat = ITEM_PATTERNS[kind]
    items: list[dict] = []
    pending_title = None
    for i, ln in enumerate(lines):
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        if kind == "IEA-WA" and not pat.match(ln) and pat.match(nxt):
            pending_title = ln
            continue
        if pat.match(ln):
            item = {"label": LABEL.match(ln).group(1).rstrip(":"), "lines": [ln]}
            if pending_title:
                item["title"] = pending_title
                pending_title = None
            items.append(item)
        elif items:
            items[-1]["lines"].append(ln)
        else:
            raise ValueError(f"{kind}: ラベルの前の行: {ln}")
    out = []
    for it in items:
        d = {"label": it["label"], "text": join_lines("\n".join(it["lines"]))}
        if "title" in it:
            d["title"] = it["title"]
        out.append(d)
    return out


def abet(cfg: dict, R: Resolver, status: dict[str, str]) -> tuple[list[dict], dict]:
    names = cfg["columns"]
    cols = None
    header: list[list[str]] = []
    rows = []
    for no in range(cfg["pages"][0], cfg["pages"][1] + 1):
        for tb in pdfsrc.tables(no):
            for ri, row in enumerate(tb.rows):
                if no == cfg["pages"][0] and ri < cfg["header_rows"]:
                    if ri == cfg["header_rows"] - 1:
                        cols = [c.x0 for c in row]
                    header.append([c.text for c in row])
                    continue
                rows.append((no, assign(row, cols)))
    out = []
    for i, (no, cells) in enumerate(rows, start=1):
        rid = f"mcc2023:rel:abet:{i:02d}"
        items = {names[k]: split_items(names[k], cells[k] or "") for k in range(len(names) - 1)}
        mcc_raw = split_refs(cells[-1] or "")
        targets = [r.target(ref) for ref in mcc_raw for r in R.ref(ref)]
        out.append({"id": rid, "type": "external-standard", "standard": "ABET-JABEE-IEA", "row": i,
                    "items": items, "mcc_raw": mcc_raw, "targets": targets,
                    "source": source([no]), "verification": status.get(rid, "machine")})
    meta_header = {names[k]: [join_lines(h[k]) if k < len(h) and h[k] else None for h in header] for k in range(len(names))}
    return out, meta_header


# ---------- CDIO ----------

def cdio(cfg: dict, R: Resolver, status: dict[str, str]) -> list[dict]:
    p = pdfsrc.page(cfg["page"])
    split, L, Rt, top, bot = cfg["split_x"], cfg["left"], cfg["right"], cfg["top"], cfg["bottom"]
    cov: dict[int, list[tuple[float, float]]] = {}
    for e in p.edges:
        if e["orientation"] == "h" and top - 1 <= e["top"] <= bot + 1:
            cov.setdefault(round(e["top"]), []).append((e["x0"], e["x1"]))

    def covers(iv, a, b):
        x = a
        for s, t in sorted(iv):
            if s <= x + 3 and t > x:
                x = t
        return x >= b - 3

    def bands(a, b):
        ys = sorted(y for y, iv in cov.items() if covers(iv, a, b))
        ys = [y for i, y in enumerate(ys) if i == 0 or y - ys[i - 1] > 3]
        return list(zip(ys, ys[1:]))

    def text(x0, x1, y0, y1):
        c = p.crop((x0, y0, x1, y1), strict=False)
        return c.extract_text(y_tolerance=pdfsrc.Y_TOLERANCE) or ""

    out = []
    rights = [((y0, y1), text(split, Rt, y0, y1)) for y0, y1 in bands(split, Rt)]
    for y0, y1 in bands(L + 20, split):
        t = join_lines(text(L, split, y0, y1))
        if not t:
            continue
        m = re.match(r"^(\d(?:\.\d)?)\s+(.*)$", t)
        if not m:
            raise ValueError(f"CDIO: 番号のない項目: {t}")
        num, title = m.group(1), m.group(2)
        mid = (y0 + y1) / 2
        right_raw = "\n".join(txt for (a, b), txt in rights if (a < mid < b or y0 <= (a + b) / 2 <= y1) and txt.strip())
        mcc_raw = split_refs(right_raw)
        targets = [r.target(ref) for ref in mcc_raw for r in R.ref(ref)]
        rid = f"mcc2023:rel:cdio:{num}"
        out.append({"id": rid, "type": "external-standard", "standard": "CDIO",
                    "items": {"CDIO": [{"label": num, "text": title}]}, "mcc_raw": mcc_raw, "targets": targets,
                    "source": source([cfg["page"]]), "verification": status.get(rid, "machine")})
    return out
