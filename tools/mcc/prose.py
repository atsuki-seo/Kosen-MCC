"""散文と図の抽出器（設計 5.6、6.1）。

text/mcc2023/sections/NNN.md に節ごとの Markdown を、text/mcc2023/figures/ に図の画像と書き起こしを出力する。
節と図には、文書の中の位置にもとづく ID（mcc2023:doc:NNN）を振る。
"""
from __future__ import annotations

import collections
import re
from dataclasses import dataclass, field

from . import pdfsrc
from .textnorm import join_lines

RE_SECTION = re.compile(r"^(第\s*[0-9]+\s*章|[0-9]+-[0-9]+(\.[0-9]+)?)\s*\S")
RIGHT_FULL = 505  # これより右で終わる行は、行末まで詰まっている（段落が続く）とみなす


@dataclass
class PLine:
    page: int
    top: float
    x0: float
    x1: float
    text: str
    gothic: bool


@dataclass
class Block:
    kind: str  # heading | para | table | figure | layout
    page: int
    text: str = ""
    level: int = 0
    rows: list = field(default_factory=list)
    figure: dict | None = None
    pages: set = field(default_factory=set)
    lines: list = field(default_factory=list)


@dataclass
class Section:
    title: str
    heading_raw: str | None
    part: str | None
    blocks: list[Block] = field(default_factory=list)
    pages: set = field(default_factory=set)


def _inside(obj, box, pad=1.0) -> bool:
    cx = (obj["x0"] + obj["x1"]) / 2
    cy = (obj["top"] + obj["bottom"]) / 2
    return box[0] - pad <= cx <= box[2] + pad and box[1] - pad <= cy <= box[3] + pad


def page_lines(no: int, exclude: list[tuple]) -> list[PLine]:
    p = pdfsrc.page(no)
    q = p.filter(lambda o: o.get("object_type") != "char" or not any(_inside(o, b) for b in exclude))
    out = []
    for ln in q.extract_text_lines(y_tolerance=pdfsrc.Y_TOLERANCE, return_chars=True):
        text = ln["text"].strip()
        if not text:
            continue
        if ln["top"] >= pdfsrc.FOOTER_TOP and re.fullmatch(r"\d{1,3}", text):
            continue
        chs = [c for c in ln["chars"] if c["text"].strip()]
        fn = collections.Counter(c["fontname"].split("+")[-1] for c in chs).most_common(1)[0][0]
        big = max(c["size"] for c in chs) >= 10
        out.append(PLine(no, ln["top"], ln["x0"], ln["x1"], text, ("Gothic" in fn or "Arial" in fn) and big))
    return out


def figures_on(no: int, figcfg: list[dict]) -> list[dict]:
    return [f for f in figcfg if f["page"] == no]


