"""誤記の記録（config/errata.yaml）を、引用を照合してから正本に書き出す。"""
from __future__ import annotations

from . import pdfsrc


def build(cfg: dict) -> list[dict]:
    out = []
    for e in cfg["entries"]:
        for occ in e["occurrences"]:
            if pdfsrc.squash(occ["quote"]) not in pdfsrc.squash(pdfsrc.stream_text(occ["page_pdf"])):
                raise ValueError(f"{e['id']}: 引用が PDF {occ['page_pdf']} ページにありません: {occ['quote']}")
        out.append(e)
    return out
