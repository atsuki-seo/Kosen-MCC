"""到達目標の抽出器（第 2 部の様式 1〜3、複合融合学科への配慮事項、第 3 部の MCC plus）。

ページ順に「表の外の行」と「表」を並べ、見出し・説明文・表のヘッダー行・データ行を
状態機械で処理する。設計 6.1、6.2 に対応する。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import pdfsrc
from .pdfsrc import Line, Table
from .textnorm import ROMAN, code as norm_code, join_lines, roman, split_items

PREFIX = "mcc2023"
PLUS_PREFIX = "mccplus2023"

RE_CHAPTER = re.compile(r"^第\s*(\d)\s*章\s*(.+)$")
RE_MAJOR = re.compile(rf"^(\d)-(\d)\s+({ROMAN})\s+(.+)$")
RE_FIELD = re.compile(rf"^(\d)-(\d)\.(\d)\s+({ROMAN})(?:\s*-\s*([A-I]))?\s+(.+)$")
RE_AREA = re.compile(rf"^({ROMAN})\s*-\s*([A-I])\s*-\s*(\d+)\s+(.+)$")
RE_HAIRYO_TOP = re.compile(r"^3-3\s+(複合融合学科.+)$")
RE_HAIRYO_SEC = re.compile(r"^3-3\.(\d)\s+(.+)$")
RE_PLUS_FIELD = re.compile(r"^2-2\.(\d)\s+(.+)$")
RE_GROUP = re.compile(r"^(≪.+≫|上記以外の観点)$")
RE_NOTE_ROW = re.compile(r"^注\s*[0-9０-９]+$")
RE_GOAL_NOTE = re.compile(r"（([^（）]*と共通)）$")
RE_CONTENT_NOTE = re.compile(r"^(.*?)\s*(（注\s*[0-9０-９]+）)$")
RE_DESC_START = re.compile(r"^(【|\d\s|\(\d+\)|（\d+）)")

HEADER_KINDS = {
    "学習内容": "content",
    "到達目標": "goal",
    "学習の目安となる項目": "supplement",
    "キーワード": "supplement",
    "MCC対応": "mcc",
    "学習領域": "area",
    "複合融合学科/コースにおいて必須となる到達目標": "goal",
    "履修上の配慮": "consideration",
}


@dataclass
class Node:
    id: str
    type: str
    parent: str | None
    page: int
    data: dict = field(default_factory=dict)
    children: int = 0  # 学習内容・到達目標の番号付け用
    description: list[str] = field(default_factory=list)
    description_pages: list[int] = field(default_factory=list)


@dataclass
class GoalRow:
    """到達目標の行。複数のページにまたがる場合はセルの断片を足していく。"""

    node: Node
    goal_parts: list[str]
    supp_parts: list[str]
    mcc_parts: list[str]
    pages: list[int]
    supp_kind: str | None = None
    page_top: bool = False  # ページ先頭の行（前ページからの続きの表の 1 行目）


@dataclass
class HairyoRow:
    section: str
    section_no: int
    area_parts: list[str]
    goal_parts: list[str]
    consideration_parts: list[str]
    pages: list[int]
    consideration_inherited: bool = False
    page_top: bool = False


@dataclass
class Unclassified:
    page: int
    table: int
    reason: str
    rows: list[list[str | None]]
    context: str | None


class GoalExtractor:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.nodes: list[Node] = []
        self.by_id: dict[str, Node] = {}
        self.goal_rows: list[GoalRow] = []
        self.hairyo: list[HairyoRow] = []
        self.unclassified: list[Unclassified] = []
        self.chapter: str | None = None
        self.major: Node | None = None
        self.field: Node | None = None
        self.area: Node | None = None
        self.content: Node | None = None
        self.content_parts: list[str] = []
        self.group: str | None = None
        self.desc_target: Node | None = None
        self.columns: list[tuple[float, str]] = []
        self.supp_kind: str | None = None
        self.mode = "goals"  # goals | hairyo | plus
        self.hairyo_section: tuple[int, str] | None = None
        self.hairyo_area_parts: list[str] = []
        self.hairyo_consideration: list[str] = []
        self.plus_codes = {f["number"]: f for f in cfg["plus_fields"]}
        self.headings: list[dict] = []

    # ---- ノード ----
    def add(self, node: Node) -> Node:
        if node.id in self.by_id:
            raise ValueError(f"ID が重複しました: {node.id}")
        self.nodes.append(node)
        self.by_id[node.id] = node
        return node

    def container(self) -> Node:
        return self.area or self.field or self.major

    # ---- 見出し ----
    def heading(self, ln: Line) -> bool:
        text = roman(ln.text)
        if m := RE_CHAPTER.match(text):
            self.chapter = ln.text
            self.headings.append({"kind": "chapter", "raw": ln.text, "page": ln.page})
            self.desc_target = None
            return True
        if self.mode == "plus":
            if m := RE_PLUS_FIELD.match(text):
                num = int(m.group(1))
                fc = self.plus_codes[num]
                nid = f"{PLUS_PREFIX}:{fc['code']}"
                self.field = self.add(Node(nid, "field", None, ln.page, {
                    "code": fc["code"], "code_defined_by": "this-repository",
                    "name": fc["name"], "heading_raw": ln.text,
                }))
                self.major, self.area, self.content, self.group = None, None, None, None
                self.desc_target = self.field
                return True
            if m := RE_GROUP.match(ln.text):
                self.group = ln.text
                self.desc_target = None
                return True
            return False
        if m := RE_HAIRYO_TOP.match(text):
            self.mode = "hairyo"
            self.hairyo_title = ln.text
            self.desc_target = None
            return True
        if self.mode == "hairyo":
            if m := RE_HAIRYO_SEC.match(text):
                self.hairyo_section = (int(m.group(1)), m.group(2))
                self.hairyo_area_parts, self.hairyo_consideration = [], []
                return True
            if RE_MAJOR.match(text):
                self.mode = "goals"
            else:
                return False
        if m := RE_MAJOR.match(text):
            code = m.group(3)
            nid = f"{PREFIX}:{code}"
            self.major = self.add(Node(nid, "category", None, ln.page, {
                "code": code, "name": m.group(4), "heading_raw": ln.text, "chapter": self.chapter,
            }))
            self.field = self.area = self.content = None
            self.group = None
            self.desc_target = self.major
            return True
        if m := RE_FIELD.match(text):
            code = m.group(4) + (f"-{m.group(5)}" if m.group(5) else "")
            if code == self.major.data["code"]:
                # 「2-1.1 I 数学」: 分野のない大分類。ノードは作らない
                self.major.data["heading_raw_sub"] = ln.text
                return True
            nid = f"{PREFIX}:{code}"
            self.field = self.add(Node(nid, "field", self.major.id, ln.page, {
                "code": code, "name": m.group(6), "heading_raw": ln.text,
            }))
            self.area = self.content = None
            self.group = None
            self.desc_target = self.field
            return True
        if m := RE_AREA.match(text):
            code = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
            nid = f"{PREFIX}:{code}"
            parent = self.field
            if parent is None or not code.startswith(parent.data["code"] + "-"):
                raise ValueError(f"p{ln.page}: 領域 {code} の親の分野が見つかりません")
            self.area = self.add(Node(nid, "area", parent.id, ln.page, {
                "code": code, "name": m.group(4), "heading_raw": ln.text,
            }))
            self.content = None
            self.group = None
            self.desc_target = self.area
            return True
        if RE_GROUP.match(ln.text):
            self.group = ln.text
            self.desc_target = None
            return True
        return False

    # ---- 説明文 ----
    def describe(self, page: int, text: str) -> None:
        if self.desc_target is None:
            raise ValueError(f"p{page}: 説明文の行き先がありません: {text[:40]}")
        tgt = self.desc_target
        tgt.description.extend(ln.strip() for ln in text.split("\n") if ln.strip())
        if page not in tgt.description_pages:
            tgt.description_pages.append(page)

    # ---- 表 ----
    def set_header(self, row) -> None:
        cols = []
        for c in row:
            if c.text is None or c.x0 is None:
                continue
            kind = HEADER_KINDS.get(join_lines(c.text).replace(" ", ""))
            if kind is None:
                raise ValueError(f"未知のヘッダー: {c.text!r}")
            if kind == "supplement":
                self.supp_kind = join_lines(c.text).replace(" ", "")
            cols.append((c.x0, kind))
        self.columns = cols

    def assign(self, row) -> dict[str, str | None]:
        """セルを x 座標でヘッダーの列に割り当てる。"""
        out: dict[str, str | None] = {k: None for _, k in self.columns}
        prev = -1
        for c in row:
            if c.x0 is not None:
                idx = min(range(len(self.columns)), key=lambda i: abs(self.columns[i][0] - c.x0))
                if abs(self.columns[idx][0] - c.x0) > 40:
                    raise ValueError(f"列に割り当てられないセル x0={c.x0}")
            else:
                idx = prev + 1
            prev = idx
            if idx < len(self.columns):
                kind = self.columns[idx][1]
                if c.text is not None:
                    out[kind] = c.text if out[kind] is None else out[kind] + "\n" + c.text
        return out

    def table(self, tb: Table, first_on_page: bool) -> None:
        for spec in self.cfg.get("unclassified_tables", []):
            if spec["page"] == tb.page and spec["table"] == tb.index:
                ctx = None
                if self.goal_rows:
                    ctx = f"直前の到達目標の行（p{self.goal_rows[-1].pages[0]}）: {join_lines(chr(10).join(self.goal_rows[-1].goal_parts))}"
                self.unclassified.append(Unclassified(tb.page, tb.index, spec["reason"],
                                                      [[c.text for c in r] for r in tb.rows], ctx))
                return
        seen_header = False
        for ri, row in enumerate(tb.rows):
            texts = [c.text for c in row]
            c0 = join_lines(texts[0]) if texts else ""
            c0s = c0.replace(" ", "")
            if c0s in ("学習内容", "学習領域"):
                self.set_header(row)
                seen_header = True
                continue
            others_empty = all(t in (None, "") for t in texts[1:])
            if others_empty and texts[0] and (not seen_header) and (ri == 0 or not self.columns or c0.startswith("【")) \
                    and RE_DESC_START.match(texts[0].strip()):
                self.describe(tb.page, texts[0])
                continue
            if not self.columns:
                raise ValueError(f"p{tb.page} 表{tb.index}: ヘッダー行より前のデータ行: {texts}")
            page_top = first_on_page and ri == 0 and not seen_header
            if self.mode == "hairyo":
                self.hairyo_row(tb.page, self.assign(row), page_top)
            else:
                self.goal_row(tb.page, self.assign(row), page_top)
        self.desc_target = None

    def new_content(self, page: int, raw: str) -> None:
        parent = self.container()
        parent.children += 1
        name = join_lines(raw)
        data = {"name": name}
        if m := RE_CONTENT_NOTE.match(name):
            data = {"name": m.group(1), "note": m.group(2)}
        if self.group:
            data["group"] = self.group
        nid = f"{parent.id}:{parent.children:02d}"
        self.content = self.add(Node(nid, "content", parent.id, page, data))
        self.content_parts = [raw]

    def goal_row(self, page: int, cells: dict, page_top: bool) -> None:
        content, goal = cells.get("content"), cells.get("goal")
        supp, mcc = cells.get("supplement"), cells.get("mcc")
        if content and RE_NOTE_ROW.match(join_lines(content)):
            tgt = self.container()
            tgt.data.setdefault("notes", []).append({"label": join_lines(content), "text": join_lines(goal), "page": page})
            return
        cont_row = page_top and page in self.cfg.get("row_continues", [])
        if cont_row or (not goal and (supp or mcc)):
            last = self.goal_rows[-1]
            if goal:
                last.goal_parts.append(goal)
            if supp:
                last.supp_parts.append(supp)
            if mcc:
                last.mcc_parts.append(mcc)
            if page not in last.pages:
                last.pages.append(page)
            if page_top:
                last.page_top = True
            if content:
                raise ValueError(f"p{page}: 継続行に学習内容があります: {content!r}")
            return
        if not goal:
            if content or supp or mcc:
                raise ValueError(f"p{page}: 到達目標のない行: {cells}")
            return
        if content:
            if page_top and page in self.cfg.get("content_name_continues", []):
                self.content_parts.append(content)
                name = join_lines("\n".join(self.content_parts))
                self.content.data["name"] = name
                if m := RE_CONTENT_NOTE.match(name):
                    self.content.data.update(name=m.group(1), note=m.group(2))
                self.content.data["name_pages"] = sorted({self.content.page, page})
            else:
                self.new_content(page, content)
        if self.content is None:
            # 原本で学習内容のセルが空欄のまま到達目標が始まる（PDF 88 ページ V-C-7）。名称を空で持つ
            self.new_content(page, "")
            self.content.data["name_empty_in_source"] = True
        self.content.children += 1
        nid = f"{self.content.id}.{self.content.children:02d}"
        node = self.add(Node(nid, "goal", self.content.id, page, {}))
        kinds = {k for _, k in self.columns}
        self.goal_rows.append(GoalRow(node, [goal], [supp] if supp else [], [mcc] if mcc else [], [page],
                                      self.supp_kind if "supplement" in kinds else None, page_top))

    def hairyo_row(self, page: int, cells: dict, page_top: bool) -> None:
        area, goal, cons = cells.get("area"), cells.get("goal"), cells.get("consideration")
        cont_row = page_top and page in self.cfg.get("hairyo_row_continues", [])
        if cont_row or (not goal and cons):
            last = self.hairyo[-1]
            if goal:
                last.goal_parts.append(goal)
            if cons:
                last.consideration_parts.append(cons)
            if page not in last.pages:
                last.pages.append(page)
            if page_top:
                last.page_top = True
            return
        if not goal:
            if area or cons:
                raise ValueError(f"p{page}: 配慮事項の到達目標のない行: {cells}")
            return
        if area:
            self.hairyo_area_parts = [area]
        inherited = False
        if cons is None:
            inherited = True
            cons_parts = list(self.hairyo_consideration)
        else:
            cons_parts = [cons] if cons else []
            self.hairyo_consideration = cons_parts
        no, sec = self.hairyo_section
        self.hairyo.append(HairyoRow(sec, no, list(self.hairyo_area_parts), [goal], cons_parts, [page], inherited,
                                     page_top))

    # ---- 実行 ----
    def run_pages(self, first: int, last: int, mode: str) -> None:
        self.mode = mode
        for no in range(first, last + 1):
            first_table = True
            for ev in pdfsrc.events(no):
                if isinstance(ev, Line):
                    if self.heading(ev):
                        continue
                    if self.desc_target is not None:
                        self.describe(no, ev.text)
                        continue
                    raise ValueError(f"p{no}: 扱えない行: {ev.text}")
                else:
                    self.table(ev, first_table and ev.top < 110)
                    first_table = False
        self.desc_target = None