class ProseExtractor:
    def __init__(self, cfg: dict, figcfg: list[dict]):
        self.cfg = cfg
        self.figcfg = figcfg
        self.marker = re.compile(cfg["paragraph_markers"])
        self.extra = set(cfg.get("extra_headings", []))
        self.sections: list[Section] = []

    # ---- 段落 ----
    def paragraph_segment(self, seg: dict) -> None:
        first, last = seg["pages"]
        cur: Section | None = None
        if seg.get("title"):
            cur = Section(seg["title"], None, seg.get("part"))
            self.sections.append(cur)
        for no in range(first, last + 1):
            figs = figures_on(no, self.figcfg)
            tables = [] if seg.get("skip_tables") else [t for t in pdfsrc.tables(no)
                                                         if not any(_inside({"x0": t.bbox[0], "x1": t.bbox[2], "top": t.bbox[1], "bottom": t.bbox[3]}, f["bbox"], 2) for f in figs)]
            exclude = [tuple(f["bbox"]) for f in figs] + [t.bbox for t in (pdfsrc.tables(no) if seg.get("skip_tables") else tables)]
            items = [(ln.top, "line", ln) for ln in page_lines(no, exclude)]
            items += [(t.top, "table", t) for t in tables]
            items += [(f["bbox"][1], "figure", f) for f in figs]
            items.sort(key=lambda x: (round(x[0], 1), {"figure": 0, "table": 1, "line": 2}[x[1]]))
            for _, kind, obj in items:
                if kind == "line" and self.is_section(obj):
                    cur = Section(obj.text, obj.text, seg.get("part"))
                    self.sections.append(cur)
                    cur.blocks.append(Block("heading", no, obj.text, self.level(obj.text)))
                    cur.pages.add(no)
                    continue
                if cur is None:
                    raise ValueError(f"p{no}: 見出しより前の本文: {getattr(obj, 'text', kind)}")
                cur.pages.add(no)
                if kind == "figure":
                    cur.blocks.append(Block("figure", no, figure=obj))
                elif kind == "table":
                    cur.blocks.append(Block("table", no, rows=[[c.text for c in r] for r in obj.rows]))
                else:
                    self.add_line(cur, obj)
        if cur is not None:
            cur.pages.add(last)
            # 区間の終わりまでの空白ページを最後の節に含める
            cur.pages.update(range(min(cur.pages), last + 1))

    def is_section(self, ln: PLine) -> bool:
        if ln.text in self.extra:
            return True
        return ln.gothic and ln.x0 < 90 and bool(RE_SECTION.match(ln.text))

    @staticmethod
    def level(text: str) -> int:
        if text.startswith("第"):
            return 1
        if re.match(r"^\d+-\d+\.\d+", text):
            return 3
        if re.match(r"^\d+-\d+", text):
            return 2
        return 2

    def add_line(self, sec: Section, ln: PLine) -> None:
        last = sec.blocks[-1] if sec.blocks else None
        if ln.gothic and ln.x0 < 90:
            sec.blocks.append(Block("heading", ln.page, ln.text, 4))
            return
        cont = (last is not None and last.kind == "para" and last.lines
                and last.lines[-1].x1 >= RIGHT_FULL
                and not self.marker.match(ln.text)
                and not (ln.x0 > 78 and last.lines[-1].x0 <= 75))
        if cont:
            last.lines.append(ln)
            last.pages.add(ln.page)
        else:
            sec.blocks.append(Block("para", ln.page, lines=[ln], pages={ln.page}))

    # ---- 行の配置を保つ ----
    def layout_segment(self, seg: dict) -> None:
        first, last = seg["pages"]
        sec = Section(seg["title"], None, seg.get("part"))
        sec.pages.update(range(first, last + 1))
        self.sections.append(sec)
        for no in range(first, last + 1):
            figs = figures_on(no, self.figcfg)
            for f in figs:
                sec.blocks.append(Block("figure", no, figure=f))
            lines = page_lines(no, [tuple(f["bbox"]) for f in figs])
            if lines:
                sec.blocks.append(Block("layout", no, lines=lines, pages={no}))

    # ---- 見出しだけ ----
    def headings_segment(self, seg: dict) -> None:
        first, last = seg["pages"]
        pat = re.compile(seg.get("heading_pattern", r"^第\s*[0-9]+\s*章"))
        found = []
        for no in range(first, last + 1):
            for ln in pdfsrc.outside_lines(no):
                if pat.match(ln.text):
                    found.append((no, ln.text))
        for i, (no, text) in enumerate(found):
            end = found[i + 1][0] - 1 if i + 1 < len(found) else last
            sec = Section(text, text, seg.get("part"))
            sec.blocks.append(Block("heading", no, text, self.level(text)))
            sec.pages.update(range(no, end + 1))
            self.sections.append(sec)
        if found and found[0][0] != first:
            raise ValueError(f"headings: p{first} から見出しまでの範囲が節に入らない")

    def run(self) -> list[Section]:
        for seg in self.cfg["segments"]:
            {"paragraph": self.paragraph_segment, "layout": self.layout_segment,
             "headings": self.headings_segment}[seg["mode"]](seg)
        return self.sections


# ---------- Markdown ----------

def para_text(b: Block) -> str:
    return join_lines("\n".join(ln.text for ln in b.lines))


def md_table(rows: list[list[str | None]]) -> str:
    def cell(c):
        return join_lines(c).replace("|", "\\|") if c else ""
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    if width == 1:
        return "\n".join("> " + cell(r[0]) for r in rows if r[0])
    out = []
    for i, r in enumerate(rows):
        r = list(r) + [None] * (width - len(r))
        out.append("| " + " | ".join(cell(c) for c in r) + " |")
        if i == 0:
            out.append("|" + "---|" * width)
    return "\n".join(out)


def layout_text(b: Block) -> str:
    out = []
    for ln in b.lines:
        indent = max(0, round((ln.x0 - 71) / 10.6))
        out.append("　" * indent + ln.text)
    return "\n".join(out)


def checkable_texts(b: Block) -> list[str]:
    """原文照合（text-in-source）の対象にする文字列。"""
    if b.kind == "heading":
        return [b.text]
    if b.kind == "para":
        return [para_text(b)]
    if b.kind == "table":
        return [join_lines(c) for r in b.rows for c in r if c]
    if b.kind == "layout":
        return [ln.text for ln in b.lines]
    return []


# ---------- 書き出し ----------

def _load_transcriptions() -> dict:
    from . import yamlio
    from .paths import CONFIG

    path = CONFIG / "figure-transcriptions.yaml"
    return {k: v.strip() for k, v in (yamlio.load(path) or {}).items()} if path.exists() else {}


TRANSCRIPTIONS = _load_transcriptions()

