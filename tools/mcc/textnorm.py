"""表記の正規化。原文そのものは変えず、照合・ID 生成のためにだけ使う。"""
from __future__ import annotations

import re

_FW_ROMAN = str.maketrans({
    "Ⅰ": "I", "Ⅱ": "II", "Ⅲ": "III", "Ⅳ": "IV", "Ⅴ": "V",
    "Ⅵ": "VI", "Ⅶ": "VII", "Ⅷ": "VIII", "Ⅸ": "IX", "Ⅹ": "X",
})
ROMAN = r"(?:VIII|VII|VI|IX|IV|V|III|II|I)"
ROMANS = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"]


def roman(s: str) -> str:
    """全角ローマ数字を半角に。"""
    return s.translate(_FW_ROMAN)


def code(s: str) -> str:
    """コード表記を正規化する（`Ⅴ-D` → `V-D`、`II -C` → `II-C`）。"""
    s = roman(s)
    s = re.sub(r"\s*[-－‐―]\s*", "-", s.strip())
    return s


_ASCII_END = re.compile(r"[A-Za-z0-9.,;:)\]]$")
_ASCII_START = re.compile(r"^[A-Za-z0-9(\[]")


def join_lines(raw: str | None) -> str:
    """セル内の改行（紙面の折り返し）をつなぐ。英数字どうしの境目だけ空白を入れる。"""
    if raw is None:
        return ""
    lines = [ln.strip() for ln in raw.split("\n")]
    lines = [ln for ln in lines if ln]
    out = ""
    for ln in lines:
        if out and _ASCII_END.search(out) and _ASCII_START.search(ln):
            out += " " + ln
        else:
            out += ln
    return out


_OPEN = "（(「『［[〔【"
_CLOSE = "）)」』］]〕】"


def split_items(s: str) -> list[str]:
    """読点で分割する。括弧の中の読点では分割しない。"""
    items, depth, cur = [], 0, ""
    for ch in s:
        if ch in _OPEN:
            depth += 1
        elif ch in _CLOSE and depth > 0:
            depth -= 1
        if ch == "、" and depth == 0:
            if cur.strip():
                items.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        items.append(cur.strip())
    return items
