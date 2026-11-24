"""原本の PDF を取得し、SOURCE.yaml の SHA-256 と照合する。

使い方: uv run python source/fetch.py [--force]
既に取得済みでハッシュが一致すれば、再取得しない。
"""
from __future__ import annotations

import hashlib
import http.client
import sys
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
META = yaml.safe_load((ROOT / "source" / "SOURCE.yaml").read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(dest: Path, attempts: int = 5) -> None:
    """Content-Length まで取得する。途中で切れたら Range で続きから取り直す。"""
    print(f"downloading: {META['url']}")
    tmp = dest.with_suffix(".part")
    tmp.unlink(missing_ok=True)
    total = None
    for _ in range(attempts):
        have = tmp.stat().st_size if tmp.exists() else 0
        headers = {"User-Agent": "kosen-mcc-fetch"}
        if have:
            headers["Range"] = f"bytes={have}-"
        req = urllib.request.Request(META["url"], headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                if total is None:
                    total = int(r.headers["Content-Length"]) + have
                mode = "ab" if have and r.status == 206 else "wb"
                with tmp.open(mode) as f:
                    while chunk := r.read(1 << 16):
                        f.write(chunk)
        except (OSError, http.client.HTTPException) as e:
            print(f"  interrupted: {e!r}")
        size = tmp.stat().st_size if tmp.exists() else 0
        print(f"  received {size}/{total} bytes")
        if total is not None and size >= total:
            break
    tmp.replace(dest)


def main() -> int:
    dest = ROOT / META["local_path"]
    force = "--force" in sys.argv[1:]
    if dest.exists() and not force and sha256(dest) == META["sha256"]:
        print(f"already present: {META['local_path']}")
    else:
        download(dest)
    got = sha256(dest)
    size = dest.stat().st_size
    print(f"sha256 expected: {META['sha256']}")
    print(f"sha256 actual:   {got}")
    print(f"bytes expected: {META['bytes']}  actual: {size}")
    if got != META["sha256"]:
        print("MISMATCH: SHA-256 が SOURCE.yaml と一致しません", file=sys.stderr)
        return 1
    print("OK: sha256 一致")
    return 0


if __name__ == "__main__":
    sys.exit(main())
