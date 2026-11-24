"""機械検査（設計 7.3、plan 5 節）。

各検査は (ok, 要約, 詳細の行) を返す。ok が None のときは SKIP（PDF がない環境）。
"""
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import jsonschema
from referencing import Registry, Resource

from . import yamlio
from .paths import BUILD, CONFIG, DATA, EXTENSIONS, ROOT, SCHEMA, TEXT, rel

PAGES = 234
EMAIL = "146819854+atsuki-seo@users.noreply.github.com"


@dataclass
class Result:
    name: str
    ok: bool | None
    summary: str
    details: list[str] = field(default_factory=list)


# ---------- 正本の読み込み ----------

def node_files() -> list[Path]:
    out = sorted(DATA.glob("*.yaml")) + sorted((DATA / "mccplus").glob("*.yaml"))
    special = {"errata.yaml", "verification-log.yaml", "unclassified.yaml"}
    return [p for p in out if p.name not in special]


def relation_files() -> list[Path]:
    return sorted((DATA / "relations").glob("*.yaml"))


def prose_files() -> list[Path]:
    return sorted(TEXT.rglob("*.md"))


def front_matter(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise ValueError(f"{rel(path)}: front matter がありません")
    import yaml

    return yaml.safe_load(m.group(1)), m.group(2)


def all_nodes() -> list[dict]:
    out = []
    for p in node_files():
        out.extend(yamlio.load(p)["nodes"])
    return out


def all_relations() -> list[dict]:
    out = []
    for p in relation_files():
        out.extend(yamlio.load(p)["relations"])
    return out


def unclassified() -> list[dict]:
    p = DATA / "unclassified.yaml"
    return (yamlio.load(p) or {}).get("tables", []) if p.exists() else []


def unresolved_entries() -> list[tuple[str, str]]:
    """未解決の参照と未分類の表。(キー, 説明) のリスト。キーは STATUS.md に載る文字列。"""
    out = []
    for r in all_relations():
        for i, t in enumerate(r["targets"]):
            if t["id"] is None:
                out.append((f"{r['id']}#{i}", t.get("reason", "")))
        for key in ("area", "content"):
            if r.get(key) is not None and r[key]["id"] is None:
                out.append((f"{r['id']}#{key}", r[key].get("reason", "")))
    for t in unclassified():
        out.append((t["id"], t["reason"]))
    return out


# ---------- 検査 ----------

def check_page_config() -> Result:
    """config/pages.yaml で、どの抽出器にも当たっていないページを出す（plan フェーズ 1）。"""
    cfg = yamlio.load(CONFIG / "pages.yaml")["pages"]
    missing = [p for p in range(1, PAGES + 1) if not (cfg.get(p) or {}).get("extractors")]
    extra = [p for p in cfg if not (1 <= int(p) <= PAGES)]
    ok = not missing and not extra
    details = [f"抽出器のないページ: {missing}"] if missing else []
    if extra:
        details.append(f"範囲外のページ: {extra}")
    return Result("page-config", ok, f"{PAGES - len(missing)}/{PAGES}", details)


def _registry() -> Registry:
    resources = []
    for p in SCHEMA.glob("*.schema.json"):
        s = json.loads(p.read_text(encoding="utf-8"))
        res = Resource.from_contents(s)
        resources.append((s["$id"], res))
        resources.append((p.name, res))
    return Registry().with_resources(resources)


def _validator(name: str) -> jsonschema.Draft202012Validator:
    schema = json.loads((SCHEMA / name).read_text(encoding="utf-8"))
    return jsonschema.Draft202012Validator(schema, registry=_registry())


def schema_targets() -> list[tuple[Path, str]]:
    targets = [(p, "nodes.schema.json") for p in node_files()]
    targets += [(p, "relations.schema.json") for p in relation_files()]
    for name, schema in (("errata.yaml", "errata.schema.json"), ("verification-log.yaml", "verification-log.schema.json"),
                         ("unclassified.yaml", "unclassified.schema.json")):
        if (DATA / name).exists():
            targets.append((DATA / name, schema))
    targets += [(p, "extension.schema.json") for p in sorted(EXTENSIONS.rglob("*.yaml"))]
    return targets


def check_schema() -> Result:
    details = []
    validators: dict[str, jsonschema.Draft202012Validator] = {}
    targets = schema_targets()
    for path, name in targets:
        v = validators.setdefault(name, _validator(name))
        for err in sorted(v.iter_errors(yamlio.load(path)), key=lambda e: list(e.path))[:5]:
            details.append(f"{rel(path)}: {'/'.join(map(str, err.path))}: {err.message[:200]}")
    pv = validators.setdefault("prose.schema.json", _validator("prose.schema.json"))
    prose = prose_files()
    for path in prose:
        try:
            fm, _ = front_matter(path)
        except ValueError as e:
            details.append(str(e))
            continue
        for err in pv.iter_errors(fm):
            details.append(f"{rel(path)}: {'/'.join(map(str, err.path))}: {err.message[:200]}")
    n = len(targets) + len(prose)
    return Result("schema", not details and n > 0, f"{n} files", details)
