"""参照の解決器（設計 5.4）。

MCC 側の参照（コード、名称、再掲された到達目標の文）を、正本のノード ID に変換する。
- コードと名称の両方が書かれていれば両方で照合し、食い違う場合は解決しない
- 解決できない参照は捨てず、id を None にして理由を返す
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from .textnorm import ROMAN, roman

RE_REF = re.compile(rf"^\s*({ROMAN}(?:\s*-\s*[A-I](?:\s*-\s*\d+)?)?)(?:\s*([^（(\s][^（(]*?))?\s*(?:[（(](.*)[）)])?\s*$")
RE_CODE_ONLY = re.compile(rf"^\s*({ROMAN}(?:\s*-\s*[A-I](?:\s*-\s*\d+)?)?)\s*$")


def norm_name(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    return re.sub(r"\s+", "", s)


def norm_text(s: str) -> str:
    """到達目標の文の照合用。空白、句点、文頭の箇条記号を除く。"""
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"^[･・•●○◦\-－]\s*", "", s.strip())
    s = re.sub(r"\s+", "", s)
    return s.rstrip("。．.")


@dataclass
class Resolved:
    id: str | None
    method: str | None = None
    reason: str | None = None

    def target(self, raw: str) -> dict:
        t = {"raw": raw, "id": self.id}
        if self.id is None:
            t["reason"] = self.reason or "解決できない"
        else:
            t["method"] = self.method
        return t


class Resolver:
    def __init__(self, nodes: list[dict], prefix: str = "mcc2023"):
        self.nodes = [n for n in nodes if n["id"].startswith(prefix + ":")]
        self.by_id = {n["id"]: n for n in self.nodes}
        self.by_code = {n["code"]: n for n in self.nodes if "code" in n and n["type"] != "goal"}
        self.children: dict[str, list[dict]] = {}
        for n in self.nodes:
            if n["parent"]:
                self.children.setdefault(n["parent"], []).append(n)
        self.goals = [n for n in self.nodes if n["type"] == "goal"]
        self.goal_by_text: dict[str, list[dict]] = {}
        for g in self.goals:
            self.goal_by_text.setdefault(norm_text(g["text"]), []).append(g)

    def descendants(self, node_id: str, type_: str | None = None) -> list[dict]:
        out, stack = [], [node_id]
        while stack:
            for c in self.children.get(stack.pop(), []):
                if type_ is None or c["type"] == type_:
                    out.append(c)
                stack.append(c["id"])
        return out

    def code(self, raw_code: str) -> dict | None:
        c = re.sub(r"\s*-\s*", "-", roman(raw_code).strip())
        return self.by_code.get(c)

    # ---- コードと名称による参照 ----
    def ref(self, raw: str) -> list[Resolved]:
        """「Ⅳ 工学基礎（Ⅳ-C 情報リテラシー）」のような参照を解決する。複数の指し先になりうる。"""
        text = roman(raw).strip()
        if RE_CODE_ONLY.match(text):
            n = self.code(text)
            if n is None:
                return [Resolved(None, reason=f"コード {text} のノードがない")]
            return [Resolved(n["id"], "code-only")]
        m = RE_REF.match(text)
        if not m:
            return [Resolved(None, reason="コードで始まる参照の形ではない")]
        code_raw, name, paren = m.group(1), (m.group(2) or "").strip(), m.group(3)
        n = self.code(code_raw)
        if n is None:
            return [Resolved(None, reason=f"コード {code_raw} のノードがない")]
        if name and norm_name(name) != norm_name(n["name"]):
            return [Resolved(None, reason=f"コード {code_raw} の名称は「{n['name']}」で、参照の名称「{name}」と食い違う")]
        method = "code+name" if name else "code-only"
        if not paren:
            return [Resolved(n["id"], method)]
        inner = paren.strip()
        if RE_REF.match(roman(inner)) and re.match(rf"^{ROMAN}\s*-", roman(inner)):
            sub = self.ref(inner)
            out = []
            for r in sub:
                if r.id and not r.id.startswith(n["id"]):
                    out.append(Resolved(None, reason=f"括弧内の {inner} が {code_raw} の下にない"))
                else:
                    out.append(r)
            return out
        # 括弧内は学習内容の名称（読点区切り）
        names = [x.strip() for x in re.split(r"[、,]", inner) if x.strip()]
        contents = self.descendants(n["id"], "content")
        out = []
        for nm in names:
            hits = [c for c in contents if norm_name(c["name"]) == norm_name(nm)]
            if len(hits) == 1:
                out.append(Resolved(hits[0]["id"], "content-name"))
            elif not hits:
                out.append(Resolved(None, reason=f"{code_raw} の下に学習内容「{nm}」がない"))
            else:
                out.append(Resolved(None, reason=f"{code_raw} の下に学習内容「{nm}」が {len(hits)} 件ある"))
        return out

    # ---- 再掲された到達目標の文 ----
    def goal_text(self, text: str, scope_id: str | None = None) -> Resolved:
        key = norm_text(text)
        hits = self.goal_by_text.get(key, [])
        if scope_id:
            scoped = [g for g in hits if g["id"].startswith(scope_id + ":") or g["id"].startswith(scope_id + "-")]
            if len(scoped) == 1:
                return Resolved(scoped[0]["id"], "text-exact-in-scope")
            if len(scoped) > 1:
                return Resolved(None, reason=f"{scope_id} の中に同じ文の到達目標が {len(scoped)} 件ある")
            if hits:
                return Resolved(None, reason=f"同じ文の到達目標は {scope_id} の外にだけある（{', '.join(g['id'] for g in hits[:3])}）")
            return Resolved(None, reason=f"{scope_id} の中に同じ文の到達目標がない")
        if len(hits) == 1:
            return Resolved(hits[0]["id"], "text-exact")
        if hits:
            return Resolved(None, reason=f"同じ文の到達目標が {len(hits)} 件ある")
        return Resolved(None, reason="同じ文の到達目標がない")
