"""リポジトリ内のパス。"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_META = ROOT / "source" / "SOURCE.yaml"
CONFIG = ROOT / "config"
DATA = ROOT / "data" / "mcc2023"
TEXT = ROOT / "text" / "mcc2023"
BUILD = ROOT / "build"
SCHEMA = ROOT / "schema"
EXTENSIONS = ROOT / "extensions"
WORK = ROOT / "work"


def rel(path: Path) -> str:
    """リポジトリ相対のパス文字列（絶対パスを出力に残さないため）。"""
    return path.resolve().relative_to(ROOT).as_posix()
