"""原本 PDF の読み取り。

ページ番号はすべて PDF のページ番号（1 始まり）で扱う。
"""
from __future__ import annotations

import functools
import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

import pdfplumber

from . import yamlio
from .paths import ROOT, SOURCE_META

# セル内の行を束ねるときの縦の許容幅。下付き文字（PDF 95 ページの SN2 など）を同じ行に入れるため、
# pdfplumber の既定値 3 より広くする。本文の行間（約 13pt）より十分小さい。
Y_TOLERANCE = 5
FOOTER_TOP = 765  # これより下の数字だけの行はページ番号（ノンブル）


class SourceMissing(RuntimeError):
    pass


def meta() -> dict:
    return yamlio.load(SOURCE_META)


def pdf_path() -> Path:
    return ROOT / meta()["local_path"]


def available() -> bool:
    return pdf_path().exists()


def sha256() -> str:
    h = hashlib.sha256()
    with pdf_path().open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


@functools.cache
def _pdf() -> pdfplumber.PDF:
    path = pdf_path()
    if not path.exists():
        raise SourceMissing(f"{meta()['local_path']} がありません。uv run python source/fetch.py で取得してください")
    return pdfplumber.open(path)


def page_count() -> int:
    return len(_pdf().pages)


@functools.cache
def page(no: int):
    return _pdf().pages[no - 1]


@functools.cache
def stream_text(no: int) -> str:
    """ページの文字をコンテンツストリームの順に並べた文字列（照合用）。"""
    return "".join(c["text"] for c in page(no).chars)


def squash(s: str | None) -> str:
    """照合用に空白と改行を除く。"""
    return re.sub(r"\s+", "", s or "")


@functools.cache
def printed_page(no: int) -> int | None:
    """紙面のページ番号（フッターの数字）。ない場合は None。"""
    for w in page(no).extract_words():
        if w["top"] >= FOOTER_TOP and re.fullmatch(r"\d{1,3}", w["text"]):
            return int(w["text"])
    return None


@dataclass
class Cell:
    text: str | None  # None は結合セル（上の行の値を引き継ぐ）
    x0: float | None
    top: float | None
    col: int = -1


@dataclass
class Table:
    page: int
    index: int
    bbox: tuple[float, float, float, float]
    rows: list[list[Cell]] = field(default_factory=list)

    @property
    def top(self) -> float:
        return self.bbox[1]


@dataclass
class Line:
    page: int
    text: str
    top: float
    x0: float
    size: float


@functools.cache
def tables(no: int) -> tuple[Table, ...]:
    out = []
    for i, t in enumerate(page(no).find_tables()):
        tb = Table(no, i, tuple(t.bbox))
        texts = t.extract(y_tolerance=Y_TOLERANCE)
        for prow, trow in zip(t.rows, texts):
            cells = []
            for bbox, text in zip(prow.cells, trow):
                if bbox is None:
                    cells.append(Cell(None, None, None))
                else:
                    cells.append(Cell(text if text is not None else "", bbox[0], bbox[1]))
            tb.rows.append(cells)
        out.append(tb)
    return tuple(out)


def _inside(obj, boxes, pad=1.0) -> bool:
    cx = (obj["x0"] + obj["x1"]) / 2
    cy = (obj["top"] + obj["bottom"]) / 2
    return any(b[0] - pad <= cx <= b[2] + pad and b[1] - pad <= cy <= b[3] + pad for b in boxes)


@functools.cache
def outside_lines(no: int, exclude: tuple[tuple[float, float, float, float], ...] = ()) -> tuple[Line, ...]:
    """表の外にある本文の行（フッターのページ番号を除く）。"""
    p = page(no)
    boxes = [t.bbox for t in tables(no)] + list(exclude)
    q = p.filter(lambda o: o.get("object_type") != "char" or not _inside(o, boxes))
    out = []
    for ln in q.extract_text_lines(y_tolerance=Y_TOLERANCE, return_chars=True):
        text = ln["text"].strip()
        if not text:
            continue
        if ln["top"] >= FOOTER_TOP and re.fullmatch(r"\d{1,3}", text):
            continue
        sizes = [c["size"] for c in ln["chars"] if c["text"].strip()]
        out.append(Line(no, text, ln["top"], ln["x0"], max(sizes) if sizes else 0.0))
    return tuple(out)


def events(no: int):
    """ページ内の行と表を、上から順に並べる。"""
    items = [(ln.top, 0, ln) for ln in outside_lines(no)] + [(t.top, 1, t) for t in tables(no)]
    items.sort(key=lambda x: (round(x[0], 1), x[1]))
    return [x[2] for x in items]


@functools.cache
def body_stream(no: int) -> str:
    """照合用のページ本文。ストリーム順で、フッターのページ番号の数字と空白を除く。"""
    chars = [c["text"] for c in page(no).chars
             if not (c["top"] >= FOOTER_TOP and c["text"].isdigit())]
    return squash("".join(chars))


def pages_stream(pages) -> str:
    return "".join(body_stream(p) for p in sorted(set(pages)))


@functools.cache
def views(no: int) -> tuple[str, ...]:
    """照合用のページの抽出テキスト（空白とフッターのページ番号を除く）。

    1. 文字のストリーム順（PDF に書かれた順）
    2. 行単位の抽出（上から下、左から右）
    3. 表の列ごとの抽出（各表を列の幅で切り出し、上から下に読む）
    """
    p = page(no)
    body = p.filter(lambda o: o.get("object_type") != "char"
                    or not (o["top"] >= FOOTER_TOP and o["text"].isdigit()))
    out = [body_stream(no), squash(body.extract_text(y_tolerance=Y_TOLERANCE))]
    for t in p.find_tables():
        xs = sorted({round(c[0], 1) for row in t.rows for c in row.cells if c} | {round(t.bbox[2], 1)})
        for x0, x1 in zip(xs, xs[1:]):
            crop = body.crop((x0, t.bbox[1], x1, t.bbox[3]), strict=False)
            out.append(squash(crop.extract_text(y_tolerance=Y_TOLERANCE)))
    return tuple(out)