TRANSCRIPTION_NOTE = ("書き起こしは原文ではない。図の構成と要素の関係を、このリポジトリで文章にしたもの。"
                      "図の中の文字そのものは「図の中の文字」の節にあり、そちらは PDF の文字層から抽出した原文である。")


def front(d: dict) -> str:
    from . import yamlio

    return "---\n" + yamlio.dump(d) + "---\n"


def write_all(sections: list[Section], out_dir, status: dict[str, str]) -> tuple[list, list]:
    """節と図を書き出す。(節のパスのリスト, 図のパスのリスト) を返す。"""
    sec_dir, fig_dir = out_dir / "sections", out_dir / "figures"
    sec_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    sec_paths, fig_paths = [], []
    fig_count: dict[int, int] = {}
    for sec in sections:
        n += 1
        sec_no = n
        sid = f"mcc2023:doc:{sec_no:03d}"
        body: list[str] = []
        for b in sec.blocks:
            if b.kind == "heading":
                body.append("#" * b.level + " " + b.text)
            elif b.kind == "para":
                body.append(para_text(b))
            elif b.kind == "table":
                body.append(md_table(b.rows))
            elif b.kind == "layout":
                body.append("```text\n" + layout_text(b) + "\n```")
            elif b.kind == "figure":
                n += 1
                f = b.figure
                k = fig_count[f["page"]] = fig_count.get(f["page"], 0) + 1
                stem = f"fig-{f['page']:03d}-{k}"
                fid = f"mcc2023:doc:{n:03d}"
                title = f.get("caption") or f.get("label")
                fig_paths.append(write_figure(f, stem, fid, title, fig_dir, status))
                body.append(f"![{title}](../figures/{stem}.png)\n\n（図の書き起こし: [{stem}.md](../figures/{stem}.md)、{fid}）")
        pages = sorted(sec.pages)
        fm = {"id": sid, "kind": "section", "title": sec.title, "heading_raw": sec.heading_raw, "part": sec.part,
              "pages_pdf": pages, "pages_printed": [pdfsrc.printed_page(p) for p in pages],
              "verification": status.get(sid, "machine")}
        path = sec_dir / f"{sec_no:03d}.md"
        path.write_text(front(fm) + "\n" + "\n\n".join(body) + "\n", encoding="utf-8")
        sec_paths.append(path)
    return sec_paths, fig_paths


def figure_lines(f: dict) -> list[str]:
    """図の領域の文字を、ストリーム順（PDF に書かれた順）に並べ、隣り合わない位置で区切る。

    図の中には縦書きや回転した文字があり、行単位の抽出では文字の順が崩れるため。
    """
    p = pdfsrc.page(f["page"])
    x0, top, x1, bottom = f["bbox"]
    chars = [c for c in p.chars if x0 - 1 <= (c["x0"] + c["x1"]) / 2 <= x1 + 1 and top - 1 <= (c["top"] + c["bottom"]) / 2 <= bottom + 1]
    runs: list[str] = []
    prev = None
    for c in chars:
        if prev is not None:
            size = max(prev["size"], c["size"])
            near_h = abs(c["top"] - prev["top"]) < size * 0.6 and -size * 0.5 < c["x0"] - prev["x1"] < size * 1.5
            near_v = abs(c["x0"] - prev["x0"]) < size * 0.6 and -size * 0.5 < c["top"] - prev["bottom"] < size * 1.0
            if not (near_h or near_v):
                runs.append("")
        else:
            runs.append("")
        runs[-1] += c["text"]
        prev = c
    return [r.strip() for r in runs if r.strip()]


def write_figure(f: dict, stem: str, fid: str, title: str, fig_dir, status: dict[str, str]):
    p = pdfsrc.page(f["page"])
    img = p.crop(tuple(f["bbox"]), strict=False).to_image(resolution=150)
    img.save(fig_dir / f"{stem}.png")
    lines = figure_lines(f)
    fm = {"id": fid, "kind": "figure", "title": title, "heading_raw": f.get("caption"), "part": None,
          "pages_pdf": [f["page"]], "pages_printed": [pdfsrc.printed_page(f["page"])],
          "image": f"{stem}.png", "bbox": [float(v) for v in f["bbox"]],
          "transcription_note": TRANSCRIPTION_NOTE, "verification": status.get(fid, "machine")}
    body = [f"# {title}", f"![{title}]({stem}.png)", "## 図の中の文字（原文。PDF の文字層から抽出）"]
    body.append("```text\n" + "\n".join(lines) + "\n```" if lines else "（図の中に文字層の文字はない）")
    body.append("## 書き起こし（原文ではない）")
    body.append(TRANSCRIPTIONS.get(stem) or "（未作成）")
    path = fig_dir / f"{stem}.md"
    path.write_text(front(fm) + "\n" + "\n\n".join(body) + "\n", encoding="utf-8")
    return path
