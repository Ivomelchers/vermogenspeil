"""Gedeelde helpers om platform-fixtures te laden in tests en management commands."""

import json
from pathlib import Path


def fixtures_dir() -> Path:
    """backend/fixtures/ (één niveau boven apps/)."""
    return Path(__file__).resolve().parents[3] / "fixtures"


def load_text_fixture(platform: str, filename: str, *, encoding: str = "utf-8-sig") -> str:
    path = fixtures_dir() / platform / filename
    if not path.exists():
        raise FileNotFoundError(f"Fixture niet gevonden: {path}")
    return path.read_text(encoding=encoding)


def load_bytes_fixture(platform: str, filename: str) -> bytes:
    path = fixtures_dir() / platform / filename
    if not path.exists():
        raise FileNotFoundError(f"Fixture niet gevonden: {path}")
    return path.read_bytes()


def load_json_fixture(platform: str, filename: str):
    return json.loads(load_text_fixture(platform, filename, encoding="utf-8"))
