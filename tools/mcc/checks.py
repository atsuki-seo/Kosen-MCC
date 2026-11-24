"""機械検査（設計 7.3、plan 5 節）。

各検査は (ok, 要約, 詳細の行) を返す。ok が None のときは SKIP（PDF がない環境）。
"""
from __future__ import annotations

import collections
import json
import re
import subprocess
import sys
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


# ---------- 原文の断片の取り出し（page-coverage、text-in-source で使う） ----------

def _pages(src: dict) -> list[int]:
    return src.get("pages_pdf") or [src["page_pdf"]]


def node_pieces(n: dict):
    """(レコード ID, ページ, 原文) を返す。"""
    pages = _pages(n["source"])
    if n["type"] == "goal":
        yield n["id"], pages, n["text"]
        if n.get("note"):
            yield n["id"], pages, n["note"]
        if n.get("supplement") and n["supplement"]["raw"]:
            yield n["id"], pages, n["supplement"]["raw"]
        return
    if n["type"] == "content":
        if n["name"]:
            yield n["id"], pages, n["name"]
        if n.get("note"):
            yield n["id"], pages, n["note"]
        if n.get("group"):
            yield n["id"], [n["group"]["page_pdf"]], n["group"]["raw"]
        return
    yield n["id"], pages, n["heading_raw"]
    if n.get("heading_raw_sub"):
        yield n["id"], pages, n["heading_raw_sub"]
    if n.get("chapter"):
        yield n["id"], [n["chapter"]["page_pdf"]], n["chapter"]["raw"]
    if n.get("description"):
        for line in n["description"]["lines"]:
            yield n["id"], n["description"]["pages_pdf"], line
    for note in n.get("notes", []):
        yield n["id"], [note["page"]], note["label"]
        yield n["id"], [note["page"]], note["text"]
    if n["type"] == "category" and n.get("level"):
        yield n["id"], [n["level"]["page_pdf"]], n["level"]["quote"]


def relation_pieces(r: dict):
    pages = _pages(r["source"])
    back = pages
    t = r["type"]
    if t == "composite-required":
        yield r["id"], back, r["area"]["raw"]
        yield r["id"], pages, r["text"]
        if r["consideration"]:
            yield r["id"], back if r.get("consideration_shared") else pages, r["consideration"]
    elif t == "mccplus-correspondence":
        yield r["id"], pages, r["raw"]
    elif t == "external-standard":
        for items in r["items"].values():
            for it in items:
                yield r["id"], pages, it["text"]
                if it.get("title"):
                    yield r["id"], pages, it["title"]
        for m in r["mcc_raw"]:
            yield r["id"], pages, m
    elif t == "curriculum-guideline":
        if r.get("content"):
            yield r["id"], back, r["content"]["raw"]
        if r.get("content_raw"):
            yield r["id"], back, r["content_raw"]
        if r["mcc_raw"]:
            yield r["id"], back if r["goals_shared"] else pages, r["mcc_raw"]
        if r["guideline_raw"]:
            yield r["id"], back if r["guideline_shared"] else pages, r["guideline_raw"]
        for tg in r["targets"]:
            yield r["id"], back, tg["raw"]
    elif t == "common-goal":
        yield r["id"], pages, r["note_raw"]


def prose_pieces(path: Path):
    fm, body = front_matter(path)
    pages = fm["pages_pdf"]
    if fm["kind"] == "figure":
        if fm.get("heading_raw"):
            yield fm["id"], pages, fm["heading_raw"]
        m = re.search(r"```text\n(.*?)\n```", body, re.S)
        if m:
            for line in m.group(1).split("\n"):
                yield fm["id"], pages, line
        return
    for block in re.split(r"\n\s*\n", body.strip()):
        block = block.strip()
        if not block or block.startswith(("![", "（図の書き起こし")):
            continue
        if block.startswith("```text"):
            for line in block.split("\n")[1:-1]:
                yield fm["id"], pages, line.lstrip("　")
        elif block.startswith("|"):
            for line in block.split("\n"):
                if re.fullmatch(r"\|(---\|)+", line):
                    continue
                for cell in re.split(r"(?<!\\)\|", line.strip("|")):
                    cell = cell.strip().replace("\\|", "|")
                    if cell:
                        yield fm["id"], pages, cell
        elif block.startswith(">"):
            for line in block.split("\n"):
                yield fm["id"], pages, line.lstrip("> ")
        elif block.startswith("#"):
            yield fm["id"], pages, block.lstrip("#").strip()
        else:
            yield fm["id"], pages, block


def all_pieces():
    for n in all_nodes():
        yield from node_pieces(n)
    for r in all_relations():
        yield from relation_pieces(r)
    for t in unclassified():
        for row in t["rows"]:
            for c in row:
                if c:
                    yield t["id"], _pages(t["source"]), c
    for p in prose_files():
        yield from prose_pieces(p)


# ---------- 検査（plan 5 節の 12 項目） ----------

