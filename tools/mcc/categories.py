"""大分類の区分（表 3、PDF 25 ページ）と到達水準（本文の引用）。"""
from __future__ import annotations

import re

from . import pdfsrc
from .textnorm import ROMAN, join_lines, roman


def divisions(page_no: int) -> dict[str, dict]:
    """表 3 から、大分類コード → {mcc, group} を取る。"""
    (tb,) = [t for t in pdfsrc.tables(page_no) if len(t.rows) > 10]
    mcc = None
    groups: dict[int, str] = {}
    out: dict[str, dict] = {}
    for row in tb.rows:
        texts = [join_lines(c.text) if c.text else "" for c in row]
        nonempty = [(i, t) for i, t in enumerate(texts) if t]
        if len(nonempty) == 1 and nonempty[0][1] in ("MCC(コア)", "MCC(モデル)"):
            mcc = nonempty[0][1]
            groups = {}
            continue
        for i, t in nonempty:
            m = re.match(rf"^({ROMAN})\s+(.+)$", roman(t))
            if m:
                if i not in groups:
                    raise ValueError(f"表 3: 区分の見出しより前の大分類: {t}")
                out[m.group(1)] = {"mcc": mcc, "group": groups[i], "page_pdf": page_no, "name_in_table": m.group(2)}
            elif re.match(rf"^({ROMAN})-", roman(t)):
                continue
            else:
                groups[i] = t
    return out


def levels(cfg: dict) -> dict[str, dict]:
    out = {}
    for lv in cfg["levels"]:
        if pdfsrc.squash(lv["quote"]) not in pdfsrc.squash(pdfsrc.stream_text(lv["page_pdf"])):
            raise ValueError(f"到達水準の引用が PDF {lv['page_pdf']} ページにありません: {lv['quote']}")
        for c in lv["categories"]:
            out[c] = {"value": lv["value"], "quote": lv["quote"], "page_pdf": lv["page_pdf"]}
    return out
