"""参照の解決器（設計 5.4）。

MCC 側の参照（コード、名称、再掲された到達目標の文）を、正本のノード ID に変換する。
- コードと名称の両方が書かれていれば両方で照合し、食い違う場合は解決しない
- 解決できない参照は捨てず、id を None にして理由を返す
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from .textnorm import ROMAN, join_lines, roman

RE_REF = re.compile(rf"^\s*({ROMAN}(?:\s*-\s*[A-I](?:\s*-\s*\d+)?)?)(?:\s*([^（(\s][^（(]*?))?\s*(?:[（(](.*)[）)])?\s*$")
RE_CODE_ONLY = re.compile(rf"^\s*({ROMAN}(?:\s*-\s*[A-I](?:\s*-\s*\d+)?)?)\s*$")


RE_STARTS_CODE = re.compile(rf"^\s*{ROMAN}(\s|-|$)")


def split_refs(text: str) -> list[str]:
    """参照の並びを分ける。括弧の外の改行・読点のうち、次がコードで始まるところだけで切る。"""
    parts, cur, depth = [], "", 0
    i = 0
    t = text
    while i < len(t):
        ch = t[i]
        if ch in "（(":
            depth += 1
        elif ch in "）)" and depth > 0:
            depth -= 1
        if ch in "\n、" and depth == 0 and RE_STARTS_CODE.match(roman(t[i + 1:i + 8])):
            if cur.strip():
                parts.append(cur.strip())
            cur = ""
        elif ch == "\n":
            pass
        else:
            cur += ch
        i += 1
    if cur.strip():
        parts.append(cur.strip())
    return parts


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
    def _name_matches(self, n: dict, name: str, paren: str | None) -> tuple[bool, bool]:
        """名称の照合。(一致したか, 括弧を名称として使ったか) を返す。

        受け付ける形:
        - ノードの名称そのもの（「Ⅳ-C 情報リテラシー」）
        - 親の名称：ノードの名称（「Ⅳ-B 工学基礎：技術者倫理」）
        - 親の名称（ノードの名称）（「Ⅳ-C 工学基礎（情報リテラシー）」）
        """
        own = norm_name(n["name"])
        if norm_name(name) == own:
            return True, False
        parent = self.by_id.get(n["parent"]) if n.get("parent") else None
        if parent is None:
            return False, False
        pname = norm_name(parent["name"])
        if "：" in name or ":" in name:
            a, b = re.split(r"[：:]", name, maxsplit=1)
            return norm_name(a) == pname and norm_name(b) == own, False
        if paren is not None and norm_name(name) == pname and norm_name(paren) == own:
            return True, True
        return False, False

    def ref(self, raw: str) -> list[Resolved]:
        """「Ⅳ 工学基礎（Ⅳ-C 情報リテラシー）」のような参照を解決する。複数の指し先になりうる。"""
        text = roman(join_lines(raw)).strip()
        if RE_CODE_ONLY.match(text):
            n = self.code(text)
            if n is None:
                return [Resolved(None, reason=f"コード {text} のノードがない")]
            return [Resolved(n["id"], "code-only")]
        m = RE_REF.match(text)
        if not m:
            return [Resolved(None, reason="コードで始まる参照の形ではない")]
        code_raw, name, paren = m.group(1), (m.group(2) or "").strip(), m.group(3)
        code_norm = re.sub(r"\s*-\s*", "-", code_raw)
        n = self.code(code_raw)
        if n is None:
            return [Resolved(None, reason=f"コード {code_norm} のノードがない")]
        out: list[Resolved] = []
        if name:
            ok, used_paren = self._name_matches(n, name, paren)
            if ok and used_paren:
                return [Resolved(n["id"], "code+parent-name+name")]
            if not ok:
                out.append(Resolved(None, reason=f"コード {code_norm} の名称は「{n['name']}」で、参照の名称「{name}」と食い違う"))
        method = "code+name" if name else "code-only"
        if not paren:
            return out or [Resolved(n["id"], "code+parent-name+name" if name and ("：" in name or ":" in name) else method)]
        inner = paren.strip()
        parts = split_refs(inner)
        if all(re.match(rf"^{ROMAN}\s*-", roman(p)) for p in parts):
            # 括弧内は下位の分野・領域の参照
            for part in parts:
                for r in self.ref(part):
                    if r.id and not (r.id + ":").startswith(n["id"]) and not r.id.startswith(n["id"] + "-"):
                        out.append(Resolved(None, reason=f"括弧内の {part} が {code_norm} の下にない"))
                    else:
                        out.append(r)
            return out
        if out:
            return out
        # 括弧内は学習内容の名称（読点区切り）
        names = [x.strip() for x in re.split(r"[、,]", inner) if x.strip()]
        contents = self.descendants(n["id"], "content")
        for nm in names:
            hits = [c for c in contents if norm_name(c["name"]) == norm_name(nm)]
            if len(hits) == 1:
                out.append(Resolved(hits[0]["id"], "content-name"))
            elif not hits:
                out.append(Resolved(None, reason=f"{code_norm} の下に学習内容「{nm}」がない"))
            else:
                out.append(Resolved(None, reason=f"{code_norm} の下に学習内容「{nm}」が {len(hits)} 件ある"))
        return out

    # ---- 再掲された到達目標の文 ----
    def goal_text(self, text: str, scope_id: str | None = None) -> Resolved:
        key = norm_text(text)
        hits = self.goal_by_text.get(key, [])
        if scope_id:
            scoped = [g for g in hits if any(g["id"].startswith(scope_id + c) for c in (":", "-", "."))]
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