def check_source_hash() -> Result:
    from . import pdfsrc

    if not pdfsrc.available():
        return Result("source-hash", None, "SKIP 原本の PDF がない")
    got, want = pdfsrc.sha256(), pdfsrc.meta()["sha256"]
    return Result("source-hash", got == want, "sha256 一致" if got == want else "sha256 不一致", [] if got == want else [f"expected {want}", f"actual   {got}"])


def covered_pages() -> dict[int, set[str]]:
    cov: dict[int, set[str]] = {}

    def add(pages, rid):
        for p in pages:
            cov.setdefault(p, set()).add(rid)

    for n in all_nodes():
        add(_pages(n["source"]), n["id"])
        if n.get("description"):
            add(n["description"]["pages_pdf"], n["id"])
    for r in all_relations():
        add(_pages(r["source"]), r["id"])
    for t in unclassified():
        add(_pages(t["source"]), t["id"])
    for path in prose_files():
        fm, _ = front_matter(path)
        add(fm["pages_pdf"], fm["id"])
    return cov


def check_page_coverage() -> Result:
    from . import pdfsrc

    if not pdfsrc.available():
        return Result("page-coverage", None, "SKIP 原本の PDF がない")
    n = pdfsrc.page_count()
    cov = covered_pages()
    missing = [p for p in range(1, n + 1) if p not in cov]
    return Result("page-coverage", not missing and n == PAGES, f"{n - len(missing)}/{n}",
                  [f"どのレコードにも散文ファイルにも対応しないページ: {missing}"] if missing else [])


def check_text_in_source() -> Result:
    from . import pdfsrc

    if not pdfsrc.available():
        return Result("text-in-source", None, "SKIP 原本の PDF がない")
    records: dict[str, bool] = {}
    details = []
    for rid, pages, text in all_pieces():
        ok = in_source(pdfsrc.squash(text), sorted(set(p for p in pages if 1 <= p <= PAGES)))
        records[rid] = records.get(rid, True) and ok
        if not ok and len(details) < 30:
            details.append(f"{rid} p{pages}: {text[:60]}")
    good = sum(records.values())
    return Result("text-in-source", good == len(records) and good > 0, f"{good}/{len(records)} records", details)


def in_source(sq: str, pages: list[int]) -> bool:
    """空白を除いた原文が、該当ページの抽出テキストに連続して含まれるか（設計 7.3）。

    抽出テキストは、ページの文字をストリーム順に並べたもの、行単位の抽出、表の列ごとの抽出の
    3 つの見方とし、どれか 1 つに連続して含まれれば一致とする（pdfsrc.views）。
    ページをまたぐ行は、ページごとに連続した 1 つの断片に分かれ、各断片がそのページの
    いずれかの見方に含まれ、ページの順に並ぶことを求める。
    """
    from . import pdfsrc

    if not sq:
        return True
    views = [pdfsrc.views(p) for p in pages]
    if any(sq in v for vs in views for v in vs):
        return True
    reach = {0}
    for vs in views:
        nxt = set(reach)
        for pos in reach:
            lo, hi = 0, len(sq) - pos
            while lo < hi:  # このページのいずれかの見方に含まれる、最長の続き
                mid = (lo + hi + 1) // 2
                if any(sq[pos:pos + mid] in v for v in vs):
                    lo = mid
                else:
                    hi = mid - 1
            nxt.update(range(pos + 1, pos + lo + 1))
        reach = nxt
        if len(sq) in reach:
            return True
    return False


def all_ids() -> list[str]:
    ids = [n["id"] for n in all_nodes()] + [r["id"] for r in all_relations()] + [t["id"] for t in unclassified()]
    for p in prose_files():
        ids.append(front_matter(p)[0]["id"])
    return ids


def check_id_unique() -> Result:
    ids = all_ids()
    dup = [i for i, c in collections.Counter(ids).items() if c > 1]
    return Result("id-unique", not dup and bool(ids), f"{len(ids)} ids", [f"重複: {d}" for d in dup[:20]])


def check_relations_target() -> Result:
    ids = set(all_ids())
    bad = []
    for r in all_relations():
        refs = [t["id"] for t in r["targets"]] + [r.get("from")]
        for key in ("area", "content"):
            if r.get(key):
                refs.append(r[key]["id"])
        bad += [f"{r['id']} → {x}" for x in refs if x is not None and x not in ids]
    for n in all_nodes():
        if n["parent"] is not None and n["parent"] not in ids:
            bad.append(f"{n['id']} の親 {n['parent']}")
    for e in (yamlio.load(DATA / "errata.yaml") or {}).get("entries", []) if (DATA / "errata.yaml").exists() else []:
        bad += [f"{e['id']} → {x}" for x in e.get("related_ids", []) if x not in ids]
    return Result("relations-target", not bad, f"未解決の指し先 {len(bad)}", bad[:20])


