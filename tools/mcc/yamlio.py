"""YAML の読み書き。出力の形を固定し、再生成で差分が出ないようにする。"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class _Dumper(yaml.SafeDumper):
    pass


def _str_representer(dumper: yaml.SafeDumper, data: str) -> yaml.Node:
    style = "|" if "\n" in data else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


_Dumper.add_representer(str, _str_representer)


def dump(data: Any) -> str:
    return yaml.dump(data, Dumper=_Dumper, allow_unicode=True, sort_keys=False, width=1000)


def write(path: Path, data: Any, header: str | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = dump(data)
    if header:
        text = "".join(f"# {line}\n" if line else "#\n" for line in header.splitlines()) + text
    path.write_text(text, encoding="utf-8")


def load(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))