def check_unresolved_listed() -> Result:
    status = BUILD / "STATUS.md"
    entries = unresolved_entries()
    if not status.exists():
        return Result("unresolved-listed", False, "build/STATUS.md がない")
    text = status.read_text(encoding="utf-8")
    missing = [k for k, _ in entries if k not in text]
    return Result("unresolved-listed", not missing, f"未解決 {len(entries)} 件はすべて STATUS.md に記載" if not missing
                  else f"未記載 {len(missing)} 件", missing[:20])


def image_targets() -> dict[str, set[str]]:
    """設計 7.2 の画像照合の対象。種類 → レコード ID の集合。"""
    out: dict[str, set[str]] = {k: set() for k in ("page-top-row", "committee", "abet", "cdio", "unresolved", "figure")}
    for n in all_nodes():
        if n["source"].get("page_top"):
            out["page-top-row"].add(n["id"])
    for r in all_relations():
        if r["source"].get("page_top"):
            out["page-top-row"].add(r["id"])
        if r.get("standard") == "ABET-JABEE-IEA":
            out["abet"].add(r["id"])
        if r.get("standard") == "CDIO":
            out["cdio"].add(r["id"])
    for k, _ in unresolved_entries():
        out["unresolved"].add(k.split("#")[0])
    for p in prose_files():
        fm, _ = front_matter(p)
        if fm["kind"] == "figure":
            out["figure"].add(fm["id"])
        elif fm["title"] == "審議過程・委員名簿":
            out["committee"].add(fm["id"])
    return out


def check_image_verification() -> Result:
    targets = image_targets()
    log_path = DATA / "verification-log.yaml"
    log = (yamlio.load(log_path) or {}).get("entries", []) if log_path.exists() else []
    done: dict[str, set[str]] = {}
    for e in log:
        if e["result"] == "mismatch-open":
            continue
        done.setdefault(e["target"], set()).update(e["record_ids"])
    missing = []
    for kind, ids in targets.items():
        missing += [f"{kind}: {i}" for i in sorted(ids - done.get(kind, set()))]
    total = sum(len(v) for v in targets.values())
    return Result("image-verification", not missing and total > 0,
                  f"対象 {total} 件はすべて記録あり" if not missing else f"記録のない対象 {len(missing)}/{total} 件", missing[:20])


def check_build_up_to_date() -> Result:
    import shutil
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "build"
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "build.py"), "--out", str(out)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            return Result("build-up-to-date", False, "生成に失敗", r.stderr.splitlines()[-5:])
        diffs = []
        new = {p.relative_to(out).as_posix(): p for p in out.rglob("*") if p.is_file()}
        old = {p.relative_to(BUILD).as_posix(): p for p in BUILD.rglob("*") if p.is_file()} if BUILD.exists() else {}
        for k in sorted(set(new) | set(old)):
            if k not in new or k not in old or new[k].read_bytes() != old[k].read_bytes():
                diffs.append(f"build/{k}")
        shutil.rmtree(out, ignore_errors=True)
    return Result("build-up-to-date", not diffs, "" if not diffs else f"差分 {len(diffs)} ファイル", diffs[:20])


def check_rulesync() -> Result:
    cmd = rulesync_command() + ["generate", "--check"]
    try:
        import os

        env = {**os.environ, "npm_config_cache": str(ROOT / "work" / "npm-cache")}  # 手元の npm キャッシュの状態に左右されないため
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=300, env=env)
    except (OSError, subprocess.TimeoutExpired) as e:
        return Result("rulesync-check", False, f"実行できない: {e}")
    tail = (r.stdout + r.stderr).strip().splitlines()[-10:]
    return Result("rulesync-check", r.returncode == 0, "" if r.returncode == 0 else f"exit {r.returncode}", [] if r.returncode == 0 else tail)


def rulesync_command() -> list[str]:
    version = (ROOT / ".rulesync-version").read_text(encoding="utf-8").strip() if (ROOT / ".rulesync-version").exists() else "latest"
    return ["npx", "--yes", f"rulesync@{version}"]


ABS_PATH = re.compile(r"/Users/[A-Za-z0-9._-]+/")


def tracked_files() -> list[str]:
    r = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, text=True, check=True)
    return [f for f in r.stdout.split("\0") if f]


def check_no_absolute_path() -> Result:
    bad = []
    for f in tracked_files():
        p = ROOT / f
        if not p.is_file() or p.is_symlink():
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if ABS_PATH.search(line):
                bad.append(f"{f}:{i}")
    return Result("no-absolute-path", not bad, "" if not bad else f"{len(bad)} か所", bad[:20])


def check_commit_identity() -> Result:
    r = subprocess.run(["git", "log", "--format=%ae%n%ce"], cwd=ROOT, capture_output=True, text=True, check=True)
    emails = [e for e in r.stdout.splitlines() if e]
    other = sorted(set(emails) - {EMAIL})
    return Result("commit-identity", not other and bool(emails), f"{len(emails) // 2} commits",
                  [f"想定外のメールアドレスのコミットがある（{len(other)} 種類）"] if other else [])
